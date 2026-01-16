# CHANGELOG

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
- Hardened server restart behavior and error messaging (quota/429).
- Strengthened council personas and enforced X/10 scoring format.
