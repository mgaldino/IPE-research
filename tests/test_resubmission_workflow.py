import shutil
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db import create_db_and_tables, engine
from app.main import app, BASE_DIR
from app.models import (
    AgentMemo,
    CouncilMemo,
    DossierKind,
    DossierPart,
    GateResult,
    Idea,
    Run,
    RunStatus,
)


class ResubmissionWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        create_db_and_tables()
        with Session(engine) as session:
            run = Run(status=RunStatus.completed, provider="openai", model="gpt-4o-mini", idea_count=1)
            session.add(run)
            session.commit()
            session.refresh(run)
            self.run_id = run.id

            idea = Idea(run_id=run.id, title="Test Idea")
            session.add(idea)
            session.commit()
            session.refresh(idea)
            self.idea_id = idea.id

            parts = [
                DossierPart(idea_id=idea.id, kind=DossierKind.pitch, content="Working title: Test"),
                DossierPart(idea_id=idea.id, kind=DossierKind.design, content="Research question: Test"),
                DossierPart(idea_id=idea.id, kind=DossierKind.data_plan, content="Candidate datasets: Test"),
            ]
            session.add_all(parts)
            memo = CouncilMemo(
                idea_id=idea.id,
                referee="Referee A",
                content="\n".join([
                    "Verdict: revise",
                    "Required revisions (ranked)",
                    "- tighten estimand definition",
                    "- expand falsification plan",
                    "Scores: novelty 8/10",
                ]),
            )
            session.add(memo)
            session.commit()

        self.client = TestClient(app)

    def tearDown(self) -> None:
        with Session(engine) as session:
            session.exec(AgentMemo.__table__.delete().where(AgentMemo.idea_id == self.idea_id))
            session.exec(CouncilMemo.__table__.delete().where(CouncilMemo.idea_id == self.idea_id))
            session.exec(DossierPart.__table__.delete().where(DossierPart.idea_id == self.idea_id))
            session.exec(GateResult.__table__.delete().where(GateResult.idea_id == self.idea_id))
            idea = session.get(Idea, self.idea_id)
            if idea:
                session.delete(idea)
            run = session.get(Run, self.run_id)
            if run:
                session.delete(run)
            session.commit()
        engine.dispose()

        idea_dir = BASE_DIR / "ideas" / str(self.idea_id)
        if idea_dir.exists():
            shutil.rmtree(idea_dir, ignore_errors=True)

    def test_resubmission_creates_version_and_updates_status(self) -> None:
        response = self.client.post(
            f"/api/ideas/{self.idea_id}/council/resubmit",
            json={"run_review": False, "apply_revisions": True},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "resubmitted")
        self.assertIn("version_id", payload)

        idea_response = self.client.get(f"/api/ideas/{self.idea_id}")
        self.assertEqual(idea_response.status_code, 200)
        idea_data = idea_response.json()
        self.assertEqual(idea_data["idea"]["status"], "resubmitted")

        versions_response = self.client.get(f"/api/ideas/{self.idea_id}/versions")
        self.assertEqual(versions_response.status_code, 200)
        versions = versions_response.json()
        self.assertTrue(any(v["id"] == payload["version_id"] for v in versions))

        version_response = self.client.get(
            f"/api/ideas/{self.idea_id}/versions/{payload['version_id']}"
        )
        self.assertEqual(version_response.status_code, 200)
        version_payload = version_response.json()
        self.assertIn("Label: pre-resubmission", version_payload["metadata"])
        kinds = {part["kind"] for part in version_payload["dossier_parts"]}
        self.assertIn("PITCH", kinds)
        self.assertIn("DESIGN", kinds)


if __name__ == "__main__":
    unittest.main()
