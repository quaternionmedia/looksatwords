"""News gathering and generation service for the web API."""

from typing import List, Optional
from datetime import datetime
from pandas import DataFrame, concat
from pydantic import BaseModel


class NewsArticle(BaseModel):
    """A news article."""
    headline: str
    description: Optional[str] = None
    url: Optional[str] = None
    published_date: Optional[str] = None
    publisher: Optional[str] = None
    source_type: str = "gathered"  # "gathered" or "generated"


class GatherRequest(BaseModel):
    """Request for gathering news."""
    keyword: Optional[str] = None
    topic: Optional[str] = None  # WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SPORTS, SCIENCE, HEALTH
    location: Optional[str] = None
    site: Optional[str] = None
    top: bool = False
    max_results: int = 5


class GenerateRequest(BaseModel):
    """Request for generating news."""
    seed_word: str
    count: int = 3


VALID_TOPICS = [
    "WORLD", "NATION", "BUSINESS", "TECHNOLOGY",
    "ENTERTAINMENT", "SPORTS", "SCIENCE", "HEALTH"
]


class NewsService:
    """Service for gathering and generating news articles."""
    
    def __init__(self, max_results: int = 10):
        self.max_results = max_results
        self._gnews = None
        self._ollama = None
    
    @property
    def gnews_available(self) -> bool:
        """Check if GNews is available."""
        try:
            from gnews import GNews
            return True
        except ImportError:
            return False
    
    @property
    def llm_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            import ollama
            client = ollama.Client(host="http://localhost:11434")
            client.list()  # Test connection
            return True
        except:
            return False
    
    def _get_gnews(self, max_results: int = None):
        """Get or create GNews instance."""
        if self._gnews is None:
            from gnews import GNews
            self._gnews = GNews(max_results=max_results or self.max_results)
        else:
            self._gnews.max_results = max_results or self.max_results
        return self._gnews
    
    def gather_news(self, request: GatherRequest) -> List[NewsArticle]:
        """Gather news articles from GNews API.
        
        Args:
            request: GatherRequest with search parameters
            
        Returns:
            List of NewsArticle objects
        """
        if not self.gnews_available:
            raise RuntimeError("GNews package not installed. Install with: pip install gnews")
        
        gnews = self._get_gnews(request.max_results)
        articles = []
        
        # Gather based on parameters
        if request.keyword:
            results = gnews.get_news(request.keyword)
            articles.extend(results)
        
        if request.topic:
            topic_upper = request.topic.upper()
            if topic_upper not in VALID_TOPICS:
                raise ValueError(f"Invalid topic '{request.topic}'. Valid topics: {', '.join(VALID_TOPICS)}")
            results = gnews.get_news_by_topic(topic_upper)
            articles.extend(results)
        
        if request.location:
            results = gnews.get_news_by_location(request.location)
            articles.extend(results)
        
        if request.site:
            results = gnews.get_news_by_site(request.site)
            articles.extend(results)
        
        if request.top:
            results = gnews.get_top_news()
            articles.extend(results)
        
        # If no parameters specified, get top news
        if not any([request.keyword, request.topic, request.location, request.site, request.top]):
            results = gnews.get_top_news()
            articles.extend(results)
        
        # Convert to NewsArticle objects
        news_articles = []
        seen_titles = set()  # Deduplicate
        
        for article in articles[:request.max_results]:
            title = article.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                news_articles.append(NewsArticle(
                    headline=title,
                    description=article.get('description'),
                    url=article.get('url'),
                    published_date=article.get('published date'),
                    publisher=article.get('publisher', {}).get('title') if isinstance(article.get('publisher'), dict) else str(article.get('publisher', '')),
                    source_type="gathered"
                ))
        
        return news_articles
    
    def generate_news(self, request: GenerateRequest) -> List[NewsArticle]:
        """Generate synthetic news articles using LLM.
        
        Args:
            request: GenerateRequest with seed word and count
            
        Returns:
            List of generated NewsArticle objects
        """
        if not self.llm_available:
            raise RuntimeError("Ollama not available. Make sure Ollama is running at localhost:11434")
        
        import ollama
        client = ollama.Client(host="http://localhost:11434")
        
        articles = []
        
        for i in range(request.count):
            # Generate headline
            headline_response = client.chat(
                model="llama3.1",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a journalist writing news headlines. Generate only the headline, no explanation. Include subtle perspectives but keep it professional."
                    },
                    {
                        "role": "user",
                        "content": f"Generate a single news headline about: {request.seed_word}"
                    }
                ]
            )
            headline = headline_response["message"]["content"].strip().strip('"')
            
            # Generate description
            desc_response = client.chat(
                model="llama3.1",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a journalist writing news article summaries. Generate a brief 2-3 sentence description, no explanation."
                    },
                    {
                        "role": "user",
                        "content": f"Write a brief news description for this headline: {headline}"
                    }
                ]
            )
            description = desc_response["message"]["content"].strip()
            
            articles.append(NewsArticle(
                headline=headline,
                description=description,
                url=None,
                published_date=datetime.now().isoformat(),
                publisher="LLM Generated",
                source_type="generated"
            ))
        
        return articles
    
    def analyze_articles(self, articles: List[NewsArticle]) -> dict:
        """Analyze a list of news articles using NLTK.
        
        Args:
            articles: List of NewsArticle objects
            
        Returns:
            Analytics dictionary with sentiment, word frequency, etc.
        """
        from .analytics_service import get_analytics_service
        
        # Build time points format from articles
        time_points = []
        for i, article in enumerate(articles):
            time_points.append({
                "time": i,
                "speaker": article.publisher or "Unknown",
                "text": f"{article.headline}. {article.description or ''}"
            })
        
        analytics_service = get_analytics_service()
        return analytics_service.analyze_conversation(time_points)


# Singleton instance
_news_service = None


def get_news_service() -> NewsService:
    """Get or create the news service singleton."""
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service
