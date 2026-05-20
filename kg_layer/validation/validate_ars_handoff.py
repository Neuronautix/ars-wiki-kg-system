import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kg_layer.extraction.ingest_structured import (  # noqa: E402
    ALLOWED_REVIEW_STATUS,
    ALLOWED_TYPES,
    REQUIRED_ITEM_FIELDS,
    normalize_item,
    validate_item,
)
from kg_layer.extraction.ars_handoff_adapter import (  # noqa: E402
    ARS_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    adapt_handoff,
)

RECOMMENDED_SUFFIX = ".kg_candidates.json"
EXPECTED_CONTRACT_VERSION = "1.1"
ALLOWED_COMPATIBILITY_POLICY = {"strict", "backward_compatible"}
ARS_REQUIRED_ITEM_FIELDS = {
    "source_anchor",
    "source_citation_id",
    "confidence_rationale",
    "review_decision",
}
ARS_ALLOWED_LINK_RELATION_TYPES = {
    "claim_supported_by_evidence",
    "claim_contradicted_by_evidence",
    "claim_about_concept",
    "evidence_about_concept",
}
ARS_ALLOWED_LINK_POLARITIES = {"support", "contradiction", "neutral"}


def discover_handoff_files(path: Path) -> Tuple[List[Path], List[str]]:
    warnings: List[str] = []
    if not path.exists():
        raise SystemExit(f"Handoff path not found: {path}")

    if path.is_dir():
        files = sorted(path.glob(f"*{RECOMMENDED_SUFFIX}"))
        if not files:
            raise SystemExit(f"No *{RECOMMENDED_SUFFIX} files found in: {path}")
        return files, warnings

    if not path.is_file():
        raise SystemExit(f"Handoff path is not a file or directory: {path}")

    if not path.name.endswith(RECOMMENDED_SUFFIX):
        warnings.append(
            f"{path.name}: filename should end with *{RECOMMENDED_SUFFIX} for pipeline discovery."
        )
    return [path], warnings


def validate_handoff_file(path: Path) -> Tuple[int, List[str], List[str], List[Tuple[str, int, str]]]:
    errors: List[str] = []
    warnings: List[str] = []
    item_ids: List[Tuple[str, int, str]] = []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return 0, [f"{path.name}: invalid JSON: {exc}"], warnings, item_ids

    if not isinstance(data, dict):
        return 0, [f"{path.name}: top-level JSON value must be an object."], warnings, item_ids

    if "source_document" not in data:
        errors.append(f"{path.name}: missing top-level field: source_document")
    elif not str(data["source_document"]).strip():
        errors.append(f"{path.name}: top-level source_document must be non-empty")

    schema_version = str(data.get("schema_version", ""))
    if "schema_version" not in data:
        errors.append(f"{path.name}: missing top-level field: schema_version")
    elif schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(
            f"{path.name}: schema_version must be one of {sorted(SUPPORTED_SCHEMA_VERSIONS)} "
            f"(got {data.get('schema_version')})"
        )

    is_ars_100 = schema_version == ARS_SCHEMA_VERSION
    if not is_ars_100 and "contract_version" not in data:
        errors.append(f"{path.name}: missing top-level field: contract_version")
    elif "contract_version" in data and str(data.get("contract_version")) != EXPECTED_CONTRACT_VERSION:
        errors.append(
            f"{path.name}: contract_version must be {EXPECTED_CONTRACT_VERSION} (got {data.get('contract_version')})"
        )

    if is_ars_100:
        for field in ("article_id", "title", "run_id", "run_metadata", "links"):
            if field not in data:
                errors.append(f"{path.name}: missing ARS 1.0.0 top-level field: {field}")
        if "run_metadata" in data and not isinstance(data["run_metadata"], dict):
            errors.append(f"{path.name}: run_metadata must be an object")
        if "links" in data and not isinstance(data["links"], list):
            errors.append(f"{path.name}: top-level links must be a JSON array")

    compatibility_policy = data.get("compatibility_policy")
    if compatibility_policy is not None and compatibility_policy not in ALLOWED_COMPATIBILITY_POLICY:
        errors.append(
            f"{path.name}: compatibility_policy must be one of {sorted(ALLOWED_COMPATIBILITY_POLICY)}"
        )

    retrieval_policy = data.get("retrieval_policy")
    if retrieval_policy is not None:
        if not isinstance(retrieval_policy, dict):
            errors.append(f"{path.name}: retrieval_policy must be an object")
        else:
            default_mode = retrieval_policy.get("default_mode")
            if default_mode is not None and default_mode not in {"accepted_only", "draft"}:
                errors.append(f"{path.name}: retrieval_policy.default_mode must be accepted_only or draft")
            allow_needs_revision = retrieval_policy.get("allow_needs_revision")
            if allow_needs_revision is not None and not isinstance(allow_needs_revision, bool):
                errors.append(f"{path.name}: retrieval_policy.allow_needs_revision must be boolean")

    if "items" not in data:
        errors.append(f"{path.name}: missing top-level field: items")
        return 0, errors, warnings, item_ids
    if not isinstance(data["items"], list):
        errors.append(f"{path.name}: top-level items must be a JSON array")
        return 0, errors, warnings, item_ids

    adapted_data = adapt_handoff(data)
    article_metadata: Dict = {
        k: adapted_data[k] for k in ("article_id", "run_id", "title", "contract_version") if k in adapted_data
    }
    seen_in_file = set()

    for idx, item in enumerate(adapted_data["items"], start=1):
        if not isinstance(item, dict):
            errors.append(f"[{path.name}:{idx}] Item must be a JSON object")
            continue

        for field in ("extraction_method", "review_status"):
            if field not in item:
                errors.append(f"[{path.name}:{idx}] Missing required field: {field}")

        normalized = normalize_item(item, article_metadata)
        errors.extend(validate_item(normalized, path.name, idx))

        for field in REQUIRED_ITEM_FIELDS:
            if field in normalized and normalized[field] is None:
                errors.append(f"[{path.name}:{idx}] Null value for required field: {field}")

        if is_ars_100:
            for field in ARS_REQUIRED_ITEM_FIELDS:
                if field not in item:
                    errors.append(f"[{path.name}:{idx}] Missing ARS 1.0.0 required field: {field}")
                elif item[field] is None or (isinstance(item[field], str) and not item[field].strip()):
                    errors.append(f"[{path.name}:{idx}] Empty ARS 1.0.0 required field: {field}")
            review_decision = item.get("review_decision")
            if review_decision is not None:
                if not isinstance(review_decision, dict):
                    errors.append(f"[{path.name}:{idx}] review_decision must be an object")
                else:
                    for field in ("decision_by", "decision_at", "rationale"):
                        if not str(review_decision.get(field, "")).strip():
                            errors.append(f"[{path.name}:{idx}] review_decision missing or empty field: {field}")

        if isinstance(normalized.get("confidence"), bool):
            errors.append(f"[{path.name}:{idx}] confidence is not numeric")

        item_id = normalized.get("id")
        if item_id in seen_in_file:
            errors.append(f"[{path.name}:{idx}] Duplicate id within file: {item_id}")
        else:
            seen_in_file.add(item_id)

        if item_id is not None:
            item_ids.append((str(item_id), idx, path.name))

    if is_ars_100 and isinstance(data.get("links"), list):
        validate_ars_links(data["links"], {item_id for item_id, _, _ in item_ids}, path.name, errors)

    return len(data["items"]), errors, warnings, item_ids


