from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


@dataclass(frozen=True)
class ReviewSection:
    section_id: str
    title: str
    content: str
    page_start: int
    page_end: int
    excerpt: str


SECTION_HINTS = [
    "abstract",
    "introduction",
    "theory",
    "background",
    "literature",
    "research design",
    "identification",
    "methods",
    "data",
    "measurement",
    "results",
    "discussion",
    "robustness",
    "conclusion",
]


def extract_pdf_pages(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        pages.append((page.extract_text() or "").strip())
    return pages


def split_sections(pages: Iterable[str]) -> list[ReviewSection]:
    lines_with_page = []
    for page_idx, page_text in enumerate(pages, start=1):
        for line in page_text.splitlines():
            lines_with_page.append((page_idx, line.strip()))

    sections = []
    current_lines = []
    current_title = "Document"
    current_start = 1
    section_index = 1

    for page_idx, line in lines_with_page:
        if _is_heading(line):
            if current_lines:
                sections.append(
                    _build_section(
                        section_index,
                        current_title,
                        current_lines,
                        current_start,
                        page_idx,
                    )
                )
                section_index += 1
            current_title = line
            current_start = page_idx
            current_lines = []
            continue
        if line:
            current_lines.append((page_idx, line))

    if current_lines:
        sections.append(
            _build_section(section_index, current_title, current_lines, current_start, current_lines[-1][0])
        )

    if not sections:
        combined = "\n".join(page for page in pages if page)
        sections.append(
            ReviewSection(
                section_id="S1",
                title="Document",
                content=combined.strip(),
                page_start=1,
                page_end=max(len(list(pages)), 1),
                excerpt=_excerpt(combined),
            )
        )
    return sections


def build_grounded_artifacts(
    sections: list[ReviewSection],
    *,
    review_type: str,
    level: str | None,
    language: str,
) -> dict[str, str]:
    labels = _labels_for(language)
    level_label = level or "n/a"
    if not sections:
        memo = "\n".join([
            labels["memo_title"],
            "",
            f"- {labels['review_type']}: {review_type}",
            f"- {labels['level']}: {level_label}",
            f"- {labels['summary']}: {labels['no_sections']}",
            f"- {labels['contribution']}: n/a",
            f"- {labels['design']}: n/a",
            f"- {labels['measurement']}: n/a",
            f"- {labels['feasibility']}: n/a",
            f"- {labels['verdict']}: revise",
        ])
        checklist = "\n".join([
            labels["checklist_title"],
            "",
            f"- {labels['section']}: n/a",
            f"  {labels['evidence']}: n/a",
            f"  {labels['issue']}: {labels['missing_doc']}",
            f"  {labels['fix']}: {labels['attach_pdf']}",
        ])
        return {"REFEREE_MEMO": memo, "REVISION_CHECKLIST": checklist}

    top_sections = sections[:3]
    expectations = _expectations_for(review_type, level, language)
    summary_lines = [
        labels["memo_title"],
        "",
        f"- {labels['review_type']}: {review_type}",
        f"- {labels['level']}: {level_label}",
        f"- {labels['summary']}: {labels['generated']}",
        f"- {labels['contribution']}: n/a (needs manual assessment).",
        f"- {labels['design']}: n/a (needs manual assessment).",
        f"- {labels['measurement']}: n/a (needs manual assessment).",
        f"- {labels['feasibility']}: n/a (needs manual assessment).",
        f"- {labels['expectations']}: {expectations}",
        f"- {labels['verdict']}: revise",
    ]
    checklist_lines = [labels["checklist_title"], ""]
    for section in top_sections:
        checklist_lines.extend([
            f"- {labels['section']}: {section.section_id} {section.title}",
            f"  {labels['evidence']}: \"{section.excerpt}\"",
            f"  {labels['issue']}: {labels['grounded_issue']}",
            f"  {labels['fix']}: {labels['grounded_fix']}",
            "",
        ])
    return {
        "REFEREE_MEMO": "\n".join(summary_lines),
        "REVISION_CHECKLIST": "\n".join(checklist_lines).strip(),
    }


def _expectations_for(review_type: str, level: str | None, language: str) -> str:
    if review_type == "paper":
        return (
            "Journal-standard contribution, clarity, and design credibility."
            if language != "pt"
            else "Contribuicao de nivel de journal, clareza e credibilidade do desenho."
        )
    if not level:
        return (
            "Project-standard contribution and feasibility."
            if language != "pt"
            else "Contribuicao e viabilidade em nivel de projeto."
        )
    level_map_en = {
        "IC": "Scope discipline and feasibility at an undergraduate level.",
        "Mestrado": "Coherent theory and feasible design at a masters level.",
        "Doutorado": "Agenda-setting contribution with deep identification logic.",
        "Research Grant": "Feasibility, execution risk, and public value clarity.",
    }
    level_map_pt = {
        "IC": "Disciplina de escopo e viabilidade em nivel de IC.",
        "Mestrado": "Teoria coerente e desenho viavel em nivel de mestrado.",
        "Doutorado": "Contribuicao agenda-setting com identificacao profunda.",
        "Research Grant": "Viabilidade, risco de execucao e clareza de valor publico.",
    }
    if language == "pt":
        return level_map_pt.get(level, "Contribuicao e viabilidade em nivel de projeto.")
    return level_map_en.get(level, "Project-standard contribution and feasibility.")


def _labels_for(language: str) -> dict[str, str]:
    if language == "pt":
        return {
            "memo_title": "Referee Memo",
            "checklist_title": "Revision Checklist",
            "review_type": "Tipo de revisao",
            "level": "Nivel",
            "summary": "Resumo",
            "contribution": "Contribuicao",
            "design": "Desenho/ID",
            "measurement": "Medicao",
            "feasibility": "Viabilidade",
            "verdict": "Veredito",
            "expectations": "Expectativas",
            "section": "Secao",
            "evidence": "Evidencia",
            "issue": "Problema",
            "fix": "Correcao minima",
            "no_sections": "Sem secoes para revisar.",
            "generated": "Revisao gerada a partir das secoes indexadas.",
            "missing_doc": "Conteudo ausente.",
            "attach_pdf": "Anexe um PDF e rode novamente.",
            "grounded_issue": "A revisao exige critica ancorada; adicionar notas especificas.",
            "grounded_fix": "Fornecer critica focada para esta secao.",
        }
    return {
        "memo_title": "Referee Memo",
        "checklist_title": "Revision Checklist",
        "review_type": "Review type",
        "level": "Level",
        "summary": "Summary",
        "contribution": "Contribution",
        "design": "Design/ID",
        "measurement": "Measurement",
        "feasibility": "Feasibility",
        "verdict": "Verdict",
        "expectations": "Expectations",
        "section": "Section",
        "evidence": "Evidence",
        "issue": "Issue",
        "fix": "Minimal fix",
        "no_sections": "No sections available for review.",
        "generated": "Review generated from indexed sections.",
        "missing_doc": "Missing document content.",
        "attach_pdf": "Attach a PDF and re-run review.",
        "grounded_issue": "Review requires grounded critique; add specific notes.",
        "grounded_fix": "Provide focused critique for this section.",
    }


def _is_heading(line: str) -> bool:
    if not line or len(line) > 80:
        return False
    normalized = re.sub(r"\s+", " ", line).strip()
    lower = normalized.lower()
    if any(hint in lower for hint in SECTION_HINTS):
        return True
    if re.match(r"^\d+(\.\d+)*\s+[A-Za-z].{2,}$", normalized):
        return True
    if normalized.isupper() and len(normalized) >= 6:
        return True
    return False


def _build_section(
    index: int,
    title: str,
    lines: list[tuple[int, str]],
    page_start: int,
    page_end: int,
) -> ReviewSection:
    content = "\n".join(line for _, line in lines).strip()
    return ReviewSection(
        section_id=f"S{index}",
        title=title.strip() or "Section",
        content=content,
        page_start=page_start,
        page_end=page_end,
        excerpt=_excerpt(content),
    )


def _excerpt(content: str, limit: int = 200) -> str:
    cleaned = re.sub(r"\s+", " ", content).strip()
    return cleaned[:limit]
