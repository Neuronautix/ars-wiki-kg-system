import argparse
import json
from pathlib import Path
from typing import Dict, List

ALLOWED_STATUS = {"pending", "in_review", "accepted", "rejected", "needs_revision"}

CONTEXT = {
    "@vocab": "https://example.org/ars/kg#",
    "source_document": "https://schema.org/isBasedOn",
    "source_section": "https://schema.org/text",
    "supporting_quote_or_span": "https://schema.org/quotation",
    "confidence": "https://schema.org/confidence",
    "review_status": "https://schema.org/creativeWorkStatus"
}


def to_jsonld_node(obj: Dict) -> Dict:
    node = {
        "@id": obj.get("id"),
        "@type": obj.get("type"),
        "source_document": obj.get("source_document"),
        "source_section": obj.get("source_section"),
        "supporting_quote_or_span": obj.get("supporting_quote_or_span"),
        "confidence": obj.get("confidence"),
        "extraction_method": obj.get("extraction_method"),
        "review_status": obj.get("review_status"),
        "reviewer_notes": obj.get("reviewer_notes", "")
    }
    return node


def main() -> None:
    parser = argparse.ArgumentParser(description="Export accepted reviewed objects to JSON-LD graph.")
    parser.add_argument("--input", required=True, help="Reviewed objects JSON input.")
    parser.add_argument("--output", required=True, help="JSON-LD output path.")
    parser.add_argument(
        "--include-status",
        action="append",
        default=None,
        choices=sorted(ALLOWED_STATUS),
        help="Review status to include in export. Repeatable. Defaults to accepted.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    objects: List[Dict] = json.loads(input_path.read_text(encoding="utf-8"))
    statuses = set(args.include_status or ["accepted"])
    accepted = [o for o in objects if o.get("review_status") in statuses]

    doc = {
        "@context": CONTEXT,
        "@graph": [to_jsonld_node(o) for o in accepted]
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Exported {len(accepted)} objects to {output_path} (statuses: {sorted(statuses)})")


if __name__ == "__main__":
    main()
