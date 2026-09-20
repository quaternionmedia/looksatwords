"""Database configuration and session management."""

import os
from pathlib import Path
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

# WHICH DATABASE, AND WHY IT IS A SETTING.
#
# The default is this repository's own `looksatwords.db`, which is what a person
# running `looksatwords serve` wants. `LOOKSATWORDS_DB` moves it, and the reason
# is that anything demonstrating the tool -- a screenshot run, a walkthrough, an
# assistant showing what the analysis does -- writes conversations into whatever
# database the process is pointed at. Without this the only database available
# was the operator's, and demo rows landed beside real ones with nothing to tell
# them apart.
DEFAULT_DATABASE_PATH = Path(__file__).parent.parent.parent / "looksatwords.db"
DATABASE_PATH = Path(os.environ.get("LOOKSATWORDS_DB", DEFAULT_DATABASE_PATH))
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
