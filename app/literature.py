import re
from urllib.parse import quote
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import httpx
from pypdf import PdfReader
from sqlmodel import Session, select

from .db import engine
from .models import LiteratureAssessment, LiteratureQuery, LiteratureWork

OPENALEX_URL = "https://api.openalex.org/works"
CROSSREF_URL = "https://api.crossref.org/works"
SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

STOPWORDS = {
    "the", "and", "of", "to", "in", "a", "for", "on", "with", "is", "that", "as", "by",
    "an", "are", "from", "this", "be", "or", "at", "it", "we", "not", "can", "have",
    "has", "will", "which", "their", "these", "its", "also", "our", "they", "was", "were",
}

METHOD_TERMS = {
    "difference-in-differences": ["difference-in-differences", "difference in differences", "did"],
    "synthetic control": ["synthetic control", "scm"],
    "shift-share": ["shift-share", "shift share", "bartik"],
    "ideal point": ["ideal point", "ideal points", "irt", "item response"],
}

DATASET_TERMS = [
    "un comtrade",
    "baci",
    "imf",
    "world bank",
    "wto",
    "ofac",
    "swif",
    "swift",
    "oecd",
    "bis",
    "un voting",
    "unga",
]

EXCLUDED_WORK_TYPES = {
    "book",
    "book-chapter",
    "monograph",
    "edited-book",
    "reference-book",
    "book-section",
}


def _normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def _safe_filename(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", text).strip("_")
    return cleaned or "paper"


def _flatten_authors(authors: Iterable[dict], key: str = "name") -> str:
    names = []
    for author in authors:
        value = author.get(key) or author.get("family") or author.get("given")
        if value:
            names.append(value)
    return ", ".join(names) if names else None


def fetch_openalex(query: str, limit: int, mailto: str | None) -> list[dict]:
    params = {"search": query, "per-page": limit}
    if mailto:
        params["mailto"] = mailto
    response = httpx.get(OPENALEX_URL, params=params, timeout=30.0)
    response.raise_for_status()
    data = response.json()
    results = []
    for item in data.get("results", []):
        authorship = item.get("authorships", [])
        host_venue = (item.get("host_venue") or {}).get("display_name")
        primary_source = ((item.get("primary_location") or {}).get("source") or {}).get("display_name")
        venue = host_venue or primary_source
        results.append({
            "source": "openalex",
            "title": item.get("title") or "",
            "authors": _flatten_authors([a.get("author", {}) for a in authorship]),
            "year": item.get("publication_year"),
            "venue": venue,
            "work_type": item.get("type"),
            "doi": item.get("doi"),
            "abstract": item.get("abstract"),
            "open_access_url": (item.get("best_oa_location") or {}).get("pdf_url")
            or (item.get("best_oa_location") or {}).get("landing_page_url"),
        })
    return results


def fetch_openalex_by_doi(doi: str, mailto: str | None) -> dict | None:
    encoded = quote(doi, safe=":/")
    params = {"mailto": mailto} if mailto else {}
    response = httpx.get(f"{OPENALEX_URL}/{encoded}", params=params, timeout=30.0)
    if response.status_code != 200:
        return None
    item = response.json()
    host_venue = (item.get("host_venue") or {}).get("display_name")
    primary_source = ((item.get("primary_location") or {}).get("source") or {}).get("display_name")
    venue = host_venue or primary_source
    return {
        "venue": venue,
        "open_access_url": (item.get("best_oa_location") or {}).get("pdf_url")
        or (item.get("best_oa_location") or {}).get("landing_page_url"),
    }


def fetch_crossref(query: str, limit: int) -> list[dict]:
    params = {"query": query, "rows": limit}
    response = httpx.get(CROSSREF_URL, params=params, timeout=30.0)
    response.raise_for_status()
    data = response.json()
    results = []
    for item in data.get("message", {}).get("items", []):
        title = "".join(item.get("title", []))
        results.append({
            "source": "crossref",
            "title": title,
            "authors": _flatten_authors(item.get("author", []), key="family"),
            "year": (item.get("issued", {}).get("date-parts") or [[None]])[0][0],
            "venue": (item.get("container-title") or [None])[0],
            "work_type": item.get("type"),
            "doi": item.get("DOI"),
            "abstract": item.get("abstract"),
            "open_access_url": None,
        })
    return results


def fetch_crossref_by_doi(doi: str) -> dict | None:
    encoded = quote(doi)
    response = httpx.get(f"{CROSSREF_URL}/{encoded}", timeout=30.0)
    if response.status_code != 200:
        return None
    item = response.json().get("message", {})
    venue = (item.get("container-title") or [None])[0]
    return {"venue": venue}


def fetch_semantic_scholar(query: str, limit: int, api_key: str | None) -> list[dict]:
    headers = {"x-api-key": api_key} if api_key else {}
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,authors,year,venue,externalIds,openAccessPdf,publicationTypes",
    }
    response = httpx.get(SEMANTIC_SCHOLAR_URL, params=params, headers=headers, timeout=30.0)
    response.raise_for_status()
    data = response.json()
    results = []
    for item in data.get("data", []):
        results.append({
            "source": "semantic_scholar",
            "title": item.get("title") or "",
            "authors": _flatten_authors(item.get("authors", [])),
            "year": item.get("year"),
            "venue": item.get("venue"),
            "work_type": (item.get("publicationTypes") or [None])[0],
            "doi": (item.get("externalIds") or {}).get("DOI"),
            "abstract": item.get("abstract"),
            "open_access_url": (item.get("openAccessPdf") or {}).get("url"),
        })
    return results


