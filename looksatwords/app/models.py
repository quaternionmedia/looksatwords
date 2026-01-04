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
