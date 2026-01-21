# 90-Day Plan: Review Mode v1 (IPE-only) + Grounding

Status: Review mode v1 delivered (paper/project, PDF ingestion, grounded artifacts, LLM run, validation warnings). Remaining items focus on evaluation harness, UI PDF upload, and stricter output enforcement.

Goal: Ship a trusted Review mode within the existing app, without building domain-pack infrastructure yet.
Success is measured by concrete improvements in review quality and traceability, not by breadth.

## Month 1 — Review v1 in IPE (minimal scope)
Milestone: Review mode workflow live, using current council personas and no-execution constraints (method-agnostic review).

Key deliverables:
- Review workflow (UI + API) parallel to Ideation workflow.
- Input: PDF + optional metadata (target journal tier, contribution type, method).
- Support review types:
  - Paper: single standard, journal-style referee report.
- Project: IC / Mestrado / Doutorado / Research Grant expectations.
- Output: “Referee Memo + Revision Checklist” artifact with a fixed template.
- Gate logic for Review mode (basic pass/fail + scores).

Success criteria:
- Users can submit a paper and receive a structured review in one flow.
- 100% of review critiques include a section anchor (from extracted structure).

## Month 2 — Grounding + traceability
Milestone: Review critiques are anchored to document evidence.

Key deliverables:
- Ingestion pipeline: PDF -> structured text with section IDs.
- Evidence rules: each critique must include a short quote or paraphrase plus section ID.
- UI surfacing: show evidence snippet inline with critique.

Success criteria:
- 90%+ critiques include a traceable snippet and section ID.
- User feedback indicates “grounded review” vs generic feedback.

## Month 3 — Evaluation harness + hardening
Milestone: Review mode quality is testable and stable.

Key deliverables:
- Evaluation set (15–30 artifacts: papers + proposals).
- Rubric-based scoring harness aligned with council criteria.
- Regression tests for “grounding compliance” and rubric coverage.

Success criteria:
- Baseline scores recorded; regressions caught in tests.
- Review mode outputs stable across runs for fixed inputs.

## Out of scope (explicitly deferred)
- Domain packs / multi-field generalization.
- Full rubric/config system refactor.
- Broad “social science” expansion.
