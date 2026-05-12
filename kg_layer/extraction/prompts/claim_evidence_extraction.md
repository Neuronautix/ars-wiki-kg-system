# Claim/Evidence Extraction Prompt Contract

Task:
- Extract Claim and Evidence objects from ARS markdown artifacts.
- Preserve exact supporting quote/span when possible.

Output contract:
- JSON array of objects.
- Object type must be one of: Claim, Evidence.
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
- Do not invent references or quotes.
- Keep confidence in [0,1].
- Set `review_status` to `pending` initially.
- Use concise, auditable spans.
