import argparse
import json
from pathlib import Path
from typing import Dict, List

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
ALLOWED_REVIEW_STATUS = {"pending", "in_review", "accepted", "rejected", "needs_revision"}


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

    return errors


def ingest_file(path: Path) -> List[Dict]:
    """Read one *.kg_candidates.json handoff file and return validated, normalized items."""
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Handoff file must be a JSON object: {path}")

    items = data.get("items", [])
    if not isinstance(items, list):
        raise ValueError(f"'items' must be a JSON array in: {path}")

    article_metadata = {k: data[k] for k in ("article_id", "run_id", "title") if k in data}

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
        raise ValueError(f"{path.name} validation issues:\n" + "\n".join(f"  - {err}" for err in all_errors))

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
    failures: List[tuple[str, str]] = []

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
