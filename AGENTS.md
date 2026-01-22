# AGENTS.md — IPE Breakthrough Idea Swarm (No Execution)

## 0) Mission
Build a local web app that orchestrates a swarm of AI agents to generate and vet **International Political Economy (IPE)** research ideas, and to produce APSR-level reviews of papers and research projects (IC, Mestrado, Doutorado, Research Grant). The system’s outputs are design-only and do not execute analysis.

Ideation is breakthrough-oriented:
- **Theoretically ambitious** (agenda-setting, not incremental).
- **Empirically serious** at the level of *design* (credible identification/measurement plans), but **not executed**.
- Explicitly aligned with:
  - **Causal designs**: DiD, SCM, Shift-Share.
  - **Descriptive designs**: ideal point estimation from votes or comparable revealed-preference behavior.

Review mode is method-agnostic:
- Evaluate theory, design, and evidence as written (quantitative, qualitative, or mixed).
- No execution or new analysis.

The system’s purpose is to maximize the probability that the PI selects ideas capable of becoming **breakthrough papers** suitable for top journals, under the assumption that incremental execution is increasingly commoditized. Review mode’s purpose is to vet and improve papers/projects at the appropriate level, not to require breakthrough claims.

**Non-goal:** automatic data collection, estimation, or paper execution. No “Stage D.”

---

## 1) Product scope (what the app produces)
For each candidate idea, the app must produce a structured “idea dossier” containing:
1) **Big claim** (one sentence) + why it would change minds in IPE.
2) **Theoretical puzzle** + mechanism(s) + falsifiable predictions.
3) **Design blueprint**:
   - If causal: DiD / SCM / Shift-Share choice, estimand, assumptions, threats, falsification plan.
   - If descriptive: ideal point model blueprint, identification/interpretation of the latent dimension, validation plan.
4) **Data feasibility plan** (candidate datasets, measurement construction, risks; but no acquisition/execution).
5) **Novelty positioning** vs. adjacent literatures (what is genuinely new).
6) **Council-style referee memos** with scores and required revisions.
7) **Next-step checklist for the PI** (what to do to execute later, if chosen).

For each review (paper or project; IC/Mestrado/Doutorado/Research Grant levels), the app must produce:
1) **Three Referee Memos** (APSR-level, 350–500 words), one per persona, each with summary, persona-focused assessment, verdict, and overall score.
2) **Three Revision Checklists**, one per persona, with 3 major and 3 minor issues, grounded to section IDs; minors must include quotes labeled `Quote:`.
Personas are selected by the user (duplicates allowed with confirmation).

---

## 2) Hard constraints (non-negotiable)
### 2.1 Domain
- Primary: **International Political Economy**.
- Adjacent fields allowed only when instrumental.

### 2.2 Methods (design-level only)
- **Ideation:** causal questions must be structured around **DiD**, **SCM**, or **Shift-Share**.
- **Ideation:** descriptive questions must be structured around **ideal point estimation** (or closely related latent trait models) from behavioral/vote-like data.
- **Review mode:** method-agnostic; evaluate the method used by the paper/project (quantitative, qualitative, or mixed) with design/evidence critique.
- **Ideation outputs** must remain at the level of: *design spec + diagnostics/falsification plan + feasible data sources*.
- **Review outputs** must assess theory + design + evidence as written (empirical) or theory + contribution (theoretical), without new analysis.

### 2.3 Ambition requirement (idea dossiers only)
Ideas must aim for at least one:
- Mechanism that reconciles or overturns a core debate.
- New measurement that re-sets an empirical argument.
- New identification strategy enabling “hard” questions.
- Reframing that creates a new research agenda.

Incremental ideas must be tagged and deprioritized. Review mode does not require breakthrough-level contributions.

### 2.4 No execution
Agents must not:
- Run analyses, estimate models, scrape data, or generate empirical results.
- Write “Results” sections.
- Claim any finding is true.

They may:
- Propose what results would look like *if* the theory is correct (predictions).
- Specify diagnostics, falsification tests, and robustness strategies.

---