def _dedupe(results: list[dict]) -> list[dict]:
    seen_doi = set()
    seen_title = set()
    deduped = []
    for item in results:
        doi = (item.get("doi") or "").lower()
        title_key = _normalize_title(item.get("title") or "")
        if doi and doi in seen_doi:
            continue
        if not doi and title_key and title_key in seen_title:
            continue
        if doi:
            seen_doi.add(doi)
        if title_key:
            seen_title.add(title_key)
        deduped.append(item)
    return deduped


def _download_pdf(url: str, target_path: Path) -> bool:
    try:
        response = httpx.get(url, timeout=60.0)
        response.raise_for_status()
    except httpx.HTTPError:
        return False
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(response.content)
    return True


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    text = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text.append(page_text)
    return "\n".join(text).strip()


def _top_terms(texts: list[str], limit: int = 15) -> list[tuple[str, int]]:
    counter = Counter()
    for text in texts:
        for term in re.findall(r"[a-zA-Z]{3,}", text.lower()):
            if term in STOPWORDS:
                continue
            counter[term] += 1
    return counter.most_common(limit)


def _count_methods(texts: list[str]) -> dict:
    counts = {}
    combined = "\n".join(texts).lower()
    for label, variants in METHOD_TERMS.items():
        counts[label] = sum(combined.count(variant) for variant in variants)
    return counts


def _detect_datasets(texts: list[str]) -> list[str]:
    combined = "\n".join(texts).lower()
    detected = []
    for term in DATASET_TERMS:
        if term in combined:
            detected.append(term)
    return detected


def generate_assessment(texts: list[str], total_works: int) -> str:
    top_terms = _top_terms(texts)
    method_counts = _count_methods(texts)
    datasets = _detect_datasets(texts)
    missing_methods = [k for k, v in method_counts.items() if v == 0]

    lines = [
        "# Literature Assessment",
        "",
        f"Total works reviewed: {total_works}",
        "",
        "## Top recurring terms (heuristic)",
    ]
    for term, count in top_terms:
        lines.append(f"- {term}: {count}")

    lines.extend([
        "",
        "## Method mentions (heuristic)",
    ])
    for method, count in method_counts.items():
        lines.append(f"- {method}: {count}")

    lines.extend([
        "",
        "## Dataset mentions (heuristic)",
    ])
    if datasets:
        for dataset in datasets:
            lines.append(f"- {dataset}")
    else:
        lines.append("- None detected in abstracts/full text")

    lines.extend([
        "",
        "## Potential gaps (heuristic, to verify)",
    ])
    if missing_methods:
        lines.append("- Missing method coverage: " + ", ".join(missing_methods))
    else:
        lines.append("- No obvious method gaps detected from keyword scan")

    return "\n".join(lines) + "\n"


def ingest_local_pdfs(query_id: int, base_dir: Path) -> None:
    local_dir = base_dir / "literature" / "pdfs" / str(query_id)
    local_dir.mkdir(parents=True, exist_ok=True)
    with Session(engine) as session:
        for pdf_path in local_dir.glob("*.pdf"):
            existing = session.exec(
                select(LiteratureWork).where(
                    LiteratureWork.query_id == query_id,
                    LiteratureWork.pdf_path == str(pdf_path),
                )
            ).first()
            if existing:
                continue
            try:
                text = extract_pdf_text(pdf_path)
            except Exception:
                continue
            if not text:
                continue
            work = LiteratureWork(
                query_id=query_id,
                source="local",
                title=pdf_path.stem,
                pdf_path=str(pdf_path),
                full_text=text,
                updated_at=datetime.now(timezone.utc),
            )
            session.add(work)
        session.commit()


