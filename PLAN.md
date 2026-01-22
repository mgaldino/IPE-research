# PLAN

Active work queue and checkpoints.

## Work completed
- App scaffolded with FastAPI + SQLite, UI dashboard, and gate workflow.
- Literature review pipeline implemented (OpenAlex/Crossref/Semantic Scholar metadata, OA PDF download, local PDF ingest).
- Query management UI: run review, rebuild assessment, remove results, delete query.
- PDF tools: attach/detach PDFs, per-query PDF folders, OA download, assessment generation.
- Council gate workflow for IDEA-006 with memos and dossier files.
- Frontier map updated with LIO assessment gap note.
- EVAL rubric expanded with Lane Fit and Breakthrough Plausibility thresholds.
- DESIGN_PLAYBOOK expanded with concrete standards for DiD/SCM/Shift-Share/Ideal points.
- Council resubmission workflow with dossier version snapshots and round-scoped memos.
- Gate 4 auto-recompute from council memo scores/verdicts.
- LLM-based literature assessment from full text with token-budget selection.
- Literature assessment injection into idea generation prompts via run selection.
- Assessment-seeded idea generation (use assessment idea prompts).
- UI improvements: persistent run form state, LLM assessment controls, full-width works/assessment layout.
- Provider connectivity testing and model normalization (Gemini/OpenAI).
- Core refactor: mode-aware prompts, migration table, artifact writers.
- Review mode v2: paper/project reviews, persona selection, PDF ingestion, section indexing.
- Review artifacts: persona-based memo/checklist sets, LLM run, validation warnings in UI.
- Review PDF upload in UI (multipart).
- Review language toggle (EN/PT) and localized placeholders.
- Review evaluation harness (offline validation runner + fixtures).

## Current focus
- IDEA-006 is at Gate 4 with council memos; revisions pending.
- LIO query (ID 2) rebuilt and used for anchors; per-query PDFs now supported.
- Live LLM assessment and idea generation runs using OpenAI gpt-5-nano or Gemini 2.5-flash.

## Next pending items
- Expand DATA_CATALOG.md with concrete standards and sources.
- Add UI filters for journal/source/type and export lists of missing PDFs.
- Add PI decision logging in DECISIONS.md and UI shortcuts.
- Add UI indicator for assessment freshness (last-run timestamp).
- Tighten council scoring compliance (full rubric coverage and more conservative scoring).
- Build out the evaluation harness with 15–30 real artifacts and rubric-based regression checks.
- Enforce exact 3 major + 3 minor counts in Review output.

## Backlog (project-level)
- Dossier export improvements (batch export, zip per idea).
- Additional tests for resubmission and assessment endpoints.
- Align Review verdict with score rubric in prompt and validation.
- Enforce exact 3 major + 3 minor counts in Review validation (pending decision).
