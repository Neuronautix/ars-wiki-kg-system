# Production KG Contract (v1.1)

This contract defines release gates for a professional, machine-actionable KG used as:

- a constraint layer for embedding systems
- a navigation/grounding layer for LLM workflows

## Acceptance Criteria (Blocker Gates)

Release is **blocked** unless all of the following pass:

1. **Schema completeness**
   - Handoff files include `schema_version=1.1.0` and `contract_version=1.1`.
   - Required candidate fields remain valid for all object types.
2. **Provenance completeness**
   - Objects preserve source document/section/span evidence.
   - Accepted claims include citation data (`source_citation` or `citation_ids`).
3. **Semantic consistency**
   - No broken references across related IDs.
   - Accepted claims link evidence through `related_evidence_ids` or typed `relation_edges`.
   - Deterministic object ID policy is enforced: `<type>:<slug>:<index>`.
4. **Retrieval utility**
   - Constraint artifacts exist (`nodes`, `edges`, embedding payloads, indexes, manifest).
   - Accepted and draft graphs are both published for risk-aware retrieval.
5. **Reproducibility**
   - Release metadata and quality reports are generated on each run.
   - CI workflow validates contract + semantic + artifact integrity.

## Versioning and Compatibility Policy

- **Schema version**: `1.1.0`
- **Contract version**: `1.1`
- **Compatibility policy**:
  - `strict`: consumers require exact contract fields/semantics.
  - `backward_compatible`: consumers tolerate additive optional fields.

## Required Constraint Signals

The contract supports the following machine-facing signals:

- Claim semantics: `claim_polarity`, `claim_modality`
- Citation identifiers: `citation_ids` (DOI/URL)
- Span anchors: `source_span_start`, `source_span_end`
- Typed edges: `relation_edges[]` with `relation_type`, `target_id`, `confidence`
- Concept normalization: `canonical_id`, `canonical_label`, `aliases`, `ontology_mappings`

## Published Outputs

The pipeline now emits:

- `published/graph.jsonld` (selected statuses)
- `published/graph.accepted.jsonld` (strict accepted graph)
- `published/graph.draft.jsonld` (accepted + draft statuses)
- `published/constraints/{selected|accepted|draft}/...` artifacts
- `published/quality/run_quality_report.json`
- `published/quality/quality_trends.json`

## ARS Fork Additions (Required Upstream Work)

For highest-leverage improvements in the ARS vendor fork:

1. Native handoff emitter that writes `*.kg_candidates.json` with:
   - deterministic IDs
   - typed relation edges
   - citation identifiers
   - reviewer and run metadata
2. Structured Claim Verification export in machine-readable JSON (plus markdown view).
3. Prompt/protocol updates to produce:
   - explicit claim→evidence and claim→concept links
   - contradiction/support labels
   - normalized concept labels and aliases
   - confidence and rationale fields
4. ARS-side pre-export contract validator (fail-fast on invalid handoff).
5. ARS tests for this repository’s handoff + semantic validation gates.
6. Optional ARS command: “KG-ready export package” (article + handoff + verification + manifest).
