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
        response = self.client.post(
            "/api/reviews",
            json={"review_type": "paper", "title": "Paper X"},
        )
        self.review_id = response.json()["review_id"]

    def tearDown(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
