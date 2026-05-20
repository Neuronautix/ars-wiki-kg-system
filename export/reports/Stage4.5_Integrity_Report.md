# Stage 4.5 — Final Integrity Verification Report

**Manuscript:** Constraint Is Not a Limitation: Graphs, Ontologies, and the Future of Efficient LLM Systems in Life Sciences  
**Authors:** Thibault Géoui, Damien Huzard  
**Pipeline stage:** Stage 4.5 — Final Integrity Verification (ARS v3.7.0)  
**Verification date:** 20 May 2026  
**Verdict:** **PASS** (after corrections)

---

## Verification Protocol

Five-phase verification per ARS integrity agent specification:

| Phase | Scope |
|-------|-------|
| A — Existence | All cited sources traceable to real publications/documents |
| B — Context | Citations used in ways consistent with source content |
| C — Data | Numerical claims, statistics, and cost figures accurate and appropriately caveated |
| D — Originality | No plagiarism; appropriate attribution throughout |
| E — Claims | Normative claims grounded in evidence; hedging appropriate to claim strength |

---

## Pre-Correction Issues Found

Three issues were identified during Phase C and E verification. All were corrected before the final PASS verdict was issued.

---

### Issue 1 (MEDIUM) — EMA document title incorrect

**Location:** Bibliography entry for European Medicines Agency 2024 guidance  
**Problem found:** The bibliography listed the EMA reflection paper title as "Reflection paper on the use of artificial intelligence in the lifecycle of medicines." The official document title, as shown on EMA's scientific guideline page and confirmed by the PDF filename, is "Reflection paper on the use of artificial intelligence (AI) in the medicinal product lifecycle."  
**Discrepancy type:** "lifecycle of medicines" vs. "medicinal product lifecycle" — factually distinct phrasing in a regulatory citation context.  
**Severity:** MEDIUM — regulatory citations must match official titles for traceability in regulatory-facing arguments.  
**Resolution:** Bibliography entry corrected to: "Reflection paper on the use of artificial intelligence (AI) in the medicinal product lifecycle." EMA document number EMA/CHMP/CVMP/83833/2023 confirmed.  
**Status:** RESOLVED ✓

---

### Issue 2 (MINOR) — Hripcsak et al. 2015 missing DOI

**Location:** Bibliography entry for Hripcsak et al., MEDINFO 2015  
**Problem found:** The bibliography entry lacked a DOI, reducing traceability for an entry where a verified DOI was available.  
**Resolution:** DOI added: `10.3233/978-1-61499-564-7-574`. PMID 26262116 also confirmed and retained.  
**Status:** RESOLVED ✓

---

### Issue 3 (MINOR) — Surviving dichotomy in §2 body text

**Location:** §2, final sentence of the "Long context problem" subsection  
**Problem found:** The sentence "That is a knowledge infrastructure problem, not a model capability problem" retained the binary framing that the P0 revision was intended to soften throughout the paper. This formulation was inconsistent with the revised abstract and §2 opening, which had been updated to "not solely a model capability problem" to reflect the DA CRITICAL #1 fix.  
**Resolution:** Sentence updated to: "That is primarily a knowledge infrastructure problem — not solely a model capability problem."  
**Status:** RESOLVED ✓

---

## Reference Verification Summary

All 61 references verified across five dimensions:

| Dimension | Status |
|-----------|--------|
| Existence (traceable to real publication) | 61/61 VERIFIED |
| Title accuracy (spot-checked 15 entries with DOIs/arXiv IDs) | VERIFIED (1 MEDIUM correction applied) |
| Author list (first author confirmed for all; full list confirmed for fully named entries) | VERIFIED |
| DOI/URL validity (checked against DOI resolver and live URLs) | VERIFIED (1 MINOR addition) |
| Citation-in-context alignment (10 spot-checks: claim vs. source content) | VERIFIED |

New references added during Stage 4 revision (7 entries) were verified at time of addition:
- Bender & Sartipi 2013 (FHIR): DOI 10.1109/CBMS.2013.6627810 ✓
- Dao et al. 2022 (FlashAttention): arXiv 2205.14135 ✓
- Hripcsak et al. 2015 (OHDSI/OMOP): DOI 10.3233/978-1-61499-564-7-574 ✓ (after MINOR fix)
- FDA January 2025 draft guidance: URL verified ✓
- FDA December 2024 final guidance: URL verified ✓
- EMA September 2024 reflection paper: title corrected (MEDIUM fix), URL verified ✓
- EU AI Act 2024/1689: Official Journal reference verified ✓

Three previously orphaned references now cited substantively in body text:
- Soiland-Reyes et al. 2022 (RO-Crate): cited in §3 validation layer discussion ✓
- O'Connor et al. 2026 (CEDAR Embeddable Editor): cited in §3 metadata authoring discussion ✓
- Pusch et al. 2026 (HITL KG-QA): cited in §5 human-in-the-loop discussion ✓

---

## Claim Integrity Assessment

### Numerical and cost claims (Phase C)

| Claim | Source | Verdict |
|-------|--------|---------|
| "9× to 900× per year" inference cost reduction range | Epoch AI, March 2025 | VERIFIED |
| Schematic cost scenario (USD 30K + USD 500/month, ~14–15 month break-even) | Original calculation; caveats added per P1 requirement | APPROPRIATELY CAVEATED |
| "1,000 queries per week" scenario baseline | Illustrative; presented as planning number | CORRECTLY LABELED ILLUSTRATIVE |
| "25% of AI initiatives deliver expected ROI" | IBM Institute for Business Value, May 2025 | VERIFIED |
| "16% scale enterprise-wide" | Same source | VERIFIED |
| Energy correlates with output token length | Poddar et al., NAACL 2025 | VERIFIED |

### Normative claims (Phase E)

All major normative claims carry appropriate evidential qualification:
- Five-waste taxonomy: retitled "(proposed framework)" with explicit MECE caveats
- Hallucination reduction via KGs: hedged as "promising" and "task-specific" per Lavrinovics et al. 2024
- Break-even scenario: explicitly labeled "schematic" and "illustrative, not predictive" with five caveats listed
- Failure conditions: explicitly framed as conditions under which the argument "would weaken," not as certain future states

---

## Post-Correction Final Status

**Overall verdict: PASS**

All pre-submission integrity requirements are satisfied. The manuscript is cleared for Stage 5 finalization and export.

| Phase | Result |
|-------|--------|
| A — Existence | PASS |
| B — Context | PASS |
| C — Data | PASS (after MEDIUM + 1 MINOR fix) |
| D — Originality | PASS |
| E — Claims | PASS (after 1 MINOR fix) |
| **Overall** | **PASS** |
