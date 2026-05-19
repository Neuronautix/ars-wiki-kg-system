import argparse
import json
from pathlib import Path
from typing import Dict, List

try:
    from kg_layer.exports.jsonld_utils import DEFAULT_BASE_IRI, build_jsonld_doc
except ModuleNotFoundError:
    from jsonld_utils import DEFAULT_BASE_IRI, build_jsonld_doc

ALLOWED_STATUS = {"pending", "in_review", "accepted", "rejected", "needs_revision"}


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
    parser.add_argument(
        "--base-iri",
        default=DEFAULT_BASE_IRI,
        help=f"Base IRI for generated object and article identifiers. Defaults to {DEFAULT_BASE_IRI}",
    )
    parser.add_argument(
        "--metadata-file",
        default=None,
        help="Optional JSON file containing graph release metadata to embed in output.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    objects: List[Dict] = json.loads(input_path.read_text(encoding="utf-8"))
    statuses = set(args.include_status or ["accepted"])
    accepted = [o for o in objects if o.get("review_status") in statuses]

    metadata = None
    if args.metadata_file:
        metadata_path = Path(args.metadata_file)
        if not metadata_path.exists():
            raise SystemExit(f"Metadata file not found: {metadata_path}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    doc = build_jsonld_doc(accepted, args.base_iri, metadata=metadata)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Exported {len(accepted)} objects to {output_path} (statuses: {sorted(statuses)})")


if __name__ == "__main__":
    main()
