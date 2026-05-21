import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kg_layer.extraction.ars_handoff_adapter import adapt_handoff

REQUIRED_ITEM_FIELDS = [
    "id",
    "type",
    "source_document",
    "source_section",
    "supporting_quote_or_span",
    "confidence",
    "extraction_method",
    "review_status",
]
ALLOWED_TYPES = {"Paper", "Concept", "Claim", "Evidence"}
ALLOWED_REVIEW_STATUS = {
    "pending",
    "in_review",
    "accepted",
    "rejected",
    "needs_revision",
    "candidate",
    "evidence_supported",
    "human_reviewed",
    "superseded",
}
ALLOWED_RELATION_TYPES = {
    "supports",
    "contradicts",
    "relates_to_concept",
    "derived_from",
    "cites",
    "same_as",
    "uses_system",
    "measures_endpoint",
    "reports_finding",
    "has_species",
    "has_strain",
    "uses_assay",
    "requires_metadata",
    "compares_condition",
    "supports_claim",
    "contradicts_claim",
    "has_limitation",
    "derived_from_source",
}
ID_RE = re.compile(r"^(paper|concept|claim|evidence):.+:.+$")
DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)
URL_RE = re.compile(r"^https?://[^\s<>{}|\\^`\[\]\"]+$")


def normalize_item(item: Dict, article_metadata: Dict) -> Dict:
    """Fill in defaults and propagate article-level metadata to an item."""
    out = dict(item)

    # Propagate article-level metadata when not already present on the item.
    for field in ("article_id", "run_id"):
        if field in article_metadata and field not in out:
            out[field] = article_metadata[field]

    # Default extraction_method to ars_hitl when absent or blank.
    if not str(out.get("extraction_method", "")).strip():
        out["extraction_method"] = "ars_hitl"

    if "reviewer_notes" not in out:
        out["reviewer_notes"] = ""

    if "review_status" not in out:
        out["review_status"] = "pending"

    if "contract_version" not in out and article_metadata.get("contract_version"):
        out["contract_version"] = article_metadata["contract_version"]

    return out


def validate_item(item: Dict, source_file: str, idx: int) -> List[str]:
    errors: List[str] = []
    for field in REQUIRED_ITEM_FIELDS:
        if field not in item:
            errors.append(f"[{source_file}:{idx}] Missing required field: {field}")

    if "type" in item and item["type"] not in ALLOWED_TYPES:
        errors.append(f"[{source_file}:{idx}] Invalid type: {item['type']}")

    if "review_status" in item and item["review_status"] not in ALLOWED_REVIEW_STATUS:
        errors.append(f"[{source_file}:{idx}] Invalid review_status: {item['review_status']}")

    if "confidence" in item:
        try:
            conf = float(item["confidence"])
            if conf < 0.0 or conf > 1.0:
                errors.append(f"[{source_file}:{idx}] confidence out of range [0,1]: {conf}")
        except Exception:
            errors.append(f"[{source_file}:{idx}] confidence is not numeric")

    for txt_field in ("id", "source_document", "source_section", "supporting_quote_or_span"):
        if txt_field in item and not str(item[txt_field]).strip():
            errors.append(f"[{source_file}:{idx}] Empty value for required field: {txt_field}")

    item_id = str(item.get("id", "")).strip()
    if item_id and not ID_RE.match(item_id):
        errors.append(f"[{source_file}:{idx}] id does not follow policy (<type>:<namespace>:<local-id>): {item_id}")

    if item.get("source_span_start") is not None or item.get("source_span_end") is not None:
        start = item.get("source_span_start")
        end = item.get("source_span_end")
        if not isinstance(start, int) or not isinstance(end, int):
            errors.append(f"[{source_file}:{idx}] source_span_start/source_span_end must both be integers when present")
        elif start < 0 or end < 0 or end <= start:
            errors.append(f"[{source_file}:{idx}] invalid source span offsets: start={start}, end={end}")

    citation_ids = item.get("citation_ids")
    if citation_ids is not None:
        if not isinstance(citation_ids, list):
            errors.append(f"[{source_file}:{idx}] citation_ids must be an array")
        else:
            for citation_id in citation_ids:
                value = str(citation_id).strip()
                if not value:
                    errors.append(f"[{source_file}:{idx}] citation_ids must not contain empty values")
                    continue
                if not DOI_RE.match(value) and not URL_RE.match(value):
                    errors.append(f"[{source_file}:{idx}] citation_id must be DOI or URL format: {value}")

    relation_edges = item.get("relation_edges")
    if relation_edges is not None:
        if not isinstance(relation_edges, list):
            errors.append(f"[{source_file}:{idx}] relation_edges must be an array")
        else:
            for rel_idx, edge in enumerate(relation_edges, start=1):
                if not isinstance(edge, dict):
                    errors.append(f"[{source_file}:{idx}] relation_edges[{rel_idx}] must be an object")
                    continue
                target_id = str(edge.get("target_id", "")).strip()
                rel_type = str(edge.get("relation_type", "")).strip()
                rel_conf = edge.get("confidence")
                if not target_id:
                    errors.append(f"[{source_file}:{idx}] relation_edges[{rel_idx}] missing target_id")
                if rel_type not in ALLOWED_RELATION_TYPES:
                    errors.append(f"[{source_file}:{idx}] relation_edges[{rel_idx}] invalid relation_type: {rel_type}")
                if rel_conf is not None:
                    try:
                        rel_conf_val = float(rel_conf)
                    except Exception:
                        errors.append(f"[{source_file}:{idx}] relation_edges[{rel_idx}] confidence is not numeric")
                    else:
                        if rel_conf_val < 0.0 or rel_conf_val > 1.0:
                            errors.append(f"[{source_file}:{idx}] relation_edges[{rel_idx}] confidence out of range [0,1]")

    return errors


