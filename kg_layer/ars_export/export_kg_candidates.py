import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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
ARS_V1_SCHEMA_VERSION = "1.0.0"
CLAIM_MODALITY_TO_ARS = {
    "measured": "measured",
    "observed": "observed",
    "reported": "reported",
    "inferred": "inferred",
    "hypothesized": "hypothesized",
    "hypothetical": "hypothesized",
    "speculative": "speculative",
    "asserted": "reported",
    "negated": "reported",
}


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


def citation_ids_from_source(value: str) -> List[str]:
    source = str(value or "").strip()
    if source.startswith("http://") or source.startswith("https://"):
        return [source]
    return []


def valid_citation_ids(values: List[str]) -> List[str]:
    return [
        value
        for value in values
        if value.startswith("http://") or value.startswith("https://") or re.match(r"^10\.\d{4,9}/", value)
    ]


def first_nonempty(values: List[Any], default: str = "") -> str:
    for value in values:
        if value not in (None, "", []):
            return str(value).strip()
    return default


def evidence_id_for_claim(claim_id: str, article_id: str, idx: int) -> str:
    if claim_id.startswith("claim:"):
        return f"evidence:{claim_id[len('claim:'):]}"
    return f"evidence:{article_id}:{idx}"


def ars_claim_modality(item: Dict) -> str:
    modality = str(item.get("modality") or item.get("claim_modality") or "reported")
    key = modality.strip().lower().replace("-", "_").replace(" ", "_")
    return CLAIM_MODALITY_TO_ARS.get(key, "reported")


