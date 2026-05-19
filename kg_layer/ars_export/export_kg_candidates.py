import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kg_layer.extraction.extract_candidates import extract_from_file

VERDICT_TO_STATUS = {
    "VERIFIED": "accepted",
    "MINOR_DISTORTION": "needs_revision",
    "MAJOR_DISTORTION": "needs_revision",
    "UNVERIFIABLE": "rejected",
    "UNVERIFIABLE_ACCESS": "in_review",
}
SCHEMA_VERSION = "1.1.0"
CONTRACT_VERSION = "1.1"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "article"


def default_title(article_path: Path) -> str:
    text = article_path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+)$", line.strip())
        if match:
            return match.group(1).strip()
    return article_path.stem.replace("_", " ").replace("-", " ").title()


def split_markdown_row(line: str) -> List[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    cells = []
    current = []
    escaped = False
    for char in stripped[1:-1]:
        if char == "\\" and not escaped:
            escaped = True
            current.append(char)
            continue
        if char == "|" and not escaped:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        escaped = False
    cells.append("".join(current).strip())
    return cells


def is_separator_row(cells: List[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def parse_claim_verification_report(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    header: Optional[List[str]] = None

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        cells = split_markdown_row(line)
        if not cells:
            header = None
            continue
        if is_separator_row(cells):
            continue

        normalized = [cell.strip().lower().replace(" ", "_") for cell in cells]
        if "claim" in normalized and "verdict" in normalized:
            header = normalized
            continue

        if header and len(cells) == len(header):
            row = dict(zip(header, cells))
            if row.get("claim") and row.get("verdict"):
                rows.append(row)

    return rows


def reviewed_fields(status: str, reviewer: str, reviewed_at: str, notes: str) -> Dict[str, str]:
    return {
        "review_status": status,
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
        "reviewer_notes": notes,
    }


def build_object(
    object_type: str,
    object_id: str,
    source_document: str,
    source_section: str,
    span: str,
    confidence: float,
    status: str,
    reviewer: str,
    reviewed_at: str,
    notes: str,
    article_id: str,
    run_id: Optional[str],
    extra: Optional[Dict] = None,
) -> Dict:
    obj = {
        "id": object_id,
        "type": object_type,
        "source_document": source_document,
        "source_section": source_section or "Document",
        "supporting_quote_or_span": span,
        "confidence": confidence,
        "extraction_method": "ars_hitl",
        **reviewed_fields(status, reviewer, reviewed_at, notes),
        "article_id": article_id,
        "contract_version": CONTRACT_VERSION,
    }
    if run_id:
        obj["run_id"] = run_id
    if extra:
        obj.update({k: v for k, v in extra.items() if v not in (None, "", [])})
    return obj


def concept_candidates(article_path: Path, source_document: str, article_id: str, run_id: Optional[str]) -> List[Dict]:
    concepts = []
    seen = set()
    for obj in extract_from_file(article_path, source_document):
        if obj.get("type") != "Concept":
            continue
        span = str(obj.get("supporting_quote_or_span", "")).strip()
        key = span.lower()
        if not span or key in seen:
            continue
        seen.add(key)
        obj["id"] = f"concept:{article_id}:{len(concepts) + 1}"
        obj["article_id"] = article_id
        obj["canonical_label"] = span
        obj.setdefault("aliases", [])
        if run_id:
            obj["run_id"] = run_id
        obj["extraction_method"] = "ars_article_concept_heuristic"
        concepts.append(obj)
    return concepts


def claim_objects_from_report(
    report_path: Path,
    source_document: str,
    article_id: str,
    run_id: Optional[str],
    reviewer: str,
    reviewed_at: str,
) -> List[Dict]:
    rows = parse_claim_verification_report(report_path)
    objects: List[Dict] = []

    for idx, row in enumerate(rows, start=1):
        verdict = row.get("verdict", "").strip().upper()
        status = VERDICT_TO_STATUS.get(verdict, "in_review")
        claim = row.get("claim", "").strip()
        section = row.get("section", "").strip() or "Document"
        source = row.get("source", "").strip()
        detail = row.get("detail", "").strip()
        notes = f"ARS claim verification verdict: {verdict or 'UNKNOWN'}"
        if detail:
            notes = f"{notes}. {detail}"

        claim_id = f"claim:{article_id}:{idx}"
        evidence_id = f"evidence:{article_id}:{idx}"

        objects.append(
            build_object(
                "Claim",
                claim_id,
                source_document,
                section,
                claim,
                0.95 if status == "accepted" else 0.75,
                status,
                reviewer,
                reviewed_at,
                notes,
                article_id,
                run_id,
                {
                    "related_evidence_ids": [evidence_id],
                    "source_citation": source,
                    "citation_ids": [source] if source.startswith("http://") or source.startswith("https://") else [],
                    "claim_polarity": "supports",
                    "claim_modality": "asserted",
                    "relation_edges": [
                        {"target_id": evidence_id, "relation_type": "supports", "confidence": 0.9}
                    ],
                    "contract_version": CONTRACT_VERSION,
                },
            )
        )

        evidence_span = detail or source or claim
        evidence_notes = f"Evidence row for claim {idx}"
        if source:
            evidence_notes = f"{evidence_notes}; source: {source}"
        objects.append(
            build_object(
                "Evidence",
                evidence_id,
                source_document,
                section,
                evidence_span,
                0.9 if status == "accepted" else 0.7,
                status,
                reviewer,
                reviewed_at,
                evidence_notes,
                article_id,
                run_id,
                {
                    "source_citation": source,
                    "citation_ids": [source] if source.startswith("http://") or source.startswith("https://") else [],
                    "relation_edges": [
                        {"target_id": claim_id, "relation_type": "supports", "confidence": 0.9}
                    ],
                    "contract_version": CONTRACT_VERSION,
                },
            )
        )

    return objects


def objects_from_article_fallback(
    article_path: Path,
    source_document: str,
    article_id: str,
    run_id: Optional[str],
    reviewer: str,
    reviewed_at: str,
    status: str,
) -> List[Dict]:
    objects = extract_from_file(article_path, source_document)
    counters: Dict[str, int] = {}
    for obj in objects:
        object_type = obj["type"]
        counters[object_type] = counters.get(object_type, 0) + 1
        obj["id"] = f"{object_type.lower()}:{article_id}:{counters[object_type]}"
        obj["extraction_method"] = "ars_article_markdown_export"
        obj["article_id"] = article_id
        obj["contract_version"] = CONTRACT_VERSION
        if run_id:
            obj["run_id"] = run_id
        obj.update(
            reviewed_fields(
                status,
                reviewer,
                reviewed_at,
                "Exported from final ARS article markdown; no claim verification report supplied.",
            )
        )
    return objects


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export ARS article/review artifacts as a *.kg_candidates.json handoff file."
    )
    parser.add_argument("--article", required=True, help="Final ARS article markdown file.")
    parser.add_argument(
        "--claim-verification-report",
        help="Optional ARS Claim Verification Report markdown containing the Claim Registry table.",
    )
    parser.add_argument("--output-dir", required=True, help="Directory for the handoff file.")
    parser.add_argument("--article-id", help="Stable article id. Defaults to the article filename stem.")
    parser.add_argument("--title", help="Article title. Defaults to first H1 or filename.")
    parser.add_argument("--run-id", help="ARS run id for provenance.")
    parser.add_argument("--reviewer", default="ars_hitl", help="Reviewer identity to stamp on exported items.")
    parser.add_argument(
        "--reviewed-at",
        default=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        help="ISO 8601 review timestamp. Defaults to current UTC time.",
    )
    parser.add_argument(
        "--fallback-status",
        default="accepted",
        choices=["pending", "in_review", "accepted", "rejected", "needs_revision"],
        help="Review status for article-only fallback extraction.",
    )
    args = parser.parse_args()

    article_path = Path(args.article)
    if not article_path.exists():
        raise SystemExit(f"Article file not found: {article_path}")

    report_path = Path(args.claim_verification_report) if args.claim_verification_report else None
    if report_path and not report_path.exists():
        raise SystemExit(f"Claim verification report not found: {report_path}")

    article_id = slugify(args.article_id or article_path.stem)
    title = args.title or default_title(article_path)
    source_document = article_path.name

    paper = build_object(
        "Paper",
        f"paper:{article_id}:1",
        source_document,
        "Document",
        f"Source document {source_document}",
        1.0,
        "accepted",
        args.reviewer,
        args.reviewed_at,
        "Final ARS article exported for KG handoff.",
        article_id,
        args.run_id,
    )

    if report_path:
        claim_evidence = claim_objects_from_report(
            report_path, source_document, article_id, args.run_id, args.reviewer, args.reviewed_at
        )
        if not claim_evidence:
            raise SystemExit(f"No Claim Verification Report rows found in: {report_path}")
        concepts = concept_candidates(article_path, source_document, article_id, args.run_id)
        for idx, concept in enumerate(concepts, start=1):
            concept.update(
                reviewed_fields(
                    "pending",
                    "",
                    "",
                    "Concept candidate extracted from final ARS article; requires review.",
                )
            )
            concept["id"] = f"concept:{article_id}:{idx}"
        items = [paper, *concepts, *claim_evidence]
    else:
        fallback_items = objects_from_article_fallback(
            article_path,
            source_document,
            article_id,
            args.run_id,
            args.reviewer,
            args.reviewed_at,
            args.fallback_status,
        )
        items = [paper, *[obj for obj in fallback_items if obj["type"] != "Paper"]]

    handoff = {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "compatibility_policy": "backward_compatible",
        "retrieval_policy": {"default_mode": "accepted_only", "allow_needs_revision": True},
        "article_id": article_id,
        "title": title,
        "source_document": source_document,
        "items": items,
    }
    if args.run_id:
        handoff["run_id"] = args.run_id

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{article_id}.kg_candidates.json"
    output_path.write_text(json.dumps(handoff, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Exported {len(items)} KG candidates -> {output_path}")


if __name__ == "__main__":
    main()
