# ARS Wiki Knowledge Graph System

> Each ARS research run produces two synchronized outputs: a polished article for humans and a reusable knowledge graph for machines — no coding experience required to get started.

---

## What is this?

This system works **alongside the ARS CLI** to automatically turn reviewed research outputs into a structured knowledge graph and browsable wiki.

When ARS finishes a research run you get **two paired deliverables**:

| Output | What it is |
|---|---|
| **ARS article** (`article.md`) | The human-readable research synthesis |
| **Knowledge graph** (`article.kg.json`, `article.graph.jsonld`) | Machine-readable structured knowledge |
| **Wiki pages** (`wiki/`) | Browsable summaries of key concepts and claims |

The knowledge graph captures the concepts, claims, and evidence from the same reviewed reasoning that produced the article, so it can later be used as structured memory for future research runs.

### What the KG layer extracts

| What it finds | Example |
|---|---|
| **Papers** | A source document you feed in |
| **Concepts** | "Machine Learning", "Neural Network" |
| **Claims** | Any sentence backed by a citation |
| **Evidence** | The supporting quote for each claim |

---

## Before You Begin

You need **two free tools** installed on your computer:

1. **Python 3.8 or later** — [Download here](https://www.python.org/downloads/)  
   *(During installation on Windows, tick "Add Python to PATH")*
2. **Git** — [Download here](https://git-scm.com/downloads)

That's it. No databases, no cloud accounts, no paid software.

---

## Recommended: ARS + KG together

The preferred workflow uses structured ARS HITL outputs for the best graph quality.

### Step 1 — Get the code

```bash
git clone --recurse-submodules https://github.com/Neuronautix/ars-wiki-kg-system.git
cd ars-wiki-kg-system
```

### Step 2 — Produce ARS HITL handoff files

After a research run, export structured KG candidates from the ARS HITL loop into a
directory as `*.kg_candidates.json` files.

See [`kg_layer/data/examples/example_article.kg_candidates.json`](kg_layer/data/examples/example_article.kg_candidates.json)
for the exact file format, and [`kg_layer/schemas/ars_handoff_schema.json`](kg_layer/schemas/ars_handoff_schema.json)
for the full JSON Schema.

Each handoff file covers one article and looks like this (abbreviated):

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
      "supporting_quote_or_span": "X improves Y by 34% under Z conditions (Smith, 2025).",
      "confidence": 0.92,
      "extraction_method": "ars_hitl",
      "review_status": "accepted",
      "reviewer": "alice",
      "reviewed_at": "2026-05-17T10:00:00Z",
      "reviewer_notes": "Confirmed against source."
    }
  ]
}
```

### Step 3 — Run the pipeline with structured input

```bash
python kg_layer/pipeline/run_pipeline.py \
  --structured-input-dir /path/to/ars/hitl/outputs
```

The pipeline:
- Reads all `*.kg_candidates.json` files from the structured input directory
- Validates and reviews each item
- Publishes per-article and global KG outputs

### Step 4 — Find your results

| Output | Location |
|---|---|
| **Per-article KG JSON** | `kg_layer/data/published/per_article/{article-slug}.kg.json` |
| **Per-article JSON-LD** | `kg_layer/data/published/per_article/{article-slug}.graph.jsonld` |
| **Global knowledge graph** | `kg_layer/data/published/graph.jsonld` |
| **Wiki pages** | `kg_layer/data/published/wiki/` |
| Review queue | `kg_layer/data/review_queue/review_queue.json` |
| Reviewed objects | `kg_layer/data/reviewed/reviewed.json` |

Open any `.md` file in the wiki folder with a text editor or Markdown viewer to read it.

`article-slug` is a filesystem-safe normalization of `article_id` (or the source
document stem when `article_id` is absent). If two articles normalize to the same
slug, a short hash suffix is appended to keep filenames distinct.

---

## Live sidecar: ARS markdown + automatic KG refresh

If ARS continuously writes or updates markdown files to a folder, run the KG layer
in **watch mode** alongside it:

```bash
python kg_layer/pipeline/run_pipeline.py \
  --input-dir /absolute/path/to/ars/articles \
  --watch \
  --poll-seconds 5
```

The KG layer automatically re-runs whenever ARS adds or updates markdown files.
You can also combine watch mode with `--structured-input-dir` to pick up both
structured handoff files and markdown articles as they appear.

---

## Manual mode (markdown only)

If you are not using ARS or just want to try the system with your own files:

1. Copy your `.md` documents into `kg_layer/data/raw/`.
2. Run:

```bash
python kg_layer/pipeline/run_pipeline.py
```

This is the markdown-only fallback and produces the same outputs.

---

## How to Review Extracted Items

After running the pipeline, items start with `"review_status": "pending"` (markdown extraction)
or carry their ARS HITL status (structured input). To approve or reject pending items:

1. Open `kg_layer/review/reviews.json` in any text editor.
2. Add an entry for each object you want to update:

```json
[
  {
    "object_id": "claim:mypaper:1",
    "review_status": "accepted",
    "reviewer": "Your Name",
    "reviewed_at": "2026-05-17T12:00:00Z",
    "reviewer_notes": "Confirmed against source."
  }
]
```

Valid `review_status` values: `pending` · `in_review` · `accepted` · `rejected` · `needs_revision`

3. Re-run the pipeline to publish the updated graph and wiki.

For prioritized triage:

```bash
python kg_layer/review/hitl_review.py next \
  --queue kg_layer/data/review_queue/review_queue.json \
  --top 5
