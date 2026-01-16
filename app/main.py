from datetime import datetime, timezone
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional
import re
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select

from .crypto import prepare_encrypted_secret, decrypt_secret
from .db import create_db_and_tables, engine
from .artifacts import write_review_artifacts
from .files import ensure_required_files, export_idea_markdown, snapshot_idea_version
from .models import (
    CouncilMemo,
    CouncilRound,
    DossierPart,
    GateResult,
    GateStatus,
    Idea,
    AgentMemo,
    LiteratureAssessment,
    LiteratureQuery,
    LiteratureWork,
    ProviderCredential,
    ProjectLevel,
    Review,
    ReviewArtifact,
    ReviewArtifactKind,
    ReviewGateResult,
    ReviewSection,
    ReviewStatus,
    ReviewType,
    Run,
    RunStatus,
)
from .orchestrator import DEFAULT_MODELS, run_swarm, PROVIDERS
from .literature import EXCLUDED_WORK_TYPES, rebuild_assessment, run_literature_query
from .literature import extract_pdf_text
from .review_ingest import extract_pdf_pages, split_sections, build_grounded_artifacts
from .modes import MODE_IDEATION, get_mode_config
from .prompts import (
    build_council_prompt_with_dossier,
    build_literature_paper_prompt,
    build_literature_synthesis_prompt,
    build_review_prompt,
)

BASE_DIR = Path(__file__).resolve().parents[1]

@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    ensure_required_files(BASE_DIR)
    app.state.passphrase = None
    (BASE_DIR / "literature" / "pdfs").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "literature" / "oa").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "literature" / "assessments").mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="IPE Breakthrough Idea Swarm", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class SessionUnlock(BaseModel):
    passphrase: str


class CredentialInput(BaseModel):
    provider: str
    api_key: str
    name: Optional[str] = None


class RunInput(BaseModel):
    provider: str
    model: Optional[str] = None
    idea_count: int = 1
    topic_focus: Optional[str] = None
    literature_query_id: Optional[int] = None
    use_assessment_seeds: bool = False


class ReviewInput(BaseModel):
    review_type: ReviewType
    level: Optional[ProjectLevel] = None
    title: Optional[str] = None
    domain: Optional[str] = None
    method_family: Optional[str] = None


class ReviewAttachPdfInput(BaseModel):
    filename: str


class ReviewRunInput(BaseModel):
    provider: str
    model: Optional[str] = None


class GateUpdate(BaseModel):
    status: GateStatus
    notes: Optional[str] = None


class LiteratureQueryInput(BaseModel):
    query: str
    sources: List[str] = ["openalex"]
    per_source_limit: int = 20
    include_non_article: bool = False
    openalex_email: Optional[str] = None
    semantic_scholar_key: Optional[str] = None


class AttachPdfInput(BaseModel):
    filename: str