def update_full_texts(query_id: int) -> None:
    with Session(engine) as session:
        works = session.exec(
            select(LiteratureWork).where(
                LiteratureWork.query_id == query_id,
                LiteratureWork.pdf_path.is_not(None),
            )
        ).all()
        for work in works:
            if work.full_text:
                continue
            try:
                text = extract_pdf_text(Path(work.pdf_path))
            except Exception:
                continue
            if text:
                work.full_text = text
                work.updated_at = datetime.now(timezone.utc)
                session.add(work)
        session.commit()


def rebuild_assessment(query_id: int, base_dir: Path) -> str:
    ingest_local_pdfs(query_id, base_dir)
    update_full_texts(query_id)

    with Session(engine) as session:
        works = session.exec(select(LiteratureWork).where(LiteratureWork.query_id == query_id)).all()
        texts = []
        for work in works:
            combined = " ".join(filter(None, [work.abstract, work.full_text]))
            if combined:
                texts.append(combined)
        assessment = generate_assessment(texts, total_works=len(works))

        assessment_dir = base_dir / "literature" / "assessments"
        assessment_dir.mkdir(parents=True, exist_ok=True)
        assessment_path = assessment_dir / f"assessment_{query_id}.md"
        assessment_path.write_text(assessment, encoding="utf-8")

        existing = session.exec(
            select(LiteratureAssessment).where(LiteratureAssessment.query_id == query_id)
        ).first()
        if existing:
            existing.content = assessment
            session.add(existing)
        else:
            session.add(LiteratureAssessment(query_id=query_id, content=assessment))

        query_row = session.get(LiteratureQuery, query_id)
        if query_row:
            query_row.status = "completed"
            query_row.updated_at = datetime.now(timezone.utc)
            query_row.notes = f"assessment_path={assessment_path}"
            session.add(query_row)
        session.commit()

    return assessment


def run_literature_query(
    query_id: int,
    query: str,
    sources: list[str],
    per_source_limit: int,
    base_dir: Path,
    include_non_article: bool = False,
    openalex_email: str | None = None,
    semantic_scholar_key: str | None = None,
) -> None:
    results = []
    if "openalex" in sources:
        results.extend(fetch_openalex(query, per_source_limit, openalex_email))
    if "crossref" in sources:
        results.extend(fetch_crossref(query, per_source_limit))
    if "semantic_scholar" in sources:
        results.extend(fetch_semantic_scholar(query, per_source_limit, semantic_scholar_key))

    deduped = _dedupe(results)
    if not include_non_article:
        deduped = [
            item for item in deduped
            if not item.get("work_type") or item.get("work_type") not in EXCLUDED_WORK_TYPES
        ]
    for item in deduped:
        if item.get("venue") or not item.get("doi"):
            continue
        doi = item.get("doi")
        enriched = fetch_openalex_by_doi(doi, openalex_email)
        if not enriched:
            enriched = fetch_crossref_by_doi(doi)
        if enriched:
            item["venue"] = enriched.get("venue") or item.get("venue")
            if enriched.get("open_access_url") and not item.get("open_access_url"):
                item["open_access_url"] = enriched.get("open_access_url")

    with Session(engine) as session:
        session.exec(select(LiteratureWork).where(LiteratureWork.query_id == query_id)).all()
        for item in deduped:
            work = LiteratureWork(
                query_id=query_id,
                source=item["source"],
                title=item["title"],
                authors=item.get("authors"),
                year=item.get("year"),
                venue=item.get("venue"),
                work_type=item.get("work_type"),
                doi=item.get("doi"),
                abstract=item.get("abstract"),
                open_access_url=item.get("open_access_url"),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(work)
        query_row = session.get(LiteratureQuery, query_id)
        if query_row:
            query_row.status = "fetched"
            query_row.updated_at = datetime.now(timezone.utc)
            session.add(query_row)
        session.commit()

    oa_dir = base_dir / "literature" / "oa" / str(query_id)
    with Session(engine) as session:
        works = session.exec(select(LiteratureWork).where(LiteratureWork.query_id == query_id)).all()
        for work in works:
            if work.open_access_url and not work.pdf_path:
                filename = _safe_filename(work.doi or work.title)
                target = oa_dir / f"{filename}.pdf"
                if _download_pdf(work.open_access_url, target):
                    work.pdf_path = str(target)
                    work.updated_at = datetime.now(timezone.utc)
                    session.add(work)
        session.commit()

    rebuild_assessment(query_id, base_dir)
