# Review Mode v2: Persona Reviews + Grounding Rules

Scope: IPE-first. Review mode is method-agnostic and does not require breakthrough-level contributions. No execution or new analysis.

## Inputs
- PDF (required)
- Review type: `paper` or `project`
- If `project`: level = `IC` | `Mestrado` | `Doutorado` | `Research Grant`
- If `paper`: level is ignored (single standard)
- Language: `en` or `pt` (default `en`)
- Reviewer personas: choose 3 from 6 (duplicates allowed with confirmation)
  - Theory & Positioning
  - Identification & Design
  - Measurement & Constructs
  - Contribution & Agenda
  - Feasibility & Clarity
  - Evidence & Robustness
- LLM provider/model selected in Session Control (shared across workflows)

## Ingestion output (internal)
- Structured sections with stable IDs:
  - `S1: Title/Abstract`
  - `S2: Introduction`
  - `S3: Theory/Mechanism`
  - `S4: Research Design`
  - `S5: Data/Measurement`
  - `S6: Results` (if present; review must not infer findings beyond stated text)
  - `S7: Robustness/Threats`
  - `S8: Conclusion`
- Each section: text, page range, and short excerpt list (for quoting).

## Review artifacts (outputs)
For each selected persona (3 total):
1) **Referee Memo** (fixed template, 350–500 words)
   - Summary (2–3 sentences)
   - Persona-focused assessment (based on persona guidance)
   - Verdict (reject / revise / major revise)
   - Overall score (X/10)
   - Must explicitly label the reviewer persona in the memo

2) **Revision Checklist**
   - Major issues (3 items)
     - Section ID, Issue, Suggested fix
   - Minor issues (3 items)
     - Section ID, Issue, Quote (<=20 words), Suggested fix
     - Quote must be on its own line labeled `Quote:`

## Grounding rules (non-negotiable)
- Every critique must cite a section ID.
- Minor critiques must include a short quote labeled `Quote:`.
- Major critiques should be grounded; quotes are optional.
- No claims about results unless explicitly stated in the text.
- No new theory or execution beyond design-level assessment.

## Review-type distinctions
- **Paper**: single standard; output targets a journal-style referee report.
- **Project**: level-specific expectations in the Referee Memo and Checklist
  - IC: emphasize clarity, feasibility, and scope discipline.
  - Mestrado: emphasize coherent theory + feasible design.
  - Doutorado: emphasize agenda-setting contribution + identification depth.
  - Research Grant: emphasize feasibility, policy relevance, and execution risk.

## Validation behavior
- If the LLM output violates format requirements (missing Section IDs or Quote lines),
  `VALIDATION_NOTES` are appended to the checklist and the UI displays a warning.

## Success signals (for harness)
- Rubric coverage >= 90% of required fields.
- Grounding compliance >= 90% of critiques.
- Low rate of “generic” feedback (human spot check).
