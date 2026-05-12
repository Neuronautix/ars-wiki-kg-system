# LinkML Schema Notes

`knowledge_model.yaml` is the minimal pilot schema draft for Paper, Concept, Claim, and Evidence.

This file is a practical starting point for LinkML-based validation and generation. It is intentionally small to keep the first pilot testable.

## Mapping guidance

- `source_document`: typically input markdown file path or artifact ID.
- `source_section`: markdown heading extracted by parser.
- `supporting_quote_or_span`: exact quote/snippet from source text.
- `extraction_method`: parser or model strategy used.
- `review_status`: pending, in_review, accepted, rejected, needs_revision.

## Next step (after pilot)

If you want strict LinkML runtime validation, add the LinkML toolchain and generate JSON Schema from this model for CI-time checking.
