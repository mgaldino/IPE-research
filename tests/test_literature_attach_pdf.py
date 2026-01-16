import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfWriter
from sqlmodel import Session

from app.db import create_db_and_tables, engine
from app.main import app
from app.models import LiteratureQuery, LiteratureWork


class LiteratureAttachPdfTest(unittest.TestCase):
    def setUp(self) -> None:
        create_db_and_tables()
        with Session(engine) as session:
            query = LiteratureQuery(query="alignment", sources="openalex", per_source_limit=1)
            session.add(query)
            session.commit()
            session.refresh(query)
            self.query_id = query.id

            work = LiteratureWork(query_id=self.query_id, source="openalex", title="Test Work")
            session.add(work)
            session.commit()
            session.refresh(work)
            self.work_id = work.id

        pdf_dir = Path("/Users/manoelgaldino/Documents/DCP/Papers/CodexCouncil/literature/pdfs") / str(self.query_id)
        pdf_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_path = pdf_dir / "test_attach.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with self.pdf_path.open("wb") as f:
            writer.write(f)

        self.client = TestClient(app)

    def tearDown(self) -> None:
        with Session(engine) as session:
            work = session.get(LiteratureWork, self.work_id)
            if work:
                session.delete(work)
            query = session.get(LiteratureQuery, self.query_id)
            if query:
                session.delete(query)
            session.commit()
        if self.pdf_path.exists():
            self.pdf_path.unlink()
        engine.dispose()

    def test_attach_pdf_from_query_folder(self) -> None:
        response = self.client.post(
            f"/api/literature/works/{self.work_id}/attach-pdf",
            json={"filename": self.pdf_path.name},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn(str(self.query_id), payload["pdf_path"])


if __name__ == "__main__":
    unittest.main()
