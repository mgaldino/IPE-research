import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import text

from app.artifacts import IDEA_LAYOUT, write_council_memos, write_dossier_parts
from app.migrations import apply_migrations
from app.modes import MODE_IDEATION, get_mode_config
from app.models import CouncilMemo, DossierKind, DossierPart
from app.prompts import build_prompt


class CoreRefactorTest(unittest.TestCase):
    def test_mode_config_and_prompt_set(self) -> None:
        config = get_mode_config(MODE_IDEATION)
        self.assertEqual(config.prompt_set, "ideation")

        prompt = build_prompt("pitch", mode=config.prompt_set)
        self.assertIn("Produce a single idea dossier", prompt)

        with self.assertRaises(ValueError):
            build_prompt("pitch", mode="unknown")

    def test_migrations_are_idempotent(self) -> None:
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            apply_migrations(session)
            session.commit()
            apply_migrations(session)
            session.commit()
            result = session.exec(text("SELECT COUNT(*) FROM schema_migrations")).one()
        self.assertGreater(result[0], 0)

    def test_artifact_writers(self) -> None:
        now = datetime.now(timezone.utc)
        parts = [
            DossierPart(idea_id=1, kind=DossierKind.pitch, content="First", updated_at=now),
            DossierPart(
                idea_id=1,
                kind=DossierKind.pitch,
                content="Second",
                updated_at=now + timedelta(seconds=10),
            ),
        ]
        memos = [CouncilMemo(idea_id=1, referee="Ref A", content="Memo A")]

        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            write_dossier_parts(base, IDEA_LAYOUT, parts, latest_only=True)
            write_council_memos(base / "council", memos)

            pitch_path = base / "PITCH.md"
            self.assertTrue(pitch_path.exists())
            self.assertEqual(pitch_path.read_text(encoding="utf-8").strip(), "Second")

            memo_path = base / "council" / "Ref_A.md"
            self.assertTrue(memo_path.exists())
            self.assertEqual(memo_path.read_text(encoding="utf-8").strip(), "Memo A")


if __name__ == "__main__":
    unittest.main()
