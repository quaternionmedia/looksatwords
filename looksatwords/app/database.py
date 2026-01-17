"""Database configuration and session management."""

from pathlib import Path
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

# Database file location
DATABASE_PATH = Path(__file__).parent.parent.parent / "looksatwords.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)


def create_db_and_tables():
    """Create database tables."""
    # Import models to register them with SQLModel
    from .models import Conversation  # noqa: F401
    from .collection_models import Collection  # noqa: F401
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    with Session(engine) as session:
        yield session
