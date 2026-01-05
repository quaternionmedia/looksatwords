"""Analytics service for conversation analysis.

This module bridges the NLTK-based Analyzer from the core analytics engine
with the conversation timeline visualization frontend. It adapts the news-focused
analyzer to work with conversation text, providing sentiment analysis, word
frequency, and grammar metrics over time.
"""

from collections import Counter
from typing import Any, Dict, List, Optional

from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag

# Initialize NLTK components
try:
    _sia = SentimentIntensityAnalyzer()
    _lemmatizer = WordNetLemmatizer()
    _stop_words = set(stopwords.words("english"))
    NLTK_AVAILABLE = True
except Exception:
    _sia = None
    _lemmatizer = None
    _stop_words = set()
    NLTK_AVAILABLE = False


# POS tag groupings (from analyzer.py)
POS_GROUPS = {
    "noun": ["NN", "NNS", "NNP", "NNPS"],
    "verb": ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"],
    "adjective": ["JJ", "JJR", "JJS"],
    "adverb": ["RB", "RBR", "RBS"],
    "pronoun": ["PRP", "PRP$", "WP", "WP$"],
    "conjunction": ["CC"],
    "preposition": ["IN"],
    "interjection": ["UH"],
}


class ConversationAnalyticsService:
    """Service for analyzing conversation text with NLTK.
    
    Provides:
    - Sentiment analysis per message and aggregated
    - Word frequency analysis
    - Part-of-speech (grammar) analysis
    - Metrics over time for timeline visualization
    """
    
    def __init__(self):
        """Initialize the analytics service."""
        self.sia = _sia
        self.lemmatizer = _lemmatizer
        self.stop_words = _stop_words
        
    def analyze_conversation(self, time_points: List[Dict]) -> Dict[str, Any]:
        """Perform full analytics on parsed conversation time points.
        
        Args:
            time_points: List of parsed time points from ThreadVisualizerBackend
                Each point has: time, text, originalLine, speaker, speakerInfo
                
        Returns:
            Dictionary containing all analytics results
        """
        if not time_points:
            return self._empty_analytics()
        
        # Collect speaker names to exclude from word frequency
        speaker_names = set()
        for point in time_points:
            speaker = point.get("speaker", "")
            if speaker:
                # Add full name and individual parts (first/last names)
                speaker_names.add(speaker.lower())
                for part in speaker.lower().split():
                    speaker_names.add(part)
            
        # Analyze each time point
        analyzed_points = []
        all_words = []
        all_pos_tags = []
        
        for point in time_points:
            # Use 'text' (message content only) not 'originalLine' (includes speaker name)
            text = point.get("text", point.get("originalLine", ""))
            analysis = self.analyze_text(text, exclude_words=speaker_names)
            
            analyzed_points.append({
                "time": point.get("time", 0),
                "speaker": point.get("speaker", "Unknown"),
                "text": text,
                "sentiment": analysis["sentiment"],
                "word_count": analysis["word_count"],
                "pos_counts": analysis["pos_counts"],
            })
            
            all_words.extend(analysis["words"])
            all_pos_tags.extend(analysis["pos_tags"])
        
        # Aggregate analytics
        aggregated = self._aggregate_analytics(analyzed_points, all_words, all_pos_tags)
        
        # Compute sentiment timeline
        sentiment_timeline = self._compute_sentiment_timeline(analyzed_points)
        
        # Compute speaker analytics
        speaker_analytics = self._compute_speaker_analytics(analyzed_points)
        
        return {
            "points": analyzed_points,
            "aggregated": aggregated,
            "sentiment_timeline": sentiment_timeline,
            "speaker_analytics": speaker_analytics,
            "nltk_available": NLTK_AVAILABLE,
        }
    
    def analyze_text(self, text: str, exclude_words: Optional[set] = None) -> Dict[str, Any]:
        """Analyze a single text string.
        
        Args:
            text: Text to analyze
            exclude_words: Optional set of words to exclude from word frequency
                          (e.g., speaker names)
            
        Returns:
            Dictionary with sentiment, word count, POS counts, etc.
        """
        if not text or not NLTK_AVAILABLE:
            return {
                "sentiment": {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0},
                "word_count": 0,
                "words": [],
                "pos_tags": [],
                "pos_counts": {k: 0 for k in POS_GROUPS.keys()},
            }
        
        # Combine stopwords with any excluded words (like speaker names)
        words_to_exclude = self.stop_words
        if exclude_words:
            words_to_exclude = self.stop_words | exclude_words
        
        # Sentiment analysis
        sentiment = self.sia.polarity_scores(text)
        
        # Tokenize and clean
        tokens = word_tokenize(text.lower())
        words = [w for w in tokens if w.isalpha() and w not in words_to_exclude]
        
        # Lemmatize
        lemmatized = [self.lemmatizer.lemmatize(w) for w in words]
        
        # POS tagging
        pos_tags = pos_tag(tokens)
        
        # Count POS groups
        pos_counts = {group: 0 for group in POS_GROUPS.keys()}
        for word, tag in pos_tags:
            for group, tags in POS_GROUPS.items():
                if tag in tags:
                    pos_counts[group] += 1
                    break
        
        return {
            "sentiment": sentiment,
            "word_count": len(words),
            "words": lemmatized,
            "pos_tags": pos_tags,
            "pos_counts": pos_counts,
        }
    
    def _aggregate_analytics(
        self, 
        points: List[Dict], 
        all_words: List[str],
        all_pos_tags: List
    ) -> Dict[str, Any]:
        """Aggregate analytics across all points.
        
        Args:
            points: Analyzed time points
            all_words: All collected words (lemmatized, no stopwords)
            all_pos_tags: All POS tags
            
        Returns:
            Aggregated analytics dictionary
        """
        if not points:
            return self._empty_aggregated()
            
        # Aggregate sentiment
        avg_sentiment = {
            "neg": sum(p["sentiment"]["neg"] for p in points) / len(points),
            "neu": sum(p["sentiment"]["neu"] for p in points) / len(points),
            "pos": sum(p["sentiment"]["pos"] for p in points) / len(points),
            "compound": sum(p["sentiment"]["compound"] for p in points) / len(points),
        }
        
        # Word frequency (top 20)
        word_freq = Counter(all_words).most_common(20)
        
        # Total POS counts
        total_pos = {group: 0 for group in POS_GROUPS.keys()}
        for point in points:
            for group, count in point["pos_counts"].items():
                total_pos[group] += count
        
        # Total word count
        total_words = sum(p["word_count"] for p in points)
        
        # Sentiment classification
        compound = avg_sentiment["compound"]
        if compound >= 0.05:
            overall_sentiment = "positive"
        elif compound <= -0.05:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        return {
            "total_messages": len(points),
            "total_words": total_words,
            "average_words_per_message": total_words / len(points) if points else 0,
            "average_sentiment": avg_sentiment,
            "overall_sentiment": overall_sentiment,
            "word_frequency": [{"word": w, "count": c} for w, c in word_freq],
            "pos_distribution": total_pos,
        }
    
    def _compute_sentiment_timeline(self, points: List[Dict]) -> List[Dict]:
        """Compute sentiment values over time for visualization.
        
        Args:
            points: Analyzed time points
            
        Returns:
            List of sentiment data points for timeline chart
        """
        return [
            {
                "time": p["time"],
                "compound": p["sentiment"]["compound"],
                "positive": p["sentiment"]["pos"],
                "negative": p["sentiment"]["neg"],
                "neutral": p["sentiment"]["neu"],
                "speaker": p["speaker"],
            }
            for p in points
        ]
    
    def _compute_speaker_analytics(self, points: List[Dict]) -> Dict[str, Dict]:
        """Compute per-speaker analytics.
        
        Args:
            points: Analyzed time points
            
        Returns:
            Dictionary of speaker name -> analytics
        """
        speaker_data: Dict[str, List[Dict]] = {}
        
        for point in points:
            speaker = point["speaker"]
            if speaker not in speaker_data:
                speaker_data[speaker] = []
            speaker_data[speaker].append(point)
        
        result = {}
        for speaker, speaker_points in speaker_data.items():
            total_words = sum(p["word_count"] for p in speaker_points)
            avg_sentiment = sum(p["sentiment"]["compound"] for p in speaker_points) / len(speaker_points)
            
            result[speaker] = {
                "message_count": len(speaker_points),
                "total_words": total_words,
                "average_words_per_message": total_words / len(speaker_points),
                "average_sentiment": avg_sentiment,
                "sentiment_label": self._sentiment_label(avg_sentiment),
            }
        
        return result
    
    def _sentiment_label(self, compound: float) -> str:
        """Convert compound sentiment score to label."""
        if compound >= 0.05:
            return "positive"
        elif compound <= -0.05:
            return "negative"
        return "neutral"
    
    def _empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure."""
        return {
            "points": [],
            "aggregated": self._empty_aggregated(),
            "sentiment_timeline": [],
            "speaker_analytics": {},
            "nltk_available": NLTK_AVAILABLE,
        }
    
    def _empty_aggregated(self) -> Dict[str, Any]:
        """Return empty aggregated analytics structure."""
        return {
            "total_messages": 0,
            "total_words": 0,
            "average_words_per_message": 0,
            "average_sentiment": {"neg": 0.0, "neu": 0.0, "pos": 0.0, "compound": 0.0},
            "overall_sentiment": "neutral",
            "word_frequency": [],
            "pos_distribution": {k: 0 for k in POS_GROUPS.keys()},
        }


# Singleton instance for reuse
_analytics_service: Optional[ConversationAnalyticsService] = None


def get_analytics_service() -> ConversationAnalyticsService:
    """Get or create the analytics service singleton."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = ConversationAnalyticsService()
    return _analytics_service
