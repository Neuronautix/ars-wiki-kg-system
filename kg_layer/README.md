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
3. Inspect prioritized review queue at `kg_layer/data/review_queue/review_queue.json`.

## Suggested run command

```powershell
python kg_layer/pipeline/run_pipeline.py
```

## Orchestrator options

- `--input-dir`: where ARS markdown artifacts live (can be outside `kg_layer/data/raw`).
- `--include-glob` / `--exclude-glob`: extraction file filters.
- `--publish-mode accepted|draft|all`: publishing status policy.
- `--publish-status <status>` (repeatable): explicit status list, overrides `--publish-mode`.
- `--skip-review-apply`: skip review merge and publish validated objects directly (auto-accepted under default `--publish-mode accepted`).
- `--auto-accept-validated`: mark all validated objects as accepted before export/wiki.
- `--carry-forward-accepted` / `--no-carry-forward-accepted`: keep accepted reviews on unchanged spans.
- `--watch --poll-seconds 5`: continuous sidecar mode for ARS artifact updates.

## HITL helper commands

Show next best review candidates:

```powershell
python kg_layer/review/hitl_review.py next --queue kg_layer/data/review_queue/review_queue.json --top 5
```

Record a review decision quickly:

```powershell
python kg_layer/review/hitl_review.py decide --reviews kg_layer/review/reviews.json --object-id claim:paper1:1 --status accepted --reviewer reviewer_name --notes "Looks good"
```

## Notes

- This layer is intentionally independent of ARS core prompts and orchestrators.
- It can evolve into a separate repository later with minimal changes.
