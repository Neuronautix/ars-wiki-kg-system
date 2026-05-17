import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

AUTO_REVIEWER = "pipeline_carry_forward"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint_parts(obj: Dict) -> Tuple[str, str, str, str]:
    return (
        str(obj.get("type", "")).strip(),
        str(obj.get("source_document", "")).strip(),
        str(obj.get("source_section", "")).strip(),
        str(obj.get("supporting_quote_or_span", "")).strip(),
    )


def fingerprint(obj: Dict) -> str:
    digest = hashlib.sha256(json.dumps(fingerprint_parts(obj), ensure_ascii=False).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply human review decisions to extracted objects.")
    parser.add_argument("--objects", required=True, help="Input candidate objects JSON.")
    parser.add_argument("--reviews", required=True, help="Review decisions JSON array.")
    parser.add_argument("--output", required=True, help="Output reviewed objects JSON.")
    parser.add_argument(
        "--previous-reviewed",
        help="Optional previous reviewed objects JSON for change-aware carry-forward.",
    )
    parser.add_argument(
        "--carry-forward-accepted",
        action="store_true",
        help="Carry forward accepted decisions for unchanged objects when no explicit decision exists.",
    )
    args = parser.parse_args()

    objects_path = Path(args.objects)
    reviews_path = Path(args.reviews)
    output_path = Path(args.output)
    previous_reviewed_path = Path(args.previous_reviewed) if args.previous_reviewed else None

    if not objects_path.exists():
        raise SystemExit(f"Objects file not found: {objects_path}")
    if not reviews_path.exists():
        raise SystemExit(f"Reviews file not found: {reviews_path}")

    objects: List[Dict] = load_json(objects_path)
    reviews: List[Dict] = load_json(reviews_path)
    previous_reviewed: List[Dict] = []
    if previous_reviewed_path and previous_reviewed_path.exists():
        previous_reviewed = load_json(previous_reviewed_path)

    decision_map = {r["object_id"]: r for r in reviews if "object_id" in r}
    previous_by_id: Dict[str, Dict] = {str(o.get("id")): o for o in previous_reviewed if o.get("id")}
    accepted_fingerprint_counts: Dict[str, int] = {}
    if args.carry_forward_accepted:
        for obj in previous_reviewed:
            if obj.get("review_status") != "accepted":
                continue
            fp = fingerprint(obj)
            accepted_fingerprint_counts[fp] = accepted_fingerprint_counts.get(fp, 0) + 1
    updated = 0
    carried = 0
    reviewed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    for obj in objects:
        obj_id = obj.get("id")
        obj_fingerprint = fingerprint(obj)
        if obj_id in decision_map:
            decision = decision_map[obj_id]
            decision_status = decision.get("review_status", obj.get("review_status", "pending"))
            decision_fingerprint = decision.get("source_fingerprint")
            previous_obj = previous_by_id.get(str(obj_id))
            previous_fingerprint_matches = previous_obj is not None and fingerprint(previous_obj) == obj_fingerprint
            has_stale_accepted_decision = (
                args.carry_forward_accepted
                and decision_status == "accepted"
                and (
                    (decision_fingerprint and decision_fingerprint != obj_fingerprint)
                    or (decision_fingerprint is None and previous_obj is not None and not previous_fingerprint_matches)
                )
            )
            if has_stale_accepted_decision:
                continue
            obj["review_status"] = decision_status
            obj["reviewer_notes"] = decision.get("reviewer_notes", obj.get("reviewer_notes", ""))
            obj["reviewer"] = decision.get("reviewer", "")
            obj["reviewed_at"] = decision.get("reviewed_at", "")
            updated += 1
        elif args.carry_forward_accepted and accepted_fingerprint_counts.get(obj_fingerprint, 0) > 0:
            obj["review_status"] = "accepted"
            obj["reviewer_notes"] = obj.get("reviewer_notes") or "Accepted carry-forward (unchanged source span)."
            obj["reviewer"] = AUTO_REVIEWER
            obj["reviewed_at"] = reviewed_at
            accepted_fingerprint_counts[obj_fingerprint] -= 1
            carried += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(objects, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Applied reviews to {updated} objects")
    if args.carry_forward_accepted:
        print(f"Carry-forward accepted objects: {carried}")
    print(f"Output written to {output_path}")


if __name__ == "__main__":
    main()