```

To record a decision quickly:

```bash
python kg_layer/review/hitl_review.py decide \
  --reviews kg_layer/review/reviews.json \
  --object-id claim:mypaper:1 \
  --status accepted \
  --reviewer "Your Name" \
  --notes "Confirmed against source."
```

---

## All pipeline options

```bash
python kg_layer/pipeline/run_pipeline.py [options]
```

| Option | Description |
|---|---|
| `--input-dir DIR` | Markdown input directory (default: `kg_layer/data/raw`). |
| `--structured-input-dir DIR` | Directory of `*.kg_candidates.json` ARS HITL handoff files. Preferred over markdown when files are found; a valid but empty directory falls back to markdown, while missing/non-directory paths fail fast. |
| `--merge-structured-and-markdown` | Combine structured and markdown candidates instead of preferring one source. Requires `--structured-input-dir`. |
| `--data-root DIR` | Base output directory (default: `kg_layer/data`). |
| `--reviews FILE` | Review decisions JSON (default: `kg_layer/review/reviews.json`). |
| `--include-glob GLOB` | Include filter for markdown files. Repeatable. |
| `--exclude-glob GLOB` | Exclude filter for markdown files. Repeatable. |
| `--publish-mode accepted\|draft\|all` | Status policy for export/wiki. |
| `--publish-status STATUS` | Explicit status to publish. Repeatable. Overrides `--publish-mode`. |
| `--skip-review-apply` | Publish validated objects directly (auto-accepts under default mode). |
| `--auto-accept-validated` | Mark all validated objects as accepted before publishing. |
| `--carry-forward-accepted` | Preserve accepted status for unchanged source spans (default: on). |
| `--watch` | Run as a live sidecar and re-run on file changes. |
| `--poll-seconds N` | Polling interval for `--watch` mode (default: 5). |

---

## Repository Layout

```
ars-wiki-kg-system/
├── kg_layer/                  Main pipeline (everything you interact with)
│   ├── data/
│   │   ├── raw/               ← Markdown documents (manual / fallback mode)
│   │   ├── examples/          ← Example ARS HITL handoff file
│   │   ├── normalized/        Extracted & validated candidates
│   │   ├── reviewed/          Objects after human review
│   │   └── published/
│   │       ├── graph.jsonld   Global knowledge graph
│   │       ├── per_article/   ← Per-article KG JSON + JSON-LD (new)
│   │       └── wiki/          Browsable wiki pages
│   ├── extraction/            Markdown extractor + structured ingest
│   ├── validation/            Candidate validation script
│   ├── review/                Review schema, queue, and decisions
│   ├── exports/               Global + per-article JSON-LD exporters
│   ├── wiki/                  Wiki page renderer
│   └── schemas/               Data model (LinkML + ARS handoff JSON Schema)
└── vendor/
    └── academic-research-skills/   Upstream ARS reference (pinned submodule)
```

---

## How the Pipeline Works

```
ARS HITL outputs                    Markdown articles
(*.kg_candidates.json)              (*.md / *.markdown)
        │                                   │
        ▼                                   ▼
  [ingest_structured]           [extract_candidates]
        │                                   │
        └──────────── merge ────────────────┘
                          │
                          ▼
                    [validate]  ──► candidates.validated.json
                          │
                          ▼
                    [review]    ──► reviewed.json (provenance + status preserved)
                          │
                ┌─────────┼─────────────────┐
                ▼         ▼                  ▼
           [export]   [per_article]       [wiki]
               │       export              │
               ▼           │              ▼
          graph.jsonld   {article}.    wiki/*.md
                         kg.json
                         {article}.
                         graph.jsonld
```

ARS HITL items that enter as `accepted` flow through unchanged — their reviewer identity,
timestamp, and notes are preserved in every output artifact.

---

## Using the Graph for Future Insight Generation

The per-article KG files are designed to serve as **structured memory** for future ARS runs.
Because the graph captures accepted concepts, claims, and evidence with full provenance,
a future ARS run can use it to:

- **Retrieve prior knowledge** — pull related concepts and accepted claims before generating a new article.
- **Detect gaps** — compare a new draft against the graph to find missing evidence or uncited concepts.
- **Generate hypotheses** — query the graph for under-connected concepts or unresolved tensions.

This turns each completed article into a **lasting research asset**, not just a document.

---

## Keeping the Upstream Reference Up to Date

The `vendor/academic-research-skills` folder is a pinned snapshot of the upstream ARS project. To update it:

```bash
git submodule update --init --recursive
git -C vendor/academic-research-skills fetch --tags
git -C vendor/academic-research-skills checkout v3.7.0
```

---

## Need Help?

- Read the detailed developer notes in [`kg_layer/README.md`](kg_layer/README.md).
- Open an [issue](../../issues) on GitHub if something isn't working.
