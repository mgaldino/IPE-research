import unittest

from app.prompts import build_review_prompt


class ReviewPromptTest(unittest.TestCase):
    def test_review_prompt_includes_sections_and_rules(self) -> None:
        prompt = build_review_prompt(
            review_type="paper",
            level=None,
            title="Test Paper",
            domain="IPE",
            method_family="DiD",
            language="pt",
            sections=[
                {
                    "section_id": "S1",
                    "title": "Introduction",
                    "page_start": 1,
                    "page_end": 2,
                    "excerpt": "This paper studies...",
                }
            ],
        )
        self.assertIn("Review type: paper", prompt)
        self.assertIn("Sections:", prompt)
        self.assertIn("S1 Introduction", prompt)
        self.assertIn("REFEREE_MEMO", prompt)
        self.assertIn("REVISION_CHECKLIST", prompt)
        self.assertIn('Use section IDs exactly as provided (format S#).', prompt)
        self.assertIn('For minor issues, put the quote on its own line labeled "Quote:".', prompt)
        self.assertIn("Output in Portuguese.", prompt)
        self.assertIn("Persona-focused assessment", prompt)


if __name__ == "__main__":
    unittest.main()
