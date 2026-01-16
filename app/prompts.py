from __future__ import annotations

from dataclasses import dataclass

BASE_CONTEXT = """
You are an IPE research idea agent. Only propose design-level plans; do not run analyses, estimate models, scrape data, or claim results.
Focus on International Political Economy. Use DiD, SCM, Shift-Share for causal ideas, or ideal point/latent trait models for descriptive ideas.
Aim for agenda-setting, non-incremental ideas.
""".strip()

PITCH_TEMPLATE = """
Produce a single idea dossier PITCH.md using this template and required header block.
The header block is mandatory and must appear at the very top. Do not omit any field.

- LANE_PRIMARY: <one lane from catalog>
- LANE_SECONDARY: <optional; up to two>
- BREAKTHROUGH_TYPE: <one or more types>
- WHY_THIS_IS_BREAKTHROUGH: <5-10 lines>

Then include:
- Working title
- One-sentence big claim
- Theoretical puzzle + stakes (why it matters)
- Mechanism (bullets)
- Predictions (bullets; include at least one disconfirming pattern)
- Design family (DiD/SCM/Shift-Share/Ideal points) + why it fits
- Expected objections (top 3)
- Novelty statement (2-4 sentences)
- Kill criteria (what would make you abandon it)
""".strip()

DESIGN_TEMPLATE = """
Produce DESIGN.md for the same idea using this template (design-only, no execution):
If causal:
- Research question (precise)
- Estimand
- Unit/time/treatment/outcome
- Identification strategy + assumptions
- Threats & fixes
- Diagnostics/falsification plan
- Robustness plan
- Scope conditions (where it shouldn't generalize)
If descriptive:
- Construct to be measured
- Behavioral data source + selection issues
- Model family (IRT/ideal-point variant)
- Handling of abstentions/missingness/agenda control
- Validation plan
- Interpretation limits
""".strip()

DATA_PLAN_TEMPLATE = """
Produce DATA_PLAN.md for the same idea using this template:
- Candidate datasets (with access notes)
- Key variables and constructions
- Merge keys and likely pain points
- Coverage (units, time)
- Risks + mitigation
- Feasibility score (high/med/low)
""".strip()

POSITIONING_TEMPLATE = """
Produce POSITIONING.md for the same idea using this template:
- 3-6 closest literatures or already-known explanations
- What is new (mechanism, measurement, identification, or synthesis)
- Referee objection paragraph + rebuttal
""".strip()

NEXT_STEPS_TEMPLATE = """
Produce NEXT_STEPS.md for the same idea using this template:
- Minimal execution checklist (what a human/team would do next)
- Most expensive uncertainty to resolve first
- Fast falsification plan (how to kill quickly if wrong)
""".strip()

COUNCIL_TEMPLATE = """
Produce five council memos (Referee A-E). Be tough and push back; assume top-journal standards.
Each referee has a distinct persona:

Referee A (Theory + Positioning): You are a Harvard Government professor specializing in IPE theory and debates. Prioritize mechanism clarity, agenda-setting stakes, and novelty vs adjacent literatures.
Referee B (Identification): You are a Princeton Politics professor focused on causal identification in political economy. Prioritize estimand clarity, design validity, threats, and falsification credibility.
Referee C (Measurement/Construct): You are a Stanford Political Science professor focused on measurement and latent traits in IPE. Prioritize construct validity, interpretability, and measurement/latent-trait logic.
Referee D (Contribution magnitude): You are a Chicago Political Science professor known for agenda-setting work in IPE. Prioritize whether the idea could reorient debates; be skeptical of incrementalism.
Referee E (Data Feasibility): You are a Columbia SIPA professor focused on data feasibility in global political economy. Prioritize whether data sources are adequate to answer the research question, coverage/measurement risks, and execution feasibility.

Use this template per memo:
- Verdict (short)
- Strengths (top 3)
- Fatal flaws / biggest risks (top 3)
- Required revisions (ranked)
- Scores (per rubric, include Lane Fit and Breakthrough Plausibility; always use X/10 format)

Return memos separated by "---" lines and label each as "Referee A" etc.
""".strip()

LITERATURE_PAPER_TEMPLATE = """
Summarize the paper excerpt below for IPE frontier mapping.
Return bullets with:
- Research question
- Core mechanism or argument
- Method/design family (DiD/SCM/Shift-Share/Ideal point/Other)
- Data sources (if mentioned)
- Claimed findings (as reported by the paper)
- Limitations or scope conditions
- Relevant lane(s) from the catalog
Stay faithful to the text; do not invent details.
""".strip()

