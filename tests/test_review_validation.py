import unittest

from app.review_validation import validate_review_output


class ReviewValidationTest(unittest.TestCase):
    def test_validation_flags_missing_quote(self) -> None:
        checklist = "\n".join([
            "REVISION_CHECKLIST",
            "- Major issues (3 items)",
            "- Section: S1 Issue: Missing theory Suggested fix: Add theory.",
            "- Minor issues (3 items)",
            "- Section: S2 Issue: Vague scope Suggested fix: Tighten scope.",
        ])
        errors = validate_review_output(checklist, ["S1", "S2"])
        self.assertTrue(any("Minor item missing Quote line" in error for error in errors))

    def test_validation_accepts_quote(self) -> None:
        checklist = "\n".join([
            "REVISION_CHECKLIST",
            "- Major issues (3 items)",
            "- Section: S1 Issue: Missing theory Suggested fix: Add theory.",
            "- Minor issues (3 items)",
            "- Section: S2 Issue: Vague scope Suggested fix: Tighten scope.",
            "Quote: \"test\"",
        ])
        errors = validate_review_output(checklist, ["S1", "S2"])
        self.assertFalse(errors)


if __name__ == "__main__":
    unittest.main()
