# CodexCouncil Progress & Roadmap

---

## Mission Snapshot
- Local web app for IPE idea generation + APSR-level review of papers/projects.
- Design-only: no estimation, no data scraping, no claimed results.
- Output: structured dossiers, council memos, and grounded review checklists.

---

## What We Built (Core Capabilities)
- Idea swarm: PITCH/DESIGN/DATA_PLAN/POSITIONING/NEXT_STEPS + gate workflow.
- Council review: memos, resubmissions, gate auto-recompute, version snapshots.
- Literature pipeline: metadata fetch, PDF ingest, assessments, LLM summaries.
- Review mode v1: paper/project reviews with PDF upload + section indexing.
- LLM review run with validation warnings for format/grounding breaks.
- Language toggle (EN/PT) for review output.
- Evaluation harness (offline validation runner + fixtures).

---

## Review Mode (Paper/Project)
- Two review tracks: paper vs project (IC/Mestrado/Doutorado/Research Grant).
- PDF ingestion -> section IDs + excerpts for grounding.
- Outputs:
  - Referee Memo (350–500 words, APSR-style, score + verdict).
  - Revision Checklist (3 major + 3 minor; Quote line required for minors).
- Validation notes appended when format rules break.

---

## Core Architecture Upgrades
- Mode-aware prompt sets (ready for review vs ideation).
- Schema migrations table (no more ad hoc ALTERs).
- Artifact writers unified for idea dossiers + review outputs.
- Dedicated review validation module (split + checklist validation).

---

## Quality & Safety
- 20+ tests covering review models, endpoints, prompts, parsing, validation.
- Review harness for offline validation of outputs against section IDs.
- Design-only constraints remain enforced across all workflows.

---

## Current UX (Working State)
- Two-column operational dashboard.
- Review Studio + Review Archive.
- Idea Dossier now collapsible for large sections (Pitch/Data/Positioning/Next Steps).
- Known issue: UI density/complexity needs rethinking.

---

## Next Steps (Near Term)
- Expand `DATA_CATALOG.md` with standards + sources.
- UI filters for literature (journal/source/type) and export missing PDFs.
- PI decision logging in `DECISIONS.md` + UI shortcuts.
- Assessment source indicator (heuristic vs LLM) + timestamp.
- Tighten council scoring compliance (full rubric coverage).
- Expand review harness with 15–30 real artifacts.

---

## Backlog (Project-Level)
- Dossier export improvements (batch export, zip per idea).
- Additional tests for resubmission and assessment endpoints.
- Align review verdict with score rubric (prompt + validation).
- Enforce exact 3 major + 3 minor counts (pending decision).

---

## Expected Impact (When Fully Ready)
- Faster PI triage of breakthrough ideas with credible designs.
- Higher-quality, APSR-level review feedback for papers/projects.
- Clearer identification and measurement diagnostics before execution.
- Reduced revision cycles via grounded, traceable critiques.
