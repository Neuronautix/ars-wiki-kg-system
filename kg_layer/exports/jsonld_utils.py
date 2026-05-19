import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote, urlparse

DEFAULT_BASE_IRI = "https://example.org/ars/kg/"

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
    "aboutConcept": {
        "@id": "arskg:relatesToConcept",
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
    if evidence_links:
        node["supportedBy"] = evidence_links

    concept_links = linked_ids(obj.get("related_concept_ids", []), iri_by_id, base_iri)
    if concept_links:
        node["aboutConcept"] = concept_links

    source_document = obj.get("source_document")
    if source_document:
        art_id = article_iri(str(source_document), obj.get("article_id"), base_iri)
        node["wasDerivedFrom"] = {"@id": art_id}
        node["isPartOf"] = {"@id": art_id}

    return {k: v for k, v in node.items() if v is not None}


def build_jsonld_doc(objects: List[Dict], base_iri: str = DEFAULT_BASE_IRI, title_by_article: Optional[Dict[str, str]] = None) -> Dict:
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

    return {
        "@context": CONTEXT,
        "@graph": graph,
    }
