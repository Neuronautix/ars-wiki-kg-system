import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

AUTO_REVIEWER = "pipeline_carry_forward"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fingerprint(obj: Dict) -> str:
    parts = [
        str(obj.get("type", "")).strip(),
        str(obj.get("source_document", "")).strip(),
        str(obj.get("source_section", "")).strip(),
        str(obj.get("supporting_quote_or_span", "")).strip(),
    ]
    return "|".join(parts)


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
    accepted_fingerprints = set()
    if args.carry_forward_accepted:
        accepted_fingerprints = {
            fingerprint(o)
            for o in previous_reviewed
            if o.get("review_status") == "accepted"
        }
    updated = 0
    carried = 0
    reviewed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    for obj in objects:
        obj_id = obj.get("id")
        if obj_id in decision_map:
            decision = decision_map[obj_id]
            obj["review_status"] = decision.get("review_status", obj.get("review_status", "pending"))
            obj["reviewer_notes"] = decision.get("reviewer_notes", obj.get("reviewer_notes", ""))
            obj["reviewer"] = decision.get("reviewer", "")
            obj["reviewed_at"] = decision.get("reviewed_at", "")
            updated += 1
        elif args.carry_forward_accepted and fingerprint(obj) in accepted_fingerprints:
            obj["review_status"] = "accepted"
            obj["reviewer_notes"] = obj.get("reviewer_notes") or "Accepted carry-forward (unchanged source span)."
            obj["reviewer"] = AUTO_REVIEWER
            obj["reviewed_at"] = reviewed_at
            carried += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(objects, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Applied reviews to {updated} objects")
    if args.carry_forward_accepted:
        print(f"Carry-forward accepted objects: {carried}")
    print(f"Output written to {output_path}")


if __name__ == "__main__":
    main()
