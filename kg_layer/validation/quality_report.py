import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate KG run-level quality metrics and append trend history.")
    parser.add_argument("--input", required=True, help="Reviewed objects JSON input.")
    parser.add_argument("--output", required=True, help="Output run quality report JSON path.")
    parser.add_argument(
        "--trend-file",
        required=True,
        help="Trend JSON file path; report summary is appended each run for drift tracking.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    trend_path = Path(args.trend_file)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    objects: List[Dict] = json.loads(input_path.read_text(encoding="utf-8"))
    by_type = Counter(str(obj.get("type", "unknown")) for obj in objects)
    by_status = Counter(str(obj.get("review_status", "unknown")) for obj in objects)
    accepted_claims = [obj for obj in objects if obj.get("type") == "Claim" and obj.get("review_status") == "accepted"]
    evidence_ids: Set[str] = {str(obj.get("id")) for obj in objects if obj.get("type") == "Evidence" and obj.get("id")}
    supported_evidence_ids: Set[str] = set()
    unresolved_concepts = 0
    citation_complete = 0
    contradictions = 0
    claims_without_evidence = 0

    for claim in accepted_claims:
        related_evidence = [str(v) for v in claim.get("related_evidence_ids", []) or []]
        for edge in claim.get("relation_edges", []) or []:
            if not isinstance(edge, dict):
                continue
            rel_type = str(edge.get("relation_type", "")).strip()
            target_id = str(edge.get("target_id", "")).strip()
            if rel_type == "supports" and target_id:
                related_evidence.append(target_id)
            if rel_type == "contradicts":
                contradictions += 1
        if not related_evidence:
            claims_without_evidence += 1
        supported_evidence_ids.update(related_evidence)
        if str(claim.get("source_citation") or "").strip() or (claim.get("citation_ids") or []):
            citation_complete += 1

    for obj in objects:
        if obj.get("type") != "Concept":
            continue
        if obj.get("review_status") == "accepted":
            label = str(obj.get("canonical_label") or "").strip()
            cid = str(obj.get("canonical_id") or "").strip()
            if not label and not cid:
                unresolved_concepts += 1

    orphan_evidence = sorted(evidence_ids - supported_evidence_ids)
    accepted_claim_count = len(accepted_claims)
    coverage_ratio = (
        round((accepted_claim_count - claims_without_evidence) / accepted_claim_count, 6)
        if accepted_claim_count
        else 0.0
    )
    citation_completeness = round(citation_complete / accepted_claim_count, 6) if accepted_claim_count else 0.0

    report = {
        "generated_at": now_utc(),
        "totals": {
            "objects": len(objects),
            "accepted_claims": accepted_claim_count,
            "orphan_evidence": len(orphan_evidence),
            "unresolved_concepts": unresolved_concepts,
        },
        "distribution": {
            "by_type": dict(by_type),
            "by_status": dict(by_status),
        },
        "quality_metrics": {
            "accepted_claim_evidence_coverage": coverage_ratio,
            "citation_completeness": citation_completeness,
            "conflict_count": contradictions,
            "orphan_evidence_ids": orphan_evidence[:200],
        },
        "notes": [
            "Coverage measures accepted claims with explicit related evidence links.",
            "Citation completeness accepts source_citation or citation_ids.",
            "Conflict count tracks explicit contradiction relation edges.",
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    trend_payload = []
    if trend_path.exists():
        try:
            existing = json.loads(trend_path.read_text(encoding="utf-8"))
            if isinstance(existing, list):
                trend_payload = existing
        except json.JSONDecodeError:
            trend_payload = []
    trend_payload.append(
        {
            "generated_at": report["generated_at"],
            "objects": report["totals"]["objects"],
            "accepted_claim_evidence_coverage": report["quality_metrics"]["accepted_claim_evidence_coverage"],
            "citation_completeness": report["quality_metrics"]["citation_completeness"],
            "conflict_count": report["quality_metrics"]["conflict_count"],
            "orphan_evidence": report["totals"]["orphan_evidence"],
            "unresolved_concepts": report["totals"]["unresolved_concepts"],
        }
    )
    trend_path.parent.mkdir(parents=True, exist_ok=True)
    trend_path.write_text(json.dumps(trend_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote run quality report: {output_path}")
    print(f"Updated trend history: {trend_path} ({len(trend_payload)} entries)")


if __name__ == "__main__":
    main()
