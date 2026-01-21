from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable

from sqlalchemy import text
from sqlmodel import Session

from .db_utils import column_exists


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    apply: Callable[[Session], None]


def _create_schema_migrations_table(session: Session) -> None:
    session.exec(
        text(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version INTEGER PRIMARY KEY, "
            "name TEXT NOT NULL, "
            "applied_at TEXT NOT NULL)"
        )
    )


def _applied_versions(session: Session) -> set[int]:
    rows = session.exec(text("SELECT version FROM schema_migrations"))
    return {row[0] for row in rows}


def _record_migration(session: Session, migration: Migration) -> None:
    applied_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    statement = text(
        "INSERT INTO schema_migrations (version, name, applied_at) "
        "VALUES (:version, :name, :applied_at)"
    ).bindparams(
        version=migration.version,
        name=migration.name,
        applied_at=applied_at,
    )
    session.exec(statement)


def _migrations() -> Iterable[Migration]:
    return [
        Migration(
            version=1,
            name="add_run_topic_exclude",
            apply=lambda session: _add_column(
                session, "run", "topic_exclude", "TEXT"
            ),
        ),
        Migration(
            version=2,
            name="add_run_use_assessment_seeds",
            apply=lambda session: _add_column(
                session, "run", "use_assessment_seeds", "BOOLEAN DEFAULT 0"
            ),
        ),
        Migration(
            version=3,
            name="add_run_literature_query_id",
            apply=lambda session: _add_column(
                session, "run", "literature_query_id", "INTEGER"
            ),
        ),
        Migration(
            version=4,
            name="add_literaturequery_include_non_article",
            apply=lambda session: _add_column(
                session, "literaturequery", "include_non_article", "BOOLEAN DEFAULT 0"
            ),
        ),
        Migration(
            version=5,
            name="add_literaturework_work_type",
            apply=lambda session: _add_column(
                session, "literaturework", "work_type", "TEXT"
            ),
        ),
        Migration(
            version=6,
            name="add_councilmemo_round_id",
            apply=lambda session: _add_column(
                session, "councilmemo", "round_id", "INTEGER"
            ),
        ),
        Migration(
            version=7,
            name="add_review_language",
            apply=lambda session: _add_column(
                session, "review", "language", "TEXT DEFAULT 'en'"
            ),
        ),
        Migration(
            version=8,
            name="rename_review_level_fapesp",
            apply=lambda session: session.exec(
                text(
                    "UPDATE review SET level = 'Research Grant' "
                    "WHERE level = 'FAPESP'"
                )
            ),
        ),
        Migration(
            version=9,
            name="add_reviewartifact_persona_slot",
            apply=lambda session: (
                _add_column(session, "reviewartifact", "persona", "TEXT"),
                _add_column(session, "reviewartifact", "slot", "INTEGER"),
            ),
        ),
    ]


def _add_column(session: Session, table: str, column: str, column_type: str) -> None:
    if column_exists(session, table, column):
        return
    session.exec(text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"))


def apply_migrations(session: Session) -> None:
    _create_schema_migrations_table(session)
    applied = _applied_versions(session)
    for migration in _migrations():
        if migration.version in applied:
            continue
        migration.apply(session)
        _record_migration(session, migration)
