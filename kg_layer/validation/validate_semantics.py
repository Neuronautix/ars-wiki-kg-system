import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

ALLOWED_REVIEW_STATUS = {"pending", "in_review", "accepted", "rejected", "needs_revision"}
RECOMMENDED_HANDOFF_SUFFIX = ".kg_candidates.json"
HTTP_IRI_RE = re.compile(r"^https?://[^\s<>{}|\\^`\[\]\"]+$")
EXCEPTION_NOTE_RE = re.compile(
    r"\b(exception|unsupported|no evidence|no related evidence|manual review|not source-backed)\b",
    re.IGNORECASE,
)


def object_label(obj: Dict, fallback: str) -> str:
    obj_id = obj.get("id")
    if obj_id is None or not str(obj_id).strip():
        return fallback
    return str(obj_id)


def as_non_empty_list(value) -> List:
    if isinstance(value, list):
        return [item for item in value if item is not None and str(item).strip()]
    return []


def load_items(path: Path) -> Tuple[List[Dict], List[str]]:
    warnings: List[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and isinstance(data.get("items"), list):
        items = data["items"]
    else:
        raise ValueError("top-level JSON must be an item array or a handoff object with an items array")

    dict_items: List[Dict] = []
    for idx, item in enumerate(items, start=1):
        if isinstance(item, dict):
            dict_items.append(item)
        else:
            warnings.append(f"[{path.name}:{idx}] Item is not an object; semantic checks skipped for it")
    return dict_items, warnings


def discover_json_files(path: Path) -> List[Path]:
    if not path.exists():
        raise SystemExit(f"Semantic validation path not found: {path}")
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise SystemExit(f"Semantic validation path is not a file or directory: {path}")

    handoff_files = sorted(path.glob(f"*{RECOMMENDED_HANDOFF_SUFFIX}"))
    if handoff_files:
        return handoff_files
    return sorted(path.glob("*.json"))


def normalize_key(*parts) -> str:
    return "\u001f".join(str(part).strip().casefold() for part in parts if part is not None)


def aliases_indicate_merge(first: Dict, second: Dict) -> bool:
    first_label = str(first.get("canonical_label") or "").strip().casefold()
    second_label = str(second.get("canonical_label") or "").strip().casefold()
    first_aliases = {str(alias).strip().casefold() for alias in as_non_empty_list(first.get("aliases"))}
    second_aliases = {str(alias).strip().casefold() for alias in as_non_empty_list(second.get("aliases"))}

    if first_label and first_label in second_aliases:
        return True
    if second_label and second_label in first_aliases:
        return True
    return bool(first_aliases & second_aliases)


def validate_items(
    items: List[Dict],
    source_name: str,
    known_ids: Set[str] = None,
    known_claim_evidence_ids: Set[str] = None,
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    seen_ids: Dict[str, int] = {}
    ids: Set[str] = set()

    reference_ids = known_ids if known_ids is not None else ids

    for idx, obj in enumerate(items, start=1):
        obj_id = obj.get("id")
        label = object_label(obj, f"{source_name}:{idx}")
        if obj_id is None or not str(obj_id).strip():
            errors.append(f"[{source_name}:{idx}] Missing or empty id")
        else:
            obj_id_str = str(obj_id)
            if obj_id_str in seen_ids:
                errors.append(
                    f"[{source_name}:{idx}] Duplicate id: {obj_id_str} "
                    f"(first seen at item {seen_ids[obj_id_str]})"
                )
            else:
                seen_ids[obj_id_str] = idx
                ids.add(obj_id_str)

        confidence = obj.get("confidence")
        if confidence is not None:
            if isinstance(confidence, bool):
                errors.append(f"[{source_name}:{idx}] confidence is not numeric: {label}")
            else:
                try:
                    confidence_value = float(confidence)
                except (TypeError, ValueError):
                    errors.append(f"[{source_name}:{idx}] confidence is not numeric: {label}")
                else:
                    if confidence_value < 0.0 or confidence_value > 1.0:
                        errors.append(f"[{source_name}:{idx}] confidence out of range [0,1]: {label}")

        review_status = obj.get("review_status")
        if review_status is not None and review_status not in ALLOWED_REVIEW_STATUS:
            errors.append(f"[{source_name}:{idx}] Invalid review_status for {label}: {review_status}")

        iri = obj.get("iri")
        if iri is not None and str(iri).strip() and not HTTP_IRI_RE.match(str(iri).strip()):
            errors.append(f"[{source_name}:{idx}] iri must look like an http(s) IRI for {label}: {iri}")

    claim_referenced_evidence: Set[str] = set()
    concept_keys: Dict[str, Tuple[int, Dict]] = {}

    for idx, obj in enumerate(items, start=1):
        label = object_label(obj, f"{source_name}:{idx}")
        obj_type = obj.get("type")

        for field in ("related_evidence_ids", "related_concept_ids"):
            related_ids = as_non_empty_list(obj.get(field))
            if field in obj and obj.get(field) is not None and not isinstance(obj.get(field), list):
                errors.append(f"[{source_name}:{idx}] {field} must be an array for {label}")
                continue
            for related_id in related_ids:
                related_id_str = str(related_id)
                if related_id_str not in reference_ids:
                    errors.append(f"[{source_name}:{idx}] {field} references missing id for {label}: {related_id_str}")

        if obj_type == "Claim":
            evidence_ids = as_non_empty_list(obj.get("related_evidence_ids"))
            claim_referenced_evidence.update(str(evidence_id) for evidence_id in evidence_ids)
            reviewer_notes = str(obj.get("reviewer_notes") or "")
            if obj.get("review_status") == "accepted" and not evidence_ids and not EXCEPTION_NOTE_RE.search(reviewer_notes):
                errors.append(
                    f"[{source_name}:{idx}] Accepted Claim must link related_evidence_ids "
                    f"or reviewer_notes must explain an exception: {label}"
                )
            if obj.get("review_status") == "accepted" and not str(obj.get("source_citation") or "").strip():
                warnings.append(f"[{source_name}:{idx}] Accepted Claim missing source_citation: {label}")

        if obj_type == "Concept":
            canonical_label = obj.get("canonical_label") or obj.get("label") or obj.get("name")
            span = obj.get("supporting_quote_or_span")
            if canonical_label and span:
                key = normalize_key(canonical_label, span)
                if key in concept_keys:
                    first_idx, first_obj = concept_keys[key]
                    if not aliases_indicate_merge(first_obj, obj):
                        warnings.append(
                            f"[{source_name}:{idx}] Possible duplicate Concept canonical_label/supporting span "
                            f"with item {first_idx}: {label}"
                        )
                else:
                    concept_keys[key] = (idx, obj)

    referenced_evidence_ids = (
        known_claim_evidence_ids if known_claim_evidence_ids is not None else claim_referenced_evidence
    )

    for idx, obj in enumerate(items, start=1):
        if obj.get("type") != "Evidence":
            continue
        obj_id = obj.get("id")
        if obj_id is not None and str(obj_id) not in referenced_evidence_ids:
            warnings.append(f"[{source_name}:{idx}] Evidence is not referenced by any Claim: {obj_id}")

    return errors, warnings


def validate_paths(paths: Iterable[Path]) -> Tuple[int, int, List[str], List[str]]:
    all_errors: List[str] = []
    all_warnings: List[str] = []
    item_count = 0
    loaded_files: List[Tuple[Path, List[Dict]]] = []
    global_seen_ids: Dict[str, str] = {}
    global_ids: Set[str] = set()
    global_claim_evidence_ids: Set[str] = set()

    for input_path in paths:
        for file_path in discover_json_files(input_path):
            try:
                items, load_warnings = load_items(file_path)
            except ValueError as exc:
                all_errors.append(f"{file_path}: {exc}")
                continue
            item_count += len(items)
            all_warnings.extend(load_warnings)
            loaded_files.append((file_path, items))

            for idx, obj in enumerate(items, start=1):
                obj_id = obj.get("id")
                if obj_id is not None and str(obj_id).strip():
                    obj_id_str = str(obj_id)
                    location = f"{file_path.name}:{idx}"
                    if obj_id_str in global_seen_ids:
                        all_errors.append(
                            f"[{location}] Duplicate id across checked files: {obj_id_str} "
                            f"(first seen at {global_seen_ids[obj_id_str]})"
                        )
                    else:
                        global_seen_ids[obj_id_str] = location
                        global_ids.add(obj_id_str)
                if obj.get("type") == "Claim":
                    global_claim_evidence_ids.update(
                        str(evidence_id) for evidence_id in as_non_empty_list(obj.get("related_evidence_ids"))
                    )

    known_ids = global_ids if len(loaded_files) > 1 else None
    known_claim_evidence_ids = global_claim_evidence_ids if len(loaded_files) > 1 else None
    for file_path, items in loaded_files:
        errors, warnings = validate_items(items, file_path.name, known_ids, known_claim_evidence_ids)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    return len(loaded_files), item_count, all_errors, all_warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate KG candidate/reviewed JSON semantics for ontology-quality handoffs."
    )
    parser.add_argument("paths", nargs="+", help="JSON file(s), handoff file(s), or directories to validate.")
    args = parser.parse_args()

    file_count, item_count, errors, warnings = validate_paths(Path(path) for path in args.paths)

    if warnings:
        print("Semantic warnings:")
        for warning in warnings:
            print(f"- {warning}")

    if errors:
        print("Semantic validation failed:")
        for error in errors:
            print(f"- {error}")
        print(
            f"Checked {file_count} file(s), {item_count} item(s): "
            f"{len(errors)} error(s), {len(warnings)} warning(s)."
        )
        raise SystemExit(1)

    print(
        f"Semantic validation passed: checked {file_count} file(s), {item_count} item(s); "
        f"0 error(s), {len(warnings)} warning(s)."
    )


if __name__ == "__main__":
    main()
