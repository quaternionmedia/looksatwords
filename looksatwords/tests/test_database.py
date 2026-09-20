"""A database made before a model grew a column still opens.

`SQLModel.metadata.create_all` creates missing tables and leaves existing ones
as they are, so a column added to `Conversation` is a query that fails on every
row of a file written before it. The operator's `looksatwords.db` is such a
file, and there is no migration tool in this repository. `create_db_and_tables`
adds the nullable columns itself, and this is the test that it does.

MUTATED ON 2026-09-20 AND SEEN RED. With the column adder skipped, the older
file kept its shape and the test named both missing columns. Restored, passes.
"""

import pytest
from sqlalchemy import inspect, text
from sqlmodel import Session, create_engine, select

from looksatwords.app.database import create_db_and_tables
from looksatwords.app.models import Conversation


def _old_conversation_table(engine):
    """The `conversation` table as a file written before the harness columns had it."""
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE conversation ("
            " id INTEGER NOT NULL PRIMARY KEY, title VARCHAR NOT NULL,"
            " text VARCHAR NOT NULL, total_duration FLOAT NOT NULL,"
            " created_at DATETIME NOT NULL, speakers JSON, threads JSON, tangents JSON)"
        ))
        conn.execute(text(
            "INSERT INTO conversation (title, text, total_duration, created_at,"
            " speakers, threads, tangents) VALUES ('old', 'A: hi', 0.0,"
            " '2026-01-01 00:00:00', '{}', '[]', '[]')"
        ))


def test_an_older_file_gains_the_columns_and_keeps_its_rows(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    _old_conversation_table(engine)
    before = {c["name"] for c in inspect(engine).get_columns("conversation")}
    assert "harness_source" not in before, "the fixture table is not old enough to test with"

    added = create_db_and_tables(engine)

    assert set(added) >= {"conversation.harness_source", "conversation.harness_thread_id"}
    with Session(engine) as session:
        row = session.exec(select(Conversation)).one()
    assert row.title == "old"
    assert row.harness_source is None and row.harness_thread_id is None


def test_a_current_file_is_left_alone(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'new.db'}")
    assert create_db_and_tables(engine) == [], "a fresh file has nothing to add"
    assert create_db_and_tables(engine) == [], "and asking twice adds nothing twice"


def test_a_column_that_is_not_nullable_is_refused_rather_than_guessed(tmp_path):
    """Only a nullable column can be added without inventing a value for old rows."""
    from sqlalchemy import Column, Integer, MetaData, Table

    from looksatwords.app import database

    engine = create_engine(f"sqlite:///{tmp_path / 'strict.db'}")
    _old_conversation_table(engine)

    # A stand-in metadata whose `conversation` demands a NOT NULL column the
    # file lacks, so the refusal is exercised without changing the real model.
    strict = MetaData()
    Table("conversation", strict,
          Column("id", Integer, primary_key=True),
          Column("must_exist", Integer, nullable=False))
    with pytest.raises(RuntimeError, match="must_exist"):
        database._add_missing_columns(engine, strict)
