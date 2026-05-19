# ARS KG Ontology Profile

This profile defines a compact RDF vocabulary and SHACL validation contract for ARS-derived knowledge graph objects. It is intentionally additive to the current JSON handoff schema: the pipeline can continue to emit JSON, while RDF exporters can map the same fields into stable semantic web terms.

## Files

- `ars_kg_ontology.ttl`: ontology terms, classes, properties, and review status controlled terms.
- `shapes/ars_kg_shapes.ttl`: SHACL node and property shapes for validation.

## Namespace And IRI Policy

Use the compact custom namespace only for ARS KG terms:

```turtle
@prefix arskg: <https://example.org/ars/kg#> .
```

Recommended instance IRI patterns:

- Article: `https://example.org/ars/kg/article/{article_id}`
- Paper: `https://example.org/ars/kg/paper/{article_id}/{local_id}`
- Claim: `https://example.org/ars/kg/claim/{article_id}/{local_id}`
- Evidence: `https://example.org/ars/kg/evidence/{article_id}/{local_id}`
- Concept: `https://example.org/ars/kg/concept/{normalized_label_or_id}`
- Source document: `https://example.org/ars/kg/source/{source_document_slug}`

The current JSON identifiers such as `claim:adaptive-memory-consolidation-2026:1` are acceptable as local IDs, but RDF publication should mint resolvable IRIs where possible. If a document cannot be represented as a resolvable IRI, preserve the literal path or artifact name with `arskg:sourceDocumentRef`.

## Design Choices

The ontology reuses established vocabularies for common meaning and keeps ARS-specific terms small:

- `schema.org`: articles, scholarly articles, claims, creative works, text, quotations, and topical relationships.
- `dcterms`: titles, source links, relation links, and part-of/article membership.
- `PROV-O`: derivation and source provenance using `prov:Entity` and `prov:wasDerivedFrom`.
- `SKOS`: concepts and controlled review status terms.
- `CiTO`: claim/evidence support and dispute relations.
- `Web Annotation`: selectors for spans when richer text anchoring is available.

ARS-specific terms are used where the existing KG needs precise operational semantics: confidence, review status, extraction method, reviewer metadata, source sections/spans, and article/run traceability.

## Core Classes

- `arskg:Article`: ARS article or generated narrative artifact.
- `arskg:Paper`: scholarly paper or paper-like source, also an `arskg:Article`.
- `arskg:Claim`: reviewable assertion extracted from source material.
- `arskg:Evidence`: quoted passage, citation, observation, or artifact supporting or challenging a claim.
- `arskg:Concept`: topic, mechanism, method, entity, or phrase modeled as a SKOS concept.
- `arskg:ReviewStatus`: SKOS controlled term for review state.

## Important Properties

- `arskg:text`: canonical text of a claim or extracted object.
- `arskg:quote`: exact quote preserved for evidence.
- `arskg:sourceSpan`: exact text span, quote span, selector text, or compact span locator.
- `arskg:sourceSection`: source section heading or label.
- `arskg:sourceDocument`: object link to the source document entity.
- `arskg:sourceDocumentRef`: literal source path or artifact identifier.
- `prov:wasDerivedFrom`: provenance link to the source entity that produced the KG object.
- `arskg:confidence`: normalized decimal confidence in `[0, 1]`.
- `arskg:reviewStatus`: one of `arskg:pending`, `arskg:in_review`, `arskg:accepted`, `arskg:rejected`, `arskg:needs_revision`.
- `arskg:supportedBy`: Claim to supporting Evidence.
- `arskg:supports`: Evidence to supported Claim.
- `arskg:contradictedBy`: Claim to contradicting Evidence.
- `arskg:relatesToConcept`: relation from an object to an ARS concept.
- `arskg:relatedEvidence`: relation from an object or concept to related evidence.
- `arskg:article`, `arskg:articleId`, `arskg:runId`: article and ARS run traceability.

## JSON To RDF Mapping

| KG JSON field | RDF term | Notes |
|---|---|---|
| `id` | subject IRI | Mint an IRI from the ID; keep the raw ID in local ETL metadata if needed. |
| `type = Paper` | `rdf:type arskg:Paper` | Also compatible with `schema:ScholarlyArticle`. |
| `type = Concept` | `rdf:type arskg:Concept` | Use `skos:prefLabel` for the concept label. |
| `type = Claim` | `rdf:type arskg:Claim` | Use `arskg:text` and `arskg:sourceSpan`. |
| `type = Evidence` | `rdf:type arskg:Evidence` | Use `arskg:quote` and `arskg:sourceSpan`. |
| `source_document` | `arskg:sourceDocument` and/or `arskg:sourceDocumentRef` | Prefer an IRI object for RDF graphs; keep literal path in `sourceDocumentRef`. |
| `source_section` | `arskg:sourceSection` | Literal section heading or label. |
| `supporting_quote_or_span` | `arskg:quote`, `arskg:sourceSpan`, `arskg:text` | Evidence uses quote/span; Claim uses text/span. |
| `confidence` | `arskg:confidence` | Decimal in `[0, 1]`. |
| `extraction_method` | `arskg:extractionMethod` | Literal method name. |
| `review_status` | `arskg:reviewStatus` | Map string values to review status IRIs. |
| `reviewer` | `arskg:reviewer` | Literal reviewer identity. |
| `reviewed_at` | `arskg:reviewedAt` | `xsd:dateTime`. |
| `reviewer_notes` | `arskg:reviewerNotes` | Literal note. |
| `article_id` | `arskg:articleId`; optionally `arskg:article` | Use `arskg:article` when an Article node is minted. |
| `run_id` | `arskg:runId` | Literal ARS run identifier. |

Example review status mapping:

| JSON value | RDF IRI |
|---|---|
| `pending` | `arskg:pending` |
| `in_review` | `arskg:in_review` |
| `accepted` | `arskg:accepted` |
| `rejected` | `arskg:rejected` |
| `needs_revision` | `arskg:needs_revision` |

## Validation Expectations

The SHACL profile defines these expectations:

- Article/Paper nodes should have `dcterms:title` and `arskg:sourceDocumentRef`. Extracted `Paper` item nodes also carry review status and confidence.
- Claim nodes must have `arskg:text`, `arskg:sourceSpan`, `prov:wasDerivedFrom`, `arskg:sourceDocumentRef`, `arskg:reviewStatus`, and `arskg:confidence`.
- Accepted Claim nodes must have at least one `arskg:supportedBy` Evidence.
- Evidence nodes must have `arskg:quote`, `arskg:sourceSpan`, `arskg:sourceDocumentRef`, `arskg:reviewStatus`, and `arskg:confidence`.
- Concept nodes must have `skos:prefLabel`, `arskg:reviewStatus`, and `arskg:confidence`.
- All `arskg:confidence` values must be `xsd:decimal` values from `0` through `1`.
- All `arskg:reviewStatus` values must be one of the controlled review status IRIs.

This validation profile is stricter than the base JSON schema in two places: accepted claims require explicit evidence links, and RDF review status values are IRIs rather than plain strings. RDF exporters should add those links and mappings during graph construction.