def is_claim_verification_json(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return isinstance(data, dict) and isinstance(data.get("claims"), list)


def parse_claim_verification_json(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    claims = data.get("claims", [])
    if not isinstance(claims, list):
        return []

    rows: List[Dict[str, Any]] = []
    for idx, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict):
            continue
        review_update = claim.get("kg_review_update") or {}
        if not isinstance(review_update, dict):
            review_update = {}
        cited_source_ids = claim.get("cited_source_ids") or []
        if isinstance(cited_source_ids, str):
            cited_source_ids = [cited_source_ids]
        cited_source_ids = [str(source_id).strip() for source_id in cited_source_ids if str(source_id).strip()]
        concept_links = claim.get("concept_links") or []
        if not isinstance(concept_links, list):
            concept_links = []
        related_concept_ids = [
            str(link.get("concept_id")).strip()
            for link in concept_links
            if isinstance(link, dict) and str(link.get("concept_id", "")).strip()
        ]

        rows.append(
            {
                "claim": str(claim.get("claim_text", "")).strip(),
                "claim_id": str(claim.get("claim_id", "")).strip(),
                "section": str(claim.get("section", "")).strip(),
                "source_anchor": str(claim.get("source_anchor", "")).strip(),
                "cited_source_ids": cited_source_ids,
                "source_citation_id": cited_source_ids[0] if cited_source_ids else "",
                "source": ", ".join(cited_source_ids),
                "verdict": str(claim.get("verdict", "")).strip(),
                "confidence": claim.get("confidence"),
                "detail": str(claim.get("rationale", "")).strip(),
                "rationale": str(claim.get("rationale", "")).strip(),
                "kg_new_status": str(review_update.get("new_status", "")).strip(),
                "reviewer_notes": str(review_update.get("reviewer_notes", "")).strip(),
                "related_concept_ids": related_concept_ids,
                "claim_registry_row": claim.get("claim_registry_row", idx),
            }
        )
    return rows


def parse_claim_verification_report(path: Path) -> List[Dict[str, str]]:
    if is_claim_verification_json(path):
        return parse_claim_verification_json(path)

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
        status = row.get("kg_new_status") or VERDICT_TO_STATUS.get(verdict, "in_review")
        claim = row.get("claim", "").strip()
        section = row.get("section", "").strip() or "Document"
        source = row.get("source", "").strip()
        source_anchor = row.get("source_anchor", "").strip() or section
        cited_source_ids = row.get("cited_source_ids") or citation_ids_from_source(source)
        if isinstance(cited_source_ids, str):
            cited_source_ids = [cited_source_ids]
        cited_source_ids = [str(source_id).strip() for source_id in cited_source_ids if str(source_id).strip()]
        source_citation_id = row.get("source_citation_id", "").strip() or first_nonempty(cited_source_ids, source or source_document)
        detail = row.get("detail", "").strip()
        notes = f"ARS claim verification verdict: {verdict or 'UNKNOWN'}"
        if detail:
            notes = f"{notes}. {detail}"
        reviewer_notes = row.get("reviewer_notes", "").strip()
        if reviewer_notes:
            notes = f"{notes}. Reviewer notes: {reviewer_notes}"
        confidence = row.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            confidence = 0.95 if status == "accepted" else 0.75

        claim_id = row.get("claim_id", "").strip() or f"claim:{article_id}:{idx}"
        evidence_id = evidence_id_for_claim(claim_id, article_id, idx)
        related_concept_ids = row.get("related_concept_ids") or []

        objects.append(
            build_object(
                "Claim",
                claim_id,
                source_document,
                section,
                claim,
                float(confidence),
                status,
                reviewer,
                reviewed_at,
                notes,
                article_id,
                run_id,
                {
                    "related_evidence_ids": [evidence_id],
                    "related_concept_ids": related_concept_ids,
                    "source_citation": source,
                    "citation_ids": valid_citation_ids(cited_source_ids),
                    "cited_source_ids": cited_source_ids,
                    "source_anchor": source_anchor,
                    "source_citation_id": source_citation_id,
                    "confidence_rationale": detail or f"Mapped from ARS claim verification verdict {verdict or 'UNKNOWN'}.",
                    "review_decision": {
                        "decision_by": reviewer,
                        "decision_at": reviewed_at,
                        "rationale": reviewer_notes or detail or notes,
                    },
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
        if reviewer_notes:
            evidence_notes = f"{evidence_notes}; reviewer notes: {reviewer_notes}"
        objects.append(
            build_object(
                "Evidence",
                evidence_id,
                source_document,
                section,
                evidence_span,
                min(float(confidence), 0.9) if status == "accepted" else min(float(confidence), 0.7),
                status,
                reviewer,
                reviewed_at,
                evidence_notes,
                article_id,
                run_id,
                {
                    "source_citation": source,
                    "citation_ids": valid_citation_ids(cited_source_ids),
                    "cited_source_ids": cited_source_ids,
                    "source_anchor": source_anchor,
                    "source_citation_id": source_citation_id,
                    "confidence_rationale": detail or "Evidence item generated from ARS claim verification source ids.",
                    "review_decision": {
                        "decision_by": reviewer,
                        "decision_at": reviewed_at,
                        "rationale": reviewer_notes or detail or evidence_notes,
                    },
                    "relation_edges": [
                        {"target_id": claim_id, "relation_type": "supports", "confidence": 0.9}
                    ],
                    "contract_version": CONTRACT_VERSION,
                },
            )
        )

    return objects


def ars_v1_item(item: Dict, reviewer: str, reviewed_at: str) -> Dict:
    source_citation_id = first_nonempty(
        [
            item.get("source_citation_id"),
            (item.get("citation_ids") or [""])[0] if isinstance(item.get("citation_ids"), list) else "",
            item.get("source_citation"),
            item.get("source_document"),
        ],
        "source:unspecified",
    )
    source_anchor = first_nonempty(
        [item.get("source_anchor"), item.get("source_section"), item.get("supporting_quote_or_span")],
        "Document",
    )
    rationale = first_nonempty(
        [item.get("confidence_rationale"), item.get("reviewer_notes"), "Exported from ARS KG exporter."],
        "Exported from ARS KG exporter.",
    )
    review_decision = item.get("review_decision")
    if not isinstance(review_decision, dict):
        review_decision = {
            "decision_by": item.get("reviewer") or reviewer,
            "decision_at": item.get("reviewed_at") or reviewed_at,
            "rationale": item.get("reviewer_notes") or rationale,
        }

    result = {
        "id": item["id"],
        "type": item["type"],
        "source_document": item.get("source_document") or "unknown",
        "source_section": item.get("source_section") or "Document",
        "source_anchor": source_anchor,
        "supporting_quote_or_span": item.get("supporting_quote_or_span") or source_anchor,
        "source_citation_id": source_citation_id,
        "confidence": item.get("confidence", 0.0),
        "confidence_rationale": rationale,
        "extraction_method": item.get("extraction_method") or "ars_hitl",
        "review_status": item.get("review_status") or "pending",
        "review_decision": {
            "decision_by": first_nonempty([review_decision.get("decision_by"), reviewer], reviewer),
            "decision_at": first_nonempty([review_decision.get("decision_at"), reviewed_at], reviewed_at),
            "rationale": first_nonempty([review_decision.get("rationale"), rationale], rationale),
        },
    }
    for optional_field in ("source_citation", "reviewer_notes", "iri"):
        if item.get(optional_field):
            result[optional_field] = item[optional_field]
    if item["type"] == "Concept":
        result["canonical_label"] = item.get("canonical_label") or item.get("supporting_quote_or_span") or item["id"]
        result["aliases"] = item.get("aliases") or []
    if item["type"] == "Claim":
        result["related_evidence_ids"] = item.get("related_evidence_ids") or []
        result["related_concept_ids"] = item.get("related_concept_ids") or []
        result["claim_type"] = item.get("claim_type") or "finding"
        result["modality"] = ars_claim_modality(item)
    return result


def ars_v1_links(items: List[Dict]) -> List[Dict]:
    ids = {item.get("id") for item in items}
    links: List[Dict] = []
    link_idx = 1
    for item in items:
        if item.get("type") != "Claim":
            continue
        for evidence_id in item.get("related_evidence_ids", []):
            if evidence_id in ids:
                links.append(
                    {
                        "id": f"link-{link_idx:03d}",
                        "from_id": item["id"],
                        "to_id": evidence_id,
                        "relation_type": "claim_supported_by_evidence",
                        "polarity": "support",
                        "confidence": min(float(item.get("confidence", 0.9)), 0.9),
                        "rationale": item.get("confidence_rationale")
                        or item.get("reviewer_notes")
                        or "Claim linked to evidence from ARS verification.",
                    }
                )
                link_idx += 1
        for concept_id in item.get("related_concept_ids", []):
            if concept_id in ids:
                links.append(
                    {
                        "id": f"link-{link_idx:03d}",
                        "from_id": item["id"],
                        "to_id": concept_id,
                        "relation_type": "claim_about_concept",
                        "polarity": "support",
                        "confidence": min(float(item.get("confidence", 0.9)), 0.9),
                        "rationale": item.get("confidence_rationale")
                        or item.get("reviewer_notes")
                        or "Claim linked to concept from ARS verification.",
                    }
                )
                link_idx += 1
    return links


def build_ars_v1_handoff(
    article_id: str,
    title: str,
    source_document: str,
    run_id: Optional[str],
    items: List[Dict],
    reviewer: str,
    reviewed_at: str,
    pipeline_stage: str,
    ars_version: str,
    generator_agent: str,
) -> Dict:
    v1_items = [ars_v1_item(item, reviewer, reviewed_at) for item in items]
    v1_item_ids = {item["id"] for item in v1_items}
    for item in v1_items:
        if item.get("type") == "Claim":
            item["related_concept_ids"] = [
                concept_id for concept_id in item.get("related_concept_ids", []) if concept_id in v1_item_ids
            ]
    return {
        "schema_version": ARS_V1_SCHEMA_VERSION,
        "article_id": article_id,
        "title": title,
        "run_id": run_id or f"run:{article_id}",
        "source_document": source_document,
        "run_metadata": {
            "pipeline_stage": pipeline_stage,
            "ars_version": ars_version,
            "generated_at": reviewed_at,
            "generator_agent": generator_agent,
        },
        "items": v1_items,
        "links": ars_v1_links(v1_items),
    }


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
    parser.add_argument(
        "--handoff-schema",
        default="kg_layer",
        choices=["kg_layer", "ars_v1"],
        help="Output handoff schema. Defaults to the existing kg_layer 1.1.0 format.",
    )
    parser.add_argument(
        "--pipeline-stage",
        default="2.5",
        choices=["2", "2.5", "4", "4.5", "5"],
        help="ARS v1 run_metadata.pipeline_stage.",
    )
    parser.add_argument("--ars-version", default="unknown", help="ARS v1 run_metadata.ars_version.")
    parser.add_argument(
        "--generator-agent",
        default="integrity_verification_agent",
        help="ARS v1 run_metadata.generator_agent.",
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

    if args.handoff_schema == "ars_v1":
        handoff = build_ars_v1_handoff(
            article_id,
            title,
            source_document,
            args.run_id,
            items,
            args.reviewer,
            args.reviewed_at,
            args.pipeline_stage,
            args.ars_version,
            args.generator_agent,
        )
    else:
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
