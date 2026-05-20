# Stage 3 — Peer Review Summary

**Manuscript:** Constraint Is Not a Limitation: Graphs, Ontologies, and the Future of Efficient LLM Systems in Life Sciences  
**Authors:** Thibault Géoui, Damien Huzard  
**Pipeline stage:** Stage 3 — Academic Paper Review (ARS v3.7.0)  
**Review date:** 19 May 2026  
**Decision:** **Major Revision**

---

## Review Panel

| Role | Function |
|------|----------|
| Editor-in-Chief (EIC) | Final decision authority; editorial synthesis |
| Field Analyst 1 | Technical/AI systems perspective |
| Field Analyst 2 | Life sciences / domain knowledge perspective |
| Field Analyst 3 | Organizational / strategic perspective |
| Devil's Advocate (DA) | Adversarial critique; falsifiability challenge |

---

## Decision: Major Revision

The panel reached a **Major Revision** decision. The manuscript was judged to make a defensible and timely argument about the role of knowledge infrastructure in hybrid AI architectures for life sciences, but two findings classified as **DA CRITICAL** were identified that required substantive revision before the argument could be considered intellectually robust.

No reviewer recommended rejection. The underlying argument was assessed as sound and the evidence base as adequate for a position paper. The deficiencies were in framing precision and argumentative completeness, not in the core thesis.

---

## DA CRITICAL Findings

### DA CRITICAL Issue 1 — "Architectural, not capability" framing does not engage model trajectory

**Finding:** The original manuscript framed the argument as "architectural, not capability" limitations, which risked implying a clean dichotomy between model capability and infrastructure need. The framing did not engage with the possibility that future, more capable models could absorb work currently done by structured knowledge infrastructure. As written, the claim read as ideologically resistant to model improvement rather than substantively defensible.

**Severity:** CRITICAL — the framing weakness undermined the intellectual defensibility of the central claim across the entire paper.

**Required remediation:** Reframe the claim throughout; add explicit temporal scoping; add a structural argument for why the investment case holds under optimistic model improvement.

---

### DA CRITICAL Issue 2 — No failure conditions or threshold analysis

**Finding:** The manuscript did not specify the conditions under which its central argument would weaken or fail. This gave the argument the texture of an unfalsifiable advocacy claim rather than a position subject to empirical evaluation. A paper recommending substantial capital and hiring commitments should state explicitly what evidence would overturn its recommendations.

**Severity:** CRITICAL — an unqualified position paper cannot be taken seriously as intellectual output; falsifiability is a minimum standard.

**Required remediation:** Add explicit, operational failure conditions; add a threshold analysis stating observable empirical signals for each condition.

---

## Revision Roadmap (P0–P4)

### P0 — Mandatory blocking items (5 items)
1. Reframe the "architectural vs. capability" claim throughout (Abstract, §2)
2. Add a Scope and Decision Horizon subsection to §1 (3–5 year window)
3. Add a three-reason "holds under optimistic model improvement" argument to §9
4. Add five operational failure conditions to §9
5. Add threshold analysis (per-condition empirical signals) to §9

### P1 — High-priority items (2 items)
1. Add a schematic cost scenario to §7 (with explicit sensitivity caveats)
2. Reframe the five-waste taxonomy as an explicitly proposed framework (MECE caveats, unvalidated magnitudes)

### P2 — Medium-priority items (3 items)
1. Expand dual-audience positioning statement (Abstract/closing)
2. Add FDA, EMA, EU AI Act regulatory citations to §7 and §9 threshold analysis
3. Acknowledge OMOP CDM and HL7 FHIR as established interoperable standards in §3 and §8

### P3 — Lower-priority items (4 items)
1. Correct §6 heading "Three questions" → "Four questions"
2. Review European sovereignty discussion (tighten or expand with STS framing)
3. Acknowledge hybrid talent profiles — gap narrowing, not a fixed binary
4. Add forward reference to virtual control group vignette in §1

### P4 — Housekeeping (5 items)
1. Hedge the quadratic-attention claim (FlashAttention, sparse/linear attention)
2. Name all five waste forms explicitly in Abstract
3. Acknowledge small/mid-size pharma capacity constraints
4. Resolve three orphan references (Soiland-Reyes 2022, O'Connor 2026, Pusch 2026)
5. Archive the live J&J job posting URL with accessed date and Wayback snapshot

---

## Summary Assessments by Reviewer Domain

**Technical/AI systems (Field Analyst 1):** Manuscript is technically credible. The five-waste taxonomy is a useful organizing framework but needs explicit acknowledgment that it is proposed, not established. The long-context complexity claims need hedging given FlashAttention and related work.

**Life sciences / domain (Field Analyst 2):** The preclinical data argument is compelling and the virtual control group example is well chosen. The OMOP/FHIR gap was noted — these are operational standards in regulated clinical contexts and their absence from the manuscript implied an incomplete treatment of the clinical infrastructure landscape.

**Organizational / strategic (Field Analyst 3):** The talent gap section is the most original contribution. The failure to acknowledge hybrid profiles and small-pharma constraints made the argument less actionable for the target audience. The cost scenario is needed to ground the investment case.

**Devil's Advocate:** Both CRITICAL findings were identified by the DA reviewer. The core concern: a position paper that cannot state its own failure conditions is not making a falsifiable intellectual contribution. The temporal scoping was also identified as essential — the argument as written implied a permanent rather than a horizon-bound claim.

---

## Path to Acceptance

The panel indicated that a well-executed Major Revision addressing the P0–P1 items would be likely to receive a favorable re-review verdict. The P2–P4 items were expected to be completed in full. The re-review (Stage 3') would assess whether all Roadmap items had been addressed and whether the revised framing was coherent.
