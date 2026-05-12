# Concept Extraction Prompt Contract

Task:
- Extract Concept objects from ARS markdown artifacts.
- Prefer terms explicitly defined or repeatedly used in synthesis and discussion sections.

Output contract:
- JSON array of objects.
- Object type must be: Concept.
- Required fields:
  - id
  - source_document
  - source_section
  - supporting_quote_or_span
  - confidence
  - extraction_method
  - review_status
  - reviewer_notes

Rules:
- Avoid single-use generic words.
- Capture exact phrase spans.
- Set `review_status` to `pending` initially.
