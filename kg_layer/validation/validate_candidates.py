import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

REQUIRED_TYPES = {"Paper", "Concept", "Claim", "Evidence"}
REQUIRED_FIELDS = [
    "type",
    "id",
    "source_document",
    "source_section",
    "supporting_quote_or_span",
    "confidence",
    "extraction_method",
    "review_status",
    "reviewer_notes",
]
ALLOWED_REVIEW_STATUS = {"pending", "in_review", "accepted", "rejected", "needs_revision"}
ID_RE = re.compile(r"^(paper|concept|claim|evidence):[a-z0-9][a-z0-9-]*:\d+$")


def validate_object(obj: Dict, idx: int) -> List[str]:
    errors: List[str] = []
    for field in REQUIRED_FIELDS:
        if field not in obj:
            errors.append(f"[{idx}] Missing field: {field}")

    if "type" in obj and obj["type"] not in REQUIRED_TYPES:
        errors.append(f"[{idx}] Invalid type: {obj['type']}")

    if "review_status" in obj and obj["review_status"] not in ALLOWED_REVIEW_STATUS:
        errors.append(f"[{idx}] Invalid review_status: {obj['review_status']}")

    if "confidence" in obj:
        try:
            conf = float(obj["confidence"])
            if conf < 0.0 or conf > 1.0:
                errors.append(f"[{idx}] confidence out of range [0,1]: {conf}")
        except Exception:
            errors.append(f"[{idx}] confidence is not numeric")

    for txt in ["id", "source_document", "source_section", "supporting_quote_or_span", "extraction_method"]:
        if txt in obj and not str(obj[txt]).strip():
            errors.append(f"[{idx}] Empty value: {txt}")

    obj_id = str(obj.get("id", "")).strip()
    if obj_id and not ID_RE.match(obj_id):
        errors.append(f"[{idx}] id does not follow deterministic policy (<type>:<slug>:<index>): {obj_id}")

    if obj.get("source_span_start") is not None or obj.get("source_span_end") is not None:
        start = obj.get("source_span_start")
        end = obj.get("source_span_end")
        if not isinstance(start, int) or not isinstance(end, int):
            errors.append(f"[{idx}] source_span_start/source_span_end must both be integers when present")
        elif start < 0 or end < 0 or end <= start:
            errors.append(f"[{idx}] Invalid source span offsets: start={start}, end={end}")

    return errors


def validate(data: List[Dict]) -> Tuple[List[Dict], List[str]]:
    all_errors: List[str] = []
    valid: List[Dict] = []
    seen_ids = set()

    for i, obj in enumerate(data, start=1):
        errs = validate_object(obj, i)
        obj_id = obj.get("id")
        if obj_id in seen_ids:
            errs.append(f"[{i}] Duplicate id: {obj_id}")
        else:
            seen_ids.add(obj_id)

        if errs:
            all_errors.extend(errs)
        else:
            valid.append(obj)

    return valid, all_errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate extracted candidate objects.")
    parser.add_argument("--input", required=True, help="Input JSON objects path.")
    parser.add_argument("--output", required=True, help="Output JSON path for valid objects.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    data = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Input JSON must be a list of objects.")

    valid, errors = validate(data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(valid, indent=2, ensure_ascii=False), encoding="utf-8")

    if errors:
        print("Validation completed with errors:")
        for err in errors:
            print(f"- {err}")
    else:
        print("Validation completed with no errors.")

    print(f"Valid objects written: {len(valid)} -> {output_path}")


if __name__ == "__main__":
    main()