def validate_ars_links(links: List, item_ids: set, source_name: str, errors: List[str]) -> None:
    seen_link_ids = set()
    for idx, link in enumerate(links, start=1):
        if not isinstance(link, dict):
            errors.append(f"[{source_name}:links:{idx}] Link must be a JSON object")
            continue

        link_id = str(link.get("id", "")).strip()
        if not link_id:
            errors.append(f"[{source_name}:links:{idx}] Missing required field: id")
        elif link_id in seen_link_ids:
            errors.append(f"[{source_name}:links:{idx}] Duplicate link id within file: {link_id}")
        else:
            seen_link_ids.add(link_id)

        from_id = str(link.get("from_id", "")).strip()
        to_id = str(link.get("to_id", "")).strip()
        relation_type = str(link.get("relation_type", "")).strip()
        polarity = str(link.get("polarity", "")).strip()

        if from_id not in item_ids:
            errors.append(f"[{source_name}:links:{idx}] from_id does not reference an item id: {from_id}")
        if to_id not in item_ids:
            errors.append(f"[{source_name}:links:{idx}] to_id does not reference an item id: {to_id}")
        if relation_type not in ARS_ALLOWED_LINK_RELATION_TYPES:
            errors.append(f"[{source_name}:links:{idx}] invalid relation_type: {relation_type}")
        if polarity not in ARS_ALLOWED_LINK_POLARITIES:
            errors.append(f"[{source_name}:links:{idx}] invalid polarity: {polarity}")

        if link.get("confidence") is not None:
            try:
                confidence = float(link["confidence"])
            except Exception:
                errors.append(f"[{source_name}:links:{idx}] confidence is not numeric")
            else:
                if confidence < 0.0 or confidence > 1.0:
                    errors.append(f"[{source_name}:links:{idx}] confidence out of range [0,1]: {confidence}")

        if not str(link.get("rationale", "")).strip():
            errors.append(f"[{source_name}:links:{idx}] Missing required field: rationale")


def validate_path(path: Path) -> Tuple[int, int, List[str], List[str]]:
    files, warnings = discover_handoff_files(path)
    all_errors: List[str] = []
    total_items = 0
    seen_ids: Dict[str, Tuple[str, int]] = {}

    for file_path in files:
        item_count, errors, file_warnings, item_ids = validate_handoff_file(file_path)
        total_items += item_count
        all_errors.extend(errors)
        warnings.extend(file_warnings)

        for item_id, idx, file_name in item_ids:
            if item_id in seen_ids:
                first_file, first_idx = seen_ids[item_id]
                all_errors.append(
                    f"[{file_name}:{idx}] Duplicate id across checked files: {item_id} "
                    f"(first seen in {first_file}:{first_idx})"
                )
            else:
                seen_ids[item_id] = (file_name, idx)

    return len(files), total_items, all_errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate ARS-emitted *.kg_candidates.json handoff files before KG publishing."
    )
    parser.add_argument(
        "path",
        help="A handoff file, or a directory containing *.kg_candidates.json handoff files.",
    )
    args = parser.parse_args()

    file_count, item_count, errors, warnings = validate_path(Path(args.path))

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        print(f"Checked {file_count} file(s), {item_count} item(s): {len(errors)} error(s), {len(warnings)} warning(s).")
        raise SystemExit(1)

    print(
        f"Validation passed: checked {file_count} file(s), {item_count} item(s); "
        f"0 error(s), {len(warnings)} warning(s)."
    )
    print(f"Allowed types: {', '.join(sorted(ALLOWED_TYPES))}.")
    print(f"Allowed review_status values: {', '.join(sorted(ALLOWED_REVIEW_STATUS))}.")


if __name__ == "__main__":
    main()
