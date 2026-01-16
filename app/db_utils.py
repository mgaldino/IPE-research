from __future__ import annotations

from sqlmodel import Session
from sqlalchemy import text


def column_exists(session: Session, table: str, column: str) -> bool:
    result = session.exec(text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in result)