## 2.5 Breakthrough Lanes (mandatory tagging + justification)
Applies to idea dossiers only; not required for paper/project reviews.

### Purpose
To prevent drift into “clever but narrow” ideas, every idea dossier must declare a **Breakthrough Lane**.  
A lane is a *high-level agenda* in IPE where (i) theoretical stakes are large, (ii) empirical bottlenecks are common, and (iii) a single paper can plausibly re-orient a debate.

### Requirement
Every idea in `ideas/<idea_id>/PITCH.md` must include:
- `LANE_PRIMARY:` one lane (required)
- `LANE_SECONDARY:` up to two lanes (optional)
- `BREAKTHROUGH_TYPE:` at least one type (required; multiple allowed)
- `WHY_THIS_IS_BREAKTHROUGH:` 5–10 lines that explicitly link the idea to the lane’s core puzzle and explain why the contribution is not incremental.

Ideas missing lane tags fail **Gate 1** automatically.

---

### Lane catalog (IPE)
1) **Financial Statecraft and Monetary Power**
   - Core puzzle: how cross-border finance, payments, and reserve status create coercion, insulation, or dependency.
   - Typical bottleneck: measuring exposure and disentangling coercion vs selection.

2) **Sanctions, Enforcement, and Evasion Ecosystems**
   - Core puzzle: when sanctions bite, when they backfire, and how enforcement architectures shape outcomes.
   - Typical bottleneck: hidden networks, substitution, and strategic reporting.

3) **Global Production Networks, Chokepoints, and Strategic Interdependence**
   - Core puzzle: how supply chains and input dependencies translate into leverage, vulnerability, and policy constraints.
   - Typical bottleneck: mapping dependencies credibly and identifying shocks.

4) **Trade Regimes, Industrial Policy, and Domestic Coalition Formation**
   - Core puzzle: how domestic winners/losers shape international bargains and the new era of industrial policy.
   - Typical bottleneck: separating policy intent from economic fundamentals.

5) **Technology Controls, Dual-Use Goods, and Innovation Geopolitics**
   - Core puzzle: how export controls and standards reshape innovation, alliances, and competitive trajectories.
   - Typical bottleneck: measurement of technology exposure and counterfactual trajectories.

6) **Debt, IMF Conditionality, and Crisis Politics**
   - Core puzzle: the politics of sovereign distress, conditionality, and reform credibility.
   - Typical bottleneck: identifying causal effects amid crisis endogeneity.

7) **Energy, Critical Minerals, and the Political Economy of the Transition**
   - Core puzzle: how the energy transition reorders rents, alliances, and vulnerability.
   - Typical bottleneck: endogeneity of investment and policy anticipation.

8) **Institutions Under Rivalry: Rules, Dispute Settlement, and Regime Fragmentation**
   - Core puzzle: how rivalry changes compliance, dispute behavior, and institutional design.
   - Typical bottleneck: separating strategic adaptation from institutional constraints.

9) **Global Inequality, Tax, Illicit Flows, and Regulatory Arbitrage**
   - Core puzzle: how capital mobility and regulation interact to shape distribution and state capacity.
   - Typical bottleneck: measurement of hidden flows and credible counterfactuals.

10) **Measurement of Alignment, Influence, and Dependence (Latent Traits / Ideal Points)**
   - Core puzzle: how to measure “alignment” or “dependence” in a way that is predictive, interpretable, and not circular.
   - Typical bottleneck: construct validity, agenda control, missingness, and interpretability of latent dimensions.

---

### Breakthrough types (must select at least one)
- **New Mechanism:** introduces a causal mechanism that resolves or reframes a core theoretical debate.
- **Theoretical Synthesis:** unifies literatures that currently talk past each other, yielding new testable predictions.
- **New Measurement:** creates a construct or latent measure that changes empirical adjudication of a debate.
- **New Identification Path:** uses DiD/SCM/Shift-Share in a setting where prior work lacked credible counterfactuals.
- **New Domain Generalization:** shows a mechanism/design travels across settings in a way that forces reinterpretation.
- **Negative Breakthrough:** credibly shows a widely believed mechanism is weak/conditional, altering research agendas.

