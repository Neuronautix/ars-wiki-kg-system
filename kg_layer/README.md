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

Provenance fields (populated after review, or carried from ARS HITL input):
- reviewer
- reviewed_at

Article-level metadata (optional, propagated from ARS HITL handoff):
- article_id
- run_id

## Preferred workflow: ARS HITL → KG

The ideal flow produces both an ARS article and its corresponding KG from the same
reviewed material.

### 1. ARS run

ARS synthesizes an article and, during the HITL loop, generates structured KG candidates
(claims, concepts, evidence) that reviewers accept or refine.

### 2. Export ARS HITL outputs

Export the reviewed suggestions as one `*.kg_candidates.json` handoff file per article:

```bash
python3 kg_layer/ars_export/export_kg_candidates.py \
  --article /path/to/ars/article.md \
  --claim-verification-report /path/to/ars/claim_verification_report.md \
  --output-dir /path/to/ars/hitl/outputs \
  --article-id my-article-2026 \
  --run-id ars-run-2026-05-17-001 \
  --reviewer alice
```

When `--claim-verification-report` is provided, verdicts from the ARS Claim
Verification Report are mapped into KG review statuses:

| ARS verdict | KG review_status |
|---|---|
| `VERIFIED` | `accepted` |
| `MINOR_DISTORTION` | `needs_revision` |
| `MAJOR_DISTORTION` | `needs_revision` |
| `UNVERIFIABLE` | `rejected` |
| `UNVERIFIABLE_ACCESS` | `in_review` |

If the report is unavailable, omit `--claim-verification-report`; the exporter
uses article markdown extraction and assigns `--fallback-status` to extracted
items (default: `accepted`).

Validate handoff files before publishing:

```bash
python3 kg_layer/pipeline/run_pipeline.py \
  --structured-input-dir /path/to/ars/hitl/outputs \
  --validate-only
```

Run ontology-quality semantic validation when the handoff includes claim/evidence
links and source citations:

```bash
python3 kg_layer/pipeline/run_pipeline.py \
  --structured-input-dir /path/to/ars/hitl/outputs \
  --semantic-validate-only
```

See `kg_layer/schemas/ars_handoff_schema.json` for the schema and
`kg_layer/data/examples/example_article.kg_candidates.json` for a worked example.

### 3. Run the KG pipeline

```bash
python kg_layer/pipeline/run_pipeline.py \
  --structured-input-dir /path/to/ars/hitl/outputs
```

This ingests the structured handoff files, validates them, preserves the HITL review
metadata (reviewer, reviewed_at, review_status), and publishes:

- **Per-article outputs** in `kg_layer/data/published/per_article/`:
  - `{article-slug}.kg.json` — flat KG objects for that article
  - `{article-slug}.graph.jsonld` — JSON-LD graph for that article
- **Global outputs** in `kg_layer/data/published/`:
  - `graph.jsonld` — combined JSON-LD across all articles
  - `wiki/` — human-readable wiki pages

`article-slug` is a filesystem-safe normalization of `article_id` (or the source
document stem when `article_id` is absent). If two articles normalize to the same
slug, a short hash suffix is appended to keep filenames distinct.

### 4. Reuse the graph

Per-article KG files can be fed into future ARS runs as structured memory for
retrieval, gap analysis, and hypothesis generation.

## Fallback: markdown-only workflow

Place ARS markdown artifacts in `kg_layer/data/raw/` and run:

```bash
python kg_layer/pipeline/run_pipeline.py
```

or point to any markdown directory:

```bash
python kg_layer/pipeline/run_pipeline.py --input-dir /path/to/markdown
```

When `--structured-input-dir` points to a valid directory but no
`*.kg_candidates.json` files are found, the pipeline automatically falls back to
markdown extraction. Missing or non-directory paths fail fast.

## Merging both sources

To combine ARS HITL structured artifacts with markdown extraction:

```bash
python kg_layer/pipeline/run_pipeline.py \
  --structured-input-dir /path/to/hitl/outputs \
  --merge-structured-and-markdown \
  --input-dir /path/to/markdown
```

Structured items are preferred on id collision.

## ARS HITL handoff format

Each `*.kg_candidates.json` file covers one article:

```json
{
  "article_id": "my-article-2026",
  "title": "My Research Article",
  "run_id": "ars-run-2026-05-17-001",
  "source_document": "my_article.md",
  "items": [
    {
      "id": "claim:my-article-2026:1",
      "type": "Claim",
      "source_document": "my_article.md",
      "source_section": "Discussion",
      "supporting_quote_or_span": "X improves Y by 34% (Smith, 2025).",
      "confidence": 0.92,
      "extraction_method": "ars_hitl",
      "review_status": "accepted",
      "reviewer": "alice",
      "reviewed_at": "2026-05-17T10:00:00Z",
      "reviewer_notes": "Confirmed."
    }
  ]
}
```

Full schema: `kg_layer/schemas/ars_handoff_schema.json`
Example file: `kg_layer/data/examples/example_article.kg_candidates.json`

## Orchestrator options

- `--input-dir`: markdown input directory (default: `kg_layer/data/raw`).
- `--structured-input-dir`: directory with `*.kg_candidates.json` ARS HITL handoff files.
- `--validate-only`: validate structured ARS handoff files and exit without publishing (requires `--structured-input-dir`).
- `--semantic-validate-only`: run ontology-quality semantic validation and exit.
- `--base-iri`: base IRI for JSON-LD exports (default: `https://example.org/ars/kg/`).
- `--merge-structured-and-markdown`: merge both sources instead of preferring structured (requires `--structured-input-dir`).
- `--include-glob` / `--exclude-glob`: markdown extraction file filters.
- `--publish-mode accepted|draft|all`: publishing status policy.
- `--publish-status <status>` (repeatable): explicit status list, overrides `--publish-mode`.
- `--skip-review-apply`: skip review merge and publish validated objects directly.
- `--auto-accept-validated`: mark all validated objects as accepted before export/wiki.
- `--carry-forward-accepted` / `--no-carry-forward-accepted`: keep accepted reviews on unchanged spans.
- `--watch --poll-seconds 5`: continuous sidecar mode; watches markdown, structured input, and reviews.

## Per-article outputs

After each pipeline run, `kg_layer/data/published/per_article/` contains:

- `{article_id}.kg.json` — flat JSON list of KG objects for that article
- `{article_id}.graph.jsonld` — JSON-LD graph for that article

These files preserve all provenance fields from the ARS HITL loop:
`reviewer`, `reviewed_at`, `review_status`, `extraction_method`, `article_id`, `run_id`.

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
- Structured ARS HITL items that enter as `accepted` flow through the pipeline unchanged —
  their reviewer identity, timestamp, and notes are preserved in every output artifact.
