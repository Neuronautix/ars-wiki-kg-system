# **Constraint Is Not a Limitation: Graphs, Ontologies, and the Future of Efficient LLM Systems in Life Sciences**

**Authors:** Thibault Géoui, Damien Huzard

---

## **Abstract**

The rapid adoption of large language models has created the impression that structural knowledge infrastructure, i.e. taxonomies, ontologies, metadata standards, and knowledge graphs, may no longer be necessary. If a model can read anything and reason across it, why invest in the painstaking work of building and maintaining formal knowledge systems?

This paper argues that impression is economically and technically misleading, and that its cost is becoming visible. LLM inference is not free infrastructure: it carries variable compute, energy, and governance costs that compound at scale, and the pricing models that made early adoption feel frictionless are already shifting toward usage-sensitive billing. At the same time, the technical limitations of unstructured LLM use, i.e. context degradation, retrieval fragmentation, hallucination risk, and the absence of provenance, do not disappear as models grow more capable. Many of these limitations are not solely capability problems; they are also architectural, epistemic, and governance problems — structural challenges that persist regardless of model size because they arise from the absence of shared knowledge infrastructure, not from any failure of model reasoning. The cost of this absence takes five recurring forms: conceptual waste, retrieval waste, validation waste, human waste, and energy waste, each compounding at scale in ways that structured knowledge infrastructure can systematically address.

The solution is not to abandon LLMs. It is to position them correctly within a hybrid architecture in which metadata standards, ontologies, knowledge graphs, deterministic validators, and human expertise each perform the role they are best suited for, and the model is invoked for synthesis and ambiguity management rather than for tasks that structured systems handle more reliably and cheaply.

We argue that this architectural shift also has an organizational dimension that has received insufficient attention. The people needed to build and sustain knowledge infrastructure, i.e. domain experts who understand biology, chemistry, and therapeutic context and can work with ontologies, metadata schemas, and validation rules, are not the same people who build AI models. Organizations in the life sciences that do not plan for this talent will find themselves increasingly dependent on AI vendors not only for compute, but for interpretation.

The paper is positioned as a bridge between two audiences that rarely read the same documents: the technical architects, knowledge engineers, and informatics leads who build and operate AI-supported data systems, and the senior decision-makers — research leaders, data science directors, digital transformation teams, heads of R&D informatics — who set strategy and approve investment. The intent is to make the technical case legible to leadership and the strategic case actionable for architects, so that the same evidence supports both budget decisions and design decisions. Its central claim is that constraint is not a limitation. It is how organizations stay in control of cost, quality, and knowledge.

---

## **Section 1 — The Illusion of "Just Use AI"**

### **The moment things changed**

For anyone who had spent years trying to convince a leadership team that investing in taxonomies, ontologies, and data foundations was worth the effort, the arrival of large language models felt like a gut punch.

Suddenly, you could take an article, a clinical report, a protocol document, and run it through a model. Ask it to extract concepts, map relationships, summarize findings. And it worked remarkably well, and without any of the painstaking upfront work that structured knowledge management had always required. No taxonomy team. No controlled vocabulary. No months-long ontology engineering project. Just a prompt, and something that looked a lot like intelligence.

For a while, a serious question hung in the air: *do we actually need taxonomies and ontologies anymore?*

It was not a naive question. It was the right question to ask. It did not have a clean answer, until the economics started to shift.

### **The subsidized era**

What the early LLM experience produced was not frictionless intelligence. It produced the *impression* of frictionless intelligence, at a price that did not reflect reality.

The AI industry in its early scaling phase operated, whether intentionally or not, with a logic familiar from other platform markets: make the product so cheap and so compelling that it becomes embedded in workflows before anyone has fully priced the dependency. One industry analyst described the dynamic bluntly: AI products have significant variable costs because every API call and token processed adds cost, and those costs were not being passed on \[a16z Enterprise Newsletter, December 2024\]. The infrastructure underpinning each model call, i.e. chips, energy, data centers, inference capacity, is closer to industrial infrastructure than to classic software \[Reuters Breakingviews, July 2025\]. It does not scale for free.

This does not mean prices will move in only one direction. Inference costs per token have fallen dramatically and continue to do so, but the rate varies enormously across performance tiers: between 9x and 900x per year depending on the task, a hundred-fold difference in the pace of cost reduction \[Epoch AI, "LLM inference prices have fallen rapidly but unequally across tasks," March 2025\]. The more important observation is about *total enterprise exposure*. Unit costs may fall while overall spend rises, as reasoning-capable models are deployed deeper into workflows, context windows grow, and the number of embedded AI processes multiplies. An organization that has restructured its data pipelines, its search, its literature monitoring, and its regulatory workflows around a single model provider has not reduced its dependency by watching the per-token price fall. It has increased it.

The transition from experimentation to exposure is already visible in how AI vendors are repricing their products. Early subscription models made AI feel like a flat-cost utility: bounded, predictable, absorbing whatever usage organizations threw at it. Agentic workflows break that assumption entirely. A human user generates dozens of prompts per day; an autonomous workflow can generate thousands of model calls, intermediate reasoning steps, retries, and validations in the same period. The underlying cost structure of AI, i.e. inference, context processing, output generation, and repeated interpretation, is becoming visible to the organizations that consume it. GitHub Copilot, for example, is migrating from request-based pricing to AI Credits billed by token consumption, making the cost of each operation explicit \[Rodriguez, "GitHub Copilot is moving to usage-based billing," GitHub Blog, April 27 2026\]. Anthropic has separately begun putting outside agent tool usage behind a separate credit meter, distinct from standard subscription access, a direct recognition that automated workflows consume compute at a fundamentally different rate than human users \[Fried, "Anthropic tightens Claude limits and OpenAI courts defectors," Axios, May 14 2026\]. Reports indicate that some enterprise customers, including ServiceNow and Uber, burned through their entire annual AI token budgets before the year was out \[Fried, Axios, May 14 2026\]. These are not isolated product decisions. They are the moment the underlying economics become legible.

### **What the model cannot do on its own**

Behind the apparent ease of the LLM interaction lies a technical reality that matters for anyone designing systems at scale.

When a model receives a long document, or ten documents, or a hundred, it does not reliably use all of the information it has been given. Research has shown that model performance can degrade when relevant information is located in the middle of a long context, a phenomenon sometimes called "lost in the middle" \[Liu et al., TACL 2024\]. Extending the context window does not fully solve this: only a limited number of state-of-the-art models maintain consistent accuracy beyond 64,000 tokens, and the computational cost of doing so rises steeply \[Leng et al., 2024\].

The model must also, in the absence of structure, reconstruct meaning from scratch each time. It has to infer which terms are equivalent, which measurement units are compatible, which source is authoritative, which metadata is missing. None of that work is free. It is paid for in tokens, in compute, and in error rates. Retrieval-augmented generation improves accuracy for knowledge-intensive tasks by combining the model with external knowledge sources \[Gao et al., 2024\], but standard retrieval returns text fragments without preserving the relationships between them, leaving the model to infer connections that could have been made explicit.

The result is a set of costs that compound at scale: *conceptual waste*, when the model re-infers relationships that were already known; *retrieval waste*, when irrelevant or redundant content fills the context; *validation waste*, when outputs must be corrected because the input lacked structure; *human waste*, when experts spend time reviewing generated text that a deterministic system could have checked; and *energy waste*, because inference energy correlates directly with output token length and model size \[Poddar et al., NAACL 2025; Dauner & Socher, Frontiers in Communication 2025\]. As a concrete instance we develop in Section 8, consider the construction of a virtual control group from historical preclinical data: a task in which the cost of asking a model to infer comparability across species, strain, route of administration, and endpoint definition from unstructured text — without standardized metadata or ontology-mapped variables — becomes immediately visible, both in inference cost and in the regulatory acceptability of the result.

### **A question of architecture**

The relevant metric is not price per million tokens. It is tokens per useful decision; more broadly, the total organizational cost of producing a reliable, auditable, reusable output.

That reframing changes the question. It is not: *should we use AI?* The answer to that is clearly yes. It is: *which AI system, for which task, with which supporting infrastructure, at what cost, and with what governance?*

Retrieval-augmented generation with a cost-optimized routing strategy can maintain comparable performance to long-context inference at a fraction of the compute \[Li et al., EMNLP Industry Track 2024\]. Deterministic validation systems can catch errors that would otherwise require model calls. Smaller models, guided by structured knowledge, can handle tasks that currently route unnecessarily to frontier systems.

This is a question of architecture. And architecture, in turn, is a question of what knowledge infrastructure exists before the model is ever invoked.

The organizations that will manage AI costs effectively, and that will be least exposed when pricing normalizes, are not necessarily the ones with access to the most powerful models. They are the ones that have invested in making their knowledge machine-actionable before it reaches the model: through metadata standards, ontologies, knowledge graphs, and validation layers. Infrastructure that reduces the model's interpretive burden. Infrastructure that the model cannot provide for itself.

### **Scope and decision horizon**

A note on the scope of the argument is warranted before we proceed. The case we make in this paper applies to a 3–5 year decision horizon: the window over which most current life science and pharmaceutical organizations are committing to AI infrastructure, hiring plans, vendor contracts, and regulatory positioning. We are not making an indefinite claim about what large language models will or will not be able to do at some future date. We are making a claim about which architectural and organizational choices are defensible *given current evidence* about model behaviour, *current and announced* pricing trajectories, and *current* regulatory expectations around auditability and provenance in regulated science. Section 9 addresses explicitly the conditions under which the argument would weaken, and what evidence would tell us we are approaching them.

