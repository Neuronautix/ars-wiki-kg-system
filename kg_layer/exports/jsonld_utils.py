import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote, urlparse

DEFAULT_BASE_IRI = "https://neuronautix.github.io/ars-wiki-kg-system/kg/"

TYPE_MAP = {
    "Paper": "schema:ScholarlyArticle",
    "Concept": "skos:Concept",
    "Claim": "arskg:Claim",
    "Evidence": "arskg:Evidence",
}

CONTEXT = {
    "arskg": "https://example.org/ars/kg#",
    "schema": "https://schema.org/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "prov": "http://www.w3.org/ns/prov#",
    "dcterms": "http://purl.org/dc/terms/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "sourceDocument": "arskg:sourceDocumentRef",
    "sourceSection": "arskg:sourceSection",
    "sourceSpan": "arskg:sourceSpan",
    "quote": "arskg:quote",
    "text": "arskg:text",
    "confidence": {
        "@id": "arskg:confidence",
        "@type": "xsd:decimal",
    },
    "extractionMethod": "arskg:extractionMethod",
    "reviewStatus": {
        "@id": "arskg:reviewStatus",
        "@type": "@id",
    },
    "reviewerNotes": "arskg:reviewerNotes",
    "reviewer": "prov:wasAttributedTo",
    "reviewedAt": {
        "@id": "prov:generatedAtTime",
        "@type": "xsd:dateTime",
    },
    "runId": "arskg:runId",
    "sourceCitation": "schema:citation",
    "canonicalLabel": "skos:prefLabel",
    "aliases": "skos:altLabel",
    "supportedBy": {
        "@id": "arskg:supportedBy",
        "@type": "@id",
    },
    "supports": {
        "@id": "arskg:supports",
        "@type": "@id",
    },
    "contradictedBy": {
        "@id": "arskg:contradictedBy",
        "@type": "@id",
    },
    "aboutConcept": {
        "@id": "arskg:relatesToConcept",
        "@type": "@id",
    },
    "relatedEvidence": {
        "@id": "arskg:relatedEvidence",
        "@type": "@id",
    },
    "wasDerivedFrom": {
        "@id": "prov:wasDerivedFrom",
        "@type": "@id",
    },
    "isPartOf": {
        "@id": "dcterms:isPartOf",
        "@type": "@id",
    },
    "citationIds": "arskg:citationIds",
    "sourceSpanStart": {
        "@id": "arskg:sourceSpanStart",
        "@type": "xsd:integer",
    },
    "sourceSpanEnd": {
        "@id": "arskg:sourceSpanEnd",
        "@type": "xsd:integer",
    },
    "claimPolarity": "arskg:claimPolarity",
    "claimModality": "arskg:claimModality",
    "canonicalId": "arskg:canonicalId",
    "ontologyMappings": "arskg:ontologyMappings",
    "contractVersion": "arskg:contractVersion",
}

STATUS_IRIS = {
    "pending": "arskg:pending",
    "in_review": "arskg:in_review",
    "accepted": "arskg:accepted",
    "rejected": "arskg:rejected",
    "needs_revision": "arskg:needs_revision",
}


def normalize_base_iri(base_iri: str) -> str:
    return base_iri if base_iri.endswith(("/", "#")) else f"{base_iri}/"


def compact_identifier(value: str) -> str:
    parts = [quote(part, safe="") for part in str(value).split(":") if part]
    return "/".join(parts) or "unknown"


def object_iri(obj: Dict, base_iri: str) -> str:
    explicit = str(obj.get("iri", "")).strip()
    if explicit:
        return explicit
    return normalize_base_iri(base_iri) + compact_identifier(str(obj.get("id", "unknown")))


def linked_ids(ids: Iterable[str], iri_by_id: Dict[str, str], base_iri: str) -> List[Dict[str, str]]:
    links = []
    for item_id in ids or []:
        item_id = str(item_id).strip()
        if item_id:
            links.append({"@id": iri_by_id.get(item_id, normalize_base_iri(base_iri) + compact_identifier(item_id))})
    return links


def relation_links(
    obj: Dict, relation_type: str, iri_by_id: Dict[str, str], base_iri: str, include_all: bool = False
) -> List[Dict[str, str]]:
    edges = obj.get("relation_edges")
    if not isinstance(edges, list):
        return []
    ids: List[str] = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        edge_type = str(edge.get("relation_type", "")).strip()
        if include_all or edge_type == relation_type:
            target_id = str(edge.get("target_id", "")).strip()
            if target_id:
                ids.append(target_id)
    return linked_ids(ids, iri_by_id, base_iri)


def article_key(source_document: str, article_id: Optional[str]) -> str:
    value = article_id or Path(source_document or "unknown").stem or "unknown"
    return re.sub(r"[^A-Za-z0-9_.~-]+", "-", value.strip()).strip("-") or "unknown"


def article_iri(source_document: str, article_id: Optional[str], base_iri: str) -> str:
    return normalize_base_iri(base_iri) + "article/" + quote(article_key(source_document, article_id), safe="")


def article_node(source_document: str, article_id: Optional[str], base_iri: str, title: Optional[str] = None) -> Dict:
    node = {
        "@id": article_iri(source_document, article_id, base_iri),
        "@type": "schema:ScholarlyArticle",
        "sourceDocument": source_document,
    }
    if article_id:
        node["dcterms:identifier"] = article_id
    if title:
        node["schema:name"] = title
        node["dcterms:title"] = title
    return node


