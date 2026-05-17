# Schema Files

## `knowledge_model.yaml` — Core KG object model (LinkML)

Defines the `Paper`, `Concept`, `Claim`, and `Evidence` classes with their required and
optional fields.

This file is a practical starting point for LinkML-based validation and generation.
It is intentionally small to keep the first pilot testable.

### Mapping guidance

- `source_document`: input markdown file path or artifact ID.
- `source_section`: markdown heading or section label from the source.
- `supporting_quote_or_span`: exact quote/snippet from the source text.
- `extraction_method`: strategy used — `ars_hitl` for ARS HITL inputs, or a heuristic
  name like `regex_citation_sentence` for markdown extraction.
- `review_status`: `pending`, `in_review`, `accepted`, `rejected`, `needs_revision`.
- `reviewer`: identity of the person who reviewed this item (optional, populated after review).
- `reviewed_at`: ISO 8601 timestamp of the review decision (optional).
- `article_id`: identifier for the parent article, propagated from the ARS HITL handoff file (optional).
- `run_id`: ARS run identifier for cross-run traceability (optional).

### Next step (after pilot)

If you want strict LinkML runtime validation, add the LinkML toolchain and generate
JSON Schema from this model for CI-time checking.

---

## `ars_handoff_schema.json` — ARS HITL → KG interchange format (JSON Schema)

Defines the per-article `*.kg_candidates.json` handoff file that transfers ARS HITL
outputs into the KG pipeline.

Each handoff file contains:
- Article-level metadata (`article_id`, `title`, `run_id`, `source_document`).
- An `items` array of `KGCandidate` objects, each mapping directly to a KG layer object.

`KGCandidate` fields match the `BaseExtractedObject` slots in `knowledge_model.yaml`,
with full provenance (`reviewer`, `reviewed_at`, `reviewer_notes`, `review_status`).

### Usage

Place handoff files as `*.kg_candidates.json` in a directory and pass that directory to
the pipeline:

```bash
python kg_layer/pipeline/run_pipeline.py \
  --structured-input-dir /path/to/handoff/files
```

See `kg_layer/data/examples/example_article.kg_candidates.json` for a worked example.

