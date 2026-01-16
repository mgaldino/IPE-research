import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from sqlmodel import Session, select

from .crypto import decrypt_secret
from .db import engine
from .files import export_idea_markdown
from .models import (
    AgentMemo,
    CouncilMemo,
    CouncilRound,
    DossierKind,
    DossierPart,
    GateResult,
    GateStatus,
    Idea,
    ProviderCredential,
    Run,
    RunStatus,
    LiteratureAssessment,
)
from .modes import MODE_IDEATION, get_mode_config
from .prompts import build_prompt
from .providers.anthropic_provider import AnthropicProvider
from .providers.gemini_provider import GeminiProvider
from .providers.openai_provider import OpenAIProvider

PROVIDERS = {
    "openai": OpenAIProvider(),
    "anthropic": AnthropicProvider(),
    "gemini": GeminiProvider(),
}

DEFAULT_MODELS = {
    "openai": "gpt-5-nano",
    "anthropic": "claude-3-5-sonnet-20240620",
    "gemini": "gemini-1.5-flash",
}


def _parse_header_value(content: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}\s*:\s*(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else None


def _parse_title(content: str) -> str | None:
    match = re.search(r"^Working title\s*:?\s*(.+)$", content, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _parse_big_claim(content: str) -> str | None:
    match = re.search(r"^One-sentence big claim\s*:?\s*(.+)$", content, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _gate1_status(pitch: str) -> tuple[GateStatus, str]:
    lane_primary = _parse_header_value(pitch, "LANE_PRIMARY")
    breakthrough = _parse_header_value(pitch, "BREAKTHROUGH_TYPE")
    why = _parse_header_value(pitch, "WHY_THIS_IS_BREAKTHROUGH")
    missing = []
    if not lane_primary:
        missing.append("LANE_PRIMARY")
    if not breakthrough:
        missing.append("BREAKTHROUGH_TYPE")
    if not why:
        missing.append("WHY_THIS_IS_BREAKTHROUGH")
    if missing:
        return GateStatus.failed, f"Missing required fields: {', '.join(missing)}"
    return GateStatus.passed, ""


def _build_gate1_retry_prompt(pitch: str) -> str:
    return "\n\n".join([
        "The draft below is missing required header fields.",
        "Rewrite the pitch to include this header block at the very top:",
        "- LANE_PRIMARY: <one lane from catalog>",
        "- LANE_SECONDARY: <optional; up to two>",
        "- BREAKTHROUGH_TYPE: <one or more types>",
        "- WHY_THIS_IS_BREAKTHROUGH: <5-10 lines>",
        "Then follow the PITCH template exactly.",
        "Do not omit any required fields.",
        "Return only the corrected PITCH.md content.",
        "",
        "Draft to fix:",
        pitch.strip(),
    ])


def _build_gate1_retry_prompt_with_base(base_prompt: str, draft: str) -> str:
    return "\n\n".join([
        base_prompt.strip(),
        "CRITICAL FIX: Your last output missed required header fields.",
        "The header block must be the first lines of the output.",
        "Return only the corrected PITCH.md content.",
        "",
        "Previous draft:",
        draft.strip(),
    ])


def _split_council_memos(content: str) -> List[str]:
    parts = [part.strip() for part in content.split("---") if part.strip()]
    return parts if parts else [content.strip()]


def _extract_assessment_prompts(assessment: str | None) -> List[str]:
    if not assessment:
        return []
    lines = assessment.splitlines()
    start_idx = None
    for idx, line in enumerate(lines):
        if "idea prompt" in line.lower():
            start_idx = idx + 1
            break
    if start_idx is None:
        return []
    prompts: List[str] = []
    for line in lines[start_idx:]:
        stripped = line.strip()
        if not stripped:
            if prompts:
                break
            continue
        if stripped.startswith("##"):
            break
        bullet_match = re.match(r"^[-*]\s+(.*)", stripped)
        if bullet_match:
            prompts.append(bullet_match.group(1).strip())
            continue
        numbered_match = re.match(r"^\d+[).]\s+(.*)", stripped)
        if numbered_match:
            prompts.append(numbered_match.group(1).strip())
            continue
        if prompts:
            prompts[-1] = f"{prompts[-1]} {stripped}"
    return prompts


def _next_council_round(session: Session, idea_id: int) -> int:
    last_round = session.exec(
        select(CouncilRound)
        .where(CouncilRound.idea_id == idea_id)
        .order_by(CouncilRound.round_number.desc())
    ).first()
    return (last_round.round_number + 1) if last_round else 1


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


def _build_memo(role: str, topic: str, content: str) -> str:
    return "\n".join([
        f"Context: {role} produced {topic} for the idea dossier.",
        "Decision/Recommendation: Review and route for gate checks.",
        "Evidence or reasoning: Generated by the agent per template.",
        "Next action (owner): PI Proxy Agent to log and enforce gates.",
        "",
        content.strip(),
    ])


async def run_swarm(run_id: int, passphrase: str, base_dir: Path) -> None:
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if not run:
            return
        run_provider = run.provider
        run_model = run.model
        run_idea_count = run.idea_count
        run_topic_focus = run.topic_focus
        run_literature_query_id = run.literature_query_id
        run_use_assessment_seeds = run.use_assessment_seeds
        run.status = RunStatus.running
        run.updated_at = datetime.now(timezone.utc)
        session.add(run)
        session.commit()

    try:
        with Session(engine) as session:
            credential = session.exec(
                select(ProviderCredential)
                .where(ProviderCredential.provider == run_provider)
                .order_by(ProviderCredential.created_at.desc())
            ).first()
            if not credential:
                raise RuntimeError("Missing credentials for provider")
            api_key = decrypt_secret(passphrase, credential.api_key_encrypted, credential.salt)

        provider = PROVIDERS[run_provider]
        mode_config = get_mode_config(MODE_IDEATION)
        assessment_text = None
        assessment_seeds: List[str] = []
        if run_literature_query_id:
            with Session(engine) as session:
                assessment = session.exec(
                    select(LiteratureAssessment)
                    .where(LiteratureAssessment.query_id == run_literature_query_id)
                ).first()
                if assessment:
                    assessment_text = assessment.content
                    if run_use_assessment_seeds:
                        assessment_seeds = _extract_assessment_prompts(assessment_text)

        for idx in range(run_idea_count):
            idea_seed = None
            if assessment_seeds and idx < len(assessment_seeds):
                idea_seed = assessment_seeds[idx]
            with Session(engine) as session:
                idea = Idea(run_id=run_id)
                session.add(idea)
                session.commit()
                session.refresh(idea)
                idea_id = idea.id

            pitch_prompt = build_prompt(
                "pitch",
                run_topic_focus,
                assessment_text,
                idea_seed,
                mode=mode_config.prompt_set,
            )
            pitch_response = await provider.generate(pitch_prompt, run_model, api_key)
            pitch_content = pitch_response.content
            gate_status, gate_notes = _gate1_status(pitch_content)
            if gate_status == GateStatus.failed:
                retry_prompt = _build_gate1_retry_prompt_with_base(pitch_prompt, pitch_content)
                retry_response = await provider.generate(retry_prompt, run_model, api_key)
                pitch_content = retry_response.content
                gate_status, gate_notes = _gate1_status(pitch_content)
                if gate_status == GateStatus.failed:
                    retry_prompt = _build_gate1_retry_prompt(pitch_content)
                    retry_response = await provider.generate(retry_prompt, run_model, api_key)
                    pitch_content = retry_response.content
                    gate_status, gate_notes = _gate1_status(pitch_content)

            with Session(engine) as session:
                idea = session.get(Idea, idea_id)
                idea.title = _parse_title(pitch_content)
                idea.big_claim = _parse_big_claim(pitch_content)
                idea.lane_primary = _parse_header_value(pitch_content, "LANE_PRIMARY")
                idea.lane_secondary = _parse_header_value(pitch_content, "LANE_SECONDARY")
                idea.breakthrough_type = _parse_header_value(pitch_content, "BREAKTHROUGH_TYPE")
                idea.updated_at = datetime.now(timezone.utc)
                session.add(idea)
                session.add(DossierPart(idea_id=idea_id, kind=DossierKind.pitch, content=pitch_content))
                session.add(GateResult(idea_id=idea_id, gate=1, status=gate_status, notes=gate_notes))
                session.commit()

            memo_content = _build_memo("Ideator Agent", "PITCH.md", pitch_content)
            with Session(engine) as session:
                memo = AgentMemo(
                    run_id=run_id,
                    idea_id=idea_id,
                    direction="outbox",
                    sender="Ideator Agent",
                    topic="PITCH",
                    content=memo_content,
                )
                session.add(memo)
                session.commit()
                _write_mail_memo(base_dir, memo)

            with Session(engine) as session:
                parts = session.exec(select(DossierPart).where(DossierPart.idea_id == idea_id)).all()
                memos = session.exec(select(CouncilMemo).where(CouncilMemo.idea_id == idea_id)).all()
            export_idea_markdown(base_dir, idea_id, parts, memos)

            if gate_status != GateStatus.passed:
                continue

            design_prompt = build_prompt(
                "design",
                run_topic_focus,
                assessment_text,
                idea_seed,
                mode=mode_config.prompt_set,
            )
            design_response = await provider.generate(design_prompt, run_model, api_key)
            design_content = design_response.content

            data_prompt = build_prompt(
                "data",
                run_topic_focus,
                assessment_text,
                idea_seed,
                mode=mode_config.prompt_set,
            )
            data_response = await provider.generate(data_prompt, run_model, api_key)
            data_content = data_response.content

            positioning_prompt = build_prompt(
                "positioning",
                run_topic_focus,
                assessment_text,
                idea_seed,
                mode=mode_config.prompt_set,
            )
            positioning_response = await provider.generate(positioning_prompt, run_model, api_key)
            positioning_content = positioning_response.content

            next_steps_prompt = build_prompt(
                "next_steps",
                run_topic_focus,
                assessment_text,
                idea_seed,
                mode=mode_config.prompt_set,
            )
            next_steps_response = await provider.generate(next_steps_prompt, run_model, api_key)
            next_steps_content = next_steps_response.content

            council_prompt = build_prompt(
                "council",
                run_topic_focus,
                assessment_text,
                idea_seed,
                mode=mode_config.prompt_set,
            )
            council_response = await provider.generate(council_prompt, run_model, api_key)
            council_content = council_response.content

            with Session(engine) as session:
                session.add(DossierPart(idea_id=idea_id, kind=DossierKind.design, content=design_content))
                session.add(DossierPart(idea_id=idea_id, kind=DossierKind.data_plan, content=data_content))
                session.add(DossierPart(idea_id=idea_id, kind=DossierKind.positioning, content=positioning_content))
                session.add(DossierPart(idea_id=idea_id, kind=DossierKind.next_steps, content=next_steps_content))
                session.add(GateResult(idea_id=idea_id, gate=2, status=GateStatus.needs_revision))
                session.add(GateResult(idea_id=idea_id, gate=3, status=GateStatus.needs_revision))
                session.add(GateResult(idea_id=idea_id, gate=4, status=GateStatus.needs_revision))
                session.commit()

            for role, topic, content in [
                ("Theory Architect", "DESIGN.md", design_content),
                ("Data Feasibility Agent", "DATA_PLAN.md", data_content),
                ("Measurement Agent", "POSITIONING.md", positioning_content),
                ("PI Proxy Agent", "NEXT_STEPS.md", next_steps_content),
            ]:
                memo_content = _build_memo(role, topic, content)
                with Session(engine) as session:
                    memo = AgentMemo(
                        run_id=run_id,
                        idea_id=idea_id,
                        direction="outbox",
                        sender=role,
                        topic=topic,
                        content=memo_content,
                    )
                    session.add(memo)
                    session.commit()
                    _write_mail_memo(base_dir, memo)

            memos = _split_council_memos(council_content)
            with Session(engine) as session:
                round_number = _next_council_round(session, idea_id)
                council_round = CouncilRound(
                    idea_id=idea_id,
                    round_number=round_number,
                    status="generated",
                )
                session.add(council_round)
                session.commit()
                session.refresh(council_round)
                for idx, memo_text in enumerate(memos, start=1):
                    referee = f"Referee {chr(64 + idx)}" if idx <= 5 else f"Referee {idx}"
                    session.add(CouncilMemo(
                        idea_id=idea_id,
                        round_id=council_round.id,
                        referee=referee,
                        content=memo_text,
                    ))
                session.commit()

            memo_content = _build_memo("Council Agents", "council memos", council_content)
            with Session(engine) as session:
                memo = AgentMemo(
                    run_id=run_id,
                    idea_id=idea_id,
                    direction="outbox",
                    sender="Council Agents",
                    topic="Council",
                    content=memo_content,
                )
                session.add(memo)
                session.commit()
                _write_mail_memo(base_dir, memo)

            with Session(engine) as session:
                parts = session.exec(select(DossierPart).where(DossierPart.idea_id == idea_id)).all()
                memos = session.exec(select(CouncilMemo).where(CouncilMemo.idea_id == idea_id)).all()
            export_idea_markdown(base_dir, idea_id, parts, memos)

        with Session(engine) as session:
            run = session.get(Run, run_id)
            run.status = RunStatus.completed
            run.updated_at = datetime.now(timezone.utc)
            session.add(run)
            session.commit()

    except Exception as exc:
        with Session(engine) as session:
            run = session.get(Run, run_id)
            if run:
                run.status = RunStatus.failed
                run.log = str(exc)
                run.updated_at = datetime.now(timezone.utc)
                session.add(run)
                session.commit()
