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


def create_db_and_tables(bind=None) -> list[str]:
    """Create the tables, and add any column a model has grown since the file was made.

    Returns the columns added, as `table.column`, so a caller can say what
    happened to somebody's database rather than that it was "migrated".

    **`create_all` MAKES MISSING TABLES AND LEAVES EXISTING ONES ALONE.** A
    model that gains a column after a database exists is a query that fails
    on every row of that database, and the operator's `looksatwords.db` is
    exactly such a file. There is no migration tool in this repository, so the
    one shape of change the models have needed -- a nullable column added --
    is handled here, with SQLite's `ALTER TABLE ... ADD COLUMN`.

    WHAT THIS CANNOT DO. Rename, drop, retype or constrain a column, or add
    one that is NOT NULL without a default. Any of those raises rather than
    guessing at the data, because a guess here rewrites somebody's record.
    """
    # Import models to register them with SQLModel
    from .models import Conversation  # noqa: F401
    from .collection_models import Collection  # noqa: F401

    bind = bind if bind is not None else engine
    SQLModel.metadata.create_all(bind)
    return _add_missing_columns(bind)


def _add_missing_columns(bind, metadata=None) -> list[str]:
    """Every nullable column a model declares and its table does not yet have."""
    from sqlalchemy import inspect, text

    metadata = metadata if metadata is not None else SQLModel.metadata
    inspector = inspect(bind)
    present = set(inspector.get_table_names())
    added = []
    for table in metadata.sorted_tables:
        if table.name not in present:
            continue
        have = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in have:
                continue
            if column.primary_key or not column.nullable:
                raise RuntimeError(
                    f"{table.name}.{column.name} is missing from the database and is "
                    "not a nullable column, which is the only kind added here. This "
                    "needs a migration written by a person."
                )
            ddl = (
                f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" '
                f"{column.type.compile(dialect=bind.dialect)}"
            )
            with bind.begin() as conn:
                conn.execute(text(ddl))
            added.append(f"{table.name}.{column.name}")
    return added


def get_session() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    with Session(engine) as session:
        yield session
