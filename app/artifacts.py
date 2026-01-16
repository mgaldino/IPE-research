from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import CouncilMemo, DossierKind, DossierPart, ReviewArtifact, ReviewArtifactKind


@dataclass(frozen=True)
class ArtifactLayout:
    kind_to_filename: dict[DossierKind, str]


IDEA_LAYOUT = ArtifactLayout(
    kind_to_filename={
        DossierKind.pitch: "PITCH.md",
        DossierKind.design: "DESIGN.md",
        DossierKind.data_plan: "DATA_PLAN.md",
        DossierKind.positioning: "POSITIONING.md",
        DossierKind.next_steps: "NEXT_STEPS.md",
    }
)

REVIEW_LAYOUT = {
    ReviewArtifactKind.referee_memo: "REFEREE_MEMO.md",
    ReviewArtifactKind.revision_checklist: "REVISION_CHECKLIST.md",
}


def write_dossier_parts(
    target_dir: Path,
    layout: ArtifactLayout,
    parts: Iterable[DossierPart],
    *,
    latest_only: bool = False,
) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    parts_to_write = _latest_parts(parts) if latest_only else list(parts)
    for part in parts_to_write:
        filename = layout.kind_to_filename.get(part.kind)
        if filename:
            _write_markdown(target_dir / filename, part.content)


def write_council_memos(target_dir: Path, memos: Iterable[CouncilMemo]) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for memo in memos:
        safe_ref = memo.referee.replace(" ", "_")
        memo_path = target_dir / f"{safe_ref}.md"
        _write_markdown(memo_path, memo.content)


def write_review_artifacts(
    target_dir: Path,
    artifacts: Iterable[ReviewArtifact],
) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for artifact in artifacts:
        filename = REVIEW_LAYOUT.get(artifact.kind)
        if filename:
            _write_markdown(target_dir / filename, artifact.content)


def _latest_parts(parts: Iterable[DossierPart]) -> list[DossierPart]:
    latest: dict[DossierKind, DossierPart] = {}
    for part in parts:
        current = latest.get(part.kind)
        if not current or part.updated_at >= current.updated_at:
            latest[part.kind] = part
    return list(latest.values())


def _write_markdown(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")
