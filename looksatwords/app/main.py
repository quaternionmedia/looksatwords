"""FastAPI application for conversation thread visualization."""

import json
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select

from .database import create_db_and_tables, get_session
from .models import (
    Conversation,
    ConversationCreate,
    ConversationListItem,
    ConversationResponse,
    ConversationWithAnalyticsResponse,
    AnalyticsResponse,
    AggregatedAnalytics,
    SentimentScore,
    WordFrequencyItem,
    SentimentTimelinePoint,
    ExtractedTopic,
    TopicsResponse,
)
from .collection_models import (
    Collection,
    CollectionCreate,
    CollectionUpdate,
    CollectionListItem,
    CollectionResponse,
    CollectionAnalyticsResponse,
    ComparisonResponse,
)
from .analytics_service import get_analytics_service
from .topic_service import get_topic_extractor
from .collection_service import get_collection_analytics_service
from .news_service import (
    get_news_service,
    NewsArticle,
    GatherRequest,
    GenerateRequest,
)
from .visualization_service import get_visualization_service, PlotResponse

# Import backend visualizer for analysis
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from frontend.visualizer_backend import ThreadVisualizerBackend

# Mount static files for frontend
FRONTEND_PATH = Path(__file__).parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (nothing to do)


app = FastAPI(
    title="Conversation Thread Visualizer API",
    description="API for analyzing and visualizing conversation threads",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Conversation Thread Visualizer API is running"}


@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the frontend."""
    index_path = FRONTEND_PATH / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>Conversation Thread Visualizer API</h1><p>Frontend not found. Visit <a href='/docs'>/docs</a> for API documentation.</p>")


@app.post("/api/conversations/analyze", response_model=ConversationResponse)
def analyze_conversation(
    request: ConversationCreate,
    session: Session = Depends(get_session)
):
    """Analyze a conversation and store results."""
    # Use backend visualizer for analysis
    visualizer = ThreadVisualizerBackend()
    visualizer.parseConversation(request.text)
    visualizer.identifyThreads()
    
    # Create title if not provided
    title = request.title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # Prepare thread data for storage
    threads_data = []
    for thread in visualizer.threads:
        threads_data.append({
            "name": thread["name"],
            "color": thread["color"],
            "points": thread["points"],
            "total_intensity": thread["totalIntensity"]
        })
    
    # Prepare tangent data for storage
    tangents_data = []
    for tangent in visualizer.tangents:
        tangents_data.append({
            "start_time": tangent["startTime"],
            "end_time": tangent["endTime"],
            "tangent_type": tangent["type"],
            "topics": tangent["topics"],
            "start_text": tangent["startText"],
            "resolution_text": tangent.get("resolutionText")
        })
    
    # Create conversation record
    conversation = Conversation(
        title=title,
        text=request.text,
        total_duration=visualizer.totalDuration,
        speakers=visualizer.speakers,
        threads=threads_data,
        tangents=tangents_data
    )
    
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    
    return ConversationResponse(
        conversation_id=conversation.id,
        title=conversation.title,
        total_duration=conversation.total_duration,
        speakers=conversation.speakers,
        threads=conversation.threads,
        tangents=conversation.tangents
    )


@app.get("/api/conversations", response_model=List[ConversationListItem])
def list_conversations(session: Session = Depends(get_session)):
    """List all stored conversations."""
    conversations = session.exec(select(Conversation)).all()
    
    return [
        ConversationListItem(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            total_duration=conv.total_duration,
            speaker_count=len(conv.speakers),
            thread_count=len(conv.threads),
            tangent_count=len(conv.tangents)
        )
        for conv in conversations
    ]


@app.get("/api/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific conversation by ID."""
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    session: Session = Depends(get_session)
):
    """Delete a conversation by ID."""
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    session.delete(conversation)
    session.commit()
    
    return {"status": "ok", "message": f"Conversation {conversation_id} deleted"}


@app.post("/api/extract-topics", response_model=TopicsResponse)
def extract_topics(request: ConversationCreate):
    """Extract topics dynamically from conversation text using NLTK.
    
    Uses noun phrase extraction, TF-IDF scoring, collocation detection,
    and named entity recognition to identify topics.
    """
    topic_extractor = get_topic_extractor()
    topics = topic_extractor.extract_topics(
        request.text,
        max_topics=8,
        min_occurrences=1
    )
    
    return TopicsResponse(
        topics=[
            ExtractedTopic(
                name=t["name"],
                keywords=t["keywords"],
                score=t["score"],
                normalized_score=t.get("normalized_score", 0),
                sources=t.get("sources", [])
            )
            for t in topics
        ],
        dynamic_extraction=True,
        topic_count=len(topics)
    )


