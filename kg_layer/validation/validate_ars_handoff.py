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

RECOMMENDED_SUFFIX = ".kg_candidates.json"
EXPECTED_SCHEMA_VERSION = "1.1.0"
EXPECTED_CONTRACT_VERSION = "1.1"
ALLOWED_COMPATIBILITY_POLICY = {"strict", "backward_compatible"}


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

    if "schema_version" not in data:
        errors.append(f"{path.name}: missing top-level field: schema_version")
    elif str(data.get("schema_version")) != EXPECTED_SCHEMA_VERSION:
        errors.append(
            f"{path.name}: schema_version must be {EXPECTED_SCHEMA_VERSION} (got {data.get('schema_version')})"
        )

    if "contract_version" not in data:
        errors.append(f"{path.name}: missing top-level field: contract_version")
    elif str(data.get("contract_version")) != EXPECTED_CONTRACT_VERSION:
        errors.append(
            f"{path.name}: contract_version must be {EXPECTED_CONTRACT_VERSION} (got {data.get('contract_version')})"
        )

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

    article_metadata: Dict = {
        k: data[k] for k in ("article_id", "run_id", "title", "contract_version") if k in data
    }
    seen_in_file = set()

    for idx, item in enumerate(data["items"], start=1):
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

        if isinstance(normalized.get("confidence"), bool):
            errors.append(f"[{path.name}:{idx}] confidence is not numeric")

        item_id = normalized.get("id")
        if item_id in seen_in_file:
            errors.append(f"[{path.name}:{idx}] Duplicate id within file: {item_id}")
        else:
            seen_in_file.add(item_id)

        if item_id is not None:
            item_ids.append((str(item_id), idx, path.name))

    return len(data["items"]), errors, warnings, item_ids


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
