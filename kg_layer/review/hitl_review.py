import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

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


def object_label(obj: Dict) -> str:
    return str(
        obj.get("canonical_label")
        or obj.get("supporting_quote_or_span")
        or obj.get("source_citation")
        or obj.get("id")
        or ""
    ).replace("\n", " ").strip()


def truncate(value: str, limit: int = 140) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def load_objects(path: Path) -> Dict[str, Dict]:
    if not path.exists():
        raise SystemExit(f"Objects file not found: {path}")
    data = load_json(path)
    if not isinstance(data, list):
        raise SystemExit(f"Objects file must be a JSON array: {path}")
    return {str(obj.get("id")): obj for obj in data if isinstance(obj, dict) and obj.get("id")}


def load_edges(constraints_dir: Path) -> List[Dict]:
    edge_path = constraints_dir / "constraint.edges.json"
    if not edge_path.exists():
        raise SystemExit(f"Constraint edge file not found: {edge_path}")
    data = load_json(edge_path)
    if not isinstance(data, list):
        raise SystemExit(f"Constraint edge file must be a JSON array: {edge_path}")
    return [edge for edge in data if isinstance(edge, dict)]


def iter_claim_evidence_edges(edges: Iterable[Dict]) -> Iterable[Tuple[str, str, Dict]]:
    for edge in edges:
        source_id = str(edge.get("source_id") or "")
        target_id = str(edge.get("target_id") or "")
        relation = str(edge.get("relation_type") or "")
        if relation == "supports" and source_id.startswith("claim:") and target_id.startswith("evidence:"):
            yield source_id, target_id, edge


def related_concepts(claim: Dict, objects_by_id: Dict[str, Dict], limit: int) -> List[Dict]:
    explicit_ids = []
    for field in ("related_concept_ids", "concept_ids", "about_concept_ids"):
        values = claim.get(field) or []
        if isinstance(values, list):
            explicit_ids.extend(str(value) for value in values)

    explicit = [objects_by_id[obj_id] for obj_id in explicit_ids if obj_id in objects_by_id]
    if explicit:
        return explicit[:limit]

    source_section = claim.get("source_section")
    article_id = claim.get("article_id")
    candidates = [
        obj
        for obj in objects_by_id.values()
        if obj.get("type") == "Concept"
        and obj.get("article_id") == article_id
        and obj.get("source_section") == source_section
        and obj.get("review_status") != "rejected"
    ]
    if not candidates:
        candidates = [
            obj
            for obj in objects_by_id.values()
            if obj.get("type") == "Concept"
            and obj.get("article_id") == article_id
            and obj.get("review_status") != "rejected"
            and len(object_label(obj)) > 3
        ]
    return sorted(candidates, key=lambda obj: (-float(obj.get("confidence") or 0), object_label(obj)))[:limit]


def cmd_chains(args) -> None:
    objects_by_id = load_objects(Path(args.objects))
    edges = load_edges(Path(args.constraints_dir))
    statuses = set(args.status or [])
    rows = []

    for claim_id, evidence_id, edge in iter_claim_evidence_edges(edges):
        claim = objects_by_id.get(claim_id)
        evidence = objects_by_id.get(evidence_id)
        if not claim or not evidence:
            continue
        if statuses and claim.get("review_status") not in statuses and evidence.get("review_status") not in statuses:
            continue
        score = float(claim.get("confidence") or 0) + float(evidence.get("confidence") or 0)
        rows.append((score, claim, evidence, edge, related_concepts(claim, objects_by_id, args.concepts)))

    rows.sort(key=lambda row: (-row[0], row[1].get("id", "")))
    rows = rows[: args.top]
    if not rows:
        print("No review chains found.")
        return

    for idx, (_, claim, evidence, edge, concepts) in enumerate(rows, start=1):
        print(f"[{idx}] review chain")
        if concepts:
            for concept in concepts:
                print(
                    f"    Concept:  {concept.get('id')}  candidate_link=needs_review  "
                    f"status={concept.get('review_status')}  conf={concept.get('confidence')}"
                )
                print(f"              {truncate(object_label(concept))}")
            arrow = "       -->"
        else:
            print("    Concept:  none linked; showing claim/evidence only")
            arrow = "    "

        print(
            f"{arrow} Claim:    {claim.get('id')}  "
            f"status={claim.get('review_status')}  conf={claim.get('confidence')}"
        )
        print(f"              {truncate(object_label(claim))}")
        print(
            f"       --> Evidence: {evidence.get('id')}  "
            f"relation={edge.get('relation_type')}  status={evidence.get('review_status')}  conf={evidence.get('confidence')}"
        )
        print(f"              {truncate(object_label(evidence))}")
        print(f"              source={claim.get('source_document')}#{claim.get('source_section')}")
        print()


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

    chains_cmd = sub.add_parser("chains", help="Show claim-evidence review chains with related concepts when available.")
    chains_cmd.add_argument(
        "--objects",
        default="kg_layer/data/reviewed/reviewed.json",
        help="Reviewed/validated object JSON array.",
    )
    chains_cmd.add_argument(
        "--constraints-dir",
        default="kg_layer/data/published/constraints/draft",
        help="Directory containing constraint.edges.json.",
    )
    chains_cmd.add_argument("--top", type=int, default=5, help="Number of chains to show.")
    chains_cmd.add_argument(
        "--status",
        action="append",
        choices=sorted(ALLOWED_STATUS),
        help="Only show chains where claim or evidence has this review status. Repeatable.",
    )
    chains_cmd.add_argument("--concepts", type=int, default=3, help="Maximum related concepts to show per claim.")
    chains_cmd.set_defaults(func=cmd_chains)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
