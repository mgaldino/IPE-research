# Review Harness

Minimal evaluation harness for Review outputs. It validates format and grounding rules
without calling LLMs. Add cases to `review_cases.json` and optional expected outputs
in `fixtures/`.

Run:
```bash
. .venv/bin/activate
python scripts/run_review_harness.py
```
