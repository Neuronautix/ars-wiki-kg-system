import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from kg_layer.exports.jsonld_utils import DEFAULT_BASE_IRI, object_iri
except ModuleNotFoundError:
    from jsonld_utils import DEFAULT_BASE_IRI, object_iri

ALLOWED_STATUS = {"pending", "in_review", "accepted", "rejected", "needs_revision"}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def make_edge(
    source_id: str, target_id: str, relation_type: str, confidence: Optional[float], provenance: Dict
) -> Dict:
    edge = {
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": relation_type,
        "confidence": confidence,
        "provenance": provenance,
    }
    return edge


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export machine-actionable constraint artifacts for embeddings and LLM navigation."
    )
    parser.add_argument("--input", required=True, help="Reviewed objects JSON input.")
    parser.add_argument("--output-dir", required=True, help="Output directory for constraint artifacts.")
    parser.add_argument(
        "--include-status",
        action="append",
        default=None,
        choices=sorted(ALLOWED_STATUS),
        help="Review status to include. Repeatable. Defaults to accepted.",
    )
    parser.add_argument(
        "--base-iri",
        default=DEFAULT_BASE_IRI,
        help=f"Base IRI for generated object identifiers. Defaults to {DEFAULT_BASE_IRI}",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    statuses = set(args.include_status or ["accepted"])
    objects: List[Dict] = json.loads(input_path.read_text(encoding="utf-8"))
    filtered = [obj for obj in objects if obj.get("review_status") in statuses]
    iri_by_id = {str(obj.get("id")): object_iri(obj, args.base_iri) for obj in filtered if obj.get("id")}

    nodes: List[Dict] = []
    edges: List[Dict] = []
    concept_to_claim: Dict[str, List[str]] = {}
    claim_to_evidence: Dict[str, List[str]] = {}
    article_to_subgraph: Dict[str, Dict[str, List[str]]] = {}
    embedding_payloads: List[Dict] = []
    seen_edges: Set[Tuple[str, str, str]] = set()

    for obj in filtered:
        obj_id = str(obj.get("id") or "").strip()
        if not obj_id:
            continue
        source_document = str(obj.get("source_document") or "unknown")
        node = {
            "id": obj_id,
            "iri": iri_by_id.get(obj_id),
            "type": obj.get("type"),
            "status": obj.get("review_status"),
            "confidence": obj.get("confidence"),
            "article_id": obj.get("article_id"),
            "run_id": obj.get("run_id"),
            "source_document": source_document,
            "source_section": obj.get("source_section"),
            "source_citation": obj.get("source_citation"),
            "citation_ids": obj.get("citation_ids", []),
            "canonical_label": obj.get("canonical_label"),
            "canonical_id": obj.get("canonical_id"),
            "aliases": obj.get("aliases", []),
            "ontology_mappings": obj.get("ontology_mappings", []),
            "contract_version": obj.get("contract_version"),
        }
        nodes.append(node)

        article_entry = article_to_subgraph.setdefault(
            source_document, {"node_ids": [], "edge_keys": [], "article_id": str(obj.get("article_id") or "")}
        )
        article_entry["node_ids"].append(obj_id)

        payload = {
            "id": obj_id,
            "type": obj.get("type"),
            "canonical_text": obj.get("canonical_label") or obj.get("supporting_quote_or_span"),
            "aliases": obj.get("aliases", []),
            "citation_snippet": obj.get("source_citation") or obj.get("supporting_quote_or_span"),
            "status": obj.get("review_status"),
            "confidence": obj.get("confidence"),
            "provenance": {
                "source_document": source_document,
                "source_section": obj.get("source_section"),
                "reviewer": obj.get("reviewer"),
                "reviewed_at": obj.get("reviewed_at"),
            },
            "risk_flag": obj.get("review_status") == "needs_revision",
        }
        embedding_payloads.append(payload)

        provenance = {
            "source_document": source_document,
            "source_section": obj.get("source_section"),
            "status": obj.get("review_status"),
        }

        for evidence_id in obj.get("related_evidence_ids", []) or []:
            edge_key = (obj_id, str(evidence_id), "supports")
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            edges.append(make_edge(obj_id, str(evidence_id), "supports", obj.get("confidence"), provenance))
            if obj.get("type") == "Claim":
                claim_to_evidence.setdefault(obj_id, []).append(str(evidence_id))
            article_entry["edge_keys"].append("|".join(edge_key))

        for concept_id in obj.get("related_concept_ids", []) or []:
            edge_key = (obj_id, str(concept_id), "relates_to_concept")
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            edges.append(make_edge(obj_id, str(concept_id), "relates_to_concept", obj.get("confidence"), provenance))
            if obj.get("type") == "Claim":
                concept_to_claim.setdefault(str(concept_id), []).append(obj_id)
            article_entry["edge_keys"].append("|".join(edge_key))

        for edge in obj.get("relation_edges", []) or []:
            if not isinstance(edge, dict):
                continue
            target_id = str(edge.get("target_id") or "").strip()
            relation_type = str(edge.get("relation_type") or "").strip()
            if not target_id or not relation_type:
                continue
            edge_key = (obj_id, target_id, relation_type)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            rel_conf = edge.get("confidence", obj.get("confidence"))
            edges.append(make_edge(obj_id, target_id, relation_type, rel_conf, provenance))
            if obj.get("type") == "Claim" and relation_type == "supports":
                claim_to_evidence.setdefault(obj_id, []).append(target_id)
            if obj.get("type") == "Claim" and relation_type == "relates_to_concept":
                concept_to_claim.setdefault(target_id, []).append(obj_id)
            article_entry["edge_keys"].append("|".join(edge_key))

    for mapping in (concept_to_claim, claim_to_evidence):
        for key, values in list(mapping.items()):
            mapping[key] = sorted(set(values))

    for source_document, entry in article_to_subgraph.items():
        entry["node_ids"] = sorted(set(entry["node_ids"]))
        entry["edge_keys"] = sorted(set(entry["edge_keys"]))
        entry["edge_count"] = len(entry["edge_keys"])
        entry["node_count"] = len(entry["node_ids"])
        entry["source_document"] = source_document

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "constraint.nodes.json").write_text(
        json.dumps(nodes, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "constraint.edges.json").write_text(
        json.dumps(edges, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "index.concept_to_claim.json").write_text(
        json.dumps(concept_to_claim, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "index.claim_to_evidence.json").write_text(
        json.dumps(claim_to_evidence, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "index.article_to_subgraph.json").write_text(
        json.dumps(article_to_subgraph, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with (output_dir / "embedding_payloads.jsonl").open("w", encoding="utf-8") as handle:
        for row in embedding_payloads:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "generated_at": now_utc(),
        "base_iri": args.base_iri,
        "include_statuses": sorted(statuses),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "retrieval_policy": {
            "default_mode": (
                "accepted_only" if statuses == {"accepted"} else "draft"
            ),
            "allow_needs_revision": "needs_revision" in statuses,
        },
        "files": [
            "constraint.nodes.json",
            "constraint.edges.json",
            "embedding_payloads.jsonl",
            "index.concept_to_claim.json",
            "index.claim_to_evidence.json",
            "index.article_to_subgraph.json",
        ],
    }
    (output_dir / "constraint_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Exported constraint artifacts to {output_dir} ({len(nodes)} nodes, {len(edges)} edges).")


if __name__ == "__main__":
    main()
