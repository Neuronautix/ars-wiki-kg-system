# Response to Reviewers — *Constraint Is Not a Limitation*

**Manuscript:** Constraint Is Not a Limitation: Graphs, Ontologies, and the Future of Efficient LLM Systems in Life Sciences
**Authors:** Thibault Géoui, Damien Huzard
**Revision round:** R1 (response to Major Revision decision)
**Date:** 20 May 2026

---

## Cover note

We thank the Editor-in-Chief, the three peer reviewers, and the Devil's Advocate reviewer for their careful and constructive engagement with the manuscript. The Major Revision decision identified two issues classified as **DA CRITICAL** (framing of the architectural-vs-capability claim, and absence of explicit failure conditions and threshold analysis) together with a Revision Roadmap of P0–P4 items. This revision addresses every item in the Roadmap and, where the reviewers' critiques pointed to deeper structural issues in the argument, we have rewritten rather than merely hedged. The revisions are tracked below as a point-by-point traceability matrix; the full revised manuscript accompanies this letter.

A brief note on what we did *not* do: we did not concede that the central architectural argument fails under improving model capability. We engaged the reviewers' challenge on that point directly — by reframing the claim more precisely, by adding an explicit three-reason argument for why the case holds under optimistic model trajectories, and by stating operational failure conditions that would falsify the case if met. We believe the revised manuscript is intellectually stronger as a result of those critiques, not narrower.

---

## A. Summary of substantive changes

