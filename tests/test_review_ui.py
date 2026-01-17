import unittest
from pathlib import Path


class ReviewUiTest(unittest.TestCase):
    def test_review_section_exists(self) -> None:
        html = Path("static/index.html").read_text(encoding="utf-8")
        self.assertIn('id="review-form"', html)
        self.assertIn('id="review-list"', html)
        self.assertIn('id="review-warning"', html)
        self.assertIn('id="review-detail"', html)
        self.assertIn('id="review-attach"', html)
        self.assertIn('id="review-upload"', html)
        self.assertIn('id="review-language"', html)
        self.assertIn('id="review-provider"', html)
        self.assertIn('id="review-model"', html)
        self.assertIn('id="review-run"', html)


if __name__ == "__main__":
    unittest.main()
