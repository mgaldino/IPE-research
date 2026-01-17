import unittest

from app.review_validation import split_review_output


class ReviewSplitTest(unittest.TestCase):
    def test_split_with_marker(self) -> None:
        content = "\n".join([
            "REFEREE_MEMO",
            "Line 1",
            "REVISION_CHECKLIST",
            "- Item",
        ])
        memo, checklist = split_review_output(content)
        self.assertIn("REFEREE_MEMO", memo)
        self.assertIn("REVISION_CHECKLIST", checklist)

    def test_split_with_alt_marker(self) -> None:
        content = "\n".join([
            "REFEREE_MEMO",
            "Line 1",
            "REVISION CHECKLIST",
            "- Item",
        ])
        memo, checklist = split_review_output(content)
        self.assertIn("REFEREE_MEMO", memo)
        self.assertTrue(checklist.startswith("REVISION_CHECKLIST"))

    def test_split_without_marker(self) -> None:
        content = "REFEREE_MEMO\nOnly memo text"
        memo, checklist = split_review_output(content)
        self.assertEqual(memo, content)
        self.assertIn("REVISION_CHECKLIST", checklist)


if __name__ == "__main__":
    unittest.main()