---

### Implementation (what agents must do)
1) **Ideator Agent** must assign lane tags and a breakthrough type for every idea.
2) **Theory Architect** must ensure the lane’s core puzzle is explicit and the “big claim” is genuinely agenda-setting.
3) **Identification Agent** must confirm the proposed design is commensurate with the claimed breakthrough type.
4) **Council Agents** must score “Lane Fit” and “Breakthrough Plausibility” explicitly (add these fields to `EVAL_RUBRIC.md`).

---

### `PITCH.md` header snippet (required)
Include this block at the top of every pitch:

- `LANE_PRIMARY: <one lane from catalog>`
- `LANE_SECONDARY: <optional; up to two>`
- `BREAKTHROUGH_TYPE: <one or more types>`
- `WHY_THIS_IS_BREAKTHROUGH: <5–10 lines>`


## 3) Pipeline (revised; Stage D removed)
Applies to ideation only; Review mode follows `REVIEW_MODE_SCHEMA.md` and its own validation rules.
**Stage A — Frontier Mapping**
- Maintain a living map of IPE frontiers, stuck debates, and measurement/ID bottlenecks.

**Stage B — Breakthrough Idea Generation**
- Generate research programs and paper-level pitches.

**Stage C — Design + Feasibility Gate**
- Stress-test identification/measurement plans and data feasibility.
- Reject ideas that cannot clear a skeptical referee bar *on design alone*.

**Stage D (removed) — Execution**
- Not part of this system.

**Stage E — LLM Council Review**
- Provide referee-style evaluation focused on: novelty, theoretical stakes, design credibility, feasibility.

**Stage F — PI Review in Browser**
- PI sees dossiers, scores, memos, and “what to do next if you choose this.”

---

## 4) Repository conventions (required artifacts)
Maintain these files:
- `PLAN.md` — Active work queue and checkpoints.
- `BACKLOG.md` — Idea pool with tags and rejection reasons.
- `FRONTIER_MAP.md` — Living frontier review of IPE debates and bottlenecks.
- `DESIGN_PLAYBOOK.md` — House standards for DiD/SCM/Shift-Share/Ideal points (design-only).
- `DATA_CATALOG.md` — Candidate datasets and access notes (no scraping/extraction).
- `EVAL_RUBRIC.md` — Council scoring rubric, thresholds, veto rules.
- `DECISIONS.md` — PI decisions and rationale.

Per idea dossier:
- `ideas/<idea_id>/PITCH.md`
- `ideas/<idea_id>/DESIGN.md`
- `ideas/<idea_id>/DATA_PLAN.md`
- `ideas/<idea_id>/POSITIONING.md`
- `ideas/<idea_id>/council/` (review memos + scores)
- `ideas/<idea_id>/NEXT_STEPS.md`

Per review dossier:
- `reviews/<review_id>/REFEREE_MEMO__S<slot>__<persona>.md`
- `reviews/<review_id>/REVISION_CHECKLIST__S<slot>__<persona>.md`

---

## 5) Agent roster (roles and responsibilities)
All agents must declare their role(s) and produce outputs in the templates below.

### 5.1 Scout Agent (Frontier + Bottlenecks)
Goal: Keep `FRONTIER_MAP.md` current.
Outputs:
- “Stuck debates” and why they are stuck.
- Candidate shocks/institutions suited to DiD/SCM/Shift-Share.
- Underused behavioral datasets for ideal points.

### 5.2 Ideator Agent (Breakthrough Programs)
Goal: Populate `BACKLOG.md` with ambitious ideas.
Each idea must include a plausible design path and a novelty argument.

### 5.3 Theory Architect Agent (Mechanisms + Stakes)
Goal: Upgrade ideas from “empirical exercise” to “theoretical breakthrough.”
Responsibilities:
- Clarify mechanism microfoundations where relevant.
- Derive crisp predictions and boundary conditions.
- Identify what would falsify the mechanism.

### 5.4 Identification Agent (Design Gatekeeper)
Goal: Enforce identification discipline.
Responsibilities:
- Choose DiD vs SCM vs Shift-Share (or reject).
- Define estimand and assumptions.
- Threats & fixes; falsification suite; robustness plan (design-level).