| # | Change | Scope | Location |
|---|---|---|---|
| 1 | Reframed the "architectural, not capability" claim throughout to "not solely capability problems; they are also architectural, epistemic, and governance problems" | Whole paper (Abstract, §2) | Lines 11, 77 |
| 2 | Added a Scope and decision horizon subsection establishing the 3–5 year decision window to which the recommendations apply | §1 | New subsection at end of §1 |
| 3 | Added three structural reasons why the investment case holds under optimistic model improvement (auditability/regulation; interoperability/cross-org data; capability/structure complementarity) | §9 | New subsection |
| 4 | Added five operational failure conditions that would weaken the argument if met | §9 | New subsection |
| 5 | Added threshold analysis describing observable empirical signals for each failure condition | §9 | New subsection |
| 6 | Added a schematic cost scenario (1,000 queries/week, ~10× inference reduction, USD 30,000 + USD 500/month, ~14–15 month break-even) with explicit sensitivity caveats | §7 | New subsection |
| 7 | Reframed the five-waste taxonomy as an explicitly proposed analytic framework with MECE caveats and acknowledgment of unvalidated magnitudes | §2 | Subsection rewrite |
| 8 | Clarified dual-audience positioning as a bridge between architects and senior decision-makers (research leaders, data science directors, digital transformation teams, informatics leads, technical decision-makers) | Abstract / closing positioning | Line 17 |
| 9 | Added concrete FDA, EMA, and EU AI Act regulatory citations to support claims about auditability and provenance requirements | §7 ("Connecting to responsible AI scaling"), §9 (threshold analysis) | Lines updated |
| 10 | Added OMOP Common Data Model and HL7 FHIR acknowledgment as established interoperable data standards in regulated clinical contexts | §3 (metadata standard), §8 (metadata and reproducibility) | Lines updated |
| 11 | Corrected §6 section heading "Three questions" → "Four questions" to match four-item body | §6 | Heading fix |
| 12 | Acknowledged hybrid talent profiles (computational biologists, bioinformatics-trained MDs, clinical data scientists with ontology training) — gap is narrowing, not a fixed binary | §6 | New paragraph |
| 13 | Acknowledged small and mid-size pharma capacity constraints, with three pragmatic paths (community standards participation, established-standard adoption, narrow-then-generalize) | §6 | New paragraph |
| 14 | Hedged quadratic-attention claim to acknowledge FlashAttention, sparse/linear attention, sliding-window architectures | §2 | Sentence rewrite |
| 15 | Added one-sentence forward reference to the virtual-control-group worked example so §1 connects to the §8 vignette without duplication | §1 | One sentence |
| 16 | Cited the three previously-orphaned references (Soiland-Reyes 2022 on RO-Crate, O'Connor 2026 on portable metadata authoring, Pusch 2026 on HITL KG-QA architectures) at substantive points in §3 and §5 | §3, §5 | Citations added |
| 17 | Replaced the live J&J job-posting URL annotation with an explicit accessed-date, archived-snapshot reference, and rationale for why the live URL is expected to retire | Reference list | Reference rewrite |
| 18 | Added FlashAttention reference (Dao et al., NeurIPS 2022) and clinical-standards references (Hripcsak et al., MEDINFO 2015 for OMOP; Bender & Sartipi, IEEE CBMS 2013 for FHIR), plus the four regulatory documents (FDA × 2, EMA, EU AI Act) to the reference list | References | New entries |

---

## B. Response to the DA CRITICAL findings

### DA CRITICAL Issue 1 — "Architectural, not capability" framing does not engage model trajectory

**Reviewer concern (paraphrased):** The original framing risked overstating a clean architectural-vs-capability dichotomy, and did not engage seriously enough with the possibility that future, more capable models could absorb work currently done by structured knowledge infrastructure. As written, the claim could read as ideologically resistant to model improvement rather than substantively defensible.

**Our response:** We thank the reviewer for this important comment. We agree that the original formulation risked overstating the distinction between model capability and infrastructure. Our intention was not to argue that future LLMs will fail to improve in their handling of context, provenance, or inference — they will. Our argument is that several of the limitations that matter for *scientific reuse, regulatory acceptance, and cross-organizational integration* are not solely capability problems; they are also architectural, epistemic, and governance problems that persist independently of model size, because they arise from the absence of shared, durable, machine-actionable knowledge infrastructure rather than from any specific failure of model reasoning.

We have made three concrete changes in response:

1. **Reframed the claim throughout** (Abstract, §2). The new formulation reads: "Many of these limitations are not solely capability problems; they are also architectural, epistemic, and governance problems — structural challenges that persist regardless of model size because they arise from the absence of shared knowledge infrastructure, not from any failure of model reasoning."

2. **Added a Scope and decision horizon subsection** to §1 explicitly bounding the argument to a 3–5 year decision horizon — the window over which current AI infrastructure, hiring, vendor, and regulatory commitments are made. The argument is about defensible choices given *current* evidence, *current* pricing trajectories, and *current* regulatory expectations; it does not depend on assumptions about indefinite-future model behaviour.

3. **Added a "Why the argument holds under optimistic model improvement" subsection** to §9 articulating three structural reasons: (a) auditability and versioning are regulatory requirements that externalize the audit surface from the model and persist independently of model capability; (b) interoperability across studies, sites, and decades requires stable, community-maintained schemas that no individual model can unilaterally guarantee; (c) better models *increase* the marginal value of structured infrastructure by amplifying its leverage (capable models do strictly more with good infrastructure than they do with unstructured text).

### DA CRITICAL Issue 2 — No failure conditions or threshold analysis

**Reviewer concern (paraphrased):** The argument did not specify the conditions under which it would weaken, making it difficult to evaluate as a falsifiable position and giving it the texture of an unfalsifiable advocacy claim. A serious case for infrastructure investment should be able to say what would make the case fail.

**Our response:** We accept this critique fully. A position paper that recommends substantial capital and hiring commitments should state explicitly what evidence would weaken or overturn its recommendations. We have added two new subsections to §9:

1. **Failure conditions: when this argument would weaken.** Five operational, falsifiable conditions are stated. The argument weakens substantially if models can reliably and verifiably (1) infer all relevant experimental and clinical context to regulatory standard without prior structuring; (2) preserve and reconstruct provenance automatically in a third-party-verifiable form; (3) align with community standards autonomously and remain aligned as standards evolve; (4) expose calibrated machine-actionable uncertainty at the claim level; and (5) satisfy regulatory audit requirements without any prior structuring of inputs. The conditions are stated such that each can be evaluated against observable evidence rather than rhetoric.

2. **Threshold analysis: what would tell us we are approaching the failure conditions.** For each of the five conditions we state the empirical signal that would indicate the threshold is being approached: long-context benchmark evidence on regulatory-grade primary-document tasks; machine-checkable provenance produced without external scaffolding; reproducible audited ontology mappings produced without bespoke engineering; calibrated claim-level uncertainty validated against held-out ground truth; and regulator acceptance of AI-assisted analyses on unstructured inputs. We note that current and emerging regulatory positions (FDA AI guidance, EMA reflection paper, EU AI Act) move *toward*, not away from, requiring auditability and pre-structured inputs, and we cite each.

We believe these additions transform the argument from advocacy into a falsifiable empirical claim that the reader can monitor over the 3–5 year horizon to which our recommendations apply.

---

## C. Response to the P0–P4 Revision Roadmap

### P0 (mandatory blocking items)

- **P0.1 Reframing throughout:** Done (see B.1 above; Abstract line 11 and §2 line 77 rewritten).
- **P0.2 Temporal scoping (3–5 year horizon):** Done (new §1 subsection "Scope and decision horizon").
- **P0.3 Three-reason investment-holds argument:** Done (new §9 subsection).
- **P0.4 Failure conditions in §9:** Done (new §9 subsection with five operational conditions).
- **P0.5 Threshold analysis subsection in §9:** Done (new §9 subsection with per-condition empirical signals).

### P1 (high-priority items)

- **P1.1 Schematic cost scenario:** Done (new §7 subsection: 1,000 queries/week, ~10× per-query inference reduction, USD 30,000 infrastructure + USD 500/month opex, ~14–15 month break-even, with explicit sensitivity caveats on task mix, cold-start cost, excluded staff cost, and scope of the break-even calculation).
- **P1.2 Five-waste taxonomy reframing:** Done (§2 subsection retitled "(proposed framework)" with explicit acknowledgment that boundaries are not perfectly mutually exclusive, the categories are not claimed to be collectively exhaustive, and magnitudes are organization-specific qualitative descriptions, not validated quantitative rankings).

### P2 (medium-priority items)

- **P2.1 Dual-audience positioning:** Done (Abstract line 17 expanded to position the paper as a bridge between technical architects, knowledge engineers, and informatics leads on one side, and research leaders, data science directors, digital transformation teams, and heads of R&D informatics on the other).
- **P2.2 FDA / EMA / EU AI Act regulatory citations:** Done. Citations added to §7 ("Connecting to responsible AI scaling") and to the §9 threshold analysis. Four new regulatory references added to the bibliography: FDA AI-in-Drug-and-Biological-Products draft guidance (January 2025); FDA PCCP for AI-Enabled Device Software Functions (December 2024); EMA Reflection paper on AI in the lifecycle of medicines (September 2024); EU AI Act, Regulation (EU) 2024/1689 (July 2024).
- **P2.3 OMOP CDM and HL7 FHIR acknowledgment:** Done. Added to §3 metadata-standard discussion and to §8 metadata-and-reproducibility subsection. Two new references added: Hripcsak et al., MEDINFO 2015 (OMOP/OHDSI); Bender & Sartipi, IEEE CBMS 2013 (FHIR).

### P3 (lower-priority improvements)

- **P3.1 §6 heading correction "Three questions" → "Four questions":** Done.
- **P3.2 European sovereignty tightening:** Reviewed. We elected to retain the existing structure (Capgemini-view → ASML/Mistral/GDPR counter → agency-not-autarky conclusion) on the grounds that it is already a focused argument with appropriate hedging. We did not expand it with full STS framing because that would have shifted the paper's centre of gravity away from its main architectural argument.
- **P3.3 Hybrid talent profiles acknowledgment:** Done. Added a paragraph to §6 acknowledging computational biologists who have moved into ontology engineering, bioinformatics-trained physicians, clinical data scientists with formal ontology training, and graduate programs producing cross-coverage candidates. The gap is reframed as narrowing and as a question of (1) recognising which hybrid roles exist, (2) positioning them upstream, and (3) building teams that pair domain-deep and AI-deep engineers.
- **P3.4 Virtual control group as §1 vignette:** Adopted partially. Rather than relocate the detailed §8 worked example, we added a single forward-reference sentence in §1 (within the five-waste paragraph) so that the reader encounters the concrete preclinical use case early without duplicating the §8 treatment.

### P4 (housekeeping)

- **P4.1 Hedge quadratic-attention claim:** Done. §2 rewrite acknowledges FlashAttention, sparse and linear attention, sliding-window architectures, and mixture-of-experts; new Dao et al. NeurIPS 2022 reference added. The point is explicitly stated as not depending on the precise complexity class.
- **P4.2 Five-waste taxonomy mention in Abstract:** Done in the original (yesterday's) Stage 4 edit (Abstract line 11 now names all five waste forms explicitly).
- **P4.3 Small/mid-size pharma constraints:** Done as part of the §6 hybrid-talent revision (see P3.3) — added a paragraph stating three pragmatic paths for organizations that cannot absorb the full infrastructure investment on day one.
- **P4.4 Orphan references resolution:** Done. All three orphans (Soiland-Reyes 2022, O'Connor 2026, Pusch 2026) are now cited substantively in body text — Soiland-Reyes in §3 (validation layer / RO-Crate packaging of research artefacts); O'Connor in §3 (ontology-based recommendation discussion / portable metadata authoring); Pusch in §5 (human-in-the-loop section / LLM-centred KG-QA architecture with structured hand-off to experts).
- **P4.5 Archive J&J job posting URL:** Done. Reference rewritten to include explicit requisition ID (R-069315), accessed date (14 May 2026), live URL, archived Wayback snapshot URL, and a brief explanatory note that the live URL is expected to retire when the position is filled.

---

## D. What we did not change, and why

Two reviewer-adjacent suggestions did not result in changes. We note them here so the editor can confirm we considered them.

1. **Full STS expansion of the European sovereignty discussion.** The Roadmap presented this as "tighten *or* develop with STS framing." We elected to tighten (retain) the existing three-paragraph structure rather than open a substantial new STS thread, because the paper's centre of gravity is architectural and organizational, and STS framing would have required citing a different literature and addressing different debates without strengthening the central claim. We are open to revisiting this in a follow-up if the reviewers consider it essential.

2. **Quantitative validation of the five-waste taxonomy magnitudes.** The reviewers asked us to acknowledge that the magnitudes are not empirically validated. We have done this in the reframing (§2 subsection retitled "(proposed framework)" with explicit caveats), but we did not attempt to attach validated magnitudes, because that would require an empirical study that is out of scope for a position paper. We have stated this scope decision explicitly in the revised §2.

---

## E. Statement on revision discipline

This revision was applied stage by stage from a Revision Roadmap with explicit priority levels (P0 → P4). Every Roadmap item is accounted for in the traceability matrix in §A. No reviewer concern has been silently dropped. Where we declined to make a requested change, the decision is documented in §D with reasoning. Where we made changes that went beyond the Roadmap (e.g., adding three new references to support OMOP/FHIR/FlashAttention claims), the additions are noted in §A.

We are grateful to the reviewers for sharpening the manuscript on the two points (model-trajectory engagement and falsifiability) where it most needed sharpening. The revised version is, in our view, both more defensible and more useful to the audience for whom it is written.

— T. Géoui, D. Huzard