@app.get("/api/conversations/{conversation_id}/analytics", response_model=AnalyticsResponse)
def get_conversation_analytics(
    conversation_id: int,
    session: Session = Depends(get_session)
):
    """Get detailed analytics for a conversation.
    
    Returns sentiment analysis, word frequency, POS distribution,
    and per-speaker analytics using NLTK.
    """
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Re-parse the conversation to get time points
    visualizer = ThreadVisualizerBackend(use_nltk=False)  # We'll use our own NLTK analysis
    time_points = visualizer.parseConversation(conversation.text)
    
    # Run analytics
    analytics_service = get_analytics_service()
    analytics = analytics_service.analyze_conversation(time_points)
    
    # Build response
    aggregated = analytics["aggregated"]
    
    return AnalyticsResponse(
        conversation_id=conversation_id,
        aggregated=AggregatedAnalytics.model_validate(aggregated),
        sentiment_timeline=[
            SentimentTimelinePoint(
                time=st["time"],
                compound=st["compound"],
                positive=st["positive"],
                negative=st["negative"],
                neutral=st["neutral"],
                speaker=st["speaker"],
            )
            for st in analytics["sentiment_timeline"]
        ],
        speaker_analytics=analytics["speaker_analytics"],
        nltk_available=analytics["nltk_available"],
    )


@app.post("/api/conversations/analyze-with-analytics", response_model=ConversationWithAnalyticsResponse)
def analyze_conversation_with_analytics(
    request: ConversationCreate,
    session: Session = Depends(get_session)
):
    """Analyze a conversation with full NLTK analytics included.
    
    This endpoint combines thread/tangent analysis with sentiment,
    word frequency, and grammar analytics in a single response.
    """
    # Use backend visualizer for thread analysis
    return _analyze_and_store(request.text, request.title, session)


def _analyze_and_store(
    text: str,
    title: Optional[str],
    session: Session,
    harness_source: Optional[str] = None,
    harness_thread_id: Optional[str] = None,
):
    """Parse, analyse and store one conversation, whatever produced its text.

    ONE PATH, TWO CALLERS. A person pasting into the box and the harness route
    pulling a thread reach exactly this function, so a conversation read off the
    archive is analysed by the same code, stored in the same table and appears
    in the same dashboard list as one typed by hand. A second copy of this would
    drift, and the drift would be invisible: both would still return a
    conversation.

    The harness caller passes the thread's address, and it is stored on the row
    so the topics route can find this reading again. The other caller has no
    address to give.
    """
    visualizer = ThreadVisualizerBackend(use_nltk=False)
    time_points = visualizer.parseConversation(text)
    visualizer.identifyThreads()
    
    # Run NLTK analytics
    analytics_service = get_analytics_service()
    analytics = analytics_service.analyze_conversation(time_points)

    # Create title if not provided
    title = title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # Prepare thread data for storage
    threads_data = []
    for thread in visualizer.threads:
        threads_data.append({
            "name": thread["name"],
            "color": thread["color"],
            "points": thread["points"],
            "total_intensity": thread["totalIntensity"]
        })
    
    # Prepare tangent data for storage
    tangents_data = []
    for tangent in visualizer.tangents:
        tangents_data.append({
            "start_time": tangent["startTime"],
            "end_time": tangent["endTime"],
            "tangent_type": tangent["type"],
            "topics": tangent["topics"],
            "start_text": tangent["startText"],
            "resolution_text": tangent.get("resolutionText")
        })
    
    # Create conversation record
    conversation = Conversation(
        title=title,
        text=text,
        total_duration=visualizer.totalDuration,
        speakers=visualizer.speakers,
        threads=threads_data,
        tangents=tangents_data,
        harness_source=harness_source,
        harness_thread_id=harness_thread_id,
    )

    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    # Build aggregated analytics response
    aggregated = analytics["aggregated"]
    
    return ConversationWithAnalyticsResponse(
        conversation_id=conversation.id,
        title=conversation.title,
        total_duration=conversation.total_duration,
        speakers=conversation.speakers,
        threads=conversation.threads,
        tangents=conversation.tangents,
        analytics=AggregatedAnalytics.model_validate(aggregated),
        sentiment_timeline=[
            SentimentTimelinePoint(
                time=st["time"],
                compound=st["compound"],
                positive=st["positive"],
                negative=st["negative"],
                neutral=st["neutral"],
                speaker=st["speaker"],
            )
            for st in analytics["sentiment_timeline"]
        ],
        speaker_analytics=analytics["speaker_analytics"],
    )


# ============ LLM Generation Endpoints ============

class GenerateConversationRequest(BaseModel):
    """Request model for generating conversations."""
    topic: Optional[str] = None
    num_speakers: int = 2
    num_messages: int = 8
    speaker_names: Optional[List[str]] = None


class GenerateConversationResponse(BaseModel):
    """Response model for generated conversations."""
    text: str
    topic: str
    speakers: List[str]