### 5.5 Measurement Agent (Ideal Points + Constructs)
Goal: Ensure descriptive/latent-trait ideas are interpretable and valid.
Responsibilities:
- Specify model family (IRT / ideal point variants).
- Handle abstentions/missingness/agenda control.
- Validation strategy and interpretability plan.

### 5.6 Data Feasibility Agent (Catalog + Risks)
Goal: Ensure the idea can be executed later by a real project.
Responsibilities:
- Candidate datasets, likely merges, key variables, time coverage.
- Access constraints and failure modes.
- “Feasibility score” with mitigation options.

### 5.7 Council Agents (Reviewer Panel)
Goal: Evaluate like top-journal referees—on design and contribution, not results.
Personas:
- Referee A: theory + positioning
- Referee B: identification
- Referee C: measurement/construct validity
- Referee D: magnitude of contribution / agenda-setting
- Referee E: feasibility + clarity

### 5.8 PI Proxy Agent (Orchestrator)
Goal: Keep `PLAN.md` updated; enforce gates; deduplicate; route revisions.

---

## 6) Communication protocol (memos)
All agent communications are stored as:
- `mail/inbox/<timestamp>_<from>_<topic>.md`
- `mail/outbox/<timestamp>_<to>_<topic>.md`

Each memo must contain:
- Context (1–3 sentences)
- Decision/Recommendation
- Evidence or reasoning
- Next action (owner)

No gate is passed without a memo.

---

## 7) Gates (quality control)
Gates below are for idea dossiers only; Review mode uses review-specific validation and scoring.
### Gate 1 — Ambition Gate (after ideation)
Proceed only if the idea cleanly answers:
1) What would the field believe differently if true?
2) What major debate does it resolve or reframe?
3) Why now (new design, new measurement, new shock, new data)?
4) Big claim in one sentence.

Output required: `ideas/<id>/PITCH.md`.

### Gate 2 — Design Credibility Gate
Proceed only if:
- A defensible DiD/SCM/Shift-Share blueprint exists, OR a defensible ideal-point blueprint exists.
- Assumptions are explicit.
- A falsification/diagnostics plan is credible.

Output required: `ideas/<id>/DESIGN.md`.

### Gate 3 — Data Feasibility Gate
Proceed only if:
- Plausible datasets exist with appropriate unit/time coverage.
- Key constructs are measurable.
- Access constraints are understood.

Output required: `ideas/<id>/DATA_PLAN.md`.

### Gate 4 — Council Gate
Proceed to PI shortlist only if:
- Scores exceed thresholds OR a clear revision path exists.

Output required: `ideas/<id>/council/*`.

---

## 8) House standards (design-only; minimum expectations)
Applies to idea dossiers; Review mode may reference these standards but is not restricted to these design families.
### 8.1 DiD (design level)
- Define estimand, treatment timing, unit of analysis.
- Specify event-study diagnostics and pre-trend evaluation plan.
- Anticipate heterogeneous treatment and staggered adoption issues.
- Robustness plan: alternative controls, inference, functional forms, spillovers.

### 8.2 SCM / Generalized SCM (design level)
- Define treated unit(s), donor pool logic, pre-period fit requirements.
- Placebo plan (space/time).
- Consider interference and multiple treatments.
- Uncertainty reporting plan (where feasible).

### 8.3 Shift-Share (design level)
- Define shares, shifts, exposure, and threat model (endogenous shares).
- Include alternative shares / leave-one-out / over-ID when plausible.
- Explicitly discuss exclusion and potential mechanical correlations.

### 8.4 Ideal points (design level)
- Behavioral source justification (votes/choices as revealed preference).
- Plan for abstentions/missingness/agenda control.
- Validation plan (known groups, predictive validity, stability).
- Interpretability: what the latent dimension plausibly means and doesn’t mean.

---

## 9) Novelty discipline (must be explicit)
Every idea dossier must include a `POSITIONING.md` that:
- Names 3–6 closest literatures or “already-known” explanations.
- States precisely what is new: mechanism, measurement, identification, or synthesis.
- Includes a “referee objection” paragraph and a rebuttal.