The rest of this paper explains what that infrastructure is, why it matters technically, what it takes to build and sustain it organizationally, and why the investment case is stronger now than it has ever been.

---

## **Section 2 — What LLMs Cannot Do Efficiently Alone**

### **Intelligence without memory**

A large language model is, at its core, a pattern-completion and reasoning system of remarkable capability. It can read a dense scientific paper and produce a lucid summary. It can identify relationships between entities across a long document. It can translate, reformat, compare, and explain. These are genuine capabilities, and they have changed what is possible in knowledge work.

What a large language model is not, however, is a knowledge management system. It has no persistent memory of your organization's data. It does not automatically know which terms in your corpus are equivalent, which measurement units are compatible across studies, which source should be treated as authoritative, or which metadata fields are missing from a record. Without structure provided from outside, it must reconstruct all of that context from text, every time it is invoked.

This distinction matters because it is the source of a class of costs that do not disappear as models become more capable. These are not solely capability costs; they are also architectural, epistemic, and governance costs — they arise from the absence of structured knowledge made available to the model, not from any failure of model reasoning. A more powerful model reconstructing context it was never given is still reconstructing context it was never given.

### **The five forms of waste (proposed framework)**

When unstructured text is the primary input to an LLM-based workflow, we observe that several categories of waste compound at scale. In this section we propose a working taxonomy that groups them into five categories. We present it as an analytic framework, not as an established or empirically validated typology: the categories are organizationally useful for thinking about where structured knowledge infrastructure earns its return, but the boundaries between them are not perfectly mutually exclusive (e.g., conceptual confusion downstream produces validation waste; retrieval failures often cascade into human waste), and we are not claiming that the five categories are collectively exhaustive of all forms of inefficiency in unstructured LLM workflows. The magnitudes attached to each category in any given deployment are also organization-specific and depend on task mix, model choice, and workflow design; we present qualitative descriptions and cite representative evidence where available, rather than claiming a fixed quantitative ranking.

With those caveats, we find the five categories below useful in practice for diagnosing where structured infrastructure pays back.

*Conceptual waste* occurs when a model re-infers relationships that are already known and stable. If your organization has established that "locomotor activity," "distance travelled," "velocity," and "home-cage monitoring" are related but not interchangeable concepts in preclinical research, that distinction should not need to be reconstructed from raw text on every query. An ontology encodes it once. Without one, the model guesses, sometimes correctly, sometimes not, and always at a cost.

*Retrieval waste* occurs when irrelevant or redundant content fills the context window. Standard retrieval-augmented generation returns text chunks ranked by semantic similarity. It does not preserve the relationships between those chunks, the provenance of the information they contain, or the conditions under which a finding was produced. The model receives fragments and must synthesize them without knowing how they connect. Knowledge graph-guided retrieval addresses this directly: instead of returning isolated passages, it retrieves entities, relations, provenance, and neighboring evidence as a compact, structured bundle \[Zhu et al., NAACL 2025; Peng et al., ACM Transactions on Information Systems 2025\].

*Validation waste* occurs when outputs must be corrected after generation because the inputs lacked structure. A model asked to extract experimental parameters from a document without a metadata schema has no reference point against which to check its own output. Errors surface downstream, often after human review, occasionally after a decision has already been made. A validation layer defined upstream, using standards such as SHACL for RDF graphs or JSON Schema for structured records, catches structural errors before they reach the model and flags generated outputs that violate known constraints \[Wilkinson et al., Scientific Data 2016\].

*Human waste* occurs when subject matter experts are positioned at the end of the pipeline to repair outputs that a deterministic system could have caught. This is the most expensive form of waste, not only in salary terms, but in the opportunity cost of expert attention. A scientist reviewing a list of incorrectly extracted entity relationships is not doing science. The correct position for expert judgment is upstream: defining the conceptual system, validating the schema, resolving genuinely ambiguous cases, and reviewing high-stakes outputs. Not correcting routine formatting errors or obvious hallucinations that a constraint layer would have prevented.

*Energy waste* occurs because every token processed has a computational and environmental cost. Inference energy correlates directly with output token length and response time \[Poddar et al., NAACL 2025\]. Model size and reasoning depth drive emissions further \[Dauner & Socher, Frontiers in Communication 2025\]. General-purpose generative AI systems can be orders of magnitude more energy-intensive than task-specific systems for the same underlying task \[Luccioni, Jernite & Strubell, ACM FAccT 2024\]. Sending forty pages to a frontier model and asking it to find the relevant paragraph is not only expensive in monetary terms; it is a poor engineering choice when a graph query could retrieve the relevant subgraph in milliseconds.

### **The long context problem**

One apparent solution to the context governance challenge is simply to extend the context window. If the model can read everything, the problem of deciding what to include disappears.

This solution is technically weaker than it appears. Research has demonstrated that model performance can degrade depending on where relevant information appears in a long prompt; models do not reliably attend to content located in the middle of a long context, a finding that holds even for models specifically designed for long-context tasks \[Liu et al., TACL 2024\]. Extending the context window to hundreds of thousands of tokens does not fully resolve this: only a limited number of state-of-the-art models maintain consistent accuracy beyond 64,000 tokens, and performance variation across models remains substantial \[Leng et al., arXiv 2024\].

The computational cost of long-context inference also rises steeply. Standard transformer attention scales quadratically with sequence length, and although a substantial body of work — efficient attention variants such as FlashAttention, linear and sparse attention, sliding-window architectures, and mixture-of-experts schemes — has reduced the effective constant factor and in some cases the asymptotic complexity, long-context inference remains a significant engineering and cost challenge in production at scale \[Tay et al., arXiv 2022; Dao et al., NeurIPS 2022\]. The point of this paper does not depend on the precise complexity class: even with the most efficient current implementations, retrieval-augmented approaches with structured retrieval maintain comparable task performance at a fraction of the compute, with hybrid routing between RAG and long-context inference offering a practical middle path \[Li et al., EMNLP Industry Track 2024\].

The relevant metric, therefore, is not how large a context window a model supports. It is how precisely the right information can be identified, structured, and delivered to the model before the context is assembled. That is primarily a knowledge infrastructure problem — not solely a model capability problem.

### **What the model needs, but cannot provide itself**

Stated directly: an LLM is good at language. It is not good at being a database, a schema validator, a provenance tracker, or an ontology. Asking one system to do all four jobs simultaneously produces a system that does all four jobs expensively and inconsistently.

The research literature on this point is no longer speculative. Knowledge graphs are a promising external-knowledge source for reducing hallucinations and improving reasoning accuracy \[Agrawal et al., NAACL 2024\], though the integration of KG and LLM systems remains an active area with unresolved benchmark and evaluation challenges \[Lavrinovics et al., arXiv 2024\]. Ontology-grounded retrieval, in which a domain ontology is used to retrieve a minimal and conceptually coherent context rather than a large undifferentiated one, has demonstrated improvements in fact recall, attribution speed, and fact-based reasoning relative to standard retrieval baselines \[Sharma et al., "OG-RAG," arXiv 2024\].

The practical implication is not that LLMs should be avoided. It is that they should be positioned correctly in a larger system: invoked for synthesis, explanation, and the management of genuine ambiguity, after structured retrieval, ontology mapping, and validation have done what they are better suited to do.

The next section describes what that infrastructure consists of and how each component contributes.

---

## **Section 3 — What Graphs, Ontologies, and Metadata Actually Do**

### **Four components, four jobs**

There is a persistent tendency to treat "structured knowledge" as a single monolithic concept, as if metadata, ontologies, and knowledge graphs were interchangeable terms for the same thing. They are not. Each component solves a different problem, and conflating them leads to poor architectural decisions.

A *metadata standard* defines what must be described about a piece of data. Who produced it, under which conditions, with which variables, units, protocol, species, model, instrument, version, and license. Without this, a dataset is interpretable only by the person who created it, and only for as long as they remember its context. FAIR data principles, first articulated in 2016 and now foundational to scientific data governance, make explicit that machine-actionability is the goal: data and metadata should be findable, accessible, interoperable, and reusable by machines, not only by humans \[Wilkinson et al., Scientific Data 2016\]. In clinical and translational research the same logic has produced mature, widely adopted instances: the **Observational Medical Outcomes Partnership Common Data Model (OMOP CDM)**, maintained by the OHDSI community, standardizes the representation of observational health data so that analyses can be executed identically across sites and institutions \[Hripcsak et al., MEDINFO 2015\], and **HL7 FHIR** provides a standards-based framework for the structured exchange of clinical information across systems \[Bender & Sartipi, IEEE CBMS 2013\]. These are not aspirational: both are operational infrastructure in regulated clinical research today, and they exemplify what *machine-actionable* metadata at the data-layer level looks like in practice. Metadata is not administrative paperwork. It is the control surface through which automated systems can find, filter, validate, and combine data without human mediation.

An *ontology* defines what things mean and how they relate. It is a formal, shared specification of concepts, their boundaries, their synonyms, and the relationships between them. In preclinical research, for example, "locomotor activity" may be related to "movement," "distance travelled," "velocity," "immobility," and "home-cage monitoring," but these are not interchangeable terms. The differences matter for data integration, for comparison across studies, and for any automated system that needs to reason about them. An ontology formalizes those distinctions in a way that both machines and domain experts can use. Seen from an AI efficiency perspective, an ontology is a form of semantic compression: a stable identifier and a defined relation can replace paragraphs of repeated textual explanation, reducing the interpretive burden on any model that consumes the data \[Sharma et al., arXiv 2024; Batista et al., Scientific Data 2022\].

