from __future__ import annotations

from typing import List, Tuple


def split_review_output(content: str) -> Tuple[str, str]:
    marker = "REVISION_CHECKLIST"
    upper_content = content.upper()
    if marker in upper_content:
        index = upper_content.index(marker)
        memo = content[:index].strip()
        checklist = content[index:].strip()
        return memo, checklist
    alt_marker = "REVISION CHECKLIST"
    if alt_marker in upper_content:
        index = upper_content.index(alt_marker)
        memo = content[:index].strip()
        checklist = f"{marker}\n{content[index + len(alt_marker):].strip()}"
        return memo, checklist
    return content.strip(), "REVISION_CHECKLIST\n- No checklist provided."


def validate_review_output(checklist: str, section_ids: List[str]) -> List[str]:
    errors = []
    checklist_lines = [line.rstrip() for line in checklist.splitlines() if line.strip()]
    if not any("Major" in line for line in checklist_lines):
        errors.append("Checklist missing Major issues section.")
    if not any("Minor" in line for line in checklist_lines):
        errors.append("Checklist missing Minor issues section.")

    current_bucket = None
    pending_minor = None
    for raw_line in checklist_lines:
        line = raw_line.strip()
        if line.lower().startswith("- major"):
            current_bucket = "major"
            continue
        if line.lower().startswith("- minor"):
            current_bucket = "minor"
            continue
        if not line.startswith("-"):
            if current_bucket == "minor" and pending_minor:
                if line.lower().startswith("quote:"):
                    pending_minor = None
            continue
        if current_bucket == "minor" and pending_minor:
            errors.append(f"Minor item missing Quote line: {pending_minor}")
            pending_minor = None
        if "Section" in line:
            if not any(section_id in line for section_id in section_ids):
                errors.append(f"Checklist item missing valid section id: {line}")
        if current_bucket == "minor":
            if "quote" in line.lower():
                continue
            pending_minor = line
    if pending_minor:
        errors.append(f"Minor item missing Quote line: {pending_minor}")
    return errors
