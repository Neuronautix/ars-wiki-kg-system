# ARS Wiki Knowledge Graph System

> Each ARS research run produces two synchronized outputs: a polished article for humans and a reusable knowledge graph for machines — no coding experience required to get started.

---

## What is this?

This system works **alongside the ARS CLI/plugin** to turn reviewed research outputs into a structured knowledge graph and browsable wiki.

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

For the KG pipeline alone, you need:

1. **Python 3.8 or later** — [Download here](https://www.python.org/downloads/)  
   *(During installation on Windows, tick "Add Python to PATH")*
2. **Git** — [Download here](https://git-scm.com/downloads)

For the full ARS + KG workflow, you also need **Claude Code CLI** and an
Anthropic API key because ARS runs as Claude Code plugin/skill commands.

---

## Recommended: ARS + KG together

The preferred workflow uses native structured ARS KG handoff files for the best graph quality. The KG-layer exporter remains available as a fallback when a run only produced Markdown artifacts.

In the normal current flow:

1. Install and run ARS from `Neuronautix/academic-research-skills`.
2. ARS produces the article plus a native `*.kg_candidates.json` handoff.
3. This repository validates that handoff and publishes the KG/wiki outputs.
4. The fallback exporter is only needed when ARS produced Markdown but no native KG handoff.

### Step 1 — Get the code

If you use Claude Code from WSL Ubuntu, clone the repo inside the WSL filesystem
instead of under `/mnt/c/...`:

```bash
cd ~
mkdir -p projects
cd projects
git clone --recurse-submodules https://github.com/Neuronautix/ars-wiki-kg-system.git
cd ars-wiki-kg-system
```

If you cloned without submodules, initialize them:

```bash
git submodule update --init --recursive
```

### Step 2 — Start ARS in Claude Code

Install the ARS plugin from the Neuronautix fork:

```text
/plugin marketplace add Neuronautix/academic-research-skills
/plugin install academic-research-skills
```

Start Claude Code from the repo root:

```bash
claude
```

If ARS is installed as the Claude Code plugin, start the full ARS workflow inside
Claude with:

```text
/ars-full
```

For a first test, ask for a short article with KG artifacts:

```text
Create a short complete research article about AI tutors and student learning outcomes.
Keep the scope small for a test run. Output the final article as Markdown, produce
the native {article_id}.kg_candidates.json handoff, and produce the Claim
Verification Report JSON/Markdown if available.
```

Save or move the native KG handoff into the KG input directory:

```text
kg_layer/data/ars_handoff/ai-tutors-test.kg_candidates.json
```

Keep the article and claim verification files with the run artifacts. If ARS did
not emit a native handoff, save the final article and claim verification report
for fallback export, for example:

```text
kg_layer/data/raw/ai_tutors_article.md
kg_layer/data/raw/ai_tutors_claim_verification_report.md
```

### Step 3 — Use or produce ARS KG handoff files

Native ARS KG handoff is the preferred source. When the ARS runtime writes
`*.kg_candidates.json` files, place those files in `kg_layer/data/ars_handoff/`
and skip directly to validation or publishing.

Validate the native handoff:

```bash
python3 kg_layer/pipeline/run_pipeline.py \
  --structured-input-dir kg_layer/data/ars_handoff \
  --validate-only
```

Run stricter semantic checks:

```bash
python3 kg_layer/pipeline/run_pipeline.py \
  --structured-input-dir kg_layer/data/ars_handoff \
  --semantic-validate-only
```

If the ARS run only produced Markdown, use the KG-layer fallback exporter to
derive a compatible handoff file from the final article and, when available, the
ARS Claim Verification Report:

```bash
python3 kg_layer/ars_export/export_kg_candidates.py \
  --article kg_layer/data/raw/ai_tutors_article.md \
  --claim-verification-report kg_layer/data/raw/ai_tutors_claim_verification_report.md \
  --output-dir kg_layer/data/ars_handoff \
  --article-id ai-tutors-test \
  --run-id ars-test-001 \
  --reviewer "Your Name" \
  --handoff-schema ars_v1
```

The fallback exporter writes one `*.kg_candidates.json` file into the output
directory. If you only have the final article, omit
`--claim-verification-report`; the exporter uses markdown extraction and stamps
the extracted items with `--fallback-status` (default: `accepted`).

After fallback export, use the same validation and semantic validation commands
shown above.

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

### Step 4 — Run the pipeline with structured input

```bash
python3 kg_layer/pipeline/run_pipeline.py \
  --structured-input-dir kg_layer/data/ars_handoff
```

The pipeline:
- Reads all `*.kg_candidates.json` files from the structured input directory
- Validates and reviews each item
- Enforces semantic release gates
- Publishes per-article, global, strict/draft, constraint, and quality outputs

### Step 5 — Find your results

| Output | Location |
|---|---|
| **Per-article KG JSON** | `kg_layer/data/published/per_article/{article-slug}.kg.json` |
| **Per-article JSON-LD** | `kg_layer/data/published/per_article/{article-slug}.graph.jsonld` |
| **Global knowledge graph** | `kg_layer/data/published/graph.jsonld` |
| **Strict accepted graph** | `kg_layer/data/published/graph.accepted.jsonld` |
| **Draft graph** | `kg_layer/data/published/graph.draft.jsonld` |
| **Constraint artifacts** | `kg_layer/data/published/constraints/{accepted,draft,selected}/` |
| **Quality reports** | `kg_layer/data/published/quality/{run_quality_report.json,quality_trends.json}` |
| **Wiki pages** | `kg_layer/data/published/wiki/` |
| Review queue | `kg_layer/data/review_queue/review_queue.json` |
| Reviewed objects | `kg_layer/data/reviewed/reviewed.json` |

Open any `.md` file in the wiki folder with a text editor or Markdown viewer to read it.

`article-slug` is a filesystem-safe normalization of `article_id` (or the source
document stem when `article_id` is absent). If two articles normalize to the same
slug, a short hash suffix is appended to keep filenames distinct.

---

## Live sidecar: ARS handoff/markdown + automatic KG refresh

If ARS continuously writes or updates native handoff files, point
`--structured-input-dir` at that folder and run the KG layer in **watch mode**
alongside it. If ARS only writes Markdown, use `--input-dir` instead:

```bash
python kg_layer/pipeline/run_pipeline.py \
  --structured-input-dir /absolute/path/to/ars/handoff \
  --watch \
  --poll-seconds 5
```

The KG layer automatically re-runs whenever ARS adds or updates structured
handoff files, markdown files, or review decisions. You can combine watch mode
with `--structured-input-dir` and `--input-dir` to pick up both native handoff
files and fallback markdown articles as they appear.

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
| `--validate-only` | Validate structured ARS handoff files and exit without publishing. Requires `--structured-input-dir`. |
| `--semantic-validate-only` | Run ontology-quality semantic validation and exit. Validates `--structured-input-dir` when set, otherwise validates reviewed objects under `--data-root`. |
| `--base-iri IRI` | Base IRI for JSON-LD exports (default: `https://neuronautix.github.io/ars-wiki-kg-system/kg/`). |
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

## Production contract and release gates

The production KG contract (schema versioning, compatibility policy, quality gates,
constraint artifacts, and ARS fork requirements) is documented in:

- `kg_layer/PRODUCTION_KG_CONTRACT.md`

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
    └── academic-research-skills/   ARS runtime reference (pinned submodule)
```

---

## How the Pipeline Works

```
Native ARS KG handoff               Markdown articles
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

## Keeping the ARS Runtime Reference Up to Date

The `vendor/academic-research-skills` folder is a pinned snapshot of the ARS
runtime repository at `Neuronautix/academic-research-skills`. To update it:

```bash
git submodule update --init --recursive
git -C vendor/academic-research-skills fetch neuronautix main --tags
git -C vendor/academic-research-skills switch main
git -C vendor/academic-research-skills reset --hard neuronautix/main
```

## Working With Feature Branches and the ARS Submodule

This repository has two Git histories:

| Layer | Path | Example branch |
|---|---|---|
| Parent KG system | repo root | `feature/ars-kg-semantic-ontology` |
| ARS submodule | `vendor/academic-research-skills/` | `feature/ars-kg-semantic-protocol` |

The parent repository stores only a pointer to a specific ARS submodule commit.
If a feature changes files under `vendor/academic-research-skills/`, that change
must be committed and pushed in the ARS submodule first. Then commit the updated
submodule pointer in the parent repo.

Recommended order:

```bash
# 1. Commit and push ARS changes inside the submodule
cd vendor/academic-research-skills
git switch -c feature/ars-kg-semantic-protocol
git add README.md docs/SETUP.md .claude-plugin/plugin.json
git commit -m "Add ARS KG handoff protocol"
git push -u origin feature/ars-kg-semantic-protocol

# 2. Commit and push the parent KG system branch
cd ../..
git switch -c feature/ars-kg-semantic-ontology
git add README.md kg_layer/README.md vendor/academic-research-skills
git commit -m "Add semantic ARS KG pipeline integration"
git push -u origin feature/ars-kg-semantic-ontology
```

If you cannot push to `Neuronautix/academic-research-skills`, push the ARS submodule branch
to your own fork first, then update the submodule remote or pointer accordingly.
Do not push the parent branch with a submodule commit that exists only locally;
other machines will not be able to check it out.

---

## Need Help?

- Read the detailed developer notes in [`kg_layer/README.md`](kg_layer/README.md).
- Open an [issue](../../issues) on GitHub if something isn't working.

---

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome through pull requests and issues. For significant
changes, please open an issue first so maintainers can align on scope before
implementation.
