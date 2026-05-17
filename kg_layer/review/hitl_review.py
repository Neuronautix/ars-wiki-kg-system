import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ALLOWED_STATUS = {"pending", "in_review", "accepted", "rejected", "needs_revision"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=str(path.parent),
    ) as tmp_file:
        tmp_file.write(json.dumps(data, indent=2, ensure_ascii=False))
        tmp_path = Path(tmp_file.name)
    os.replace(tmp_path, path)


def cmd_next(args) -> None:
    queue_path = Path(args.queue)
    if not queue_path.exists():
        raise SystemExit(f"Queue file not found: {queue_path}")
    queue = load_json(queue_path).get("items", [])
    if not queue:
        print("No review items in queue.")
        return

    if args.top < 1:
        raise SystemExit("--top must be >= 1")

    top = queue[: args.top]
    for idx, item in enumerate(top, start=1):
        print(f"[{idx}] {item.get('object_id')}  score={item.get('priority_score')}  status={item.get('review_status')}")
        print(f"    type={item.get('type')}  confidence={item.get('confidence')}  changed_or_new={item.get('is_changed_or_new')}")
        print(f"    source={item.get('source_document')}#{item.get('source_section')}")
        print(f"    snippet={item.get('evidence_snippet')}")


def cmd_decide(args) -> None:
    if args.status not in ALLOWED_STATUS:
        raise SystemExit(f"Invalid status: {args.status}")

    reviews_path = Path(args.reviews)
    existing: List[Dict] = []
    if reviews_path.exists():
        existing = load_json(reviews_path)
        if not isinstance(existing, list):
            raise SystemExit("reviews.json must be a JSON array.")

    reviewed_at = args.reviewed_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    decision = {
        "object_id": args.object_id,
        "review_status": args.status,
        "reviewer": args.reviewer,
        "reviewed_at": reviewed_at,
        "reviewer_notes": args.notes or "",
    }

    replaced = False
    for idx, item in enumerate(existing):
        if item.get("object_id") == args.object_id:
            existing[idx] = decision
            replaced = True
            break
    if not replaced:
        existing.append(decision)

    write_json(reviews_path, existing)
    action = "Updated" if replaced else "Added"
    print(f"{action} review decision for {args.object_id} in {reviews_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="HITL helper CLI for queue triage and quick decisions.")
    sub = parser.add_subparsers(dest="command", required=True)

    next_cmd = sub.add_parser("next", help="Show highest-priority queue items.")
    next_cmd.add_argument("--queue", required=True, help="Review queue JSON path.")
    next_cmd.add_argument("--top", type=int, default=1, help="Number of top items to show.")
    next_cmd.set_defaults(func=cmd_next)

    decide_cmd = sub.add_parser("decide", help="Add or update a review decision in reviews.json.")
    decide_cmd.add_argument("--reviews", required=True, help="Path to review decisions JSON array.")
    decide_cmd.add_argument("--object-id", required=True, help="Object ID to update.")
    decide_cmd.add_argument("--status", required=True, choices=sorted(ALLOWED_STATUS), help="Review status value.")
    decide_cmd.add_argument("--reviewer", required=True, help="Reviewer name/identifier.")
    decide_cmd.add_argument("--notes", default="", help="Optional reviewer notes.")
    decide_cmd.add_argument("--reviewed-at", help="Optional ISO timestamp; defaults to current UTC.")
    decide_cmd.set_defaults(func=cmd_decide)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
