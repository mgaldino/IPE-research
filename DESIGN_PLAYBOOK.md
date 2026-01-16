# DESIGN_PLAYBOOK

House standards for DiD/SCM/Shift-Share/Ideal points (design-only).

## General principles (all designs)
- State the estimand or construct in one sentence that a referee could restate.
- Specify unit of analysis, time period, treatment/exposure, and outcome.
- Include at least one disconfirming pattern (what would refute the mechanism).
- Provide a falsification/diagnostics plan before listing robustness checks.
- List scope conditions: where the claim should/shouldn't generalize.

## DiD (design-only)
### Minimum required
- Estimand: ATT with clear treatment timing and comparison group.
- Unit/time/treatment/outcome definitions (who, when, what).
- Event-study diagnostics plan with pre-trend evaluation.
- Staggered adoption handling (e.g., cohort-specific effects).
- Threats & fixes: selection into treatment, anticipation, spillovers.

### Design checklist
- Treatment timing plausibly exogenous to outcomes.
- Alternative control groups or synthetic controls if parallel trends are weak.
- Plan for heterogeneity (by exposure, size, prior dependence).
- Placebo treatments or outcomes that should not move.
- Inference plan (cluster level, multiple testing discipline).

### Common failure modes
- Treating policy timing as exogenous without evidence.
- Ignoring spillovers or network interference.
- Relying on a single control group with weak pre-trends.

## SCM / Generalized SCM (design-only)
### Minimum required
- Treated unit(s) and donor pool logic (why they are comparable).
- Pre-period fit requirement and justification of covariates.
- Placebo plan (in space and time).
- Interference and multiple treatments consideration.

### Design checklist
- Clearly define treatment onset and any staggered treatments.
- Specify how uncertainty will be summarized (placebos or permutation).
- Pre-register a minimum pre-period fit threshold.
- Address donor pool contamination or spillovers.

### Common failure modes
- Overfitting pre-period with too many covariates.
- Post-treatment contamination in donor pool.
- No credible placebo plan.

## Shift-Share (design-only)
### Minimum required
- Define shares, shifts, and exposure clearly.
- Threat model: endogenous shares and mechanical correlation risks.
- Alternative shares (leave-one-out or lagged shares).
- Exclusion logic and over-identification checks where possible.

### Design checklist
- Use pre-treatment shares and justify the base period.
- Show that shifts are plausibly exogenous to local outcomes.
- Include robustness to alternative shift definitions.
- Provide falsification: outcomes that should be unaffected.

### Common failure modes
- Using contemporaneous shares (mechanical endogeneity).
- Shifts contaminated by local responses to treatment.
- No defense of exclusion restriction.

## Ideal points / latent traits (design-only)
### Minimum required
- Construct definition and why behavior reveals it.
- Behavioral source and agenda control concerns.
- Model family (IRT/ideal-point variant) + identification.
- Handling of abstentions/missingness.
- Validation plan and interpretation limits.

### Design checklist
- Address selection into votes/behavior (who gets to vote).
- Provide known-group validation and predictive validity tests.
- Discuss stability over time and what changes would mean.
- Clarify what the latent dimension is not capturing.

### Common failure modes
- Equating latent position with policy preference without validation.
- Ignoring agenda control or missingness mechanisms.
- Over-interpreting a single dimension as general alignment.

## Diagnostics and falsification (required in all designs)
- At least one placebo test (time or outcome).
- At least one negative control outcome.
- At least one alternative specification that could overturn the claim.

## Design-to-claim alignment
- Breakthrough claims require design that can credibly rule out core alternatives.
- If design cannot adjudicate, reframe to a descriptive or measurement contribution.

## Documentation expectations (file-level)
- `ideas/<id>/DESIGN.md` must include all minimum required items.
- List assumptions explicitly; do not hide them in prose.
- Use bullet lists for threats/fixes and diagnostics.
