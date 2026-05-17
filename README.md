# ARS Wiki Knowledge Graph System

> Turn academic research documents into a structured, browsable knowledge graph — no coding experience required to get started.

---

## What is this?

The **ARS Wiki KG System** reads your markdown research documents and automatically pulls out key information:

| What it finds | Example |
|---|---|
| **Papers** | A source document you feed in |
| **Concepts** | "Machine Learning", "Neural Network" |
| **Claims** | Any sentence backed by a citation |
| **Evidence** | The supporting quote for each claim |

It stores everything in a structured format so you (or your team) can review, approve, and publish a searchable knowledge graph and wiki.

---

## Before You Begin

You need **two free tools** installed on your computer:

1. **Python 3.8 or later** — [Download here](https://www.python.org/downloads/)  
   *(During installation on Windows, tick "Add Python to PATH")*
2. **Git** — [Download here](https://git-scm.com/downloads)

That's it. No databases, no cloud accounts, no paid software.

---

## Quick Start (Step by Step)

### Step 1 — Get the code

Open a terminal (Mac/Linux) or Command Prompt / PowerShell (Windows) and run:

```bash
git clone --recurse-submodules https://github.com/Neuronautix/ars-wiki-kg-system.git
cd ars-wiki-kg-system
```

### Step 2 — Add your documents

Copy your research documents (`.md` or `.markdown` files) into:

```
kg_layer/data/raw/
```

> **No markdown files yet?** Any plain-text document saved with a `.md` extension works. Even a Word document copy-pasted into a text file and saved as `mypaper.md` is fine to test with.

### Step 3 — Run the pipeline

Use the one-command orchestrator:

```bash
python kg_layer/pipeline/run_pipeline.py
```

By default, this runs extract → validate → apply review → export → wiki using:
- input: `kg_layer/data/raw`
- reviews: `kg_layer/review/reviews.json`
- publish policy: `accepted` only

### Step 4 — Find your results

| Output | Location |
|---|---|
| Extracted objects (JSON) | `kg_layer/data/normalized/` |
| Validated objects (JSON) | `kg_layer/data/normalized/candidates.validated.json` |
| Reviewed objects (JSON) | `kg_layer/data/reviewed/reviewed.json` |
| Review queue (JSON) | `kg_layer/data/review_queue/review_queue.json` |
| Knowledge graph (JSON-LD) | `kg_layer/data/published/graph.jsonld` |
| Wiki pages (Markdown) | `kg_layer/data/published/wiki/` |

Open any `.md` file in the wiki folder with a text editor or a Markdown viewer to read it.

---

## How to Review Extracted Items

After Step 3 above, extracted objects start with `"review_status": "pending"`. To approve or reject them:

1. Open `kg_layer/review/reviews.json` in any text editor.
2. Add an entry for each object you want to update, following this pattern:

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

3. Re-run Step 3 to publish the updated graph and wiki.

For prioritized triage, inspect the queue and pick the next highest-impact item:

```bash
python kg_layer/review/hitl_review.py next \
  --queue kg_layer/data/review_queue/review_queue.json \
  --top 5
```

You can also quickly record a decision:

```bash
python kg_layer/review/hitl_review.py decide \
  --reviews kg_layer/review/reviews.json \
  --object-id claim:mypaper:1 \
  --status accepted \
  --reviewer "Your Name" \
  --notes "Confirmed against source."
```

---

## Automatic ARS-to-KG runs

If ARS writes article markdown to another folder, point the orchestrator at that directory:

```bash
python kg_layer/pipeline/run_pipeline.py \
  --input-dir /absolute/path/to/ars/articles
```

Useful options:
- `--include-glob` / `--exclude-glob`: include or exclude markdown paths during extraction.
- `--publish-mode accepted|draft|all`: choose what review statuses get exported/rendered.
- `--publish-status <status>` (repeatable): explicit statuses (overrides `--publish-mode`).
- `--skip-review-apply`: publish validated objects directly.
- `--auto-accept-validated`: mark all validated objects as accepted for first-pass auto publishing.
- `--carry-forward-accepted` / `--no-carry-forward-accepted`: preserve accepted status for unchanged source spans.
- `--watch --poll-seconds 5`: run as a live sidecar and re-run on ARS/review changes.

---

## Repository Layout

```
ars-wiki-kg-system/
├── kg_layer/                  Main pipeline (everything you interact with)
│   ├── data/
│   │   ├── raw/               ← Put your documents here
│   │   ├── normalized/        Extracted & validated objects
│   │   ├── reviewed/          Objects after human review
│   │   └── published/         Final knowledge graph & wiki pages
│   ├── extraction/            Script that reads documents
│   ├── validation/            Script that checks extracted data
│   ├── review/                Review schema, queue, and decisions file
│   ├── exports/               Script that writes the JSON-LD graph
│   ├── wiki/                  Script that renders wiki pages
│   └── schemas/               Data model definition (LinkML)
└── vendor/
    └── academic-research-skills/   Upstream ARS reference (pinned submodule)
```

---

## How the Pipeline Works

```
Your .md files
      │
      ▼
  [extract]  ──► candidates.json          (all items, status = pending)
      │
      ▼
  [validate] ──► candidates.validated.json (only well-formed items)
      │
      ▼
  [review]   ──► reviewed.json            (items stamped accepted/rejected/…)
      │
      ├──► [export]  ──► graph.jsonld     (accepted items as linked data)
      │
      └──► [wiki]    ──► wiki/*.md        (one readable page per accepted item)
```

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
