# Review Queue

This file is a human worklist for extracted objects awaiting review.

## Suggested process

1. Open candidate objects from `kg_layer/data/normalized/candidates.validated.json`.
2. For each object, decide `accepted`, `rejected`, or `needs_revision`.
3. Record decisions in `kg_layer/review/reviews.json` using `review_schema.json`.
4. Run `apply_review.py` to update object states.

## reviews.json template

```json
[
  {
    "object_id": "claim:paper1:1",
    "review_status": "accepted",
    "reviewer": "reviewer_name",
    "reviewed_at": "2026-05-12T12:00:00Z",
    "reviewer_notes": "Evidence is precise and traceable."
  }
]
```
