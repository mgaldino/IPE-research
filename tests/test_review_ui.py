import unittest
from pathlib import Path


class ReviewUiTest(unittest.TestCase):
    def test_review_section_exists(self) -> None:
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn('id="review-form"', html)
        self.assertIn('id="review-list"', html)
        self.assertIn('id="review-detail"', html)


if __name__ == "__main__":
    unittest.main()
