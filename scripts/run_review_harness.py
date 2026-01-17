from __future__ import annotations

import json
from pathlib import Path

from app.review_validation import split_review_output, validate_review_output


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cases_path = root / "harness" / "review_cases.json"
    if not cases_path.exists():
        print("Missing harness/review_cases.json")
        return 1

    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    failures = 0
    for case in cases:
        case_id = case.get("id", "unknown")
        output_path = root / case.get("output_path", "")
        if not output_path.exists():
            print(f"[SKIP] {case_id}: missing output {output_path}")
            continue
        content = output_path.read_text(encoding="utf-8")
        _, checklist = split_review_output(content)
        errors = validate_review_output(checklist, case.get("sections", []))
        if errors:
            failures += 1
            print(f"[FAIL] {case_id}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[OK] {case_id}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
