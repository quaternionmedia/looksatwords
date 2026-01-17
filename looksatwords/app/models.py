"""SQLModel database models for conversation analysis."""

from datetime import datetime, UTC
from typing import List, Optional

from sqlmodel import Field, SQLModel, JSON, Column


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class ConversationBase(SQLModel):
    """Base conversation model."""
    title: str
    text: str
    total_duration: float = 0.0


class Conversation(ConversationBase, table=True):
    """Stored conversation with analysis results."""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utc_now)
    speakers: dict = Field(default_factory=dict, sa_column=Column(JSON))
    threads: List[dict] = Field(default_factory=list, sa_column=Column(JSON))
    tangents: List[dict] = Field(default_factory=list, sa_column=Column(JSON))


class ConversationCreate(SQLModel):
    """Request model for creating a conversation."""
    text: str
    title: Optional[str] = None


class ConversationResponse(SQLModel):
    """Response model for conversation analysis."""
    conversation_id: int
    title: str
    total_duration: float
    speakers: dict
    threads: List[dict]
    tangents: List[dict]


class ConversationListItem(SQLModel):
    """Response model for conversation list."""
    id: int
    title: str
    created_at: datetime
    total_duration: float
    speaker_count: int
    thread_count: int
    tangent_count: int


class SentimentScore(SQLModel):
    """Sentiment score model."""
    neg: float = 0.0
    neu: float = 0.0
    pos: float = 0.0
    compound: float = 0.0


class WordFrequencyItem(SQLModel):
    """Word frequency item."""
    word: str
    count: int


class SentimentTimelinePoint(SQLModel):
    """Sentiment data point for timeline visualization."""
    time: float
    compound: float
    positive: float
    negative: float
    neutral: float
    speaker: str


class SpeakerAnalytics(SQLModel):
    """Analytics for a single speaker."""
    message_count: int
    total_words: int
    average_words_per_message: float
    average_sentiment: float
    sentiment_label: str


class AggregatedAnalytics(SQLModel):
    """Aggregated analytics for a conversation."""
    total_messages: int
    total_words: int
    average_words_per_message: float
    average_sentiment: SentimentScore
    overall_sentiment: str
    word_frequency: List[WordFrequencyItem]
    pos_distribution: dict


class AnalyticsResponse(SQLModel):
    """Response model for conversation analytics."""
    conversation_id: int
    aggregated: AggregatedAnalytics
    sentiment_timeline: List[SentimentTimelinePoint]
    speaker_analytics: dict
    nltk_available: bool


class ConversationWithAnalyticsResponse(ConversationResponse):
    """Response model for conversation with analytics included."""
    analytics: Optional[AggregatedAnalytics] = None
    sentiment_timeline: Optional[List[SentimentTimelinePoint]] = None
    speaker_analytics: Optional[dict] = None


class ExtractedTopic(SQLModel):
    """Dynamically extracted topic."""
    name: str
    keywords: List[str]
    score: float
    normalized_score: float
    sources: List[str]


class TopicsResponse(SQLModel):
    """Response model for topic extraction."""
    topics: List[ExtractedTopic]
    dynamic_extraction: bool
    topic_count: int
