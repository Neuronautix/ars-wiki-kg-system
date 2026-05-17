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

Paste these five commands one at a time into your terminal. Each one builds on the last.

```bash
# 1. Extract — reads your documents and finds Papers, Concepts, Claims, and Evidence
python kg_layer/extraction/extract_candidates.py \
  --input-dir kg_layer/data/raw \
  --output kg_layer/data/normalized/candidates.json

# 2. Validate — checks that everything extracted looks correct
python kg_layer/validation/validate_candidates.py \
  --input  kg_layer/data/normalized/candidates.json \
  --output kg_layer/data/normalized/candidates.validated.json

# 3. Apply review — stamps objects with the review decisions in reviews.json
python kg_layer/review/apply_review.py \
  --objects  kg_layer/data/normalized/candidates.validated.json \
  --reviews  kg_layer/review/reviews.json \
  --output   kg_layer/data/reviewed/reviewed.json

# 4. Export — writes the approved knowledge graph as a JSON-LD file
python kg_layer/exports/export_jsonld.py \
  --input  kg_layer/data/reviewed/reviewed.json \
  --output kg_layer/data/published/graph.jsonld

# 5. Render wiki — creates one readable markdown page per approved item
python kg_layer/wiki/render_wiki_pages.py \
  --input      kg_layer/data/reviewed/reviewed.json \
  --output-dir kg_layer/data/published/wiki
```

> **Windows users:** Replace the `\` line-continuation character with `` ` `` (backtick) in PowerShell, or just type each command on a single line.

### Step 4 — Find your results

| Output | Location |
|---|---|
| Extracted objects (JSON) | `kg_layer/data/normalized/` |
| Validated objects (JSON) | `kg_layer/data/normalized/candidates.validated.json` |
| Reviewed objects (JSON) | `kg_layer/data/reviewed/reviewed.json` |
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

3. Re-run Steps 3–5 to publish the updated graph and wiki.

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