def ingest_file(path: Path) -> List[Dict]:
    """Read one *.kg_candidates.json handoff file and return validated, normalized items."""
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Handoff file must be a JSON object: {path}")

    data = adapt_handoff(data)
    items = data.get("items", [])
    if not isinstance(items, list):
        raise ValueError(f"'items' must be a JSON array in: {path}")

    article_metadata = {k: data[k] for k in ("article_id", "run_id", "title", "contract_version") if k in data}

    all_errors: List[str] = []
    normalized: List[Dict] = []
    seen_ids = set()

    for idx, item in enumerate(items, start=1):
        norm = normalize_item(item, article_metadata)
        errs = validate_item(norm, path.name, idx)

        item_id = norm.get("id")
        if item_id in seen_ids:
            errs.append(f"[{path.name}:{idx}] Duplicate id within file: {item_id}")
        else:
            seen_ids.add(item_id)

        if errs:
            all_errors.extend(errs)
        else:
            normalized.append(norm)

    if all_errors:
        error_details = "\n".join(f"  - {err}" for err in all_errors)
        raise ValueError(f"{path.name} validation issues:\n{error_details}")

    return normalized


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest structured ARS HITL handoff artifacts into KG candidates."
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing *.kg_candidates.json handoff files.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON path for merged KG candidate objects.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_path = Path(args.output)

    if not input_dir.exists():
        raise SystemExit(f"Structured input directory not found: {input_dir}")
    if not input_dir.is_dir():
        raise SystemExit(f"Structured input path is not a directory: {input_dir}")

    handoff_files = sorted(input_dir.glob("*.kg_candidates.json"))
    if not handoff_files:
        raise SystemExit(f"No *.kg_candidates.json files found in: {input_dir}")

    all_objs: List[Dict] = []
    seen_ids = set()
    failures: List[Tuple[str, str]] = []

    for path in handoff_files:
        try:
            items = ingest_file(path)
            added = 0
            for item in items:
                item_id = item.get("id")
                if item_id in seen_ids:
                    print(f"Skipping duplicate id '{item_id}' from {path.name}")
                    continue
                seen_ids.add(item_id)
                all_objs.append(item)
                added += 1
            print(f"Ingested {added} items from {path.name}")
        except (ValueError, json.JSONDecodeError) as exc:
            message = f"Error reading {path.name}: {exc}"
            failures.append((path.name, message))
            print(message)

    if failures:
        failed_files = ", ".join(path_name for path_name, _ in failures)
        raise SystemExit(f"Structured ingest failed for {len(failures)} handoff file(s): {failed_files}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(all_objs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(all_objs)} structured objects to {output_path}")


if __name__ == "__main__":
    main()