A *knowledge graph* stores entities and their relationships explicitly, rather than leaving them buried in natural language text. Instead of a paragraph saying "mouse A received treatment B after surgery C on date D," the graph represents: Animal → received → Treatment; Treatment → occurredAfter → Surgery; Surgery → hasDate → D; Measurement → belongsTo → Animal. This representation is directly queryable. It supports targeted retrieval of specific entity relationships, provenance chains, neighboring evidence, and structured comparisons across studies, without requiring a model to read and parse unstructured text to reconstruct those connections \[Callahan et al., Scientific Data 2024; Ma et al., EMNLP 2025\].

A *validation layer* checks whether data and generated outputs conform to the expected structure. Standards such as SHACL provide a formal language for validating RDF graphs against defined conditions. OWL enables rich representation of knowledge about things and their relationships in a computationally usable form. JSON-LD provides a JSON-compatible way to serialize linked data, making semantic structure easier to integrate into existing web and API systems. Complementary packaging conventions such as RO-Crate make it possible to bundle data, metadata, code, and provenance into a portable, machine-actionable research object that can be validated and audited as a unit \[Soiland-Reyes et al., Data Science 2022\]. Validation is what makes the entire pipeline auditable: it creates a legible record of what was checked, what passed, and what was flagged, independent of the model's confidence.

### **What each component contributes to LLM efficiency**

The value of this infrastructure is not abstract. Each component reduces a specific category of the waste described in Section 2\.

Metadata standards reduce *retrieval waste* and *validation waste* by making datasets filterable before they reach the model, and by providing a schema against which outputs can be checked. Machine-actionable metadata templates that encode domain-specific requirements have been shown to support verifiable metadata quality, modularity, and interoperability across systems \[Batista et al., Scientific Data 2022; Musen et al., Scientific Data 2022\].

