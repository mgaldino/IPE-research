from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class GateStatus(str, Enum):
    passed = "passed"
    failed = "failed"
    needs_revision = "needs_revision"


class DossierKind(str, Enum):
    pitch = "PITCH"
    design = "DESIGN"
    data_plan = "DATA_PLAN"
    positioning = "POSITIONING"
    next_steps = "NEXT_STEPS"


class ProviderCredential(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(index=True)
    name: Optional[str] = None
    api_key_encrypted: bytes
    salt: bytes
    created_at: datetime = Field(default_factory=utc_now)


class Run(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    status: RunStatus = Field(default=RunStatus.queued)
    provider: str
    model: str
    idea_count: int = 1
    topic_focus: Optional[str] = None
    literature_query_id: Optional[int] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    log: Optional[str] = None


class Idea(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(index=True)
    title: Optional[str] = None
    lane_primary: Optional[str] = None
    lane_secondary: Optional[str] = None
    breakthrough_type: Optional[str] = None
    big_claim: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DossierPart(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    idea_id: int = Field(index=True)
    kind: DossierKind
    content: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CouncilMemo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    idea_id: int = Field(index=True)
    round_id: Optional[int] = Field(default=None, foreign_key="councilround.id", index=True)
    referee: str
    content: str
    created_at: datetime = Field(default_factory=utc_now)


class CouncilRound(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    idea_id: int = Field(index=True)
    round_number: int
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class GateResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    idea_id: int = Field(index=True)
    gate: int
    status: GateStatus
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class AgentMemo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(index=True)
    idea_id: Optional[int] = Field(default=None, index=True)
    direction: str
    sender: str
    topic: str
    content: str
    created_at: datetime = Field(default_factory=utc_now)


class LiteratureQuery(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    query: str
    sources: str
    per_source_limit: int = 20
    include_non_article: bool = False
    status: str = "queued"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    notes: Optional[str] = None


class LiteratureWork(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    query_id: int = Field(index=True)
    source: str
    title: str
    authors: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    work_type: Optional[str] = None
    doi: Optional[str] = Field(default=None, index=True)
    abstract: Optional[str] = None
    open_access_url: Optional[str] = None
    pdf_path: Optional[str] = None
    full_text: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class LiteratureAssessment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    query_id: int = Field(index=True)
    content: str
    created_at: datetime = Field(default_factory=utc_now)
