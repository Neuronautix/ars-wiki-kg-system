from __future__ import annotations

from copy import deepcopy
from typing import Dict, Iterable, List, Optional, Tuple

ARS_SCHEMA_VERSION = "1.0.0"
KG_SCHEMA_VERSION = "1.1.0"
SUPPORTED_SCHEMA_VERSIONS = {ARS_SCHEMA_VERSION, KG_SCHEMA_VERSION}

ARS_LINK_RELATION_MAP = {
    "claim_supported_by_evidence": "supports",
    "claim_contradicted_by_evidence": "contradicts",
    "claim_about_concept": "relates_to_concept",
    "evidence_about_concept": "relates_to_concept",
}


def is_ars_handoff(data: Dict) -> bool:
    return str(data.get("schema_version")) == ARS_SCHEMA_VERSION


def adapt_review_decision(item: Dict) -> Dict:
    """Map ARS review_decision into KG reviewer fields while preserving source fields."""
    out = dict(item)
    review_decision = out.get("review_decision")
    if isinstance(review_decision, dict):
        if "reviewer" not in out and review_decision.get("decision_by") is not None:
            out["reviewer"] = review_decision["decision_by"]
        if "reviewed_at" not in out and review_decision.get("decision_at") is not None:
            out["reviewed_at"] = review_decision["decision_at"]
        if "reviewer_notes" not in out and review_decision.get("rationale") is not None:
            out["reviewer_notes"] = review_decision["rationale"]
    return out


def adapt_handoff(data: Dict) -> Dict:
    """Return a KG-ingestion-friendly copy of a handoff payload.

    KG 1.1.0 handoffs are returned with only review_decision mapping applied.
    ARS 1.0.0 handoffs additionally get top-level links projected into each
    source item's relation_edges.
    """
    out = deepcopy(data)
    if not isinstance(out.get("items"), list):
        return out

    out["items"] = [adapt_review_decision(item) if isinstance(item, dict) else item for item in out["items"]]

    if is_ars_handoff(out):
        attach_links_as_relation_edges(out["items"], out.get("links", []))

    return out


def attach_links_as_relation_edges(items: List[Dict], links: Iterable) -> None:
    items_by_id = {item.get("id"): item for item in items if isinstance(item, dict)}
    for link in links:
        edge = link_to_relation_edge(link)
        if edge is None:
            continue

        from_id, relation_edge = edge
        source_item = items_by_id.get(from_id)
        if not isinstance(source_item, dict):
            continue

        relation_edges = source_item.setdefault("relation_edges", [])
        if isinstance(relation_edges, list) and not relation_edge_exists(relation_edges, relation_edge):
            relation_edges.append(relation_edge)

        reverse_edge = reverse_link_to_relation_edge(link)
        if reverse_edge is None:
            continue
        reverse_from_id, reverse_relation_edge = reverse_edge
        reverse_source_item = items_by_id.get(reverse_from_id)
        if not isinstance(reverse_source_item, dict):
            continue
        reverse_relation_edges = reverse_source_item.setdefault("relation_edges", [])
        if isinstance(reverse_relation_edges, list) and not relation_edge_exists(
            reverse_relation_edges, reverse_relation_edge
        ):
            reverse_relation_edges.append(reverse_relation_edge)


def link_to_relation_edge(link: object) -> Optional[Tuple[str, Dict]]:
    if not isinstance(link, dict):
        return None

    from_id = str(link.get("from_id", "")).strip()
    to_id = str(link.get("to_id", "")).strip()
    relation_type = ARS_LINK_RELATION_MAP.get(str(link.get("relation_type", "")).strip())
    if not from_id or not to_id or relation_type is None:
        return None

    edge: Dict = {
        "target_id": to_id,
        "relation_type": relation_type,
    }
    if link.get("confidence") is not None:
        edge["confidence"] = link["confidence"]
    if link.get("id") is not None:
        edge["source_link_id"] = link["id"]
    if link.get("polarity") is not None:
        edge["polarity"] = link["polarity"]
    if link.get("rationale") is not None:
        edge["rationale"] = link["rationale"]

    return from_id, edge


def reverse_link_to_relation_edge(link: object) -> Optional[Tuple[str, Dict]]:
    """Add KG-internal reverse support edges for ARS top-level claim/evidence links."""
    if not isinstance(link, dict):
        return None

    relation_type = str(link.get("relation_type", "")).strip()
    if relation_type != "claim_supported_by_evidence":
        return None

    from_id = str(link.get("from_id", "")).strip()
    to_id = str(link.get("to_id", "")).strip()
    if not from_id or not to_id:
        return None

    edge: Dict = {
        "target_id": from_id,
        "relation_type": "supports",
    }
    if link.get("confidence") is not None:
        edge["confidence"] = link["confidence"]
    if link.get("id") is not None:
        edge["source_link_id"] = link["id"]
    if link.get("polarity") is not None:
        edge["polarity"] = link["polarity"]
    if link.get("rationale") is not None:
        edge["rationale"] = link["rationale"]

    return to_id, edge


def relation_edge_exists(edges: List, candidate: Dict) -> bool:
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        if (
            edge.get("target_id") == candidate.get("target_id")
            and edge.get("relation_type") == candidate.get("relation_type")
        ):
            return True
    return False
