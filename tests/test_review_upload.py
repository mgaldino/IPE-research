import io
import shutil
import unittest

from fastapi.testclient import TestClient

from app.db import create_db_and_tables, engine
from app.main import app, BASE_DIR


class ReviewUploadTest(unittest.TestCase):
    def setUp(self) -> None:
        create_db_and_tables()
        self.client = TestClient(app)
        response = self.client.post(
            "/api/reviews",
            json={"review_type": "paper", "title": "Paper Upload"},
        )
        self.review_id = response.json()["review_id"]

    def tearDown(self) -> None:
        engine.dispose()
        review_dir = BASE_DIR / "reviews"
        if review_dir.exists():
            shutil.rmtree(review_dir, ignore_errors=True)

    def test_upload_pdf(self) -> None:
        file_content = b"%PDF-1.4\n%Test\n"
        response = self.client.post(
            f"/api/reviews/{self.review_id}/upload-pdf",
            files={"file": ("paper.pdf", io.BytesIO(file_content), "application/pdf")},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["filename"], "paper.pdf")

        stored = BASE_DIR / "reviews" / "pdfs" / str(self.review_id) / "paper.pdf"
        self.assertTrue(stored.exists())


if __name__ == "__main__":
    unittest.main()
