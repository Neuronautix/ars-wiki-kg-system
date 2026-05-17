import argparse
import json
from pathlib import Path
from typing import Dict, List

QUEUE_STATUSES = {"pending", "in_review", "needs_revision"}
TYPE_WEIGHT = {"Claim": 0.25, "Evidence": 0.2, "Concept": 0.1, "Paper": 0.05}
STATUS_WEIGHT = {"pending": 0.2, "needs_revision": 0.15, "in_review": 0.1}


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


def build_previous_fingerprints(previous_reviewed: List[Dict]) -> set:
    return {fingerprint(o) for o in previous_reviewed}


def priority_score(obj: Dict, is_changed_or_new: bool) -> float:
    confidence = float(obj.get("confidence", 0.0))
    uncertainty = max(0.0, min(1.0, 1.0 - confidence))
    score = uncertainty
    score += TYPE_WEIGHT.get(str(obj.get("type", "")), 0.0)
    score += STATUS_WEIGHT.get(str(obj.get("review_status", "")), 0.0)
    if is_changed_or_new:
        score += 0.3
    return round(score, 6)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build prioritized HITL review queue from reviewed objects.")
    parser.add_argument("--objects", required=True, help="Reviewed objects JSON input.")
    parser.add_argument("--output", required=True, help="Review queue JSON output.")
    parser.add_argument("--previous-reviewed", help="Optional previous reviewed JSON for change detection.")
    parser.add_argument("--max-items", type=int, default=0, help="Optional max queue items (0 = all).")
    args = parser.parse_args()

    objects_path = Path(args.objects)
    output_path = Path(args.output)
    previous_path = Path(args.previous_reviewed) if args.previous_reviewed else None

    if not objects_path.exists():
        raise SystemExit(f"Input objects file not found: {objects_path}")

    objects: List[Dict] = load_json(objects_path)
    previous_reviewed: List[Dict] = []
    if previous_path and previous_path.exists():
        previous_reviewed = load_json(previous_path)
    previous_fingerprints = build_previous_fingerprints(previous_reviewed)

    queue: List[Dict] = []
    for obj in objects:
        status = str(obj.get("review_status", "pending"))
        if status not in QUEUE_STATUSES:
            continue
        item_fingerprint = fingerprint(obj)
        is_changed_or_new = item_fingerprint not in previous_fingerprints
        queue.append(
            {
                "object_id": obj.get("id"),
                "type": obj.get("type"),
                "review_status": status,
                "confidence": obj.get("confidence"),
                "source_document": obj.get("source_document"),
                "source_section": obj.get("source_section"),
                "evidence_snippet": str(obj.get("supporting_quote_or_span", ""))[:300],
                "is_changed_or_new": is_changed_or_new,
                "priority_score": priority_score(obj, is_changed_or_new),
            }
        )

    queue.sort(key=lambda x: (-x["priority_score"], str(x.get("object_id", ""))))
    if args.max_items > 0:
        queue = queue[: args.max_items]

    payload = {"total_items": len(queue), "items": queue}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote review queue with {len(queue)} items to {output_path}")


if __name__ == "__main__":
    main()
