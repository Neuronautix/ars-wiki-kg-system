# KG Layer (Pilot v1)

This folder adds a minimal, additive structured knowledge layer on top of ARS outputs.

## Scope

Pilot classes:
- Paper
- Concept
- Claim
- Evidence

Common fields on extracted objects:
- id
- source_document
- source_section
- supporting_quote_or_span
- confidence
- extraction_method
- review_status
- reviewer_notes

## Workflow

1. Put ARS markdown artifacts in `kg_layer/data/raw/`.
2. Run extraction to produce candidate objects in `kg_layer/data/normalized/`.
3. Validate candidate objects.
4. Apply human review decisions.
5. Export accepted objects as JSON-LD.
6. Render wiki pages from accepted objects.

## Suggested run order

```powershell
python kg_layer/extraction/extract_candidates.py --input-dir kg_layer/data/raw --output kg_layer/data/normalized/candidates.json
python kg_layer/validation/validate_candidates.py --input kg_layer/data/normalized/candidates.json --output kg_layer/data/normalized/candidates.validated.json
python kg_layer/review/apply_review.py --objects kg_layer/data/normalized/candidates.validated.json --reviews kg_layer/review/reviews.json --output kg_layer/data/reviewed/reviewed.json
python kg_layer/exports/export_jsonld.py --input kg_layer/data/reviewed/reviewed.json --output kg_layer/data/published/graph.jsonld
python kg_layer/wiki/render_wiki_pages.py --input kg_layer/data/reviewed/reviewed.json --output-dir kg_layer/data/published/wiki
```

## Notes

- This layer is intentionally independent of ARS core prompts and orchestrators.
- It can evolve into a separate repository later with minimal changes.