@app.post("/api/generate-conversation", response_model=GenerateConversationResponse)
def generate_conversation(request: GenerateConversationRequest):
    """Generate a sample conversation using the LLM.
    
    Uses the Ollama model named by LOOKSATWORDS_OLLAMA_MODEL to generate a realistic conversation
    on a given topic with specified speakers.
    """
    try:
        import ollama
        
        from looksatwords.llm import HOST, MODEL

        client = ollama.Client(host=HOST)
        
        # Default speaker names
        speakers = request.speaker_names or ["Alice", "Bob", "Carol", "Dave"][:request.num_speakers]
        speaker_list = ", ".join(speakers[:request.num_speakers])
        
        # Generate topic if not provided
        topic = request.topic
        if not topic:
            topic_response = client.chat(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "Generate a single interesting conversation topic in 3-5 words. Just the topic, nothing else."},
                    {"role": "user", "content": "Give me a random interesting topic for a conversation."}
                ]
            )
            topic = topic_response["message"]["content"].strip().strip('"')
        
        # Build the conversation generation prompt
        prompt = f"""Generate a realistic conversation between {speaker_list} about: {topic}

Requirements:
- Exactly {request.num_messages} messages
- Use this exact format for each line: [MM:SS] Speaker: message
- Start at [00:00] and increment by 15-45 seconds each message
- Make it natural with agreements, disagreements, questions, and tangents
- Each message should be 1-3 sentences
- Include some emotional moments (excitement, concern, humor)

Generate only the conversation, no explanations or headers."""

        response = client.chat(
            model=MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a conversation script writer. Generate realistic, natural dialogues. Output only the conversation in the exact format requested."
                },
                {"role": "user", "content": prompt}
            ]
        )
        
        conversation_text = response["message"]["content"].strip()
        
        return GenerateConversationResponse(
            text=conversation_text,
            topic=topic,
            speakers=speakers[:request.num_speakers]
        )
        
    except ImportError:
        raise HTTPException(
            status_code=503, 
            detail="Ollama package not installed. Install with: pip install ollama"
        )
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"LLM service unavailable: {str(e)}. Make sure Ollama is running."
        )


# ============ Database Export/Import Endpoints ============

@app.get("/api/database/export")
def export_database(session: Session = Depends(get_session)):
    """Export all conversations as JSON.
    
    Returns a JSON file containing all stored conversations
    that can be imported later.
    """
    conversations = session.exec(select(Conversation)).all()
    
    export_data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "conversations": [
            {
                "id": conv.id,
                "title": conv.title,
                "text": conv.text,
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "total_duration": conv.total_duration,
                "speakers": conv.speakers,
                "threads": conv.threads,
                "tangents": conv.tangents,
            }
            for conv in conversations
        ]
    }
    
    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f"attachment; filename=looksatwords_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )


class ImportDatabaseRequest(BaseModel):
    """Request model for importing database."""
    data: dict
    mode: str = "merge"  # "merge" or "replace"


@app.post("/api/database/import")
def import_database(
    request: ImportDatabaseRequest,
    session: Session = Depends(get_session)
):
    """Import conversations from JSON export.
    
    Modes:
    - merge: Add new conversations, skip existing IDs
    - replace: Clear all existing data and import fresh
    """
    data = request.data
    
    if "conversations" not in data:
        raise HTTPException(status_code=400, detail="Invalid export format: missing 'conversations' key")
    
    if request.mode == "replace":
        # Delete all existing conversations
        existing = session.exec(select(Conversation)).all()
        for conv in existing:
            session.delete(conv)
        session.commit()
    
    imported_count = 0
    skipped_count = 0
    
    for conv_data in data["conversations"]:
        # Check if conversation already exists (by ID or title+text hash)
        if request.mode == "merge":
            existing = session.exec(
                select(Conversation).where(
                    (Conversation.title == conv_data["title"]) & 
                    (Conversation.text == conv_data["text"])
                )
            ).first()
            if existing:
                skipped_count += 1
                continue
        
        # Create new conversation
        conversation = Conversation(
            title=conv_data["title"],
            text=conv_data["text"],
            total_duration=conv_data.get("total_duration", 0),
            speakers=conv_data.get("speakers", {}),
            threads=conv_data.get("threads", []),
            tangents=conv_data.get("tangents", []),
        )
        
        session.add(conversation)
        imported_count += 1
    
    session.commit()
    
    return {
        "status": "ok",
        "imported": imported_count,
        "skipped": skipped_count,
        "mode": request.mode
    }


# ============ Collection/Corpus Endpoints ============

@app.post("/api/collections", response_model=CollectionResponse)
def create_collection(
    request: CollectionCreate,
    session: Session = Depends(get_session)
):
    """Create a new collection for organizing conversations.
    
    Collections allow grouping conversations for corpus-level analysis.
    """
    collection = Collection(
        name=request.name,
        description=request.description,
        conversation_ids=request.conversation_ids or []
    )
    
    # Update stats if conversations provided
    if request.conversation_ids:
        _update_collection_stats(collection, session)
    
    session.add(collection)
    session.commit()
    session.refresh(collection)
    
    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
        conversation_count=collection.conversation_count,
        total_messages=collection.total_messages,
        total_words=collection.total_words,
        avg_sentiment_compound=collection.avg_sentiment_compound,
        conversation_ids=collection.conversation_ids
    )


@app.get("/api/collections", response_model=List[CollectionListItem])
def list_collections(session: Session = Depends(get_session)):
    """List all collections."""
    collections = session.exec(select(Collection)).all()
    
    return [
        CollectionListItem(
            id=coll.id,
            name=coll.name,
            description=coll.description,
            created_at=coll.created_at,
            updated_at=coll.updated_at,
            conversation_count=coll.conversation_count,
            total_messages=coll.total_messages,
            total_words=coll.total_words,
            avg_sentiment_compound=coll.avg_sentiment_compound
        )
        for coll in collections
    ]


