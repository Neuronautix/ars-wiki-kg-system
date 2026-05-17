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
2. Run the orchestrator (`kg_layer/pipeline/run_pipeline.py`) to execute extract → validate → review → export → wiki.

## Suggested run command

```powershell
python kg_layer/pipeline/run_pipeline.py
```

## Orchestrator options

- `--input-dir`: where ARS markdown artifacts live (can be outside `kg_layer/data/raw`).
- `--include-glob` / `--exclude-glob`: extraction file filters.
- `--publish-mode accepted|draft|all`: publishing status policy.
- `--publish-status <status>` (repeatable): explicit status list, overrides `--publish-mode`.
- `--skip-review-apply`: skip review merge and publish validated objects directly.
- `--auto-accept-validated`: mark all validated objects as accepted before export/wiki.

## Notes

- This layer is intentionally independent of ARS core prompts and orchestrators.
- It can evolve into a separate repository later with minimal changes.
