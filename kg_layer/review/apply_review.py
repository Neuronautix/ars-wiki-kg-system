import argparse
import json
from pathlib import Path
from typing import Dict, List


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply human review decisions to extracted objects.")
    parser.add_argument("--objects", required=True, help="Input candidate objects JSON.")
    parser.add_argument("--reviews", required=True, help="Review decisions JSON array.")
    parser.add_argument("--output", required=True, help="Output reviewed objects JSON.")
    args = parser.parse_args()

    objects_path = Path(args.objects)
    reviews_path = Path(args.reviews)
    output_path = Path(args.output)

    if not objects_path.exists():
        raise SystemExit(f"Objects file not found: {objects_path}")
    if not reviews_path.exists():
        raise SystemExit(f"Reviews file not found: {reviews_path}")

    objects: List[Dict] = load_json(objects_path)
    reviews: List[Dict] = load_json(reviews_path)

    decision_map = {r["object_id"]: r for r in reviews if "object_id" in r}
    updated = 0

    for obj in objects:
        obj_id = obj.get("id")
        if obj_id in decision_map:
            decision = decision_map[obj_id]
            obj["review_status"] = decision.get("review_status", obj.get("review_status", "pending"))
            obj["reviewer_notes"] = decision.get("reviewer_notes", obj.get("reviewer_notes", ""))
            obj["reviewer"] = decision.get("reviewer", "")
            obj["reviewed_at"] = decision.get("reviewed_at", "")
            updated += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(objects, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Applied reviews to {updated} objects")
    print(f"Output written to {output_path}")


if __name__ == "__main__":
    main()
