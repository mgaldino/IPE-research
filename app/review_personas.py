from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewPersona:
    key: str
    label: str
    focus: str
    guidance: str | None = None


REVIEW_PERSONAS = {
    "theory_positioning": ReviewPersona(
        key="theory_positioning",
        label="Theory & Positioning",
        focus="Contribution, mechanism, debate fit, and novelty claims.",
        guidance=(
            "Evaluate whether the paper:\n"
            "- States a precise research question and, if the paper is causal, a coherent causal mechanism "
            "(what causes what, why, when).\n"
            "- Defines scope conditions and the domain of validity (who/where/when it applies).\n"
            "- Makes novelty claims that are defensible (genuinely new vs. relabeling/repackaging).\n"
            "- Is positioned in the right debate, engaging the key interlocutors and stakes. "
            "Use the literature synthesis, if provided, as input to make this assessment.\n"
            "- Avoids over-claiming and unsupported theoretical generalizations."
        ),
    ),
    "identification_design": ReviewPersona(
        key="identification_design",
        label="Identification & Design",
        focus="Design credibility, assumptions, threats, and falsification logic.",
        guidance=(
            "Your main goal is to evaluate if the research design allows the paper to credibly answer "
            "the research question. If the paper is causal, judge the causal argument based on:\n"
            "- Identification strategy: assumptions stated clearly and their plausibility.\n"
            "- Key threats: selection, confounding, anticipation, spillovers, trends, post-treatment bias, "
            "interference/SUTVA, manipulation (as relevant).\n"
            "- Falsification logic: placebo tests, pre-trends, balance, negative controls, sensitivity.\n"
            "- Clear estimand and unit of inference (ATE/ATT/ITT/LATE), timing, and source of identifying variation.\n"
            "If the paper is not causal, assess whether the paper defines main concepts clearly, if the measurements "
            "are reliable and valid with respect to concepts, if the estimators are corrected for the target "
            "descriptive estimand, and how sample selection is justified."
        ),
    ),
    "measurement_constructs": ReviewPersona(
        key="measurement_constructs",
        label="Measurement & Constructs",
        focus="Construct validity, measurement choices, and interpretability limits.",
        guidance=(
            "Evaluate:\n"
            "- Concept-to-measure alignment: does the operationalization match the construct?\n"
            "- Likely measurement error (directional bias, attenuation, differential mismeasurement).\n"
            "- Coding/scaling/aggregation choices, windows, missingness, and imputation.\n"
            "- Substantive interpretability (what a unit means; comparability across groups/time).\n"
            "- Triangulation: alternative measures, validation, and independent sources. "
            "Do not review identification/results unless measurement undermines inference."
        ),
    ),
    "contribution_agenda": ReviewPersona(
        key="contribution_agenda",
        label="Contribution & Agenda",
        focus="Magnitude of contribution and agenda-setting potential.",
        guidance=(
            "Assess:\n"
            "- Whether the paper changes beliefs (theory, empirical fact, method, or all).\n"
            "- The delta relative to the best existing paper in the space.\n"
            "- Generalizability/portability and cross-field relevance.\n"
            "- Whether it opens a cumulative research agenda (new questions, data, replicable design).\n"
            "- Avoid technicalities; prioritize “so what” and the APSR bar."
        ),
    ),
    "feasibility_clarity": ReviewPersona(
        key="feasibility_clarity",
        label="Feasibility & Clarity",
        focus="Feasibility, organization, and clarity of presentation.",
        guidance=(
            "Focus on clarity, narrative architecture and scope control. Your task is to make the paper maximally "
            "readable and publishable as a manuscript, not to judge whether the identification strategy is correct. "
            "Evaluate:\n"
            "- Whether the reader can state (in one sentence each) the research question, estimand, data, and core "
            "design by the end of the introduction.\n"
            "- Whether sections have a clear job, are ordered logically, and are signposted (what the reader learns "
            "and why it matters).\n"
            "- Whether the manuscript is over-scoped; propose a minimum viable paper: what stays in the main text, "
            "what moves to appendix, what is cut.\n"
            "- Whether the empirical narrative is reproducible at the level of “what was done,” with minimal "
            "ambiguity (but do not adjudicate causal validity).\n"
            "Hard boundaries:\n"
            "- Do not debate identification assumptions or demand extensive robustness. If the design is confusing, "
            "treat it as an exposition problem: specify how to explain it clearly.\n"
            "- Only flag non-clarity issues if they are fatal to coherence (e.g., design not defined, treatment "
            "timing unspecified, outcome undefined)."
        ),
    ),
    "evidence_robustness": ReviewPersona(
        key="evidence_robustness",
        label="Evidence & Robustness",
        focus="Evidence quality, robustness expectations, and credibility of support.",
        guidance=(
            "Evaluate:\n"
            "- Whether the presented evidence supports the claims (direction, magnitude, uncertainty).\n"
            "- Robustness expectations: alternative specifications, samples, treatment/outcome definitions, "
            "multiple testing where relevant.\n"
            "- Transparency: informative figures/tables, justified choices, replicability norms.\n"
            "- Signs of selective reporting or fragile results (“forking paths” risks).\n"
            "- Appropriate uncertainty communication (SEs, clustering, inference, heterogeneity). "
            "Avoid theory and identification unless needed to judge evidentiary support."
        ),
    ),
}

DEFAULT_REVIEW_PERSONAS = [
    "theory_positioning",
    "identification_design",
    "measurement_constructs",
]


def persona_label(key: str) -> str:
    persona = REVIEW_PERSONAS.get(key)
    return persona.label if persona else key


def persona_focus(key: str) -> str:
    persona = REVIEW_PERSONAS.get(key)
    return persona.focus if persona else "Provide a balanced, standard review."


def persona_guidance(key: str) -> str:
    persona = REVIEW_PERSONAS.get(key)
    if not persona:
        return ""
    if persona.guidance:
        return persona.guidance
    return f"Emphasis: {persona.focus}"
