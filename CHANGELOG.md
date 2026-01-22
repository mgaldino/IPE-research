# CHANGELOG

## 2026-01-21
- Added multi-persona review pipeline (3 reviewers per run) with persona selection and duplicate confirmation.
- Grouped review artifacts by persona/slot and labeled memos with reviewer persona.
- Simplified review workflow into a single “Run Review” CTA with auto-indexing.
- Added full-width Review Detail panel and capped Review Archive to latest items.
- Added global LLM provider/model settings shared across workflows.
- Added one-click local launchers for macOS and Windows.

## 2026-01-16
- Added review mode (paper/project) with PDF ingestion, section indexing, and grounded artifacts.
- Added LLM review run with APSR-level prompts and validation warnings.
- Added review UI (create, attach PDF, run review, view sections and artifacts).
- Added schema migrations table and artifact writer helpers.
- Added tests for review models, endpoints, prompts, parsing, and validation.

## 2025-02-14
- Expanded `EVAL_RUBRIC.md` with Lane Fit and Breakthrough Plausibility thresholds.
- Expanded `DESIGN_PLAYBOOK.md` with concrete standards for DiD/SCM/Shift-Share/Ideal points.
- Implemented council resubmission workflow with dossier version snapshots and round-scoped memos.
- Added Gate 4 auto-recompute based on council memo scores/verdicts.
- Added LLM-based literature assessment from full text with token-budget selection.
- Injected literature assessment into idea generation prompts via run selection.
- Added assessment-seeded idea generation (use assessment idea prompts as seeds).
- Added UI controls and persistence for run form and LLM assessment inputs.
- Moved works and assessment to full-width sections in the literature review UI.
- Added provider connectivity tests and model normalization for Gemini/OpenAI.
- Updated OpenAI provider to use Responses API for gpt-5* models.
- Increased OpenAI timeout to 180s with one retry on read timeouts.
- Hardened server restart behavior and error messaging (quota/429).
- Strengthened council personas and enforced X/10 scoring format.
