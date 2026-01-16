from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModeConfig:
    mode_id: str
    prompt_set: str
    rubric_path: Path


MODE_IDEATION = "ideation"

MODE_CONFIGS = {
    MODE_IDEATION: ModeConfig(
        mode_id=MODE_IDEATION,
        prompt_set="ideation",
        rubric_path=Path("EVAL_RUBRIC.md"),
    ),
}


def get_mode_config(mode_id: str) -> ModeConfig:
    config = MODE_CONFIGS.get(mode_id)
    if not config:
        raise ValueError(f"Unknown mode: {mode_id}")
    return config
