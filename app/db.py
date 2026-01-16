from sqlmodel import SQLModel, create_engine, Session

from .migrations import apply_migrations

DATABASE_URL = "sqlite:///./codex_council.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        apply_migrations(session)
        session.commit()


def get_session() -> Session:
    return Session(engine)
