# Constraint Is Not a Limitation

**Full title:** Constraint Is Not a Limitation: Graphs, Ontologies, and the Future of Efficient LLM Systems in Life Sciences  
**Authors:** Thibault Géoui, Damien Huzard  
**Type:** Position paper  
**Status:** Finalized — R1 revision complete, ready for submission  
**ARS Pipeline:** v3.7.0, completed 20 May 2026

---

## Summary

A position paper arguing that knowledge infrastructure — ontologies, metadata standards, and knowledge graphs — is not made obsolete by large language models, but becomes more economically defensible as LLM pricing normalizes. The paper proposes a five-waste taxonomy (conceptual, retrieval, validation, human, energy waste), presents a hybrid architecture for life science data workflows, and establishes falsifiable failure conditions for the central investment argument.

**~13,500 words · 10 sections · 61 references**

---

## Contents

```
manuscript/
├── Constraint_Is_Not_a_Limitation_FINAL.md   ← finalized source (Markdown)
├── Constraint_Is_Not_a_Limitation.docx       ← Word document
├── Constraint_Is_Not_a_Limitation.pdf        ← PDF
├── Constraint_Is_Not_a_Limitation_APA7.tex   ← APA 7.0 LaTeX source
└── references.bib                            ← BibTeX bibliography (61 entries)

reports/
├── Response_to_Reviewers_v1.md   ← R1 response letter (18-item traceability matrix)
├── Stage3_Review_Summary.md      ← Peer review decision (Major Revision → Accept)
└── Stage4.5_Integrity_Report.md  ← Integrity verification report (PASS)

PIPELINE_SUMMARY.md   ← Full ARS pipeline run record
README.md             ← this file
```

---

## KG Layer Status

KG extraction (claims, concepts, evidence) from this paper is **pending**. To generate KG candidates from this article, run:

```bash
python3 kg_layer/ars_export/export_kg_candidates.py \
  --article papers/constraint-is-not-a-limitation/manuscript/Constraint_Is_Not_a_Limitation_FINAL.md \
  --output-dir kg_layer/data/raw/constraint-is-not-a-limitation \
  --article-id constraint-is-not-a-limitation-2026
```

---

## Compiling the LaTeX PDF

```bash
cd papers/constraint-is-not-a-limitation/manuscript
latexmk -pdf Constraint_Is_Not_a_Limitation_APA7.tex
```

Requires `texlive-full` and `biber`. See the LaTeX source for full dependency notes.