@app.get("/api/collections/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific collection by ID."""
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
        conversation_count=collection.conversation_count,
        total_messages=collection.total_messages,
        total_words=collection.total_words,
        avg_sentiment_compound=collection.avg_sentiment_compound,
        conversation_ids=collection.conversation_ids
    )


@app.put("/api/collections/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: int,
    request: CollectionUpdate,
    session: Session = Depends(get_session)
):
    """Update a collection's name, description, or conversation list."""
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    if request.name is not None:
        collection.name = request.name
    if request.description is not None:
        collection.description = request.description
    if request.conversation_ids is not None:
        collection.conversation_ids = request.conversation_ids
        _update_collection_stats(collection, session)
    
    collection.updated_at = datetime.now(UTC)
    
    session.add(collection)
    session.commit()
    session.refresh(collection)
    
    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
        conversation_count=collection.conversation_count,
        total_messages=collection.total_messages,
        total_words=collection.total_words,
        avg_sentiment_compound=collection.avg_sentiment_compound,
        conversation_ids=collection.conversation_ids
    )


@app.delete("/api/collections/{collection_id}")
def delete_collection(
    collection_id: int,
    session: Session = Depends(get_session)
):
    """Delete a collection (does not delete conversations)."""
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    session.delete(collection)
    session.commit()
    
    return {"status": "ok", "message": f"Collection {collection_id} deleted"}


@app.post("/api/collections/{collection_id}/conversations/{conversation_id}")
def add_conversation_to_collection(
    collection_id: int,
    conversation_id: int,
    session: Session = Depends(get_session)
):
    """Add a conversation to a collection."""
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conversation_id not in collection.conversation_ids:
        collection.conversation_ids = collection.conversation_ids + [conversation_id]
        _update_collection_stats(collection, session)
        collection.updated_at = datetime.now(UTC)
        session.add(collection)
        session.commit()
    
    return {"status": "ok", "message": f"Conversation {conversation_id} added to collection {collection_id}"}


@app.delete("/api/collections/{collection_id}/conversations/{conversation_id}")
def remove_conversation_from_collection(
    collection_id: int,
    conversation_id: int,
    session: Session = Depends(get_session)
):
    """Remove a conversation from a collection."""
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    if conversation_id in collection.conversation_ids:
        collection.conversation_ids = [
            cid for cid in collection.conversation_ids if cid != conversation_id
        ]
        _update_collection_stats(collection, session)
        collection.updated_at = datetime.now(UTC)
        session.add(collection)
        session.commit()
    
    return {"status": "ok", "message": f"Conversation {conversation_id} removed from collection {collection_id}"}


@app.get("/api/collections/{collection_id}/analytics", response_model=CollectionAnalyticsResponse)
def get_collection_analytics(
    collection_id: int,
    session: Session = Depends(get_session)
):
    """Get aggregated analytics for all conversations in a collection.
    
    Returns corpus-level analysis including:
    - Aggregated sentiment across all conversations
    - Combined word frequency
    - Speaker statistics across corpus
    - Conversation summaries for comparison
    """
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Fetch all conversations in collection
    conversations = []
    time_points_list = []
    
    for conv_id in collection.conversation_ids:
        conv = session.get(Conversation, conv_id)
        if conv:
            conversations.append(conv)
            # Parse time points for analytics
            visualizer = ThreadVisualizerBackend(use_nltk=False)
            time_points = visualizer.parseConversation(conv.text)
            time_points_list.append(time_points)
    
    # Run collection analytics
    analytics_service = get_collection_analytics_service()
    analytics = analytics_service.aggregate_conversations(conversations, time_points_list)
    
    # Extract common topics
    common_topics = analytics_service.extract_common_topics(conversations)
    
    return CollectionAnalyticsResponse(
        collection_id=collection_id,
        collection_name=collection.name,
        conversation_count=analytics['conversation_count'],
        total_messages=analytics['total_messages'],
        total_words=analytics['total_words'],
        average_words_per_message=analytics['average_words_per_message'],
        avg_sentiment=analytics['avg_sentiment'],
        overall_sentiment=analytics['overall_sentiment'],
        sentiment_distribution=analytics['sentiment_distribution'],
        word_frequency=analytics['word_frequency'],
        pos_distribution=analytics['pos_distribution'],
        unique_speakers=analytics['unique_speakers'],
        speaker_stats=analytics['speaker_stats'],
        conversation_summaries=analytics['conversation_summaries'],
        common_topics=common_topics
    )