If novelty cannot be articulated, tag `incremental` and deprioritize.

---

## 10) Templates (strict)
### 10.1 `PITCH.md`
- Working title
- One-sentence big claim
- Theoretical puzzle + stakes (why it matters)
- Mechanism (bullets)
- Predictions (bullets; include at least one disconfirming pattern)
- Design family (DiD/SCM/Shift-Share/Ideal points) + why it fits
- Expected objections (top 3)
- Novelty statement (2–4 sentences)
- Kill criteria (what would make you abandon it)

### 10.2 `DESIGN.md`
**If causal:**
- Research question (precise)
- Estimand
- Unit/time/treatment/outcome
- Identification strategy + assumptions
- Threats & fixes
- Diagnostics/falsification plan
- Robustness plan
- Scope conditions (where it should/shouldn’t generalize)

**If descriptive (ideal points):**
- Construct to be measured
- Behavioral data source + selection issues
- Model family (IRT/ideal-point variant)
- Handling of abstentions/missingness/agenda control
- Validation plan
- Interpretation limits

### 10.3 `DATA_PLAN.md`
- Candidate datasets (with access notes)
- Key variables and constructions
- Merge keys and likely pain points
- Coverage (units, time)
- Risks + mitigation
- Feasibility score (high/med/low)

### 10.4 Council memo
- Verdict (short)
- Strengths (top 3)
- Fatal flaws / biggest risks (top 3)
- Required revisions (ranked)
- Scores (per rubric)

### 10.5 `NEXT_STEPS.md`
- Minimal execution checklist (what a human/team would do next)
- Most expensive uncertainty to resolve first
- “Fast falsification” plan (how to kill quickly if wrong)

### 10.6 Review artifacts
**Referee Memo (paper/project)**
- Summary (2–3 sentences)
- Persona-focused assessment (follow persona guidance)
- Verdict (reject / major revise / revise)
- Overall score (X/10)

**Revision Checklist**
- Major issues (3 items): Section ID, Issue, Suggested fix
- Minor issues (3 items): Section ID, Issue, Quote (<=20 words, labeled `Quote:`), Suggested fix

---

## 11) Scoring rubric (idea-level thresholds)
Minimum thresholds for PI shortlist (default):
- Novelty/agenda-setting: **≥ 8/10**
- Theoretical stakes clarity: **≥ 7/10**
- Design credibility: **≥ 8/10**
- Data feasibility: **≥ 6/10** (lower allowed if payoff is enormous and risk is explicit)
- Interpretability (measurement/construct): **≥ 7/10** where relevant

Any idea below novelty 8 is presumed outside mission unless PI overrides.

---

## 12) Stop rules (kill ideas early)
Kill or pause if:
- Identification relies on an indefensible assumption.
- Data feasibility is speculative with no credible path.
- The “big claim” collapses into a narrow application.
- The mechanism yields vague, non-falsifiable predictions.

Document the autopsy in `BACKLOG.md`.

---

## 13) Operating procedure (what every agent does first)
1) Read `AGENTS.md`, `DESIGN_PLAYBOOK.md`, and `EVAL_RUBRIC.md`.
2) Post an intro memo: role + immediate plan.
3) Pull a task from `PLAN.md` (or request assignment).
4) Produce outputs strictly in templates; no execution.
5) Run tests or smoke checks before declaring any work complete.

---

## 14) App requirements (UI expectations)
For each idea, the browser UI must show:
- Pitch summary + novelty rationale
- Design blueprint (assumptions and threats prominent)
- Data feasibility overview
- Council scorecard + memos
- Revision queue (actionable next steps)
- Tags: topic, design family, data dependency, novelty lane, risk level

For each review, the browser UI must show:
- Review metadata (type, level)
- Language selection (EN/PT)
- Persona selection (3 reviewers)
- Section index (IDs + excerpts)
- Referee Memos + Revision Checklists (per persona)
- Validation warnings when formatting fails

The orchestration layer must enforce gates (no skipping without PI override).

---
