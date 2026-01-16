import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import DossierPart, DossierKind, CouncilMemo

REQUIRED_FILES = {
    "PLAN.md": "# PLAN\n\nActive work queue and checkpoints.\n",
    "BACKLOG.md": "# BACKLOG\n\nIdea pool with tags and rejection reasons.\n",
    "FRONTIER_MAP.md": "# FRONTIER_MAP\n\nLiving frontier review of IPE debates and bottlenecks.\n",
    "DESIGN_PLAYBOOK.md": "# DESIGN_PLAYBOOK\n\nHouse standards for DiD/SCM/Shift-Share/Ideal points (design-only).\n",
    "DATA_CATALOG.md": "# DATA_CATALOG\n\nCandidate datasets and access notes (no scraping/extraction).\n",
    "EVAL_RUBRIC.md": "# EVAL_RUBRIC\n\nCouncil scoring rubric, thresholds, veto rules.\n",
    "DECISIONS.md": "# DECISIONS\n\nPI decisions and rationale.\n",
}


def ensure_required_files(base_dir: Path) -> None:
    for filename, content in REQUIRED_FILES.items():
        path = base_dir / filename
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def _write_markdown(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


def export_idea_markdown(
    base_dir: Path,
    idea_id: int,
    dossier_parts: Iterable[DossierPart],
    council_memos: Iterable[CouncilMemo],
) -> None:
    idea_dir = base_dir / "ideas" / str(idea_id)
    council_dir = idea_dir / "council"
    os.makedirs(council_dir, exist_ok=True)

    kind_to_filename = {
        DossierKind.pitch: "PITCH.md",
        DossierKind.design: "DESIGN.md",
        DossierKind.data_plan: "DATA_PLAN.md",
        DossierKind.positioning: "POSITIONING.md",
        DossierKind.next_steps: "NEXT_STEPS.md",
    }

    for part in dossier_parts:
        filename = kind_to_filename.get(part.kind)
        if filename:
            _write_markdown(idea_dir / filename, part.content)

    for memo in council_memos:
        safe_ref = memo.referee.replace(" ", "_")
        memo_path = council_dir / f"{safe_ref}.md"
        _write_markdown(memo_path, memo.content)


def snapshot_idea_version(
    base_dir: Path,
    idea_id: int,
    dossier_parts: Iterable[DossierPart],
    council_memos: Iterable[CouncilMemo],
    label: str,
    metadata: str | None = None,
) -> str:
    versions_dir = base_dir / "ideas" / str(idea_id) / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    version_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    version_dir = versions_dir / version_id
    version_dir.mkdir(parents=True, exist_ok=True)
    council_dir = version_dir / "council"
    council_dir.mkdir(parents=True, exist_ok=True)

    latest_parts: dict[DossierKind, DossierPart] = {}
    for part in dossier_parts:
        current = latest_parts.get(part.kind)
        if not current or part.updated_at >= current.updated_at:
            latest_parts[part.kind] = part

    kind_to_filename = {
        DossierKind.pitch: "PITCH.md",
        DossierKind.design: "DESIGN.md",
        DossierKind.data_plan: "DATA_PLAN.md",
        DossierKind.positioning: "POSITIONING.md",
        DossierKind.next_steps: "NEXT_STEPS.md",
    }

    for kind, part in latest_parts.items():
        filename = kind_to_filename.get(kind)
        if filename:
            _write_markdown(version_dir / filename, part.content)

    for memo in council_memos:
        safe_ref = memo.referee.replace(" ", "_")
        memo_path = council_dir / f"{safe_ref}.md"
        _write_markdown(memo_path, memo.content)

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    version_meta = "\n".join([
        f"Version: {version_id}",
        f"Created: {created_at} UTC",
        f"Label: {label}",
        "",
        metadata or "",
    ])
    _write_markdown(version_dir / "VERSION.md", version_meta)
    return version_id
