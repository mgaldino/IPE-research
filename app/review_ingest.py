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


def build_grounded_artifacts(sections: list[ReviewSection]) -> dict[str, str]:
    if not sections:
        memo = "\n".join([
            "Referee Memo",
            "",
            "- Summary: No sections available for review.",
            "- Contribution: n/a",
            "- Design/ID: n/a",
            "- Measurement: n/a",
            "- Feasibility: n/a",
            "- Verdict: revise",
        ])
        checklist = "\n".join([
            "Revision Checklist",
            "",
            "- Section: n/a",
            "  Evidence: n/a",
            "  Issue: Missing document content.",
            "  Minimal fix: Attach a PDF and re-run review.",
        ])
        return {"REFEREE_MEMO": memo, "REVISION_CHECKLIST": checklist}

    top_sections = sections[:3]
    summary_lines = [
        "Referee Memo",
        "",
        "- Summary: Review generated from indexed sections.",
        "- Contribution: n/a (needs manual assessment).",
        "- Design/ID: n/a (needs manual assessment).",
        "- Measurement: n/a (needs manual assessment).",
        "- Feasibility: n/a (needs manual assessment).",
        "- Verdict: revise",
    ]
    checklist_lines = ["Revision Checklist", ""]
    for section in top_sections:
        checklist_lines.extend([
            f"- Section: {section.section_id} {section.title}",
            f"  Evidence: \"{section.excerpt}\"",
            "  Issue: Review requires grounded critique; add specific notes.",
            "  Minimal fix: Provide focused critique for this section.",
            "",
        ])
    return {
        "REFEREE_MEMO": "\n".join(summary_lines),
        "REVISION_CHECKLIST": "\n".join(checklist_lines).strip(),
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
