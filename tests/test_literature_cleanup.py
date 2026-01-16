import unittest

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import create_db_and_tables, engine
from app.main import app
from app.models import LiteratureQuery, LiteratureWork


class LiteratureCleanupTest(unittest.TestCase):
    def setUp(self) -> None:
        create_db_and_tables()
        with Session(engine) as session:
            query = LiteratureQuery(query="lio", sources="openalex", per_source_limit=1)
            session.add(query)
            session.commit()
            session.refresh(query)
            self.query_id = query.id

            session.add(LiteratureWork(
                query_id=self.query_id,
                source="crossref",
                title="Book Chapter",
                work_type="book-chapter",
            ))
            session.add(LiteratureWork(
                query_id=self.query_id,
                source="crossref",
                title="Journal Article",
                work_type="journal-article",
            ))
            session.commit()

        self.client = TestClient(app)

    def tearDown(self) -> None:
        with Session(engine) as session:
            works = session.exec(
                LiteratureWork.__table__.select().where(LiteratureWork.query_id == self.query_id)
            ).all()
            for row in works:
                session.exec(LiteratureWork.__table__.delete().where(LiteratureWork.id == row.id))
            query = session.get(LiteratureQuery, self.query_id)
            if query:
                session.delete(query)
            session.commit()
        engine.dispose()

    def test_cleanup_removes_books(self) -> None:
        response = self.client.post(f"/api/literature/queries/{self.query_id}/cleanup")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["removed"], 1)

        with Session(engine) as session:
            remaining = session.exec(
                LiteratureWork.__table__.select().where(LiteratureWork.query_id == self.query_id)
            ).all()
            titles = {row.title for row in remaining}
        self.assertIn("Journal Article", titles)
        self.assertNotIn("Book Chapter", titles)


if __name__ == "__main__":
    unittest.main()
