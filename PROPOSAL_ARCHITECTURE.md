# Proposal: Core + Modes + Domain Packs (vs Separate Apps)

Goal: Provide an external LLM enough context to critique the proposed product path and recommend the best approach.
Repo context: see `README.md` for current MVP scope and features.

## 1) Current MVP (baseline)
- Local web app that orchestrates LLM “council” agents to generate and vet IPE research ideas.
- Outputs structured dossiers (PITCH/DESIGN/DATA_PLAN/POSITIONING/NEXT_STEPS) and referee-style memos.
- Pipeline uses gates, templates, and design-only standards (no execution).

## 2) Proposed path (preferred)
**Build a shared core, then add “modes” and “domain packs” within the same app.**

### 2.1 Core (shared across all functions)
- Orchestration engine: LLM council, gates, memo workflow.
- Template system: dossier formats, rubrics, scoring.
- Storage + UI base: runs, ideas/reviews, versions, exports.

### 2.2 Modes (feature variants in the same app)
1) **Ideation mode** (current behavior)
2) **Review mode** (new): evaluate existing artifacts across methods (quantitative, qualitative, mixed)
   - “Paper review” (referee-style critique)
   - “Project review” (IC/MSc/PhD proposals at different levels)

### 2.3 Domain packs
Modular “domain config” per field (IPE, CP, IR, broader social science):
- Lanes/agenda definitions.
- Playbook standards (methods/identification).
- Rubrics and thresholds.
- Domain-specific prompts and examples.

### Why this path
- Preserves MVP momentum; reuse council/gates/templates.
- Avoids fragmenting product and UX across multiple apps.
- Allows gradual expansion: add 1 mode, then 1 domain pack, without heavy refactors.

## 3) Second-best alternative (fast compare)
**Separate apps for each function (Ideation app, Review app, Domain-specific app).**

Pros:
- Clear positioning for each audience/use case.
- UX can be highly tailored per task.

Cons:
- Duplicated engineering: council/gates/templates repeated across apps.
- Higher maintenance and inconsistent evolution of core workflows.
- Harder to share improvements and data artifacts across products.

## 4) Decision question for reviewer (LLM)
Given the MVP and roadmap goals, which strategy is superior:
1) **Core + modes + domain packs** in a single app, or
2) **Separate apps** for ideation/review/domains?

Please assess:
- Product focus vs extensibility tradeoff.
- Engineering complexity and maintainability.
- Risk of quality dilution (from generalization).
- UX clarity and onboarding.
- Speed to deliver a useful “Review mode.”

## 5) Optional references
- `README.md` (MVP scope and current features)
- `AGENTS.md` (detailed mission and constraints)
