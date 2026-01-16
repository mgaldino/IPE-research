from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text

DATABASE_URL = "sqlite:///./codex_council.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


def _column_exists(session: Session, table: str, column: str) -> bool:
    result = session.exec(text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in result)


def _ensure_schema() -> None:
    with Session(engine) as session:
        if _column_exists(session, "run", "literature_query_id") is False:
            session.exec(
                text("ALTER TABLE run ADD COLUMN literature_query_id INTEGER")
            )
        if _column_exists(session, "literaturequery", "include_non_article") is False:
            session.exec(
                text("ALTER TABLE literaturequery ADD COLUMN include_non_article BOOLEAN DEFAULT 0")
            )
        if _column_exists(session, "literaturework", "work_type") is False:
            session.exec(
                text("ALTER TABLE literaturework ADD COLUMN work_type TEXT")
            )
        if _column_exists(session, "councilmemo", "round_id") is False:
            session.exec(
                text("ALTER TABLE councilmemo ADD COLUMN round_id INTEGER")
            )
        session.commit()


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_schema()


def get_session() -> Session:
    return Session(engine)