class ResubmitInput(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    run_review: bool = False
    apply_revisions: bool = True


class LlmAssessmentInput(BaseModel):
    provider: str
    model: Optional[str] = None
    max_docs: int = 8
    max_tokens_budget: int = 100000


class ProviderTestInput(BaseModel):
    model: Optional[str] = None


class RestartInput(BaseModel):
    port: Optional[int] = None


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    html = (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.get("/api/providers")
async def list_providers() -> List[dict]:
    return [
        {"name": name, "default_model": DEFAULT_MODELS.get(name)}
        for name in DEFAULT_MODELS.keys()
    ]


@app.post("/api/providers/{provider}/test")
async def test_provider(provider: str, payload: ProviderTestInput) -> dict:
    if app.state.passphrase is None:
        raise HTTPException(status_code=400, detail="Unlock session with passphrase first")
    provider_impl = PROVIDERS.get(provider)
    if not provider_impl:
        raise HTTPException(status_code=400, detail="Unknown provider")
    model = payload.model or DEFAULT_MODELS.get(provider)
    if not model:
        raise HTTPException(status_code=400, detail="Model required for provider")
    with Session(engine) as session:
        credential = session.exec(
            select(ProviderCredential)
            .where(ProviderCredential.provider == provider)
            .order_by(ProviderCredential.created_at.desc())
        ).first()
        if not credential:
            raise HTTPException(status_code=400, detail="Missing credentials for provider")
        api_key = decrypt_secret(app.state.passphrase, credential.api_key_encrypted, credential.salt)
    prompt = "Reply with OK if you can read this."
    try:
        response = await provider_impl.generate(prompt, model, api_key)
    except Exception as exc:
        message = _redact_secrets(str(exc))
        status = 502
        if "429" in message or "too many requests" in message.lower():
            status = 429
        raise HTTPException(status_code=status, detail=message) from exc
    return {"status": "ok", "model": model, "response": response.content}


@app.post("/api/session/unlock")
async def unlock_session(payload: SessionUnlock) -> dict:
    if not payload.passphrase:
        raise HTTPException(status_code=400, detail="Passphrase required")
    app.state.passphrase = payload.passphrase
    return {"status": "ok"}


@app.post("/api/credentials")
async def save_credentials(payload: CredentialInput) -> dict:
    if app.state.passphrase is None:
        raise HTTPException(status_code=400, detail="Unlock session with passphrase first")
    encrypted, salt = prepare_encrypted_secret(app.state.passphrase, payload.api_key)
    with Session(engine) as session:
        credential = ProviderCredential(
            provider=payload.provider,
            name=payload.name,
            api_key_encrypted=encrypted,
            salt=salt,
        )
        session.add(credential)
        session.commit()
    return {"status": "saved"}


@app.get("/api/credentials")
async def list_credentials() -> List[dict]:
    with Session(engine) as session:
        credentials = session.exec(select(ProviderCredential)).all()
    return [
        {
            "provider": cred.provider,
            "name": cred.name,
            "created_at": cred.created_at.isoformat(),
        }
        for cred in credentials
    ]


@app.post("/api/runs")
async def start_run(payload: RunInput, background_tasks: BackgroundTasks) -> dict:
    if app.state.passphrase is None:
        raise HTTPException(status_code=400, detail="Unlock session with passphrase first")
    model = payload.model or DEFAULT_MODELS.get(payload.provider)
    if not model:
        raise HTTPException(status_code=400, detail="Unknown provider or model not specified")
    with Session(engine) as session:
        run = Run(
            status=RunStatus.queued,
            provider=payload.provider,
            model=model,
            idea_count=max(1, payload.idea_count),
            topic_focus=payload.topic_focus,
            literature_query_id=payload.literature_query_id,
            use_assessment_seeds=payload.use_assessment_seeds,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
    background_tasks.add_task(run_swarm, run.id, app.state.passphrase, BASE_DIR)
    return {"run_id": run.id}


@app.get("/api/runs")
async def list_runs() -> List[dict]:
    with Session(engine) as session:
        runs = session.exec(select(Run).order_by(Run.created_at.desc()).limit(5)).all()
    return [
        {
            "id": run.id,
            "status": run.status.value,
            "provider": run.provider,
            "model": run.model,
            "idea_count": run.idea_count,
            "topic_focus": run.topic_focus,
            "literature_query_id": run.literature_query_id,
            "use_assessment_seeds": run.use_assessment_seeds,
            "created_at": run.created_at.isoformat(),
            "updated_at": run.updated_at.isoformat(),
            "log": run.log,
        }
        for run in runs
    ]


@app.get("/api/ideas")
async def list_ideas() -> List[dict]:
    with Session(engine) as session:
        ideas = session.exec(select(Idea).order_by(Idea.created_at.desc())).all()
    return [
        {
            "id": idea.id,
            "run_id": idea.run_id,
            "title": idea.title,
            "lane_primary": idea.lane_primary,
            "breakthrough_type": idea.breakthrough_type,
            "big_claim": idea.big_claim,
            "status": idea.status,
            "updated_at": idea.updated_at.isoformat(),
        }
        for idea in ideas
    ]


@app.get("/api/ideas/{idea_id}")
async def get_idea(idea_id: int) -> dict:
    with Session(engine) as session:
        idea = session.get(Idea, idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        parts = session.exec(select(DossierPart).where(DossierPart.idea_id == idea_id)).all()
        latest_round = _latest_council_round(session, idea_id)
        if latest_round:
            memos = session.exec(
                select(CouncilMemo).where(CouncilMemo.round_id == latest_round.id)
            ).all()
        else:
            memos = session.exec(
                select(CouncilMemo).where(CouncilMemo.idea_id == idea_id)
            ).all()
        gates = session.exec(select(GateResult).where(GateResult.idea_id == idea_id)).all()
    return {
        "idea": {
            "id": idea.id,
            "run_id": idea.run_id,
            "title": idea.title,
            "lane_primary": idea.lane_primary,
            "lane_secondary": idea.lane_secondary,
            "breakthrough_type": idea.breakthrough_type,
            "big_claim": idea.big_claim,
            "status": idea.status,
            "updated_at": idea.updated_at.isoformat(),
        },
        "gates": [
            {"gate": gate.gate, "status": gate.status.value, "notes": gate.notes}
            for gate in gates
        ],
        "dossier_parts": [{"kind": part.kind.value, "content": part.content} for part in parts],
        "council_round": (
            {
                "id": latest_round.id,
                "round_number": latest_round.round_number,
                "status": latest_round.status,
                "created_at": latest_round.created_at.isoformat(),
            }
            if latest_round
            else None
        ),
        "council_memos": [{"referee": memo.referee, "content": memo.content} for memo in memos],
    }


@app.get("/api/reviews")
async def list_reviews() -> List[dict]:
    with Session(engine) as session:
        reviews = session.exec(select(Review).order_by(Review.created_at.desc())).all()
    return [
        {
            "id": review.id,
            "review_type": review.review_type.value,
            "level": review.level.value if review.level else None,
            "status": review.status.value,
            "title": review.title,
            "domain": review.domain,
            "method_family": review.method_family,
            "created_at": review.created_at.isoformat(),
            "updated_at": review.updated_at.isoformat(),
        }
        for review in reviews
    ]


@app.post("/api/reviews")
async def create_review(payload: ReviewInput) -> dict:
    if payload.review_type == ReviewType.project and payload.level is None:
        raise HTTPException(status_code=400, detail="Project reviews require a level")
    level = payload.level if payload.review_type == ReviewType.project else None
    with Session(engine) as session:
        review = Review(
            review_type=payload.review_type,
            level=level,
            title=payload.title,
            domain=payload.domain,
            method_family=payload.method_family,
        )
        session.add(review)
        session.commit()
        session.refresh(review)
    return {"review_id": review.id}


@app.get("/api/reviews/{review_id}")
async def get_review(review_id: int) -> dict:
    with Session(engine) as session:
        review = session.get(Review, review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        artifacts = session.exec(
            select(ReviewArtifact).where(ReviewArtifact.review_id == review_id)
        ).all()
        gates = session.exec(
            select(ReviewGateResult).where(ReviewGateResult.review_id == review_id)
        ).all()
        sections = session.exec(
            select(ReviewSection).where(ReviewSection.review_id == review_id)
        ).all()
    return {
        "review": {
            "id": review.id,
            "review_type": review.review_type.value,
            "level": review.level.value if review.level else None,
            "status": review.status.value,
            "title": review.title,
            "domain": review.domain,
            "method_family": review.method_family,
            "created_at": review.created_at.isoformat(),
            "updated_at": review.updated_at.isoformat(),
        },
        "artifacts": [
            {"kind": artifact.kind.value, "content": artifact.content}
            for artifact in artifacts
        ],
        "gates": [
            {"gate": gate.gate, "status": gate.status.value, "notes": gate.notes}
            for gate in gates
        ],
        "sections": [
            {
                "section_id": section.section_id,
                "title": section.title,
                "page_start": section.page_start,
                "page_end": section.page_end,
                "excerpt": section.excerpt,
            }
            for section in sections
        ],
    }


@app.post("/api/reviews/{review_id}/attach-pdf")
async def attach_pdf_to_review(review_id: int, payload: ReviewAttachPdfInput) -> dict:
    pdf_dir = BASE_DIR / "reviews" / "pdfs" / str(review_id)
    pdf_path = (pdf_dir / payload.filename).resolve()
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    if pdf_dir.resolve() not in pdf_path.parents:
        raise HTTPException(status_code=400, detail="Invalid PDF path")
    pages = extract_pdf_pages(pdf_path)
    sections = split_sections(pages)
    with Session(engine) as session:
        review = session.get(Review, review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        artifacts = build_grounded_artifacts(
            sections,
            review_type=review.review_type.value,
            level=review.level.value if review.level else None,
        )
        session.exec(
            ReviewSection.__table__.delete().where(ReviewSection.review_id == review_id)
        )
        session.exec(
            ReviewArtifact.__table__.delete().where(ReviewArtifact.review_id == review_id)
        )
        session.add_all([
            ReviewSection(
                review_id=review_id,
                section_id=section.section_id,
                title=section.title,
                content=section.content,
                page_start=section.page_start,
                page_end=section.page_end,
                excerpt=section.excerpt,
            )
            for section in sections
        ])
        session.add_all([
            ReviewArtifact(
                review_id=review_id,
                kind=ReviewArtifactKind.referee_memo,
                content=artifacts["REFEREE_MEMO"],
            ),
            ReviewArtifact(
                review_id=review_id,
                kind=ReviewArtifactKind.revision_checklist,
                content=artifacts["REVISION_CHECKLIST"],
            ),
        ])
        review.updated_at = datetime.now(timezone.utc)
        session.add(review)
        session.commit()
        stored_artifacts = session.exec(
            select(ReviewArtifact).where(ReviewArtifact.review_id == review_id)
        ).all()
    review_dir = BASE_DIR / "reviews" / str(review_id)
    write_review_artifacts(review_dir, stored_artifacts)
    return {"review_id": review_id, "sections": len(sections)}


@app.post("/api/reviews/{review_id}/run")
async def run_review(review_id: int, payload: ReviewRunInput) -> dict:
    if getattr(app.state, "passphrase", None) is None:
        raise HTTPException(status_code=400, detail="Unlock session with passphrase first")
    provider_impl = PROVIDERS.get(payload.provider)
    if not provider_impl:
        raise HTTPException(status_code=400, detail="Unknown provider")
    model = payload.model or DEFAULT_MODELS.get(payload.provider)
    if not model:
        raise HTTPException(status_code=400, detail="Model required for provider")

    with Session(engine) as session:
        review = session.get(Review, review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        sections = session.exec(
            select(ReviewSection).where(ReviewSection.review_id == review_id)
        ).all()
        if not sections:
            raise HTTPException(status_code=400, detail="No sections indexed for review")
        credential = session.exec(
            select(ProviderCredential)
            .where(ProviderCredential.provider == payload.provider)
            .order_by(ProviderCredential.created_at.desc())
        ).first()
        if not credential:
            raise HTTPException(status_code=400, detail="Missing credentials for provider")
        api_key = decrypt_secret(app.state.passphrase, credential.api_key_encrypted, credential.salt)

        prompt = build_review_prompt(
            review_type=review.review_type.value,
            level=review.level.value if review.level else None,
            title=review.title,
            domain=review.domain,
            method_family=review.method_family,
            sections=[
                {
                    "section_id": section.section_id,
                    "title": section.title,
                    "page_start": section.page_start,
                    "page_end": section.page_end,
                    "excerpt": section.excerpt,
                }
                for section in sections
            ],
        )
        response = await provider_impl.generate(prompt, model, api_key)
        memo, checklist = _split_review_output(response.content)

        session.exec(
            ReviewArtifact.__table__.delete().where(ReviewArtifact.review_id == review_id)
        )
        session.add_all([
            ReviewArtifact(
                review_id=review_id,
                kind=ReviewArtifactKind.referee_memo,
                content=memo,
            ),
            ReviewArtifact(
                review_id=review_id,
                kind=ReviewArtifactKind.revision_checklist,
                content=checklist,
            ),
        ])
        review.status = ReviewStatus.completed
        review.updated_at = datetime.now(timezone.utc)
        session.add(review)
        session.commit()
        stored_artifacts = session.exec(
            select(ReviewArtifact).where(ReviewArtifact.review_id == review_id)
        ).all()
    review_dir = BASE_DIR / "reviews" / str(review_id)
    write_review_artifacts(review_dir, stored_artifacts)
    return {"review_id": review_id, "status": "completed"}


@app.put("/api/ideas/{idea_id}/gates/{gate_id}")
async def update_gate(idea_id: int, gate_id: int, payload: GateUpdate) -> dict:
    with Session(engine) as session:
        gate = session.exec(
            select(GateResult).where(
                GateResult.idea_id == idea_id,
                GateResult.gate == gate_id,
            )
        ).first()
        if not gate:
            gate = GateResult(
                idea_id=idea_id,
                gate=gate_id,
                status=payload.status,
                notes=payload.notes,
            )
        else:
            gate.status = payload.status
            gate.notes = payload.notes
        session.add(gate)
        session.commit()
        session.refresh(gate)
    return {"gate": gate.gate, "status": gate.status.value, "notes": gate.notes}


def _restart_server(port: int) -> None:
    log_path = Path("/tmp/codex_council_uvicorn.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = (
        f"sleep 1; nohup {sys.executable} -m uvicorn app.main:app "
        f"--host 127.0.0.1 --port {port} >> {log_path} 2>&1 &"
    )


def _split_review_output(content: str) -> tuple[str, str]:
    marker = "REVISION_CHECKLIST"
    if marker in content:
        before, after = content.split(marker, 1)
        memo = before.strip()
        checklist = f"{marker}{after}".strip()
        return memo, checklist
    return content.strip(), "REVISION_CHECKLIST\n- No checklist provided."
    subprocess.Popen(
        ["bash", "-lc", command],
        cwd=str(BASE_DIR),
        start_new_session=True,
    )
    time.sleep(0.5)
    os._exit(0)


def _port_open(port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


@app.post("/api/server/restart")
async def restart_server(payload: RestartInput, background_tasks: BackgroundTasks) -> dict:
    port = payload.port or 8001
    background_tasks.add_task(_restart_server, port)
    return {"status": "restarting", "port": port}


def _write_mail_memo(base_dir: Path, memo: AgentMemo) -> None:
    mailbox = "inbox" if memo.direction == "inbox" else "outbox"
    mail_dir = base_dir / "mail" / mailbox
    mail_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    safe_sender = memo.sender.replace(" ", "_")
    safe_topic = memo.topic.replace(" ", "_")
    memo_id = memo.id or "new"
    filename = f"{timestamp}_{memo_id}_{safe_sender}_{safe_topic}.md"
    (mail_dir / filename).write_text(memo.content.strip() + "\n", encoding="utf-8")


def _parse_required_revisions(content: str) -> List[str]:
    lines = content.splitlines()
    start_idx = None
    for idx, line in enumerate(lines):
        if re.search(r"required revisions", line, re.IGNORECASE):
            start_idx = idx + 1
            break
    if start_idx is None:
        return []
    revisions: List[str] = []
    for line in lines[start_idx:]:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^(scores|verdict|strengths|fatal flaws|required revisions)\b", stripped, re.IGNORECASE):
            break
        bullet_match = re.match(r"^[-*]\s+(.*)", stripped)
        if bullet_match:
            revisions.append(bullet_match.group(1).strip())
            continue
        numbered_match = re.match(r"^\d+[).]\s+(.*)", stripped)
        if numbered_match:
            revisions.append(numbered_match.group(1).strip())
            continue
        if revisions:
            revisions[-1] = f"{revisions[-1]} {stripped}"
    return revisions


def _build_revision_log(memos: List[CouncilMemo], timestamp: str) -> tuple[str, int]:
    items: List[str] = []
    for memo in memos:
        revisions = _parse_required_revisions(memo.content)
        for revision in revisions:
            items.append(f"{memo.referee}: {revision}")
    if not items:
        items.append("No explicit required revisions parsed; manual review needed.")
    unique_items = []
    seen = set()
    for item in items:
        if item not in seen:
            unique_items.append(item)
            seen.add(item)
    bullet_list = "\n".join([f"  - {item}" for item in unique_items])
    log = (
        "\n\n## Auto-Revision Log (mock)\n"
        f"- Applied: {timestamp} UTC\n"
        "- Source: Council memos\n"
        "- Action: Appended required revisions to dossier sections\n"
        "- Revisions:\n"
        f"{bullet_list}\n"
    )
    return log, len(unique_items)


def _split_council_memos(content: str) -> List[str]:
    parts = [part.strip() for part in content.split("---") if part.strip()]
    return parts if parts else [content.strip()]


def _parse_version_metadata(content: str, key: str) -> Optional[str]:
    for line in content.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return None


def _latest_parts_by_kind(parts: List[DossierPart]) -> dict[str, DossierPart]:
    latest: dict[str, DossierPart] = {}
    for part in parts:
        key = part.kind.value
        current = latest.get(key)
        if not current or part.updated_at >= current.updated_at:
            latest[key] = part
    return latest


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _next_council_round(session: Session, idea_id: int) -> int:
    last_round = session.exec(
        select(CouncilRound)
        .where(CouncilRound.idea_id == idea_id)
        .order_by(CouncilRound.round_number.desc())
    ).first()
    return (last_round.round_number + 1) if last_round else 1


def _latest_council_round(session: Session, idea_id: int) -> Optional[CouncilRound]:
    return session.exec(
        select(CouncilRound)
        .where(CouncilRound.idea_id == idea_id)
        .order_by(CouncilRound.round_number.desc())
    ).first()


def _parse_score(line: str) -> Optional[float]:
    match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", line)
    if match:
        return float(match.group(1))
    match = re.search(r"\b(\d+(?:\.\d+)?)\b", line)
    if match:
        return float(match.group(1))
    return None


def _extract_scores(memos: List[CouncilMemo]) -> dict[str, List[float]]:
    fields = {
        "novelty/agenda-setting": "novelty",
        "novelty": "novelty",
        "theoretical stakes clarity": "stakes",
        "stakes": "stakes",
        "design credibility": "design",
        "data feasibility": "data",
        "interpretability": "interpretability",
        "lane fit": "lane_fit",
        "breakthrough plausibility": "breakthrough",
    }
    scores: dict[str, List[float]] = {key: [] for key in set(fields.values())}
    for memo in memos:
        for line in memo.content.splitlines():
            lower = line.lower()
            for label, key in fields.items():
                if label in lower:
                    value = _parse_score(line)
                    if value is not None:
                        scores[key].append(value)
    return scores


def _extract_verdicts(memos: List[CouncilMemo]) -> List[str]:
    verdicts = []
    for memo in memos:
        for line in memo.content.splitlines():
            if line.lower().startswith("verdict"):
                _, _, value = line.partition(":")
                verdicts.append(value.strip().lower())
    return verdicts


def _auto_gate4_status(memos: List[CouncilMemo]) -> tuple[GateStatus, str]:
    thresholds = {
        "novelty": 8,
        "stakes": 7,
        "design": 8,
        "data": 6,
        "interpretability": 7,
        "lane_fit": 7,
        "breakthrough": 8,
    }
    scores = _extract_scores(memos)
    missing = [key for key in thresholds.keys() if not scores.get(key)]
    if missing:
        return GateStatus.needs_revision, f"Missing scores for: {', '.join(missing)}"
    averages = {key: sum(values) / len(values) for key, values in scores.items()}
    failing = [key for key, minimum in thresholds.items() if averages.get(key, 0) < minimum]
    verdicts = _extract_verdicts(memos)
    verdict_text = ", ".join(verdicts) if verdicts else "no verdicts found"
    note_parts = [
        "Auto Gate 4 recompute",
        f"Averages: {', '.join([f'{k}={averages[k]:.1f}' for k in thresholds.keys()])}",
        f"Verdicts: {verdict_text}",
    ]
    if failing:
        return GateStatus.failed, "; ".join(note_parts + [f"Below thresholds: {', '.join(failing)}"])
    if any("reject" in verdict for verdict in verdicts):
        return GateStatus.failed, "; ".join(note_parts + ["Verdict includes reject"])
    if any("revise" in verdict for verdict in verdicts):
        return GateStatus.needs_revision, "; ".join(note_parts + ["Verdict includes revise"])
    return GateStatus.passed, "; ".join(note_parts + ["All thresholds met"])


def _redact_secrets(text: str) -> str:
    redacted = re.sub(r"key=[^&\s]+", "key=REDACTED", text)
    redacted = re.sub(r"for url '[^']+'", "for url 'URL_REDACTED'", redacted)
    redacted = re.sub(r"https?://\\S+", "URL_REDACTED", redacted)
    return redacted


@app.post("/api/ideas/{idea_id}/council/revise")
async def auto_revise_idea(idea_id: int) -> dict:
    with Session(engine) as session:
        idea = session.get(Idea, idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        parts = session.exec(select(DossierPart).where(DossierPart.idea_id == idea_id)).all()
        latest_round = _latest_council_round(session, idea_id)
        if latest_round:
            memos = session.exec(
                select(CouncilMemo).where(CouncilMemo.round_id == latest_round.id)
            ).all()
        else:
            memos = session.exec(
                select(CouncilMemo).where(CouncilMemo.idea_id == idea_id)
            ).all()
        if not parts:
            raise HTTPException(status_code=400, detail="No dossier parts to revise")
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        snapshot_idea_version(
            BASE_DIR,
            idea_id,
            parts,
            memos,
            label="pre-resubmission",
            metadata="Snapshot before auto-revision/resubmission.",
        )
        revision_log, revision_count = _build_revision_log(memos, timestamp)
        for part in parts:
            part.content = part.content.rstrip() + revision_log
            part.updated_at = now
            session.add(part)
        idea.status = "resubmitted"
        idea.updated_at = now
        session.add(idea)
        for gate_id in (2, 3, 4):
            gate = session.exec(
                select(GateResult).where(
                    GateResult.idea_id == idea_id,
                    GateResult.gate == gate_id,
                )
            ).first()
            note = f"Auto-revision applied {timestamp} UTC; ready for council resubmission."
            if not gate:
                gate = GateResult(
                    idea_id=idea_id,
                    gate=gate_id,
                    status=GateStatus.needs_revision,
                    notes=note,
                )
            else:
                gate.status = GateStatus.needs_revision
                gate.notes = note
            session.add(gate)
        memo_content = "\n".join([
            "Context: Auto-Revision Engine applied council-required revisions (mock).",
            "Decision/Recommendation: Treat as resubmission-ready; request council re-review.",
            "Evidence or reasoning: Revisions extracted from council memos; no execution performed.",
            "Next action (owner): PI Proxy Agent to trigger council review and update gates.",
            "",
            revision_log.strip(),
        ])
        agent_memo = AgentMemo(
            run_id=idea.run_id,
            idea_id=idea.id,
            direction="outbox",
            sender="Auto-Revision Engine",
            topic="Council Auto-Revision",
            content=memo_content,
        )
        session.add(agent_memo)
        session.commit()
        session.refresh(agent_memo)
        _write_mail_memo(BASE_DIR, agent_memo)
        updated_parts = session.exec(select(DossierPart).where(DossierPart.idea_id == idea_id)).all()
        latest_round = _latest_council_round(session, idea_id)
        if latest_round:
            updated_memos = session.exec(
                select(CouncilMemo).where(CouncilMemo.round_id == latest_round.id)
            ).all()
        else:
            updated_memos = session.exec(
                select(CouncilMemo).where(CouncilMemo.idea_id == idea_id)
            ).all()
    export_idea_markdown(BASE_DIR, idea_id, updated_parts, updated_memos)
    return {"status": "revised", "revisions": revision_count}


@app.post("/api/ideas/{idea_id}/council/resubmit")
async def resubmit_to_council(idea_id: int, payload: ResubmitInput) -> dict:
    with Session(engine) as session:
        idea = session.get(Idea, idea_id)
        if not idea:
            raise HTTPException(status_code=404, detail="Idea not found")
        parts = session.exec(select(DossierPart).where(DossierPart.idea_id == idea_id)).all()
        memos = session.exec(select(CouncilMemo).where(CouncilMemo.idea_id == idea_id)).all()
        if not parts:
            raise HTTPException(status_code=400, detail="No dossier parts to resubmit")
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        version_id = snapshot_idea_version(
            BASE_DIR,
            idea_id,
            parts,
            memos,
            label="pre-resubmission",
            metadata="Snapshot before council resubmission.",
        )
        revision_count = 0
        if payload.apply_revisions:
            revision_log, revision_count = _build_revision_log(memos, timestamp)
            for part in parts:
                part.content = part.content.rstrip() + revision_log
                part.updated_at = now
                session.add(part)
        idea.status = "resubmitted"
        idea.updated_at = now
        session.add(idea)
        for gate_id in (2, 3, 4):
            gate = session.exec(
                select(GateResult).where(
                    GateResult.idea_id == idea_id,
                    GateResult.gate == gate_id,
                )
            ).first()
            note = f"Resubmitted {timestamp} UTC."
            if not gate:
                gate = GateResult(
                    idea_id=idea_id,
                    gate=gate_id,
                    status=GateStatus.needs_revision,
                    notes=note,
                )
            else:
                gate.status = GateStatus.needs_revision
                gate.notes = note
            session.add(gate)

        if payload.run_review:
            if app.state.passphrase is None:
                raise HTTPException(status_code=400, detail="Unlock session with passphrase first")
            provider_name = payload.provider
            if not provider_name:
                raise HTTPException(status_code=400, detail="Provider required for council review")
            provider = PROVIDERS.get(provider_name)
            if not provider:
                raise HTTPException(status_code=400, detail="Unknown provider")
            model = payload.model or DEFAULT_MODELS.get(provider_name)
            if not model:
                raise HTTPException(status_code=400, detail="Model required for provider")
            credential = session.exec(
                select(ProviderCredential)
                .where(ProviderCredential.provider == provider_name)
                .order_by(ProviderCredential.created_at.desc())
            ).first()
            if not credential:
                raise HTTPException(status_code=400, detail="Missing credentials for provider")
            api_key = decrypt_secret(app.state.passphrase, credential.api_key_encrypted, credential.salt)
            run = session.get(Run, idea.run_id)
            topic_focus = run.topic_focus if run else None
            latest_parts = _latest_parts_by_kind(parts)
            dossier_payload = {key: part.content for key, part in latest_parts.items()}
            mode_config = get_mode_config(MODE_IDEATION)
            council_prompt = build_council_prompt_with_dossier(
                dossier_payload,
                topic_focus,
                mode=mode_config.prompt_set,
            )
            council_response = await provider.generate(council_prompt, model, api_key)
            council_content = council_response.content
            round_number = _next_council_round(session, idea_id)
            council_round = CouncilRound(
                idea_id=idea.id,
                round_number=round_number,
                status="generated",
            )
            session.add(council_round)
            session.commit()
            session.refresh(council_round)
            memos = _split_council_memos(council_content)
            memo_models = []
            for idx, memo_text in enumerate(memos, start=1):
                referee = f"Referee {chr(64 + idx)}" if idx <= 5 else f"Referee {idx}"
                memo_model = CouncilMemo(
                    idea_id=idea.id,
                    round_id=council_round.id,
                    referee=referee,
                    content=memo_text,
                )
                session.add(memo_model)
                memo_models.append(memo_model)
            memo_content = "\n".join([
                "Context: Council re-review generated for resubmission.",
                "Decision/Recommendation: Log updated memos and re-open Gate 4.",
                "Evidence or reasoning: LLM council run on updated dossier content.",
                "Next action (owner): PI Proxy Agent to update gate status and route revisions.",
                "",
                council_content.strip(),
            ])
            agent_memo = AgentMemo(
                run_id=idea.run_id,
                idea_id=idea.id,
                direction="outbox",
                sender="Council Agents",
                topic="Council Resubmission",
                content=memo_content,
            )
            session.add(agent_memo)
            session.flush()
            _write_mail_memo(BASE_DIR, agent_memo)
            gate_status, gate_note = _auto_gate4_status(memo_models)
            council_round.status = gate_status.value
            council_round.notes = gate_note
            session.add(council_round)
            gate = session.exec(
                select(GateResult).where(
                    GateResult.idea_id == idea_id,
                    GateResult.gate == 4,
                )
            ).first()
            if not gate:
                gate = GateResult(
                    idea_id=idea_id,
                    gate=4,
                    status=gate_status,
                    notes=gate_note,
                )
            else:
                gate.status = gate_status
                gate.notes = gate_note
            session.add(gate)
        session.commit()
        updated_parts = session.exec(select(DossierPart).where(DossierPart.idea_id == idea_id)).all()
        updated_memos = session.exec(select(CouncilMemo).where(CouncilMemo.idea_id == idea_id)).all()
    export_idea_markdown(BASE_DIR, idea_id, updated_parts, updated_memos)
    return {
        "status": "resubmitted",
        "version_id": version_id,
        "revisions": revision_count,
        "review_ran": payload.run_review,
    }


@app.get("/api/ideas/{idea_id}/versions")
async def list_idea_versions(idea_id: int) -> List[dict]:
    versions_dir = BASE_DIR / "ideas" / str(idea_id) / "versions"
    if not versions_dir.exists():
        return []
    versions = []
    for item in sorted(versions_dir.iterdir(), reverse=True):
        if not item.is_dir():
            continue
        meta_path = item / "VERSION.md"
        label = None
        created = None
        if meta_path.exists():
            content = meta_path.read_text(encoding="utf-8")
            label = _parse_version_metadata(content, "Label")
            created = _parse_version_metadata(content, "Created")
        versions.append({
            "id": item.name,
            "label": label,
            "created_at": created,
        })
    return versions


@app.get("/api/ideas/{idea_id}/versions/{version_id}")
async def get_idea_version(idea_id: int, version_id: str) -> dict:
    version_dir = BASE_DIR / "ideas" / str(idea_id) / "versions" / version_id
    if not version_dir.exists():
        raise HTTPException(status_code=404, detail="Version not found")
    meta_path = version_dir / "VERSION.md"
    metadata = meta_path.read_text(encoding="utf-8") if meta_path.exists() else ""
    files = {
        "PITCH": version_dir / "PITCH.md",
        "DESIGN": version_dir / "DESIGN.md",
        "DATA_PLAN": version_dir / "DATA_PLAN.md",
        "POSITIONING": version_dir / "POSITIONING.md",
        "NEXT_STEPS": version_dir / "NEXT_STEPS.md",
    }
    dossier_parts = []
    for kind, path in files.items():
        if path.exists():
            dossier_parts.append({"kind": kind, "content": path.read_text(encoding="utf-8")})
    council_dir = version_dir / "council"
    council_memos = []
    if council_dir.exists():
        for memo_path in sorted(council_dir.glob("*.md")):
            council_memos.append({
                "referee": memo_path.stem.replace("_", " "),
                "content": memo_path.read_text(encoding="utf-8"),
            })
    return {
        "id": version_id,
        "metadata": metadata,
        "dossier_parts": dossier_parts,
        "council_memos": council_memos,
    }


@app.get("/api/ideas/{idea_id}/council/rounds")
async def list_council_rounds(idea_id: int) -> List[dict]:
    with Session(engine) as session:
        rounds = session.exec(
            select(CouncilRound)
            .where(CouncilRound.idea_id == idea_id)
            .order_by(CouncilRound.round_number.desc())
        ).all()
    return [
        {
            "id": round_.id,
            "round_number": round_.round_number,
            "status": round_.status,
            "notes": round_.notes,
            "created_at": round_.created_at.isoformat(),
        }
        for round_ in rounds
    ]


@app.get("/api/ideas/{idea_id}/council/rounds/{round_id}")
async def get_council_round(idea_id: int, round_id: int) -> dict:
    with Session(engine) as session:
        round_ = session.exec(
            select(CouncilRound)
            .where(CouncilRound.idea_id == idea_id, CouncilRound.id == round_id)
        ).first()
        if not round_:
            raise HTTPException(status_code=404, detail="Council round not found")
        memos = session.exec(
            select(CouncilMemo).where(CouncilMemo.round_id == round_.id)
        ).all()
    return {
        "round": {
            "id": round_.id,
            "round_number": round_.round_number,
            "status": round_.status,
            "notes": round_.notes,
            "created_at": round_.created_at.isoformat(),
        },
        "memos": [{"referee": memo.referee, "content": memo.content} for memo in memos],
    }


@app.post("/api/literature/queries")
async def start_literature_query(payload: LiteratureQueryInput, background_tasks: BackgroundTasks) -> dict:
    sources = [source for source in payload.sources if source in {"openalex", "crossref", "semantic_scholar"}]
    if not sources:
        raise HTTPException(status_code=400, detail="No valid sources provided")
    if "openalex" in sources and not payload.openalex_email:
        raise HTTPException(status_code=400, detail="OpenAlex requires an email (mailto) for requests")
    with Session(engine) as session:
        query = LiteratureQuery(
            query=payload.query,
            sources=",".join(sources),
            per_source_limit=payload.per_source_limit,
            include_non_article=payload.include_non_article,
            status="queued",
        )
        session.add(query)
        session.commit()
        session.refresh(query)
    (BASE_DIR / "literature" / "pdfs" / str(query.id)).mkdir(parents=True, exist_ok=True)
    background_tasks.add_task(
        run_literature_query,
        query.id,
        payload.query,
        sources,
        payload.per_source_limit,
        BASE_DIR,
        payload.include_non_article,
        payload.openalex_email,
        payload.semantic_scholar_key,
    )
    return {"query_id": query.id}


@app.get("/api/literature/queries")
async def list_literature_queries() -> List[dict]:
    with Session(engine) as session:
        queries = session.exec(select(LiteratureQuery).order_by(LiteratureQuery.created_at.desc())).all()
    return [
        {
            "id": query.id,
            "query": query.query,
            "sources": query.sources,
            "status": query.status,
            "per_source_limit": query.per_source_limit,
            "include_non_article": query.include_non_article,
            "created_at": query.created_at.isoformat(),
            "updated_at": query.updated_at.isoformat(),
            "notes": query.notes,
        }
        for query in queries
    ]


@app.get("/api/literature/queries/{query_id}")
async def get_literature_query(query_id: int) -> dict:
    with Session(engine) as session:
        query = session.get(LiteratureQuery, query_id)
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        works = session.exec(
            select(LiteratureWork)
            .where(LiteratureWork.query_id == query_id)
            .order_by(LiteratureWork.id)
        ).all()
        assessment = session.exec(
            select(LiteratureAssessment).where(LiteratureAssessment.query_id == query_id)
        ).first()
    return {
        "query": {
            "id": query.id,
            "query": query.query,
            "sources": query.sources,
            "status": query.status,
            "per_source_limit": query.per_source_limit,
            "include_non_article": query.include_non_article,
            "created_at": query.created_at.isoformat(),
            "updated_at": query.updated_at.isoformat(),
            "notes": query.notes,
        },
        "works": [
            {
                "id": work.id,
                "source": work.source,
                "title": work.title,
                "authors": work.authors,
                "year": work.year,
                "venue": work.venue,
                "work_type": work.work_type,
                "doi": work.doi,
                "open_access_url": work.open_access_url,
                "pdf_path": work.pdf_path,
            }
            for work in works
        ],
        "assessment": assessment.content if assessment else None,
    }


@app.post("/api/literature/queries/{query_id}/assessment")
async def rebuild_query_assessment(query_id: int, background_tasks: BackgroundTasks) -> dict:
    with Session(engine) as session:
        query = session.get(LiteratureQuery, query_id)
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        query.status = "processing"
        query.updated_at = datetime.now(timezone.utc)
        session.add(query)
        session.commit()
    background_tasks.add_task(rebuild_assessment, query_id, BASE_DIR)
    return {"status": "queued"}


@app.post("/api/literature/queries/{query_id}/assessment/llm")
async def rebuild_query_assessment_llm(query_id: int, payload: LlmAssessmentInput) -> dict:
    if app.state.passphrase is None:
        raise HTTPException(status_code=400, detail="Unlock session with passphrase first")
    provider = PROVIDERS.get(payload.provider)
    if not provider:
        raise HTTPException(status_code=400, detail="Unknown provider")
    model = payload.model or DEFAULT_MODELS.get(payload.provider)
    if not model:
        raise HTTPException(status_code=400, detail="Model required for provider")
    with Session(engine) as session:
        query = session.get(LiteratureQuery, query_id)
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        credential = session.exec(
            select(ProviderCredential)
            .where(ProviderCredential.provider == payload.provider)
            .order_by(ProviderCredential.created_at.desc())
        ).first()
        if not credential:
            raise HTTPException(status_code=400, detail="Missing credentials for provider")
        api_key = decrypt_secret(app.state.passphrase, credential.api_key_encrypted, credential.salt)
        works = session.exec(select(LiteratureWork).where(LiteratureWork.query_id == query_id)).all()

    candidates = []
    for work in works:
        combined = " ".join(filter(None, [work.abstract, work.full_text]))
        if not combined:
            continue
        has_full_text = work.full_text is not None
        candidates.append((has_full_text, work, combined))
    # Preserve query order; do not prioritize by length.
    selected = []
    token_budget = max(1000, payload.max_tokens_budget)
    used_tokens = 0
    for _, work, combined in candidates:
        if len(selected) >= max(1, payload.max_docs):
            break
        tokens = _estimate_tokens(combined)
        if used_tokens + tokens > token_budget:
            continue
        selected.append((work, combined, tokens))
        used_tokens += tokens

    if not selected and candidates:
        _, work, combined = candidates[0]
        truncated = combined[: token_budget * 4]
        selected = [(work, truncated, _estimate_tokens(truncated))]
    summaries = []
    for work, combined, _tokens in selected:
        metadata_parts = [
            f"year={work.year}" if work.year else None,
            f"venue={work.venue}" if work.venue else None,
            f"authors={work.authors}" if work.authors else None,
            f"source={work.source}" if work.source else None,
        ]
        metadata = ", ".join([item for item in metadata_parts if item])
        prompt = build_literature_paper_prompt(work.title or "Untitled", metadata, combined)
        try:
            response = await provider.generate(prompt, model, api_key)
            summaries.append(f"## {work.title or 'Untitled'}\n{response.content.strip()}")
        except Exception as exc:
            message = _redact_secrets(str(exc))
            status = 502
            if "429" in message or "too many requests" in message.lower():
                status = 429
            raise HTTPException(status_code=status, detail=message) from exc

    synthesis_prompt = build_literature_synthesis_prompt(summaries, query.query, len(works))
    try:
        synthesis_response = await provider.generate(synthesis_prompt, model, api_key)
    except Exception as exc:
        message = _redact_secrets(str(exc))
        status = 502
        if "429" in message or "too many requests" in message.lower():
            status = 429
        raise HTTPException(status_code=status, detail=message) from exc
    assessment = "\n".join([
        "# Literature Assessment (LLM)",
        "",
        synthesis_response.content.strip(),
    ]).strip() + "\n"

    with Session(engine) as session:
        existing = session.exec(
            select(LiteratureAssessment).where(LiteratureAssessment.query_id == query_id)
        ).first()
        if existing:
            existing.content = assessment
            session.add(existing)
        else:
            session.add(LiteratureAssessment(query_id=query_id, content=assessment))

        assessment_dir = BASE_DIR / "literature" / "assessments"
        assessment_dir.mkdir(parents=True, exist_ok=True)
        assessment_path = assessment_dir / f"assessment_{query_id}_llm.md"
        assessment_path.write_text(assessment, encoding="utf-8")

        query_row = session.get(LiteratureQuery, query_id)
        if query_row:
            query_row.status = "llm_assessed"
            query_row.updated_at = datetime.now(timezone.utc)
            note_value = f"llm_assessment_path={assessment_path}"
            if query_row.notes:
                query_row.notes = f"{query_row.notes};{note_value}"
            else:
                query_row.notes = note_value
            session.add(query_row)
        session.commit()

    return {
        "status": "completed",
        "summary_count": len(summaries),
        "assessment_path": str(assessment_path),
    }


@app.delete("/api/literature/queries/{query_id}")
async def delete_literature_query(query_id: int) -> dict:
    with Session(engine) as session:
        query = session.get(LiteratureQuery, query_id)
        if not query:
            raise HTTPException(status_code=404, detail="Query not found")
        works = session.exec(select(LiteratureWork).where(LiteratureWork.query_id == query_id)).all()
        for work in works:
            session.delete(work)
        assessment = session.exec(
            select(LiteratureAssessment).where(LiteratureAssessment.query_id == query_id)
        ).first()
        if assessment:
            session.delete(assessment)
        session.delete(query)
        session.commit()

    assessment_path = BASE_DIR / "literature" / "assessments" / f"assessment_{query_id}.md"
    if assessment_path.exists():
        assessment_path.unlink()
    shutil.rmtree(BASE_DIR / "literature" / "oa" / str(query_id), ignore_errors=True)
    shutil.rmtree(BASE_DIR / "literature" / "pdfs" / str(query_id), ignore_errors=True)
    return {"status": "deleted"}


@app.post("/api/literature/queries/{query_id}/cleanup")
async def cleanup_literature_query(query_id: int) -> dict:
    removed = 0
    with Session(engine) as session:
        works = session.exec(select(LiteratureWork).where(LiteratureWork.query_id == query_id)).all()
        for work in works:
            if work.work_type and work.work_type in EXCLUDED_WORK_TYPES:
                session.delete(work)
                removed += 1
        session.commit()
    return {"removed": removed}


@app.delete("/api/literature/works/{work_id}")
async def delete_literature_work(work_id: int) -> dict:
    with Session(engine) as session:
        work = session.get(LiteratureWork, work_id)
        if not work:
            raise HTTPException(status_code=404, detail="Work not found")
        session.delete(work)
        session.commit()
    return {"status": "deleted"}


@app.get("/api/literature/queries/{query_id}/local-pdfs")
async def list_local_pdfs(query_id: int) -> List[str]:
    pdf_dir = BASE_DIR / "literature" / "pdfs" / str(query_id)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    return sorted([path.name for path in pdf_dir.glob("*.pdf")])


@app.post("/api/literature/works/{work_id}/attach-pdf")
async def attach_pdf_to_work(work_id: int, payload: AttachPdfInput) -> dict:
    with Session(engine) as session:
        work = session.get(LiteratureWork, work_id)
        if not work:
            raise HTTPException(status_code=404, detail="Work not found")
        pdf_dir = BASE_DIR / "literature" / "pdfs" / str(work.query_id)
        pdf_path = (pdf_dir / payload.filename).resolve()
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="PDF not found")
        if pdf_dir.resolve() not in pdf_path.parents:
            raise HTTPException(status_code=400, detail="Invalid PDF path")

        try:
            full_text = extract_pdf_text(pdf_path)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"PDF parse error: {exc}") from exc

        work.pdf_path = str(pdf_path)
        work.full_text = full_text
        work.updated_at = datetime.now(timezone.utc)
        session.add(work)
        session.commit()
        session.refresh(work)

    return {"id": work.id, "pdf_path": work.pdf_path}


@app.delete("/api/literature/works/{work_id}/attach-pdf")
async def detach_pdf_from_work(work_id: int) -> dict:
    with Session(engine) as session:
        work = session.get(LiteratureWork, work_id)
        if not work:
            raise HTTPException(status_code=404, detail="Work not found")
        work.pdf_path = None
        work.full_text = None
        work.updated_at = datetime.now(timezone.utc)
        session.add(work)
        session.commit()
        session.refresh(work)
    return {"id": work.id, "pdf_path": work.pdf_path}
