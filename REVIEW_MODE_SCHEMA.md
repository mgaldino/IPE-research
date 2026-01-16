# Review Mode v1: Minimal Schema + Grounding Rules

Scope: IPE-only. Reuse existing council personas and design-only constraints.

## Inputs
- PDF (required)
- Optional metadata:
  - Target outlet tier (e.g., top-5, field journal)
  - Contribution type (theory/mechanism, identification, measurement)
  - Method family (DiD/SCM/Shift-Share/Ideal points/other)

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
1) **Referee Memo** (fixed template)
   - Summary (2–4 sentences)
   - Contribution + novelty assessment
   - Design/ID assessment (assumptions, threats)
   - Measurement/construct validity (if relevant)
   - Feasibility and clarity
   - Verdict (reject / revise / major revise)

2) **Revision Checklist**
   - Ranked list of required changes
   - Each item includes:
     - Section ID (e.g., S4)
     - Evidence snippet (short quote or paraphrase)
     - Why it matters
     - Minimal fix

## Grounding rules (non-negotiable)
- Every critique must cite a section ID.
- Major critiques must include a short quote or paraphrase from the paper.
- No claims about results unless explicitly stated in the text.
- No new theory or execution beyond design-level assessment.

## Gate logic (Review mode)
- Gate R1: Contribution clarity (>= threshold)
- Gate R2: Design credibility (>= threshold)
- Gate R3: Measurement/construct validity (if applicable)
- Gate R4: Feasibility/clarity

## Success signals (for harness)
- Rubric coverage >= 90% of required fields.
- Grounding compliance >= 90% of critiques.
- Low rate of “generic” feedback (human spot check).
