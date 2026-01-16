import unittest

from sqlmodel import SQLModel, Session, create_engine, select

from app.models import (
    Review,
    ReviewArtifact,
    ReviewArtifactKind,
    ReviewGateResult,
    ReviewStatus,
    ReviewType,
    ProjectLevel,
    GateStatus,
)


class ReviewModelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_review_tables_and_relations(self) -> None:
        with Session(self.engine) as session:
            review = Review(
                review_type=ReviewType.project,
                level=ProjectLevel.mestrado,
                status=ReviewStatus.queued,
                title="Test Project",
                domain="IPE",
                method_family="DiD",
            )
            session.add(review)
            session.commit()
            session.refresh(review)

            memo = ReviewArtifact(
                review_id=review.id,
                kind=ReviewArtifactKind.referee_memo,
                content="Referee memo content",
            )
            gate = ReviewGateResult(
                review_id=review.id,
                gate=1,
                status=GateStatus.needs_revision,
                notes="Missing estimand clarity",
            )
            session.add(memo)
            session.add(gate)
            session.commit()

            loaded = session.exec(select(Review).where(Review.id == review.id)).one()
            self.assertEqual(loaded.level, ProjectLevel.mestrado)

            memo_loaded = session.exec(
                select(ReviewArtifact).where(ReviewArtifact.review_id == review.id)
            ).one()
            self.assertEqual(memo_loaded.kind, ReviewArtifactKind.referee_memo)

            gate_loaded = session.exec(
                select(ReviewGateResult).where(ReviewGateResult.review_id == review.id)
            ).one()
            self.assertEqual(gate_loaded.status, GateStatus.needs_revision)


if __name__ == "__main__":
    unittest.main()
