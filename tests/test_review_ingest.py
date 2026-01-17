import shutil
import unittest
from pathlib import Path

from pypdf import PdfWriter
from fastapi.testclient import TestClient

from app.db import create_db_and_tables, engine
from app.main import app, BASE_DIR


def _write_test_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with path.open("wb") as handle:
        writer.write(handle)


class ReviewIngestTest(unittest.TestCase):
    def setUp(self) -> None:
        create_db_and_tables()
        self.client = TestClient(app)
        self.review_id = self._create_review({"review_type": "paper", "title": "Paper X"})

    def tearDown(self) -> None:
        from sqlmodel import Session
        from app.models import Review, ReviewArtifact, ReviewGateResult, ReviewSection

        with Session(engine) as session:
            session.exec(ReviewArtifact.__table__.delete())
            session.exec(ReviewGateResult.__table__.delete())
            session.exec(ReviewSection.__table__.delete())
            session.exec(Review.__table__.delete())
            session.commit()
        engine.dispose()
        review_dir = BASE_DIR / "reviews"
        if review_dir.exists():
            shutil.rmtree(review_dir, ignore_errors=True)

    def test_attach_pdf_indexes_sections(self) -> None:
        pdf_dir = BASE_DIR / "reviews" / "pdfs" / str(self.review_id)
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / "test.pdf"
        _write_test_pdf(pdf_path)

        response = self.client.post(
            f"/api/reviews/{self.review_id}/attach-pdf",
            json={"filename": "test.pdf"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(payload["sections"], 1)

        detail = self.client.get(f"/api/reviews/{self.review_id}")
        self.assertEqual(detail.status_code, 200)
        detail_payload = detail.json()
        self.assertGreaterEqual(len(detail_payload["sections"]), 1)
        artifacts = detail_payload["artifacts"]
        kinds = {artifact["kind"] for artifact in artifacts}
        self.assertIn("REFEREE_MEMO", kinds)
        self.assertIn("REVISION_CHECKLIST", kinds)
        memo = next(a["content"] for a in artifacts if a["kind"] == "REFEREE_MEMO")
        self.assertIn("Review type: paper", memo)
        self.assertIn("Expectations: Journal-standard", memo)

    def test_project_level_expectations(self) -> None:
        review_id = self._create_review(
            {"review_type": "project", "level": "Mestrado", "title": "Project Y", "language": "pt"}
        )
        pdf_dir = BASE_DIR / "reviews" / "pdfs" / str(review_id)
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / "project.pdf"
        _write_test_pdf(pdf_path)

        response = self.client.post(
            f"/api/reviews/{review_id}/attach-pdf",
            json={"filename": "project.pdf"},
        )
        self.assertEqual(response.status_code, 200)
        detail = self.client.get(f"/api/reviews/{review_id}")
        self.assertEqual(detail.status_code, 200)
        artifacts = detail.json()["artifacts"]
        memo = next(a["content"] for a in artifacts if a["kind"] == "REFEREE_MEMO")
        self.assertIn("Nivel: Mestrado", memo)
        self.assertIn("Expectativas: Teoria coerente e desenho viavel", memo)

    def _create_review(self, payload: dict) -> int:
        response = self.client.post("/api/reviews", json=payload)
        return response.json()["review_id"]


if __name__ == "__main__":
    unittest.main()
