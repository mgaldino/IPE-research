# Review Mode v1: Minimal Schema + Grounding Rules

Scope: IPE-only. Reuse existing council personas and design-only constraints.

## Inputs
- PDF (required)
- Optional metadata:
  - Target outlet tier (e.g., top-5, field journal)
  - Contribution type (theory/mechanism, identification, measurement)
  - Method family (DiD/SCM/Shift-Share/Ideal points/qualitative/mixed/other)
  - Review type: `paper` or `project`
  - If `project`: level = `IC` | `Mestrado` | `Doutorado` | `FAPESP`
  - If `paper`: level is ignored (single standard)

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
1) **Referee Memo** (fixed template, 350–500 words)
   - Summary (2–3 sentences)
   - Contribution + novelty assessment
   - Design/ID assessment (if empirical)
   - Evidence/measurement assessment (if empirical)
   - Verdict (reject / revise / major revise)
   - Overall score (X/10)

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

## Gate logic (Review mode)
- Gate R1: Contribution clarity (>= threshold)
- Gate R2: Design credibility (>= threshold)
- Gate R3: Measurement/construct validity (if applicable)
- Gate R4: Feasibility/clarity

## Review-type distinctions
- **Paper**: single standard; output targets a journal-style referee report.
- **Project**: level-specific expectations in the Referee Memo and Checklist
  - IC: emphasize clarity, feasibility, and scope discipline.
  - Mestrado: emphasize coherent theory + feasible design.
  - Doutorado: emphasize agenda-setting contribution + identification depth.
  - FAPESP: emphasize feasibility, policy relevance, and execution risk.

## Validation behavior
- If the LLM output violates format requirements (missing Section IDs or Quote lines),
  `VALIDATION_NOTES` are appended to the checklist and the UI displays a warning.

## Success signals (for harness)
- Rubric coverage >= 90% of required fields.
- Grounding compliance >= 90% of critiques.
- Low rate of “generic” feedback (human spot check).
