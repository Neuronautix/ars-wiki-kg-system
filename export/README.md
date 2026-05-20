# Export Package — Constraint Is Not a Limitation

**Authors:** Thibault Géoui, Damien Huzard  
**Version:** Finalized revision (R1 response to Major Revision decision)  
**Date:** 20 May 2026  
**ARS Pipeline:** v3.7.0, Stage 5 export

---

## Contents

```
export/
├── README.md                              ← this file
├── PIPELINE_SUMMARY.md                    ← full ARS pipeline run record
├── manuscript/
│   ├── Constraint_Is_Not_a_Limitation_FINAL.md   ← finalized manuscript (Markdown)
│   ├── Constraint_Is_Not_a_Limitation_APA7.tex   ← APA 7.0 LaTeX source
│   └── references.bib                            ← BibTeX bibliography (61 entries)
└── reports/
    ├── Stage3_Review_Summary.md           ← peer review summary (Major Revision)
    ├── Stage4.5_Integrity_Report.md       ← final integrity verification report
    └── Response_to_Reviewers_v1.md        ← formal response letter (R1)
```

---

## Compiling the PDF (LaTeX)

### Prerequisites

Install a full TeX Live distribution and the `biblatex-apa` package:

```bash
# Ubuntu / Debian
sudo apt install texlive-full

# macOS (MacTeX)
brew install --cask mactex

# Windows: install MiKTeX from https://miktex.org/
```

The `apa7` LaTeX class and `biblatex-apa` are included in `texlive-full`. If
using a minimal TeX Live, install them manually:

```bash
tlmgr install apa7 biblatex-apa biber
```

### Compile sequence

```bash
cd export/manuscript

pdflatex Constraint_Is_Not_a_Limitation_APA7.tex
biber    Constraint_Is_Not_a_Limitation_APA7
pdflatex Constraint_Is_Not_a_Limitation_APA7.tex
pdflatex Constraint_Is_Not_a_Limitation_APA7.tex
```

The three-pass compile is required: pdflatex builds the aux file, biber
processes the bibliography, two final pdflatex passes resolve all
cross-references and citation labels.

**Recommended alternative (handles passes automatically):**

```bash
latexmk -pdf Constraint_Is_Not_a_Limitation_APA7.tex
```

### Expected output

- `Constraint_Is_Not_a_Limitation_APA7.pdf` — APA 7.0 formatted PDF
- Standard manuscript layout: 12pt, double-spaced, 1-inch margins, running
  head, APA 7.0 title page, abstract page, reference list

---

## Generating DOCX (Pandoc)

### Prerequisites

```bash
# Ubuntu / Debian
sudo apt install pandoc

# macOS
brew install pandoc
```

### Option A — Convert from Markdown source (recommended for fidelity)

This path uses the finalized Markdown with a Pandoc citation filter and the
APA 7.0 CSL stylesheet. Download the APA 7.0 CSL file from the Citation
Style Language repository first:

```bash
# Download APA 7.0 CSL
curl -o apa7.csl \
  https://raw.githubusercontent.com/citation-style-language/styles/master/apa.csl

# Convert
pandoc "Constraint_Is_Not_a_Limitation_FINAL.md" \
  --citeproc \
  --bibliography=references.bib \
  --csl=apa7.csl \
  -o Constraint_Is_Not_a_Limitation.docx
```

Note: the Markdown source uses bracket-style citations (`[Author et al.,
Venue Year]`) that are not in standard Pandoc citeproc format. For
citeproc to work, you must first replace these brackets with `[@bibtex-key]`
syntax (one key per bracket). The `.tex` file uses the correct
`\parencite{key}` syntax throughout.

### Option B — Convert from LaTeX source (simpler but less complete formatting)

```bash
pandoc Constraint_Is_Not_a_Limitation_APA7.tex \
  --bibliography=references.bib \
  -o Constraint_Is_Not_a_Limitation.docx
```

Pandoc's LaTeX-to-DOCX conversion does not preserve all `apa7` class
formatting (title page, running head, double spacing). Use the resulting
DOCX as a structural starting point and apply APA 7.0 formatting manually,
or use the PDF as the canonical submission-ready document.

---

## Notes on the Bibliography

The `references.bib` file contains 61 entries covering:
- 45 peer-reviewed journal articles, conference papers, and preprints
- 16 industry reports, regulatory documents, and news sources

For entries where only the first author is known (marked `and others` in the
`author` field), the `et al.` rendering in biblatex is automatic. Full author
lists should be confirmed against DOI/PMID before formal journal submission.

Three references require special attention:
- `jj2026` (Johnson & Johnson job posting): live URL expected to retire when
  position is filled; archived Wayback snapshot is the permanent reference
- `fda2025` and `fda2024`: FDA URLs may be subject to reorganization; verify
  at time of submission
- `ema2024`: EMA document number EMA/CHMP/CVMP/83833/2023

---

## APA 7.0 Class Notes

The document uses `\documentclass[man,12pt,donotrepeattitle]{apa7}` which
produces manuscript format suitable for journal submission. To switch to
journal-published format (two-column, no double spacing), change `man` to
`jou`. To produce a student paper layout, use `stu`.

The `donotrepeattitle` option suppresses repetition of the title at the top
of the body text (after the abstract page), which is appropriate for a
position paper of this length.