LITERATURE_SYNTHESIS_TEMPLATE = """
Synthesize the paper summaries into a single literature assessment.
Provide:
- Core debates and where they are stuck
- Method/design coverage and missing designs
- Key datasets repeatedly used and missing measurements
- Candidate breakthrough opportunities (mechanism, measurement, or ID)
- 3-5 concrete idea prompts aligned to lanes
Do not claim new empirical results.
""".strip()

LANE_CATALOG = """
Lane catalog:
1) Financial Statecraft and Monetary Power
2) Sanctions, Enforcement, and Evasion Ecosystems
3) Global Production Networks, Chokepoints, and Strategic Interdependence
4) Trade Regimes, Industrial Policy, and Domestic Coalition Formation
5) Technology Controls, Dual-Use Goods, and Innovation Geopolitics
6) Debt, IMF Conditionality, and Crisis Politics
7) Energy, Critical Minerals, and the Political Economy of the Transition
8) Institutions Under Rivalry: Rules, Dispute Settlement, and Regime Fragmentation
9) Global Inequality, Tax, Illicit Flows, and Regulatory Arbitrage
10) Measurement of Alignment, Influence, and Dependence (Latent Traits / Ideal Points)
""".strip()


@dataclass(frozen=True)
class PromptSet:
    pitch: str
    design: str
    data: str
    positioning: str
    next_steps: str
    council: str


PROMPT_SETS = {
    "ideation": PromptSet(
        pitch=PITCH_TEMPLATE,
        design=DESIGN_TEMPLATE,
        data=DATA_PLAN_TEMPLATE,
        positioning=POSITIONING_TEMPLATE,
        next_steps=NEXT_STEPS_TEMPLATE,
        council=COUNCIL_TEMPLATE,
    ),
}


def build_prompt(
    section: str,
    topic_focus: str | None = None,
    assessment: str | None = None,
    idea_seed: str | None = None,
    mode: str = "ideation",
) -> str:
    focus_line = f"Topic focus: {topic_focus}\n" if topic_focus else ""
    seed_line = f"Idea seed: {idea_seed}\n" if idea_seed else ""
    assessment_block = ""
    if assessment:
        assessment_block = f"Literature assessment:\n{assessment.strip()}\n"
    prompt_set = PROMPT_SETS.get(mode)
    if not prompt_set:
        raise ValueError(f"Unknown prompt mode: {mode}")
    templates = {
        "pitch": prompt_set.pitch,
        "design": prompt_set.design,
        "data": prompt_set.data,
        "positioning": prompt_set.positioning,
        "next_steps": prompt_set.next_steps,
        "council": prompt_set.council,
    }
    return "\n\n".join([
        BASE_CONTEXT,
        LANE_CATALOG,
        assessment_block + seed_line + focus_line + templates[section],
    ])


def build_literature_paper_prompt(
    title: str,
    metadata: str,
    text: str,
) -> str:
    return "\n\n".join([
        BASE_CONTEXT,
        LANE_CATALOG,
        LITERATURE_PAPER_TEMPLATE,
        f"Title: {title}",
        f"Metadata: {metadata}",
        "Excerpt:",
        text.strip(),
    ])


def build_literature_synthesis_prompt(
    summaries: list[str],
    query: str,
    total_works: int,
) -> str:
    return "\n\n".join([
        BASE_CONTEXT,
        LANE_CATALOG,
        f"Query: {query}",
        f"Total works in query: {total_works}",
        LITERATURE_SYNTHESIS_TEMPLATE,
        "Paper summaries:",
        "\n\n".join(summaries),
    ])


def build_council_prompt_with_dossier(
    dossier_parts: dict[str, str],
    topic_focus: str | None = None,
    mode: str = "ideation",
) -> str:
    base = build_prompt("council", topic_focus, mode=mode)
    ordered_keys = ["PITCH", "DESIGN", "DATA_PLAN", "POSITIONING", "NEXT_STEPS"]
    dossier_blocks = []
    for key in ordered_keys:
        content = dossier_parts.get(key)
        if content:
            dossier_blocks.append(f"## {key}\n{content.strip()}")
    dossier_text = "\n\n".join(dossier_blocks) if dossier_blocks else "No dossier content available."
    return "\n\n".join([
        base,
        "Review the dossier below. Ground critiques in the specific design and claims provided.",
        dossier_text,
    ])