@app.get("/api/collections/{collection_id}/compare", response_model=ComparisonResponse)
def compare_collection_conversations(
    collection_id: int,
    session: Session = Depends(get_session)
):
    """Compare all conversations within a collection.
    
    Returns detailed comparison including:
    - Sentiment comparison across conversations
    - Verbosity comparison
    - Speaker overlap analysis
    - Common words across conversations
    """
    collection = session.get(Collection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Fetch all conversations
    conversations = []
    time_points_list = []
    
    for conv_id in collection.conversation_ids:
        conv = session.get(Conversation, conv_id)
        if conv:
            conversations.append(conv)
            visualizer = ThreadVisualizerBackend(use_nltk=False)
            time_points = visualizer.parseConversation(conv.text)
            time_points_list.append(time_points)
    
    # Run comparison
    analytics_service = get_collection_analytics_service()
    comparison = analytics_service.compare_conversations(conversations, time_points_list)
    
    return ComparisonResponse(
        collection_id=collection_id,
        conversations=[{
            'id': c['id'],
            'title': c['title'],
            'analytics_summary': {
                'messages': c['analytics']['aggregated']['total_messages'],
                'words': c['analytics']['aggregated']['total_words'],
                'sentiment': c['analytics']['aggregated']['overall_sentiment'],
                'compound': c['analytics']['aggregated']['average_sentiment']['compound']
            }
        } for c in comparison['conversations']],
        sentiment_comparison=comparison['sentiment_comparison'],
        verbosity_comparison=comparison['verbosity_comparison'],
        speaker_overlap=comparison['speaker_overlap'],
        common_words=comparison['common_words']
    )


def _update_collection_stats(collection: Collection, session: Session):
    """Update cached statistics for a collection."""
    total_messages = 0
    total_words = 0
    sentiment_sum = 0.0
    valid_count = 0
    
    analytics_service = get_analytics_service()
    
    for conv_id in collection.conversation_ids:
        conv = session.get(Conversation, conv_id)
        if conv:
            visualizer = ThreadVisualizerBackend(use_nltk=False)
            time_points = visualizer.parseConversation(conv.text)
            analytics = analytics_service.analyze_conversation(time_points)
            
            agg = analytics['aggregated']
            total_messages += agg['total_messages']
            total_words += agg['total_words']
            sentiment_sum += agg['average_sentiment']['compound']
            valid_count += 1
    
    collection.conversation_count = len(collection.conversation_ids)
    collection.total_messages = total_messages
    collection.total_words = total_words
    collection.avg_sentiment_compound = sentiment_sum / valid_count if valid_count > 0 else 0.0


# ============ News Gathering & Generation Endpoints ============

class NewsAnalyticsResponse(BaseModel):
    """Response model for news with analytics."""
    articles: List[NewsArticle]
    analytics: Optional[dict] = None


@app.get("/api/news/status")
def news_service_status():
    """Check availability of news-related services."""
    news_service = get_news_service()
    viz_service = get_visualization_service()
    
    return {
        "gnews_available": news_service.gnews_available,
        "llm_available": news_service.llm_available,
        "matplotlib_available": viz_service.matplotlib_available,
        "wordcloud_available": viz_service.wordcloud_available,
        "bokeh_available": viz_service.bokeh_available
    }


@app.post("/api/news/gather", response_model=NewsAnalyticsResponse)
def gather_news(request: GatherRequest):
    """Gather news articles from GNews API.
    
    Fetches real news articles based on keyword, topic, location, or site.
    Valid topics: WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SPORTS, SCIENCE, HEALTH
    """
    news_service = get_news_service()
    
    try:
        articles = news_service.gather_news(request)
        
        # Run analytics on gathered articles
        analytics = None
        if articles:
            analytics = news_service.analyze_articles(articles)
        
        return NewsAnalyticsResponse(
            articles=articles,
            analytics=analytics
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/news/generate", response_model=NewsAnalyticsResponse)
def generate_news(request: GenerateRequest):
    """Generate synthetic news articles using LLM.
    
    Uses the Ollama model named by LOOKSATWORDS_OLLAMA_MODEL to create realistic news headlines and descriptions
    based on a seed word or topic.
    """
    news_service = get_news_service()
    
    try:
        articles = news_service.generate_news(request)
        
        # Run analytics on generated articles
        analytics = None
        if articles:
            analytics = news_service.analyze_articles(articles)
        
        return NewsAnalyticsResponse(
            articles=articles,
            analytics=analytics
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/news/analyze")
def analyze_news_articles(articles: List[NewsArticle]):
    """Analyze a list of news articles.
    
    Performs sentiment analysis, word frequency, and POS tagging
    on provided news articles.
    """
    news_service = get_news_service()
    return news_service.analyze_articles(articles)


# ============ Visualization Endpoints ============

class WordCloudRequest(BaseModel):
    """Request for generating a word cloud."""
    words: List[str]
    width: int = 800
    height: int = 400
    background_color: str = "#1a1a2e"


class WordFrequencyChartRequest(BaseModel):
    """Request for generating a word frequency chart."""
    word_frequency: List[dict]  # [{word: str, count: int}]
    top_n: int = 20
    title: str = "Word Frequency"


class SentimentChartRequest(BaseModel):
    """Request for generating a sentiment chart."""
    sentiment_data: List[dict]  # [{time, compound, positive, negative, neutral}]
    title: str = "Sentiment Analysis"


class POSChartRequest(BaseModel):
    """Request for generating a POS pie chart."""
    pos_distribution: dict
    title: str = "Parts of Speech"


class SpeakerChartRequest(BaseModel):
    """Request for generating a speaker comparison chart."""
    speaker_analytics: dict
    title: str = "Speaker Comparison"


@app.post("/api/visualize/word-cloud", response_model=PlotResponse)
def generate_word_cloud(request: WordCloudRequest):
    """Generate a word cloud visualization.
    
    Creates a word cloud image from a list of words.
    Words can have duplicates to indicate frequency.
    """
    viz_service = get_visualization_service()
    return viz_service.generate_word_cloud(
        words=request.words,
        width=request.width,
        height=request.height,
        background_color=request.background_color
    )


@app.post("/api/visualize/word-frequency", response_model=PlotResponse)
def generate_word_frequency_chart(request: WordFrequencyChartRequest):
    """Generate a horizontal bar chart of word frequencies."""
    viz_service = get_visualization_service()
    return viz_service.generate_word_frequency_chart(
        word_frequency=request.word_frequency,
        top_n=request.top_n,
        title=request.title
    )


@app.post("/api/visualize/sentiment", response_model=PlotResponse)
def generate_sentiment_chart(request: SentimentChartRequest):
    """Generate a sentiment timeline/scatter chart."""
    viz_service = get_visualization_service()
    return viz_service.generate_sentiment_chart(
        sentiment_data=request.sentiment_data,
        title=request.title
    )


@app.post("/api/visualize/pos", response_model=PlotResponse)
def generate_pos_chart(request: POSChartRequest):
    """Generate a POS distribution pie chart."""
    viz_service = get_visualization_service()
    return viz_service.generate_pos_pie_chart(
        pos_distribution=request.pos_distribution,
        title=request.title
    )


@app.post("/api/visualize/speakers", response_model=PlotResponse)
def generate_speaker_chart(request: SpeakerChartRequest):
    """Generate a speaker comparison bar chart."""
    viz_service = get_visualization_service()
    return viz_service.generate_speaker_comparison_chart(
        speaker_analytics=request.speaker_analytics,
        title=request.title
    )


@app.get("/api/conversations/{conversation_id}/visualizations")
def get_conversation_visualizations(
    conversation_id: int,
    session: Session = Depends(get_session)
):
    """Generate all visualizations for a conversation.
    
    Returns word cloud, word frequency, sentiment, POS, and speaker charts
    as base64 encoded images.
    """
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get analytics
    visualizer = ThreadVisualizerBackend(use_nltk=False)
    time_points = visualizer.parseConversation(conversation.text)
    analytics_service = get_analytics_service()
    analytics = analytics_service.analyze_conversation(time_points)
    
    viz_service = get_visualization_service()
    visualizations = {}
    
    # Word cloud from all text
    all_words = []
    for tp in time_points:
        all_words.extend(tp.get('text', '').lower().split())
    if all_words:
        visualizations['word_cloud'] = viz_service.generate_word_cloud(all_words)
    
    # Word frequency chart
    word_freq = analytics['aggregated'].get('word_frequency', [])
    if word_freq:
        visualizations['word_frequency'] = viz_service.generate_word_frequency_chart(word_freq)
    
    # Sentiment chart
    sentiment_timeline = analytics.get('sentiment_timeline', [])
    if sentiment_timeline:
        visualizations['sentiment'] = viz_service.generate_sentiment_chart(sentiment_timeline)
    
    # POS chart
    pos_dist = analytics['aggregated'].get('pos_distribution', {})
    if pos_dist:
        visualizations['pos'] = viz_service.generate_pos_pie_chart(pos_dist)
    
    # Speaker comparison
    speaker_analytics = analytics.get('speaker_analytics', {})
    if speaker_analytics:
        visualizations['speakers'] = viz_service.generate_speaker_comparison_chart(speaker_analytics)
    
    return {
        "conversation_id": conversation_id,
        "visualizations": {k: v.model_dump() for k, v in visualizations.items()}
    }


# ============ Harness Seam ============
#
# READ-ONLY, AND NOTHING HERE IMPORTS qmcp. `looksatwords/harness.py` carries
# the reasoning; the short version is that the archive is somebody else's
# record with one author, and this is a reader. Every call below is a GET
# against loopback.
#
# WHY THESE EXIST. Because the answer to "what can this project do" was "paste
# a conversation into a box", which is a person doing by hand what the harness
# already holds hundreds of.


class HarnessStatusOut(BaseModel):
    """Whether the archive answered, and what it said.

    `reachable` is first because it is the field that decides how to read the
    rest. `threads_indexed` is None when nobody answered -- never 0, which is a
    real count the harness is entitled to report.
    """
    reachable: bool
    base_url: str
    reason: Optional[str] = None
    fix: Optional[str] = None
    generated_at: Optional[str] = None
    threads_indexed: Optional[int] = None
    note: Optional[str] = None


@app.get("/api/harness/status", response_model=HarnessStatusOut)
def harness_status():
    """Is the thread archive answering, and what does it hold."""
    from looksatwords import harness

    a = harness.index()
    if not a.reachable:
        return HarnessStatusOut(
            reachable=False,
            base_url=harness.base_url(),
            reason=a.reason,
            fix=a.fix,
        )
    return HarnessStatusOut(
        reachable=True,
        base_url=harness.base_url(),
        generated_at=a.generated_at,
        threads_indexed=a.totals.get("threads"),
        note=(
            "These figures are the harness's own, as of generated_at, and count "
            "conversations that were exported and indexed rather than conversations "
            "that exist."
        ),
    )


class HarnessThreadOut(BaseModel):
    source: str
    id: str
    title: str
    turns: int
    address: Optional[str] = None
    last_seen: Optional[str] = None


class HarnessThreadsOut(BaseModel):
    reachable: bool
    reason: Optional[str] = None
    fix: Optional[str] = None
    total_indexed: Optional[int] = None
    listed: int = 0
    threads: List[HarnessThreadOut] = []


@app.get("/api/harness/threads", response_model=HarnessThreadsOut)
def harness_threads(
    limit: int = 50,
    source: Optional[str] = None,
    min_turns: int = 2,
):
    """The archive's index, largest threads first.

    `listed` and `total_indexed` are both returned and are different numbers
    whenever a filter or the limit bites. Returning only the rows would let a
    reader take the length of the list for the size of the archive.
    """
    from looksatwords import harness

    a = harness.index()
    if not a.reachable:
        return HarnessThreadsOut(reachable=False, reason=a.reason, fix=a.fix)

    rows = [x for x in a.threads if x.get("turns", 0) >= min_turns]
    if source:
        rows = [x for x in rows if x.get("source") == source]
    rows.sort(key=lambda x: x.get("turns", 0), reverse=True)

    return HarnessThreadsOut(
        reachable=True,
        total_indexed=a.totals.get("threads"),
        listed=len(rows[:limit]),
        threads=[
            HarnessThreadOut(
                source=x.get("source", ""),
                id=x.get("id", ""),
                title=x.get("title") or "(untitled)",
                turns=x.get("turns", 0),
                address=x.get("address"),
                last_seen=x.get("last_seen"),
            )
            for x in rows[:limit]
        ],
    )


class HarnessIngestOut(ConversationWithAnalyticsResponse):
    """An analysed thread, plus what reading it off the archive cost.

    `conversion` is not decoration. Turn text is collapsed to one line and long
    threads are cut at a limit, and both are invisible in the numbers above it.

    `text` is the converted transcript, returned so the panel can put on screen
    exactly what was analysed. A visualisation beside an editable box holding
    something else is how somebody edits one conversation and analyses another.
    """
    conversion: dict
    text: str


@app.post("/api/harness/threads/{source}/{thread_id}/analyze",
          response_model=HarnessIngestOut)
def harness_analyze_thread(
    source: str,
    thread_id: str,
    limit: int = 400,
    session: Session = Depends(get_session),
):
    """Pull one thread from the archive and run it through the analysis.

    THE HARNESS IS NOT TOLD ANYTHING. This reads, converts and stores locally;
    no result travels back. The archive stays one record with one author.
    """
    from looksatwords import harness

    fetched = harness.thread(source, thread_id)
    if fetched.thread is None:
        # 409 when the archive answered and disagrees with its own index; 503
        # when nobody answered. Both were 502 and read as one problem.
        raise HTTPException(
            status_code=409 if fetched.answered else 503,
            detail=f"{fetched.reason} {fetched.fix}",
        )
    t = fetched.thread

    text, report = harness.as_conversation(t, limit=limit)
    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail=(
                f"{source}/{thread_id} has {report['turns_total']} turn(s) and no "
                "readable text in any of them. This is an empty thread, not an "
                "unreachable archive."
            ),
        )

    title = t.title or f"{source}/{thread_id[:8]}"
    result = _analyze_and_store(
        text, f"[harness] {title}", session,
        harness_source=source, harness_thread_id=thread_id,
    )
    return HarnessIngestOut(**result.model_dump(), conversion=report, text=text)


@app.get("/api/harness/threads/{source}/{thread_id}/deltas")
def harness_thread_deltas(source: str, thread_id: str):
    """What the harness says this thread settled.

    THE HARNESS'S OWN ANSWER, RENDERED RATHER THAN RECOMPUTED. This project
    could derive its own opinion of what a conversation decided from the same
    turns, and that would be a second record with a second author. qmcp owns
    this one; the panel shows it.
    """
    from looksatwords import harness

    d = harness.deltas(source, thread_id)
    if d is None:
        a = harness.index()
        raise HTTPException(
            status_code=502 if a.reachable else 503,
            detail=(
                f"The harness did not produce deltas for {source}/{thread_id}."
                if a.reachable
                else f"{a.reason} {a.fix}"
            ),
        )
    return d


class HarnessThreadRef(BaseModel):
    """The thread as the archive knows it, or why nobody could ask.

    `reachable` first, as everywhere on this seam. `indexed` is None when
    nobody answered -- never False, which is the archive's own claim that it
    has no such thread.
    """
    reachable: bool
    base_url: str
    reason: Optional[str] = None
    fix: Optional[str] = None
    indexed: Optional[bool] = None
    title: Optional[str] = None
    address: Optional[str] = None
    turns: Optional[int] = None


class TopicSpan(BaseModel):
    """One run of mentions with a rest, or the end, on either side."""
    start: float
    end: float
    mentions: int
    speakers: List[str]


class TopicLane(BaseModel):
    """One topic as the picture draws it: a lane, its notes, and its rests."""
    label: str
    color: str
    mentions: int
    speakers: dict
    carried_by: Optional[str] = None
    spans: List[TopicSpan]
    rests: int
    dropped: bool
    returned_to: bool


class TangentOut(BaseModel):
    """Where the conversation went off, and whether it came back."""
    start: Optional[float] = None
    end: Optional[float] = None
    type: str
    topics: List[str] = []
    start_text: str = ""
    resolution_text: Optional[str] = None


class HarnessTopicsOut(BaseModel):
    """The topics document for one archived thread.

    Two answers, kept apart: `harness` is what the archive said about the
    thread just now, and everything after `analysed` is this project's stored
    reading of it. Either can be missing without the other, and the shape says
    which. `analysed` False comes with the route that changes it.
    """
    source: str
    thread_id: str
    harness: HarnessThreadRef
    analysed: bool
    reason: Optional[str] = None
    fix: Optional[str] = None
    conversation_id: Optional[int] = None
    title: Optional[str] = None
    analysed_at: Optional[str] = None
    total_duration: Optional[float] = None
    beat: Optional[float] = None
    rest_gap: Optional[float] = None
    speakers: dict = {}
    topics: List[TopicLane] = []
    tangents: List[TangentOut] = []


@app.get("/api/harness/threads/{source}/{thread_id}/topics",
         response_model=HarnessTopicsOut)
def harness_thread_topics(
    source: str,
    thread_id: str,
    session: Session = Depends(get_session),
):
    """This project's reading of one archived thread, shaped for a graph to draw.

    A GET THAT DOES NOT WRITE. The reading is looked up by the address the
    analyse route stored, and the newest one wins when a thread was analysed
    more than once. A thread with no reading here is answered 200 with
    `analysed` False and the route that would produce one, because analysing
    on a GET would store a row nobody asked for. A reading stored before the
    address was recorded on the row is not found either, and the remedy is the
    same call. `looksatwords/app/topics_document.py` carries the shaping.
    """
    from looksatwords import harness
    from . import topics_document

    a = harness.index()
    if not a.reachable:
        ref = HarnessThreadRef(
            reachable=False, base_url=harness.base_url(), reason=a.reason, fix=a.fix,
        )
    else:
        row = next(
            (x for x in a.threads
             if x.get("source") == source and x.get("id") == thread_id),
            None,
        )
        ref = HarnessThreadRef(
            reachable=True,
            base_url=harness.base_url(),
            indexed=row is not None,
            title=row.get("title") if row else None,
            address=row.get("address") if row else None,
            turns=row.get("turns") if row else None,
        )

    conversation = session.exec(
        select(Conversation)
        .where(Conversation.harness_source == source)
        .where(Conversation.harness_thread_id == thread_id)
        .order_by(Conversation.id.desc())
    ).first()

    if conversation is None:
        return HarnessTopicsOut(
            source=source,
            thread_id=thread_id,
            harness=ref,
            analysed=False,
            reason=f"{source}/{thread_id} has not been analysed here.",
            fix=(
                f"POST /api/harness/threads/{source}/{thread_id}/analyze reads it "
                "off the archive and stores the reading; then ask again."
            ),
        )

    doc = topics_document.document(
        conversation.threads or [], conversation.tangents or [],
        conversation.total_duration,
    )
    return HarnessTopicsOut(
        source=source,
        thread_id=thread_id,
        harness=ref,
        analysed=True,
        conversation_id=conversation.id,
        title=conversation.title,
        analysed_at=conversation.created_at.isoformat() if conversation.created_at else None,
        speakers=conversation.speakers or {},
        **doc,
    )


@app.get("/api/harness/neighbours")
def harness_neighbours():
    """The sibling services, and whether either answered just now.

    A LINK, NOT AN INTEGRATION. This reports reachability and nothing else.
    Neither service is imported, neither is a dependency, and nothing here
    invents what they would have said if they were running.
    """
    from looksatwords import harness

    return {"neighbours": harness.neighbours()}


# Mount static files for frontend assets (css/, js/, etc.)
# This must come AFTER API routes so it doesn't override them
if FRONTEND_PATH.exists():
    # Mount subdirectories for CSS and JS
    css_path = FRONTEND_PATH / "css"
    js_path = FRONTEND_PATH / "js"
    if css_path.exists():
        app.mount("/css", StaticFiles(directory=str(css_path)), name="css")
    if js_path.exists():
        app.mount("/js", StaticFiles(directory=str(js_path)), name="js")
    # Mount root-level static files (visualizer.js, visualizer.html, etc.)
    app.mount("/", StaticFiles(directory=str(FRONTEND_PATH), html=True), name="frontend")