def to_jsonld_node(obj: Dict, iri_by_id: Dict[str, str], base_iri: str) -> Dict:
    span = obj.get("supporting_quote_or_span")
    review_status = obj.get("review_status")
    node = {
        "@id": object_iri(obj, base_iri),
        "@type": TYPE_MAP.get(obj.get("type"), f"arskg:{obj.get('type', 'Thing')}"),
        "sourceDocument": obj.get("source_document"),
        "sourceSection": obj.get("source_section"),
        "sourceSpan": span,
        "text": span,
        "confidence": obj.get("confidence"),
        "extractionMethod": obj.get("extraction_method"),
        "reviewStatus": STATUS_IRIS.get(str(review_status), review_status),
        "reviewerNotes": obj.get("reviewer_notes", ""),
        "citationIds": obj.get("citation_ids"),
        "sourceSpanStart": obj.get("source_span_start"),
        "sourceSpanEnd": obj.get("source_span_end"),
        "claimPolarity": obj.get("claim_polarity"),
        "claimModality": obj.get("claim_modality"),
        "canonicalId": obj.get("canonical_id"),
        "ontologyMappings": obj.get("ontology_mappings"),
        "contractVersion": obj.get("contract_version"),
    }

    if obj.get("type") == "Evidence":
        node["quote"] = span

    if obj.get("id"):
        node["dcterms:identifier"] = obj["id"]
    if obj.get("source_citation"):
        node["sourceCitation"] = obj["source_citation"]
    if obj.get("reviewer"):
        node["reviewer"] = obj["reviewer"]
    if obj.get("reviewed_at"):
        node["reviewedAt"] = obj["reviewed_at"]
    if obj.get("run_id"):
        node["runId"] = obj["run_id"]

    if obj.get("type") == "Concept":
        label = obj.get("canonical_label") or obj.get("supporting_quote_or_span")
        if label:
            node["canonicalLabel"] = label
        if obj.get("aliases"):
            node["aliases"] = obj["aliases"]

    evidence_links = linked_ids(obj.get("related_evidence_ids", []), iri_by_id, base_iri)
    evidence_links.extend(relation_links(obj, "supports", iri_by_id, base_iri))
    dedup_evidence = {}
    for link in evidence_links:
        dedup_evidence[link["@id"]] = link
    evidence_links = list(dedup_evidence.values())
    if evidence_links:
        node["supportedBy"] = evidence_links

    concept_links = linked_ids(obj.get("related_concept_ids", []), iri_by_id, base_iri)
    concept_links.extend(relation_links(obj, "relates_to_concept", iri_by_id, base_iri))
    dedup_concepts = {}
    for link in concept_links:
        dedup_concepts[link["@id"]] = link
    concept_links = list(dedup_concepts.values())
    if concept_links:
        node["aboutConcept"] = concept_links

    contradiction_links = relation_links(obj, "contradicts", iri_by_id, base_iri)
    if contradiction_links:
        node["contradictedBy"] = contradiction_links

    supports_links = relation_links(obj, "supports", iri_by_id, base_iri)
    if supports_links and obj.get("type") == "Evidence":
        node["supports"] = supports_links

    related_evidence_links = relation_links(obj, "derived_from", iri_by_id, base_iri, include_all=False)
    if related_evidence_links:
        node["relatedEvidence"] = related_evidence_links

    source_document = obj.get("source_document")
    if source_document:
        art_id = article_iri(str(source_document), obj.get("article_id"), base_iri)
        node["wasDerivedFrom"] = {"@id": art_id}
        node["isPartOf"] = {"@id": art_id}

    return {k: v for k, v in node.items() if v is not None}


def build_graph_release_node(
    objects: List[Dict], base_iri: str, metadata: Optional[Dict] = None
) -> Dict:
    statuses = sorted({str(obj.get("review_status")) for obj in objects if obj.get("review_status")})
    run_ids = sorted({str(obj.get("run_id")) for obj in objects if obj.get("run_id")})
    payload = {
        "@id": normalize_base_iri(base_iri) + "release/" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "@type": "schema:Dataset",
        "dcterms:title": "ARS KG Release",
        "dcterms:issued": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "arskg:objectCount": len(objects),
        "arskg:runIds": run_ids,
        "arskg:statuses": statuses,
    }
    if metadata:
        payload["arskg:releaseMetadata"] = metadata
    return payload


def build_jsonld_doc(
    objects: List[Dict],
    base_iri: str = DEFAULT_BASE_IRI,
    title_by_article: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict] = None,
) -> Dict:
    base_iri = normalize_base_iri(base_iri)
    iri_by_id = {str(obj.get("id")): object_iri(obj, base_iri) for obj in objects if obj.get("id")}
    graph: List[Dict] = []
    seen_articles = set()

    for obj in objects:
        source_document = obj.get("source_document")
        if source_document:
            art_id = article_iri(str(source_document), obj.get("article_id"), base_iri)
            if art_id not in seen_articles:
                title = (title_by_article or {}).get(str(source_document))
                graph.append(article_node(str(source_document), obj.get("article_id"), base_iri, title))
                seen_articles.add(art_id)
        graph.append(to_jsonld_node(obj, iri_by_id, base_iri))

    graph.append(build_graph_release_node(objects, base_iri, metadata))

    return {
        "@context": CONTEXT,
        "@graph": graph,
    }
