"""SQLModel database models for corpus collections."""

from datetime import datetime, UTC
from typing import List, Optional

from sqlmodel import Field, SQLModel, JSON, Column, Relationship


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class CollectionBase(SQLModel):
    """Base collection model."""
    name: str
    description: Optional[str] = None


class Collection(CollectionBase, table=True):
    """A collection of conversations for corpus analysis."""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    
    # Aggregated stats (cached for performance)
    conversation_count: int = 0
    total_messages: int = 0
    total_words: int = 0
    avg_sentiment_compound: float = 0.0
    
    # Store conversation IDs as JSON array (lightweight many-to-many)
    conversation_ids: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Cached aggregated analytics
    word_frequency_cache: List[dict] = Field(default_factory=list, sa_column=Column(JSON))
    pos_distribution_cache: dict = Field(default_factory=dict, sa_column=Column(JSON))
    speaker_stats_cache: dict = Field(default_factory=dict, sa_column=Column(JSON))


class CollectionCreate(SQLModel):
    """Request model for creating a collection."""
    name: str
    description: Optional[str] = None
    conversation_ids: Optional[List[int]] = None


class CollectionUpdate(SQLModel):
    """Request model for updating a collection."""
    name: Optional[str] = None
    description: Optional[str] = None
    conversation_ids: Optional[List[int]] = None


class CollectionListItem(SQLModel):
    """Response model for collection list."""
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    conversation_count: int
    total_messages: int
    total_words: int
    avg_sentiment_compound: float


class CollectionResponse(CollectionBase):
    """Full response model for a collection."""
    id: int
    created_at: datetime
    updated_at: datetime
    conversation_count: int
    total_messages: int
    total_words: int
    avg_sentiment_compound: float
    conversation_ids: List[int]


class CollectionAnalyticsResponse(SQLModel):
    """Response model for collection-wide analytics."""
    collection_id: int
    collection_name: str
    conversation_count: int
    
    # Aggregated metrics
    total_messages: int
    total_words: int
    average_words_per_message: float
    
    # Sentiment analytics
    avg_sentiment: dict  # {neg, neu, pos, compound}
    overall_sentiment: str  # positive, negative, neutral
    sentiment_distribution: dict  # {positive: count, negative: count, neutral: count}
    
    # Word frequency across corpus
    word_frequency: List[dict]  # [{word, count}]
    
    # POS distribution
    pos_distribution: dict
    
    # Speaker analytics across corpus
    unique_speakers: int
    speaker_stats: dict  # {speaker: {message_count, total_words, avg_sentiment}}
    
    # Conversation comparison data
    conversation_summaries: List[dict]  # [{id, title, sentiment, words, messages}]
    
    # Topic analysis
    common_topics: List[dict]  # [{topic, count, percentage}]


class ComparisonResponse(SQLModel):
    """Response model for comparing conversations in a collection."""
    collection_id: int
    conversations: List[dict]  # Full comparison data for each conversation
    
    # Comparative metrics
    sentiment_comparison: List[dict]  # [{id, title, compound, label}]
    verbosity_comparison: List[dict]  # [{id, title, words_per_message}]
    speaker_overlap: dict  # {speaker: [conv_ids]}
    common_words: List[dict]  # Words appearing in multiple conversations