Ontologies reduce *conceptual waste* by encoding stable distinctions once, rather than requiring models to reconstruct them on each query. They also guide extraction: ontology-based recommendations have been shown to help users enter metadata more rapidly and accurately, suggesting that constraints reduce human burden rather than increase it \[Martínez-Romero et al., AMIA 2017\]. Portable, embeddable metadata authoring tools that bring template-driven, ontology-guided entry into the systems where researchers already work — rather than requiring them to switch into a dedicated curation environment — reduce the friction of producing standards-aligned metadata at the point of capture \[O'Connor et al., Data Science Journal 2026\].

Knowledge graphs reduce *retrieval waste* by enabling graph-based retrieval that preserves entity relationships and provenance rather than returning semantically similar but structurally disconnected fragments. KG-guided RAG uses graph relationships to expand and organize retrieved content, improving both retrieval and response quality \[Zhu et al., NAACL 2025\]. Biomedical knowledge graph ecosystems have demonstrated this at scale, integrating ontologies and heterogeneous life science data to support AI-powered research across large corpora \[Callahan et al., Scientific Data 2024\].

Validation layers reduce *human waste* and *validation waste* by catching errors deterministically, before they require expert review. A system that validates outputs against a known schema surfaces problems at the point of generation rather than at the point of downstream use, where the cost of correction is highest.

### **The result: a compact evidence bundle**

The practical outcome of combining these components is a workflow in which the model receives not a large undifferentiated context, but a compact, structured evidence bundle: the relevant entities, their defined relationships, the sources from which they were drawn, the conditions under which the findings were produced, and a clear flag for anything that remains genuinely ambiguous or unresolved.

This is what the model is actually good at working with. Not forty pages of raw text. A precisely assembled question, with precisely assembled evidence, and a clearly scoped task.

The naive workflow asks: "Here are forty pages. Read everything. Understand the domain. Find what is relevant. Infer the structure. Answer my question."

The structured workflow asks: "Here is the question. Query the graph. Retrieve the relevant entities, relations, evidence, and provenance. Send the compact subgraph and any unresolved ambiguity to the model."

The difference in token consumption, latency, error rate, and auditability is not marginal.

---

## **Section 4 — Why Structure Reduces Cost, Hallucination, and Energy**

### **The hallucination problem is partly an architecture problem**

Hallucination in LLM outputs is often framed as a model quality problem, something to be solved by better training, more parameters, or improved prompting. That framing is incomplete. A substantial portion of hallucination risk is architectural: it arises when a model is asked to synthesize claims without being given the structured evidence needed to ground them.

Standard RAG improves on pure generative output by providing retrieved text as context, but it leaves a significant gap. The model still receives fragments without relationship information, without explicit provenance, and without a validation layer that could flag inconsistencies. It can mix incompatible facts from different conditions, overgeneralize from limited evidence, or ignore the source metadata that would make a finding contextually meaningful \[Lavrinovics et al., arXiv 2024\].

Graph-based retrieval imposes stronger constraints. A well-constructed GraphRAG workflow can specify which entities are valid, which relationships hold, which source supports each claim, which experimental conditions apply, which claims are directly observed versus inferred, and which answer components lack supporting evidence \[Peng et al., ACM Transactions on Information Systems 2025; Barry et al., ACL 2025\]. Hallucination does not become impossible, but it becomes easier to prevent, detect, and audit, because the system can compare generated claims against explicit structured evidence rather than relying solely on the model's internal confidence.

The research survey evidence is appropriately cautious on this point. Knowledge graphs are a promising external-knowledge source for reducing hallucinations and improving reasoning accuracy, but results are task-specific and benchmarks for KG-LLM integration remain inconsistent \[Agrawal et al., NAACL 2024; Lavrinovics et al., arXiv 2024\]. The claim is not that graphs eliminate hallucination. It is that they give you the tools to catch it.

### **Token reduction is energy reduction**

There is a dimension of this argument that extends beyond organizational cost and into environmental responsibility, particularly relevant for large pharmaceutical and life science organizations with public sustainability commitments.

Inference energy correlates directly with output token length and response time \[Poddar et al., NAACL 2025\]. Reasoning-capable models and larger models incur substantially higher emissions per query \[Dauner & Socher, Frontiers in Communication 2025\]. General-purpose generative AI is orders of magnitude more energy-intensive than task-specific systems for many tasks \[Luccioni, Jernite & Strubell, ACM FAccT 2024\], and carbon accounting for LLMs requires lifecycle thinking that includes training, hardware, operational energy, and inference through user-facing APIs \[Luccioni, Viguier & Ligozat, JMLR 2023\].

The practical implication is that token economy and energy economy are the same problem. A structured workflow that reduces context size, enables caching of stable concepts and schemas, and routes work away from frontier models where smaller models or deterministic systems suffice, is not only cheaper to operate. It is more defensible from a sustainability standpoint. Energy per token should complement accuracy benchmarks as a model selection criterion, and model selection and reasoning depth can be routed dynamically to balance accuracy and energy \[Wilhelm et al., EuroMLSys 2025\].

Data centre electricity demand is growing strongly, with AI-focused infrastructure growing particularly fast \[Noffsinger et al., McKinsey Quarterly, April 2025\]. At system scale, unnecessary model calls are not neutral. They are a governance question as much as an engineering one.

### **The economic argument for routing**

The architectural logic of the paper is ultimately an economic one. Not every task requires the same level of intelligence, and pricing AI workflows as if they do is a form of systematic waste.

Do you need a frontier model to rewrite an email? To check whether a metadata field matches a controlled vocabulary? To verify that an extracted entity name matches a known identifier in an ontology? No. These are deterministic or near-deterministic tasks. Routing them to a frontier model because it is convenient is the equivalent of using a surgical robot to open a package.

Deterministic systems should handle what is deterministic. Graphs should handle relationships. Ontologies should handle meaning. LLMs should handle synthesis, explanation, and ambiguity. Humans should handle expertise and accountability. The right architecture uses each component at the point where its cost-to-value ratio is best \[Ma et al., EMNLP 2025; Wilhelm et al., EuroMLSys 2025\].

This is not a theoretical position. It is increasingly the practical experience of organizations that have deployed AI at scale and discovered that the initial convenience of routing everything to a single large model does not survive contact with real operational costs.

---

## **Section 5 — A Practical Architecture for Efficient LLM Workflows**

### **The pipeline**

A concrete architecture for efficient LLM-based workflows in knowledge-intensive domains follows a sequence that separates deterministic processing from model-dependent processing, and positions validation at both ends.

Raw documents, datasets, protocols, and papers enter a deterministic parsing stage. Metadata is extracted and mapped against known schemas. Entities are identified and mapped to ontology terms. The resulting structured output is validated against formal constraints, using SHACL, JSON Schema, or equivalent standards depending on the representation format. Validated records are stored in a knowledge graph with full provenance.

When a query arrives, it is answered through graph query or hybrid retrieval: the system retrieves the relevant entities, relationships, provenance, and neighboring evidence as a compact structured bundle. That bundle, together with any genuinely unresolved ambiguity, is passed to an LLM for synthesis. The model's output is validated against the expected structure. Human review is triggered only when confidence is low, the case is novel, the risk is high, or the downstream consequence is significant. Validated outputs update the graph with full provenance.

The result is a system in which the model is invoked selectively, receives precisely scoped inputs, and produces outputs that are auditable against structured evidence. Each stage handles what it is best suited for \[Ma et al., EMNLP 2025\].

### **Caching and reuse**

One of the underappreciated benefits of structured knowledge infrastructure is the opportunity for caching and reuse. Stable concepts, validated definitions, known entity relationships, and confirmed schema mappings do not need to be re-inferred on every query. They can be stored, retrieved deterministically, and passed to the model as established context rather than as text to be interpreted.

This matters at scale. An organization that runs thousands of literature queries per week, each of which reconstructs the same domain terminology from scratch, is paying a compounding overhead that structured retrieval eliminates. Token reduction methods that preserve essential meaning while reducing context size are an active research direction \[TRIM, arXiv 2024\], but the most reliable form of token reduction is not compression after the fact; it is not sending information the system already knows.

### **The human in the right place**

Human-in-the-loop is a term that has been overloaded to the point of losing precision. In many current deployments, it means a human reviewing every output before it is used, which is operationally expensive and does not scale. In the architecture described here, it means something more specific: human expertise applied at the points where it has the highest leverage.

Humans should define the ontology: which concepts are in scope, where boundaries lie, which synonyms are acceptable, which exclusions matter. Humans should validate the schema and resolve ambiguous cases that the system cannot handle deterministically. Humans should review high-impact outputs, i.e. those with significant downstream consequences, novel cases outside the system's validated range, and outputs flagged by the validation layer as uncertain.

Humans do not need to manually inspect every trivial mapping, formatting correction, or deterministic validation result. The system should triage review based on confidence, novelty, risk, and downstream consequence \[García-Fernández et al., CEUR 2025; Tsaneva et al., Information Processing & Management 2025; Manzoor et al., arXiv 2022\]. Recent system designs that place an LLM at the centre of a knowledge-graph question-answering loop with structured human review at decision points have made the architectural case explicit: routing model output through graph-grounded checks and explicit hand-off to domain experts at the points where evidence is ambiguous or stakes are high is operationally more reliable than either fully automated or fully manual workflows \[Pusch et al., arXiv 2026\].

This model places human expertise upstream, where it shapes the system, rather than downstream, where it repairs its outputs. It is more efficient, more scalable, and more aligned with how expert judgment actually adds value.

---

## **Section 6 — The Organizational Imperative: People, Not Just Architecture**

### **The talent gap that nobody is planning for**

Technical architecture documents describe systems. They do not describe the people needed to build and sustain them. That gap matters, because the skills required for knowledge infrastructure work are not the same as the skills required for AI development, and confusing the two leads to organizational blind spots that are expensive to correct later.

An AI developer or data scientist working with LLMs needs skills in model selection, prompt engineering, fine-tuning, evaluation, and inference optimization. These are valuable and increasingly common competencies.

An ontologist or knowledge engineer working on life science data needs something different. They need to understand the domain: the biology, the chemistry, the assay design, the therapeutic context, the regulatory environment. They need to know why "locomotor activity" and "distance travelled" are not the same thing, and why that distinction matters when integrating data across studies. They need to understand metadata standards, controlled vocabularies, RDF, OWL, SPARQL, and validation frameworks. And they need to be able to work with domain experts to define concepts, negotiate boundaries, and maintain a living knowledge system over time.

These are not adjacent skill sets. They are different professions, and they require different hiring, development, and organizational positioning strategies.

The gap, however, is narrowing in important ways and should not be framed as a fixed binary. Hybrid profiles are increasingly visible: computational biologists who have moved into ontology engineering, bioinformatics-trained physicians who can operate FHIR or OMOP pipelines, clinical data scientists with formal ontology training, and AI engineers who have specialized in biomedical knowledge representation. Graduate programs in biomedical informatics, computational biology, and digital health are beginning to produce candidates with substantial cross-coverage of both stacks. The organizational challenge is therefore less about finding a unicorn than about (1) recognising which hybrid roles exist and where they sit in the labour market, (2) positioning them where their leverage is highest — upstream of system design, not downstream of output correction — and (3) constructing teams that pair domain-deep knowledge engineers with AI-deep engineers and give each enough authority to disagree productively with the other.

A note on organizational scale is also warranted. Not every life science organization can absorb the same investment profile on the same timeline. Mid-size and small biopharma, biotechs, contract research organizations, and academic translational groups face genuine capacity constraints: they may not be able to staff a dedicated ontologist and a dedicated knowledge engineer and a dedicated AI architect simultaneously, and the schematic USD 30,000 + USD 500/month figure used in Section 7 is illustrative for a mid-sized organization rather than universally applicable. For smaller organizations, three pragmatic paths exist: (a) participate in community efforts such as the Pistoia Alliance's Pharma General Ontology so that controlled vocabularies are not reconstructed in-house, (b) adopt established standards (OMOP CDM for observational analyses, HL7 FHIR for clinical exchange, established ontologies such as Mondo, ChEBI, NCBI Taxon) rather than building bespoke ones, and (c) start narrow — instrument one high-value workflow with structured infrastructure before generalizing. The argument of this paper is not that every organization must build the same infrastructure at the same scale; it is that no organization can afford to ignore the question, and that the cost of ignoring it has shifted.

### **The market is already signaling this**

The pharmaceutical industry is beginning to recognize this distinction in practice. Novo Nordisk has publicly described ontology-based data management as part of its digital transformation in research and early development, framing structured knowledge infrastructure as operational necessity rather than academic exercise \[Tan et al., Journal of Biomedical Semantics 2025\]. The Pistoia Alliance's Pharma General Ontology initiative has brought together pharmaceutical stakeholders to define agreed core entities and recommend controlled terminologies for data exchange across the industry, explicitly framing this as a community effort requiring domain expertise, not a problem that model generation can solve unilaterally \[Pistoia Alliance, PGO Phase 1, 2025\].

At the individual organizational level, large pharmaceutical companies are already hiring for these hybrid roles. Job descriptions for knowledge graph engineers in pharma R\&D now routinely specify large-scale knowledge graph construction, ontology development, pharmaceutical or healthcare domain integration, and proficiency with RDF, OWL, SPARQL, and graph databases alongside AI and data science skills \[Johnson & Johnson, Knowledge Graph Engineer posting, R\&D Data Science & Digital Health Data Strategy and Products, careers.jnj.com, accessed May 2026\]. These roles exist because the work cannot be done without domain-grounded semantic expertise, and that expertise cannot be substituted by a larger model.

### **The dependency risk**

Organizations that do not develop this capability internally face a specific and underappreciated risk. It is not only the risk of paying more for AI inference when prices normalize. It is the risk of having outsourced the interpretation of their own scientific data to a vendor whose incentives, architecture choices, and pricing decisions they do not control.

An organization's semantic layer, i.e. the concepts, relationships, validation rules, and metadata standards that govern how its data is understood and used, is a strategic asset. If that layer is owned by an AI vendor, or reconstructed on demand by a model the organization does not control, the organization has not built a data capability. It has rented one.

Vendor lock-in is a known risk in technology procurement, involving business, technical, and legal dimensions that extend well beyond switching costs \[Opara-Martins et al., Journal of Cloud Computing 2016\]. In the context of AI, the lock-in is deeper, because it operates at the level of meaning, not only at the level of tooling. An organization whose workflows, prompts, semantic assumptions, agents, and evaluation layers are all tightly coupled to a single model provider cannot easily disentangle them. The European Parliament's work on digital sovereignty has framed this concern at a policy level \[Madiega, EPRS, July 2020\], and European industrial actors are increasingly treating dependency on non-European technology infrastructure as a security, reliability, and strategic risk \[Chee, Reuters, March 17 2025\].

The pragmatic response is not to demand absolute independence from AI vendors. The Capgemini CEO has argued publicly that full European tech autonomy is neither achievable nor desirable, given the depth of global technology interdependencies \[Marchandon, Reuters, February 13 2026\] — though it is worth noting that Capgemini, as a global consultancy with significant cross-border AI partnerships, has a direct commercial interest in that position, and it should be read accordingly.

The fuller picture is more reciprocal. Europe is not only a technology consumer. It is home to ASML, whose extreme ultraviolet lithography machines are an irreplaceable component of the global semiconductor supply chain — including for the chips that power AI infrastructure worldwide. It has produced Mistral, one of the few non-US frontier model developers operating at scale. And through GDPR, the AI Act, and its data governance frameworks, it has become the world's de facto standard-setter in AI regulation, shaping how organizations on every continent handle data and accountability. The global AI ecosystem depends on European components, regulation, and scientific output as much as Europe depends on it.

This mutual dependency does not make the sovereignty argument irrelevant. It makes it more precise. The question is not whether European life science organizations should sever ties with US or Asian model providers. It is whether they retain enough internal capability — in semantic infrastructure, in knowledge engineering, in domain-grounded data governance — to remain strategic actors rather than passive consumers. The goal is not autarky. It is agency. Organizations that do not own their semantic layer will rent not only compute, but interpretation.

### **Four questions for leadership**

For a senior leader in a life science or pharmaceutical organization, the organizational question reduces to four practical assessments.

First: do you have people who combine domain expertise with knowledge engineering skills, i.e. who understand the biology and the ontology, the chemistry and the metadata standard, the therapeutic area and the validation rule? If not, you have a dependency that will become visible when the AI bill arrives or when a critical workflow fails.

Second: are those people positioned to shape your systems rather than repair their outputs? The test is simple: did they have a seat at the table when your current AI workflows were designed, or were they brought in afterwards to review what the system produced? Upstream expertise and downstream review are not the same investment.

Third: do you know what your semantic layer costs to replace? Most organizations that have not built one do not realize how much interpretive work they are currently outsourcing to models, and therefore cannot price the dependency. A useful exercise is to ask: if our primary model provider doubled its prices tomorrow, which workflows would break, which would degrade, and which would continue unaffected because they rest on structured knowledge we own? The answers reveal the true shape of the exposure.

Fourth: who in your organization has authority over the conceptual definitions that govern your data, i.e. the terms, the relationships, the validation rules, the metadata standards? If the answer is "nobody in particular" or "it depends on the system," that is the gap. Data foundations require governance, and governance requires ownership. Building on sand is not only a technology risk. It is a leadership gap.

---

## **Section 7 — How to Justify Investment in Data Foundations**

### **The perennial problem**

The argument for investing in data foundations is not new. It has been made, in various forms, by data governance practitioners, information architects, and scientific data managers for decades. It has consistently struggled to gain traction in budget conversations, for a simple reason: the foundation is not the application.

When a leadership team reviews an investment proposal, they naturally focus on the outcome: the search capability, the analytics dashboard, the literature monitoring tool, the regulatory submission workflow. The foundation that makes those outcomes possible, i.e. the metadata schema, the ontology, the validation layer, the knowledge graph, is invisible when it works and blamed for other things when it does not. The case for it has always been indirect.

What has changed is the cost of not having it. And that cost is now becoming legible.

### **A new framing: the cost of absence**

The traditional ROI framing for data foundations, i.e. "invest now and benefit later," has limited persuasive power because the benefits are diffuse and the timeline is long. A more effective framing in the current environment is the cost of absence: what does it cost, in AI inference, in human correction, in re-curation, in missed reuse, to operate without structured knowledge infrastructure?

The answer, at scale, is substantial. An organization running AI-powered literature review, entity extraction, data integration, and regulatory reporting across a large corpus, without metadata standards or ontologies to reduce context and pre-filter retrieval, is paying a compounding overhead on every query. That overhead is not visible as a line item. It is distributed across inference costs, human review time, error correction, and the opportunity cost of results that are slower, less reliable, and harder to audit than they would be with structure in place.

### **A schematic cost scenario**

To make the cost-of-absence framing concrete, consider a schematic scenario for a mid-sized life science organization. The scenario is illustrative, not predictive: the precise figures depend on team size, model selection, pricing, and the structure of the underlying corpus. Each value below is a rounded planning number, not a measured outcome. We present it to show how the categories compose, not as a forecast.

Assume an organization running roughly **1,000 AI-assisted scientific-context queries per week** — literature triage, protocol comparison, regulatory summarization, entity extraction, and similar tasks. Assume each unstructured query draws on the equivalent of two documents pulled into the context window, where a structured-retrieval variant of the same query would draw on a compact subgraph plus targeted snippets. Under current frontier pricing, and across a representative mix of task types, the structured approach can reduce per-query inference cost by **roughly one order of magnitude** for the inference component, with additional savings on human review time because outputs become more auditable and validation can be partially automated.

Set against this, assume an infrastructure investment of approximately **USD 30,000** to stand up a usable initial knowledge graph and metadata schema (covering tooling, data modelling, and initial population from existing curated sources), plus approximately **USD 500 per month** in ongoing operating cost (hosting, validation, light curation; excludes the fully loaded cost of dedicated knowledge engineering staff, which is a separate hiring decision discussed in Section 6). Under those assumptions, the inference-cost differential alone produces a **break-even point of approximately 14–15 months**, with several caveats.

The caveats matter. The order-of-magnitude inference reduction depends on task mix; tasks that are intrinsically open-ended or require frontier reasoning will not benefit as much as structured retrieval and validation tasks. The USD 30,000 figure assumes the organization has existing curated data sources (controlled vocabularies, study metadata, internal taxonomies) that can be ingested with moderate engineering effort; from a true cold start, both the cost and the timeline rise. The USD 500/month operating estimate excludes the cost of a dedicated knowledge engineer or ontologist; a serious deployment includes one. And, critically, the break-even calculation captures only the inference-cost component; it does not capture the larger and more durable benefits of auditability, reuse across projects, reduced human correction load, and reduced vendor dependency, which compound over a longer horizon.

The point of the scenario is not the specific 14–15 month figure. It is that the cost of *not* building structured knowledge infrastructure, evaluated against current and announced pricing trajectories, is no longer obviously cheaper than the cost of building it — and at the scale at which AI workflows are now being deployed across pharmaceutical R&D, the calculation increasingly tilts toward investment. Organizations should perform this calculation with their own numbers; the categories are stable even where the magnitudes vary.

Data without appropriate metadata cannot be fully interrogated or integrated into new projects, creating wasted resources and missed opportunities for reuse \[Moresis et al., Lab Animal 2024\]. FAIR data principles make explicit that the goal of machine-actionability is not an aspiration; it is a prerequisite for automated systems to operate reliably at scale \[Wilkinson et al., Scientific Data 2016\]. Community-defined metadata standards that encode domain requirements have been shown to support verifiable quality, interoperability, and complex reporting needs \[Batista et al., Scientific Data 2022; Musen et al., Scientific Data 2022\].

### **The portfolio argument**

A second reframing that resonates with leadership is the portfolio argument \[Vereckey, MIT Sloan Management Review, April 2025\]. Data foundations are rarely justified by the first application they enable. They are justified by the portfolio of applications that become possible over time, and by the reduction in per-application cost that comes from having the foundation already in place.

An ontology built to support one preclinical data integration project does not need to be rebuilt for the next one. A metadata schema validated for one regulatory submission workflow can be extended for the next therapeutic area. A knowledge graph populated with one year's experimental data becomes more valuable with each year that follows, because the number of queryable relationships grows, the number of comparison points increases, and the cost of answering new questions falls.

Leading organizations focus their AI efforts more narrowly and expect higher ROI than peers precisely because they invest in the infrastructure that makes multiple applications efficient, rather than building each application from scratch \[Apotheker et al., BCG, January 2025\]. The ROI of data foundations is often indirect because the foundation is not the application. It shows up as reduced duplication, faster reuse, better retrieval, lower validation burden, improved auditability, lower inference waste, and higher probability that AI systems can be deployed safely at scale.

The converse is equally relevant: only about 25% of AI initiatives deliver their expected ROI, and only 16% scale enterprise-wide \[IBM Institute for Business Value, "CEO Study: CEOs double down on AI while navigating enterprise hurdles," May 2025\]. Weak data foundations and weak governance are consistently identified as contributing factors. The investment in structured knowledge infrastructure is, among other things, an investment in the probability that AI initiatives succeed.

### **Connecting to responsible AI scaling**

There is a final dimension to the business case that is increasingly relevant for organizations with public sustainability and governance commitments. Data centre electricity demand is growing sharply, driven in significant part by AI workloads \[Noffsinger et al., McKinsey Quarterly, April 2025\]. Reducing unnecessary inference through better knowledge infrastructure is not a niche technical optimization. It is part of responsible AI scaling, a way of ensuring that the organization's AI investment generates value proportional to its environmental and financial cost.

For pharmaceutical and life science organizations, this argument has particular force. The regulatory environment around AI in drug development is evolving rapidly, and auditability, provenance, and reproducibility are not optional features. They are requirements. The FDA's evolving guidance on AI/ML-enabled medical devices and on the use of AI in regulatory decision-making for drugs and biological products emphasises lifecycle traceability, documented data provenance, and pre-specified evaluation \[FDA, "Considerations for the Use of Artificial Intelligence To Support Regulatory Decision-Making for Drug and Biological Products," draft guidance, January 2025; FDA, "Marketing Submission Recommendations for a Predetermined Change Control Plan for AI-Enabled Device Software Functions," December 2024\]. The European Medicines Agency's reflection paper on the use of AI in the medicinal product lifecycle is closely aligned: it calls for documented data quality, model transparency, and reproducible analytical pipelines from preclinical through post-authorisation phases \[EMA, "Reflection paper on the use of artificial intelligence in the lifecycle of medicines," September 2024\]. The EU AI Act applies high-risk obligations — including data governance, technical documentation, traceability, and human oversight — to AI systems used in regulated medical contexts, and those obligations bind organizations regardless of where the underlying model was trained \[Regulation (EU) 2024/1689, "Artificial Intelligence Act," July 2024\]. Structured knowledge infrastructure is not in tension with these requirements. It is how they are met.

---

## **Section 8 — Why This Matters in Life Sciences**

### **The particular stakes of getting it wrong**

In most domains, a hallucinated output or a poorly integrated dataset is an inconvenience. In life sciences, it can be a safety issue, a regulatory failure, or years of wasted research investment. The stakes of getting the knowledge infrastructure right are not abstract.

Preclinical research produces large volumes of experimental data across species, models, protocols, assay types, and therapeutic areas. That data is only useful at scale if it can be compared, integrated, and reused across studies. Comparison requires shared terminology. Integration requires compatible metadata. Reuse requires provenance. Without these, each dataset is an island, legible to the team that produced it and opaque to everyone else, including the AI systems that are increasingly being asked to extract insight from it.

### **Metadata and reproducibility**

The connection between metadata standards and scientific reproducibility is well established. ARRIVE 2.0 defines the minimum reporting information for animal research; cite it to show that standardized metadata is connected to reproducibility and reporting quality, not only to AI \[du Sert et al., PLOS Biology 2020\]. A minimal metadata set designed specifically to support repurposing of nonclinical in vivo data has been proposed and validated in the literature, explicitly aligned with ARRIVE 2.0 and FAIR compliance \[Moresis et al., Lab Animal 2024\]. On the clinical side, the OMOP Common Data Model and HL7 FHIR play a parallel structural role: OMOP supports reproducible observational and real-world evidence analyses across institutions \[Hripcsak et al., MEDINFO 2015\], while FHIR underpins interoperable exchange of clinical and trial data across systems and regulators \[Bender & Sartipi, IEEE CBMS 2013\]. Both exemplify how machine-actionable structure earns its return in regulated biomedical contexts independent of any particular AI capability. The argument is not that metadata is needed because AI requires it. It is that metadata is needed because science requires it, and AI makes the absence of it more expensive.

### **Knowledge graphs in biomedical research**

The life sciences have been among the most active domains for knowledge graph development, for reasons that are directly related to the complexity of the domain's conceptual landscape. Biomedical concepts are numerous, interrelated, often ambiguous across contexts, and organized by multiple competing ontologies that must be reconciled for data integration to work.

Biomedical knowledge graph ecosystems that integrate ontologies and heterogeneous life science data are being developed explicitly for AI-powered research, combining experimental results, literature, pathway data, and clinical information in a structured form that supports both querying and model-based reasoning \[Callahan et al., Scientific Data 2024\]. PubMed knowledge graph systems have demonstrated the strategic value of connecting papers, patents, clinical trials, biomedical entities, citations, and author networks at scale \[Xu et al., PubMed KG 2.0, 2025\]. Graph data models are increasingly used to structure biomedical and clinical information in ways that enable new forms of analysis over heterogeneous data that relational databases cannot easily support \[Hänsel et al., 2023\].

PubMed metadata converted to a knowledge graph format has been shown to support semantic biomedical retrieval using entities, MeSH terms, citations, grants, and author metadata, demonstrating the practical value of the metadata-to-graph-to-retrieval pipeline in a domain directly relevant to pharmaceutical research \[Ebeid et al., Frontiers in Big Data 2022\].

### **Ontologies as operational infrastructure**

For a long time, ontologies in pharma were associated primarily with academic bioinformatics and standards bodies. That association is changing. The Novo Nordisk case is instructive: a major pharmaceutical company has publicly framed ontology-based data management as part of its core digital transformation in research and early development, not as a future aspiration but as current operational practice \[Tan et al., Journal of Biomedical Semantics 2025\].

The Pistoia Alliance's Pharma General Ontology initiative represents a broader industry recognition that interoperability across FAIR datasets requires shared, community-maintained controlled vocabularies, and that building those vocabularies requires the kind of domain-grounded expertise described in Section 6 \[Pistoia Alliance, PGO Phase 1, 2025\].

FAIR principles recommend controlled vocabularies and ontologies to define data and metadata concepts, and this is not a recommendation made in the context of AI adoption. It predates the current generation of AI tools and reflects a longstanding understanding in biomedical data management that semantic precision is a prerequisite for scientific reuse \[Bernabé et al., 2023\].

### **The specific case for preclinical data**

The preclinical domain illustrates the argument with particular clarity. Consider the challenge of constructing a virtual control group, i.e. drawing on historical control data to reduce the number of animals used in new studies. This requires identifying historical experiments that are sufficiently comparable on species, strain, age, sex, housing conditions, route of administration, assay protocol, and endpoint definition. Without standardized metadata encoding those variables consistently, the comparison cannot be made reliably. The AI system, however capable, cannot infer comparability from unstructured text with sufficient precision for a regulatory context.

With standardized metadata, ontology-mapped endpoints, and a knowledge graph that preserves provenance and experimental conditions, the comparison becomes a structured query. The model's role is reduced to synthesis and interpretation of a pre-filtered, structurally coherent evidence set. The result is faster, cheaper, more reproducible, and more auditable, all of which matters in an environment where regulators are increasingly scrutinizing the provenance and reliability of AI-assisted analysis.

---

## **Section 9 — Risks, Limitations, and What This Approach Does Not Solve**

### **Intellectual honesty about the constraints**

Any argument for a particular architectural approach is incomplete without an honest account of its limitations. The case for graphs, ontologies, and metadata standards is strong, but it is not a case for a frictionless solution. These components have real costs and genuine failure modes that organizations need to understand before investing.

### **Graphs are not free**

Knowledge graphs require design, curation, tooling, and maintenance. Building a graph that accurately represents a complex domain is a significant engineering and intellectual undertaking. Populating it requires either manual curation, which is expensive and slow, or automated extraction, which introduces its own error rates. Maintaining it as the domain evolves, as new assay types emerge, as regulatory standards change, as scientific understanding advances, requires ongoing investment.

Ontology-guided extraction with in-context learning can support semi-automated knowledge graph construction for domain-specific data with limited labelled examples \[van Cauter & Yakovets, KaLLM/ACL 2024\], and LLMs can assist in drafting ontology structures from domain descriptions \[Lippolis et al., arXiv 2025\]. But these are aids, not substitutes, for the domain expertise and engineering discipline that knowledge graph construction requires. An organization that expects to deploy a production-quality biomedical knowledge graph without sustained investment in people, tooling, and process will be disappointed.

### **Ontologies can become too rigid**

An ontology that is designed without deep involvement from domain users risks encoding the wrong distinctions, or encoding them too rigidly for the actual variety of the domain. Ontologies that are too fine-grained become difficult to maintain and fail to generalize; those that are too coarse-grained fail to capture the distinctions that matter for data integration.

LLM support for ontology engineering is an active research area, but it remains fragmented and benchmark-challenged \[Garijo et al., CEUR 2025\]. LLMs can support ontology extension and drafting, but ontology engineering still requires the kind of human-LLM collaboration in which domain experts validate conceptual boundaries and relations that automated generation cannot reliably produce \[García-Fernández et al., CEUR 2025\]. The risk of delegating ontology design to a model without expert validation is an ontology that looks formally correct but encodes semantic errors that propagate through every downstream system.

### **GraphRAG can still hallucinate**

Grounding a model's output in a knowledge graph reduces hallucination risk but does not eliminate it. If the retrieved subgraph is wrong, incomplete, or poorly linearized into the model's context, the model can still produce inaccurate outputs. KG-LLM integration remains an active research area with unresolved challenges around datasets, benchmarks, knowledge integration, and hallucination evaluation \[Lavrinovics et al., arXiv 2024\]. The claim in this paper is that graphs give you better tools to detect and audit hallucination; it is not that they prevent it.

### **Bad metadata creates false precision**

A metadata standard that is poorly designed, inconsistently applied, or maintained without quality control can be worse than no standard at all, because it creates the illusion of structured, comparable data where no real comparability exists. Token reduction should be measured empirically, not assumed \[TRIM, arXiv 2024\]. The benefits of structured knowledge infrastructure are contingent on the quality of that structure. Quality requires investment, governance, and ongoing validation.

### **Human review can become a bottleneck**

The human-in-the-loop model described in Section 5 depends on human review being applied selectively, at the points of highest leverage. If review is applied too broadly, the bottleneck moves from the model to the reviewer, and the efficiency gains of the structured pipeline are consumed by the cost of manual oversight. The system must be designed to triage review intelligently, surfacing only the cases where human judgment is genuinely needed \[Tsaneva et al., Information Processing & Management 2025\].

### **Why the argument holds under optimistic model improvement**

A reasonable objection to the case we have made is that continued model improvement may dissolve some of the costs we describe: a sufficiently capable future model might infer missing context, reconstruct provenance, harmonize terminology across studies, and self-validate its outputs to the point where much of the infrastructure we advocate becomes redundant. This objection deserves a direct response, not a dismissal.

We argue the investment case holds even under optimistic assumptions about model trajectory, for three reasons that are structural rather than capability-bound.

First, **auditability and versioning are regulatory requirements, not capability requirements**. In regulated life science contexts, what matters is not only that an answer is correct but that the chain of evidence and definitional choices behind it is independently inspectable, versioned, and reproducible by a third party. A model that infers context accurately on a single query does not by itself produce an audit-grade record of *how* it inferred it, against *which* definitional baseline, and *whether* that baseline matches the one the regulator or the next investigator will use. Structured knowledge infrastructure exists in part to externalize this audit surface from the model. Better model reasoning does not replace that externalization; it operates against it.

Second, **interoperability requires stable schemas that no individual model can unilaterally guarantee**. Data integration across studies, sites, sponsors, and decades depends on shared, durable, community-maintained representations of meaning. A model that reads two unstructured datasets and "understands" both is not the same as two datasets that conform to a shared ontology and a common metadata standard. Only the latter supports reliable downstream integration by *other* systems, *other* models, and *other* organizations operating on different software stacks and at different points in time. Interoperability is a property of the data layer, not of any particular model.

Third, **better models tend to *increase*, not decrease, the marginal value of structured knowledge infrastructure**. A capable model paired with a high-quality ontology, knowledge graph, and validation layer can do strictly more than the same model operating on unstructured text: it can decompose tasks more precisely, retrieve more focused evidence, attribute claims to specific sources, and route subtasks deterministically where appropriate. The complementarity is asymmetric in favour of structure: capable models amplify the leverage of good infrastructure more than they substitute for it. Organizations that under-invest in structure will not catch up to better infrastructure simply by buying access to better models.

These three reasons are not contingent on assumptions about whether the next model generation will or will not be substantially more capable. They concern, respectively, what regulators require, what cross-organizational data exchange requires, and how capability and structure compose at scale.

### **Failure conditions: when this argument would weaken**

Intellectual honesty also requires being explicit about the conditions under which the case we have made would weaken. The argument we make is not unconditional. It would lose force, in roughly increasing order of how plausible we believe each condition to be on a 3–5 year horizon, if models could reliably and verifiably do *all five* of the following:

1. **Infer all relevant experimental and clinical context** from primary documents, including unstated assumptions, protocol amendments, instrument calibration history, and tacit lab conventions, to a standard acceptable in a regulatory submission, without prior structuring.
2. **Preserve and reconstruct provenance automatically**, producing for every claim a machine-readable, third-party-verifiable trace back to source documents, dataset versions, and experimental conditions, without an externalized provenance layer.
3. **Align with community standards autonomously**, mapping any organization's internal terminology to evolving consensus vocabularies (e.g., OMOP CDM, HL7 FHIR, FAIR-aligned ontologies) without explicit ontology engineering, and remaining aligned as those standards change.
4. **Expose calibrated, machine-actionable uncertainty** at the level of individual claims, sufficient for automated downstream systems to route low-confidence outputs to human review or alternative evidence sources without bespoke validation logic.
5. **Satisfy regulatory audit requirements** for AI-assisted analysis without any prior structuring of inputs — i.e., demonstrating to a regulator that the model's reasoning process and evidence selection are reproducible, inspectable, and stable across reruns.

If *all five* of these conditions were met, the marginal value of organization-owned structured knowledge infrastructure would fall substantially. We do not believe this is achievable on the 3–5 year horizon to which this paper's recommendations apply, but the test is empirical, not rhetorical: the conditions above are operational, observable, and falsifiable.

### **Threshold analysis: what would tell us we are approaching the failure conditions**

Beyond stating the failure conditions, it is useful to identify the empirical signals that would indicate we are approaching them. For each condition, observable thresholds exist.

For **context inference** (condition 1), the relevant signal is independent benchmark evidence that frontier models, evaluated on representative samples of preclinical or clinical primary documents, can recover the variables required for a virtual control group reconstruction (species, strain, age, sex, route of administration, assay protocol, endpoint definition) with regulatory-grade accuracy and *without* prior schema-mapping. At present, the evidence base shows degradation on long contexts, lost-in-the-middle behaviour, and inconsistency across model families \[Liu et al., TACL 2024; Leng et al., arXiv 2024\]; we are not close to the threshold.

For **automatic provenance** (condition 2), the threshold signal would be machine-checkable provenance traces produced by models without external scaffolding, validated against established provenance standards. Current systems produce provenance only when prompted or when integrated with external provenance layers; the gap is structural, not graduating.

For **community-standard alignment** (condition 3), the signal would be reproducible, audited mappings from arbitrary organizational terminology to community-maintained vocabularies (OMOP, FHIR, Mondo, ChEBI, etc.) produced by models without bespoke ontology engineering. Current evidence indicates LLMs can *assist* ontology engineering but cannot reliably replace it \[García-Fernández et al., CEUR 2025; Garijo et al., CEUR 2025\].

For **calibrated machine-actionable uncertainty** (condition 4), the threshold is reliable, well-calibrated confidence scores at the claim level, validated against held-out ground truth across representative tasks. Calibration evaluation remains an active research area with substantial gaps.

For **regulatory audit acceptance** (condition 5), the threshold is explicit acceptance by major regulators (FDA, EMA, PMDA) of AI-assisted analyses where the input has not been pre-structured. Current and emerging regulatory positions (FDA AI/ML SaMD guidance, EMA reflection paper on AI in the medicinal product lifecycle, EU AI Act high-risk provisions) move in the opposite direction: they emphasise auditability, traceability, and pre-specified data structuring as prerequisites for trustworthy AI use in regulated contexts.

In short: each failure condition can be operationally monitored. A reader who suspects this paper's investment case is fragile to model improvement can answer that suspicion empirically, by tracking the five thresholds above. We argue the cumulative weight of current evidence does not support abandoning structured knowledge infrastructure on the 3–5 year horizon, but we welcome that determination being made on evidence rather than on faith in either direction.

---

## **Section 10 — Conclusion: Constraint as a Competitive Advantage**

### **What we have argued**

This paper has made a case in two registers, one strategic and one technical, that we hope are mutually reinforcing rather than merely parallel.

The strategic argument is this: the early experience of LLMs created a misleading impression about the cost and complexity of AI-powered knowledge work. The pricing was subsidized, the dependency was underpriced, and the structural limitations of unguided model use were invisible at small scale. That is changing. As AI workflows become embedded in organizational processes, as pricing shifts toward usage-sensitive models, and as the cost of inference, energy, and human correction becomes legible, the organizations that have invested in knowledge infrastructure will be significantly better positioned than those that have not.

The technical argument is this: LLMs are good at language, not at memory, meaning, or discipline. Graphs are good at memory. Ontologies are good at meaning. Metadata standards are good at discipline. Asking one component to do all four jobs produces a system that does all four jobs expensively and inconsistently. The right architecture assigns each job to the component best suited for it, positions the model as an orchestrated component rather than a universal solution, and places human expertise upstream, where it shapes the system, rather than downstream, where it repairs its outputs.

### **The organizational synthesis**

The dimension of this argument that we believe has received insufficient attention in the existing literature is the organizational one. Architectural diagrams and technical papers describe systems. They do not describe the people needed to build and sustain them, the organizational structures needed to support those people, or the budget conversations needed to justify the investment.

The people who build and maintain knowledge infrastructure in life sciences are domain experts first. Their value comes from understanding the biology, the chemistry, the regulatory context, and the data well enough to make precise conceptual decisions. That expertise cannot be substituted by a larger model or a smarter prompt. It requires hiring, development, organizational positioning, and sustained investment.

Organizations that do not plan for this talent will find, when the pricing shift fully arrives, that they have built AI capabilities on a foundation they do not own. They will be dependent on vendors not only for compute, but for interpretation. The semantic layer of their data, the part that encodes what their data means and how it can be used, will be reconstructed on demand, expensively and imprecisely, by systems they do not control.

### **Three things to do in the next twelve months**

For a senior leader in a life science or pharmaceutical organization reading this paper, the practical implications reduce to four priorities.

First: audit your semantic layer. Do you have ontologies, metadata standards, and validation rules that govern your key data assets? Are they machine-actionable, domain-validated, and actively maintained? If not, identify the highest-priority gaps and begin closing them, starting with the data that your AI systems rely on most heavily.

Second: assess your talent. Do you have people who combine domain expertise with knowledge engineering skills? Are they positioned to shape your data systems, or are they reviewing outputs they had no role in designing? If the role does not exist in your organization, consider what it would take to build it, whether through hiring, development, or partnership with academic groups or industry consortia such as the Pistoia Alliance.

Third: reframe your AI investment thesis. The question is not which AI tools to buy. It is what knowledge infrastructure those tools require to deliver reliable, auditable, reusable results, and whether that infrastructure is being built in proportion to the AI investment. The return on frontier model access is limited by the quality of the inputs it receives.

Fourth: assign governance ownership. Semantic infrastructure without governance degrades. Decide who in your organization has authority over the conceptual definitions, validation rules, and metadata standards that govern your key data assets. If that authority is diffuse or absent, the infrastructure you build will not hold. This is not a technical decision. It is a leadership one.

### **The final argument**

Constraint is not a limitation. It is how organizations stay in control of cost, quality, and knowledge.

An unconstrained LLM workflow feels flexible. Much of that flexibility is paid for through ambiguity, retries, hallucination risk, and human correction. A constrained workflow, one in which metadata standards, ontologies, graphs, validators, and human expertise each operate at the point of highest leverage, trades that apparent flexibility for something more valuable: reliability, auditability, reusability, and the ability to know, with confidence, what your AI systems actually know.

Organizations that invest in that infrastructure now are not choosing caution over ambition. They are building the foundation on which AI-powered knowledge work, at scale, in regulated environments, with scientific and legal accountability, actually rests.

The organizations that do not own their semantic layer will rent not only compute, but interpretation. The organizations that do will have built something that no vendor can take away.

---

## **References**

*Note: References are listed here for completeness. All citations marked ⚠ in the verification report require confirmation of exact title, DOI, URL, or finding before submission.*

### **Peer-reviewed and preprint sources**

Agrawal et al., "Can Knowledge Graphs Reduce Hallucinations in LLMs? A Survey," NAACL 2024\.

Barry et al., "GraphRAG: Leveraging Graph-Based Efficiency to Minimize Hallucinations in LLM-Driven RAG for Finance Data," GenAIK/ACL 2025\.

Batista et al., "Machine actionable metadata models," Scientific Data 2022\. DOI: 10.1038/s41597-022-01707-6.

Bender, D., and Sartipi, K., "HL7 FHIR: An Agile and RESTful Approach to Healthcare Information Exchange," in *Proceedings of the 26th IEEE International Symposium on Computer-Based Medical Systems (CBMS)* (2013), 326–331\. DOI: 10.1109/CBMS.2013.6627810.

Bernabé et al., "The use of foundational ontologies in biomedical research," *Journal of Biomedical Semantics* 14:21 (2023)\. DOI: 10.1186/s13326-023-00300-z.

Callahan et al., "An open source knowledge graph ecosystem for the life sciences," Scientific Data 2024\. DOI: 10.1038/s41597-024-03171-w.

Dao, T., Fu, D. Y., Ermon, S., Rudra, A., and Ré, C., "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness," in *Advances in Neural Information Processing Systems (NeurIPS)* 35 (2022)\. arXiv 2205.14135.

Dauner & Socher, "Energy costs of communicating with AI," Frontiers in Communication 2025\. DOI: 10.3389/fcomm.2025.1572947.

du Sert et al., "Reporting animal research: Explanation and elaboration for the ARRIVE guidelines 2.0," PLOS Biology 2020\.

Ebeid et al., "MedGraph: A semantic biomedical information retrieval framework using knowledge graph embedding for PubMed," Frontiers in Big Data 2022\. DOI: 10.3389/fdata.2022.965619.

Gao et al., "Retrieval-Augmented Generation for Large Language Models: A Survey," arXiv 2312.10997.

García-Fernández et al., "Ontology Engineering with Large Language Models," CEUR Workshop Proceedings 2025\.

Garijo et al., "LLMs for Ontology Engineering: A landscape of Tasks and Benchmarking challenges," CEUR Workshop Proceedings 2025\.

Hänsel et al., "From Data to Wisdom: Biomedical Knowledge Graphs for Real-World Data Insights," *Journal of Medical Systems* 47(1):65 (2023)\. DOI: 10.1007/s10916-023-01951-2.

Hripcsak, G., Duke, J. D., Shah, N. H., Reich, C. G., Huser, V., Schuemie, M. J., Suchard, M. A., et al., "Observational Health Data Sciences and Informatics (OHDSI): Opportunities for Observational Researchers," *Studies in Health Technology and Informatics* (MEDINFO 2015) 216: 574–578\. PMID: 26262116\. DOI: 10.3233/978-1-61499-564-7-574.

Johnson & Johnson, "Knowledge Graph Engineer — R\&D Data Science & Digital Health Data Strategy and Products" (job posting, requisition R-069315), careers.jnj.com, accessed 14 May 2026\. Original URL: https://www.careers.jnj.com/en/jobs/r-069315/knowledge-graph-engineer-rd-data-science-digital-health-data-strategy-and-products/. Archived snapshot: https://web.archive.org/web/2026*/https://www.careers.jnj.com/en/jobs/r-069315/knowledge-graph-engineer-rd-data-science-digital-health-data-strategy-and-products/ (Wayback Machine). The posting is cited as illustrative market evidence of pharma demand for hybrid knowledge-graph engineering roles; the live URL is expected to be retired once the position is filled, in which case the archived snapshot is the canonical reference.

Lavrinovics et al., "Knowledge Graphs, Large Language Models, and Hallucinations: An NLP Perspective," arXiv 2411.14258.

Leng et al., "Long Context RAG Performance of Large Language Models," arXiv 2411.03538.

Li et al., "Retrieval Augmented Generation or Long-Context LLMs? A Comprehensive Study and Hybrid Approach," EMNLP Industry Track 2024\.

Lippolis et al., "Ontology Generation using Large Language Models," arXiv 2503.05388.

Liu et al., "Lost in the Middle: How Language Models Use Long Contexts," TACL 2024\. DOI: 10.1162/tacl\_a\_00638.

Luccioni, Jernite & Strubell, "Power Hungry Processing: Watts Driving the Cost of AI Deployment?" ACM FAccT 2024\. DOI: 10.1145/3630106.3658542.

Luccioni, Viguier & Ligozat, "Estimating the Carbon Footprint of BLOOM, a 176B Parameter Language Model," JMLR 2023\. arXiv 2211.02001.

Ma et al., "Large Language Models Meet Knowledge Graphs for Question Answering: Synthesis and Opportunities," EMNLP 2025\. DOI: 10.18653/v1/2025.emnlp-main.1249.

Manzoor et al., "Expanding Knowledge Graphs with Humans in the Loop," arXiv 2212.05189.

Martínez-Romero et al., "Fast and Accurate Metadata Authoring Using Ontology-Based Recommendations," AMIA 2017\. PMID: 29854196\.

Moresis et al., "A minimal metadata set (MNMS) to repurpose nonclinical in vivo data," Lab Animal 2024\. DOI: 10.1038/s41684-024-01335-0.

Musen et al., "Modeling community standards for metadata as templates makes data FAIR," Scientific Data 2022\. PMID: 36371407\.

O'Connor et al., "Author Once, Publish Everywhere: Portable Metadata Authoring with the CEDAR Embeddable Editor," Data Science Journal 2026\. DOI: 10.5334/dsj-2026-002.

Opara-Martins et al., "Critical analysis of vendor lock-in and its impact on cloud computing migration," Journal of Cloud Computing 2016\.

Peng et al., "Graph Retrieval-Augmented Generation: A Survey," arXiv 2408.08921 / *ACM Transactions on Information Systems* 44, no. 2 (2025)\. DOI: 10.1145/3777378.

Pistoia Alliance, "Pharma General Ontology Phase 1," 2025\.

Poddar et al., "Towards Sustainable NLP: Insights from Benchmarking Inference Energy in Large Language Models," NAACL 2025\. DOI: 10.18653/v1/2025.naacl-long.632.

Pusch et al., "A Human-in-the-Loop, LLM-Centered Architecture for Knowledge-Graph Question Answering," arXiv 2602.05512.

Sharma et al., "OG-RAG: Ontology-Grounded Retrieval-Augmented Generation For Large Language Models," arXiv 2412.15235.

Soiland-Reyes et al., "Packaging research artefacts with RO-Crate," Data Science 2022\. DOI: 10.3233/DS-210053.

Tan et al., "Digital evolution: Novo Nordisk's shift to ontology-based data management," Journal of Biomedical Semantics 2025\.

Tay et al., "Efficient Transformers: A Survey," arXiv 2009.06732.

TRIM, "Token Reduction and Inference Modeling for Cost-Effective Language Generation," arXiv 2412.07682.

Tsaneva et al., "Knowledge graph validation by integrating LLMs and human-in-the-loop," Information Processing & Management 2025\.

van Cauter & Yakovets, "Ontology-guided Knowledge Graph Construction from Maintenance Short Texts," KaLLM/ACL 2024\. DOI: 10.18653/v1/2024.kallm-1.8.

Wilkinson et al., "The FAIR Guiding Principles for scientific data management and stewardship," Scientific Data 2016\. DOI: 10.1038/sdata.2016.18.

Wilhelm et al., "Beyond Test-Time Compute Strategies: Advocating Energy-per-Token in LLM Inference," EuroMLSys 2025\. DOI: 10.1145/3721146.3721953.

Xu et al., "PubMed Knowledge Graph 2.0," 2025\. PMID: 40527887\. arXiv 2410.07969.

Zhu et al., "Knowledge Graph-Guided Retrieval Augmented Generation," arXiv 2502.06864 / NAACL 2025\.

### **Industry, policy, and grey literature sources**

a16z Enterprise Newsletter, "AI Is Driving A Shift Towards Outcome-Based Pricing," December 2024\. https://a16z.com/newsletter/december-2024-enterprise-newsletter-ai-is-driving-a-shift-towards-outcome-based-pricing/

Fried, I., "Anthropic tightens Claude limits and OpenAI courts defectors," Axios, May 14 2026\. https://www.axios.com/2026/05/14/anthropic-claude-price-openai-tokens

Apotheker, J., Duranton, S., Lukic, V., de Bellefonds, N., Iyer, S., Bouffault, O., and de Laubier, R. (BCG), "From Potential to Profit: Closing the AI Impact Gap," Boston Consulting Group, January 15 2025\. https://www.bcg.com/publications/2025/closing-the-ai-impact-gap

Epoch AI, "LLM inference prices have fallen rapidly but unequally across tasks," March 12 2025\. CC-BY. https://epoch.ai/data-insights/llm-inference-price-trends

European Medicines Agency (EMA), "Reflection paper on the use of artificial intelligence (AI) in the medicinal product lifecycle," EMA/CHMP/CVMP/83833/2023, adopted September 2024\. https://www.ema.europa.eu/en/documents/scientific-guideline/reflection-paper-use-artificial-intelligence-ai-medicinal-product-lifecycle\_en.pdf

European Parliament and Council of the European Union, "Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act)," Official Journal of the European Union, 12 July 2024\. https://eur-lex.europa.eu/eli/reg/2024/1689/oj

FDA (U.S. Food and Drug Administration), "Considerations for the Use of Artificial Intelligence To Support Regulatory Decision-Making for Drug and Biological Products," draft guidance for industry, January 2025\. https://www.fda.gov/regulatory-information/search-fda-guidance-documents/considerations-use-artificial-intelligence-support-regulatory-decision-making-drug-and-biological

FDA (U.S. Food and Drug Administration), "Marketing Submission Recommendations for a Predetermined Change Control Plan for Artificial Intelligence-Enabled Device Software Functions," final guidance, December 2024\. https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial-intelligence

Madiega, T., "Digital sovereignty for Europe," EPRS Ideas Paper, European Parliamentary Research Service, PE 651.992, July 2020\. https://www.europarl.europa.eu/thinktank/en/document/EPRS\_BRI(2020)651992

Rodriguez, M., "GitHub Copilot is moving to usage-based billing," GitHub Blog, April 27 2026\. https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/

IBM Institute for Business Value, "CEOs double down on AI while navigating enterprise hurdles," IBM Newsroom, May 6 2025\. https://newsroom.ibm.com/2025-05-06-ibm-study-ceos-double-down-on-ai-while-navigating-enterprise-hurdles

Noffsinger, J., Goodpaster, M., Patel, M., Chang, H., Sachdeva, P., and Bhan, A. (McKinsey), "The cost of compute: A $7 trillion race to scale data centers," McKinsey Quarterly, April 28 2025\. https://www.mckinsey.com/industries/technology-media-and-telecommunications/our-insights/the-cost-of-compute-a-7-trillion-dollar-race-to-scale-data-centers

Vereckey, B., "How to make data indispensable to your organization," MIT Sloan Management Review, April 7 2025\. https://mitsloan.mit.edu/ideas-made-to-matter/how-to-make-data-indispensable-to-your-organization

Chee, F.Y., "Airbus leads call for Europe to create sovereign infrastructure fund, buy European," Reuters, March 17 2025\. https://www.reuters.com/business/aerospace-defense/airbus-others-call-sovereign-infrastructure-fund-buy-european-2025-03-17/

Marchandon, L., "Capgemini CEO dismisses calls for full European tech autonomy," Reuters, February 13 2026\. https://www.reuters.com/business/retail-consumer/capgemini-ceo-dismisses-calls-full-european-tech-autonomy-2026-02-13/

Reuters Breakingviews, "AI boom is infrastructure masquerading as software," July 23 2025\. https://www.reuters.com/commentary/breakingviews/ai-boom-is-infrastructure-masquerading-software-2025-07-23/

