import unittest
from pathlib import Path
from unittest.mock import patch

from sqlmodel import Session, select

from app.db import create_db_and_tables, engine
from app.literature import run_literature_query
from app.models import LiteratureQuery, LiteratureWork


class LiteratureEnrichmentTest(unittest.TestCase):
    def setUp(self) -> None:
        create_db_and_tables()
        with Session(engine) as session:
            query = LiteratureQuery(query="sanctions enforcement", sources="openalex", per_source_limit=1)
            session.add(query)
            session.commit()
            session.refresh(query)
            self.query_id = query.id

    def tearDown(self) -> None:
        with Session(engine) as session:
            works = session.exec(select(LiteratureWork).where(LiteratureWork.query_id == self.query_id)).all()
            for work in works:
                session.delete(work)
            query = session.get(LiteratureQuery, self.query_id)
            if query:
                session.delete(query)
            session.commit()
        engine.dispose()
        assessment_path = Path("/Users/manoelgaldino/Documents/DCP/Papers/CodexCouncil/literature/assessments")
        for path in assessment_path.glob(f"assessment_{self.query_id}.md"):
            path.unlink()
        pdf_dir = Path("/Users/manoelgaldino/Documents/DCP/Papers/CodexCouncil/literature/pdfs") / str(self.query_id)
        if pdf_dir.exists():
            for path in pdf_dir.glob("*.pdf"):
                path.unlink()

    @patch("app.literature.fetch_openalex_by_doi")
    @patch("app.literature.fetch_semantic_scholar")
    @patch("app.literature.fetch_crossref")
    @patch("app.literature.fetch_openalex")
    def test_enrichment_fills_venue(self, mock_openalex, mock_crossref, mock_semantic, mock_openalex_by_doi):
        mock_openalex.return_value = [
            {
                "source": "openalex",
                "title": "What Friends are Made of",
                "authors": "Author",
                "year": 2014,
                "venue": None,
                "doi": "https://doi.org/10.1111/fpa.12050",
                "abstract": "text",
                "open_access_url": None,
            }
        ]
        mock_crossref.return_value = []
        mock_semantic.return_value = []
        mock_openalex_by_doi.return_value = {"venue": "Foreign Policy Analysis"}

        base_dir = Path("/Users/manoelgaldino/Documents/DCP/Papers/CodexCouncil")
        run_literature_query(
            query_id=self.query_id,
            query="sanctions enforcement",
            sources=["openalex"],
            per_source_limit=1,
            base_dir=base_dir,
            openalex_email="test@example.com",
            semantic_scholar_key=None,
        )

        with Session(engine) as session:
            work = session.exec(
                select(LiteratureWork).where(LiteratureWork.query_id == self.query_id)
            ).first()
            self.assertIsNotNone(work)
            self.assertEqual(work.venue, "Foreign Policy Analysis")


if __name__ == "__main__":
    unittest.main()
