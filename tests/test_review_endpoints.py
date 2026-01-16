import shutil
import unittest

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import create_db_and_tables, engine
from app.main import app, BASE_DIR
from app.models import Review, ReviewArtifact, ReviewGateResult


class ReviewEndpointsTest(unittest.TestCase):
    def setUp(self) -> None:
        create_db_and_tables()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        with Session(engine) as session:
            session.exec(ReviewArtifact.__table__.delete())
            session.exec(ReviewGateResult.__table__.delete())
            session.exec(Review.__table__.delete())
            session.commit()
        engine.dispose()

        review_dir = BASE_DIR / "reviews"
        if review_dir.exists():
            shutil.rmtree(review_dir, ignore_errors=True)

    def test_create_and_get_review(self) -> None:
        response = self.client.post(
            "/api/reviews",
            json={
                "review_type": "paper",
                "title": "Paper X",
                "domain": "IPE",
                "method_family": "DiD",
                "level": "Mestrado",
            },
        )
        self.assertEqual(response.status_code, 200)
        review_id = response.json()["review_id"]

        detail = self.client.get(f"/api/reviews/{review_id}")
        self.assertEqual(detail.status_code, 200)
        payload = detail.json()
        self.assertEqual(payload["review"]["review_type"], "paper")
        self.assertIsNone(payload["review"]["level"])

    def test_project_requires_level(self) -> None:
        response = self.client.post(
            "/api/reviews",
            json={
                "review_type": "project",
                "title": "Project Y",
                "domain": "IPE",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_list_reviews(self) -> None:
        self.client.post(
            "/api/reviews",
            json={"review_type": "paper", "title": "Paper A"},
        )
        self.client.post(
            "/api/reviews",
            json={"review_type": "project", "level": "IC", "title": "Project B"},
        )
        response = self.client.get("/api/reviews")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(len(payload), 2)


if __name__ == "__main__":
    unittest.main()
