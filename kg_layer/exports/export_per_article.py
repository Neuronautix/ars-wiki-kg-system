import argparse
from collections import defaultdict
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List

ALLOWED_STATUS = {"pending", "in_review", "accepted", "rejected", "needs_revision"}

CONTEXT = {
    "@vocab": "https://example.org/ars/kg#",
    "source_document": "https://schema.org/isBasedOn",
    "source_section": "https://schema.org/text",
    "supporting_quote_or_span": "https://schema.org/quotation",
    "confidence": "https://schema.org/confidence",
    "review_status": "https://schema.org/creativeWorkStatus",
}

PROVENANCE_FIELDS = ("reviewer", "reviewed_at", "article_id", "run_id")


def article_slug(source_document: str, article_id: str = None) -> str:
    """Derive a filesystem-safe slug for an article."""
    val = article_id if article_id else Path(source_document).stem
    val = val.strip().lower()
    val = re.sub(r"[^a-z0-9]+", "-", val)
    return val.strip("-") or "article"


def article_slug_suffix(source_document: str, article_id: str = None) -> str:
    """Return a deterministic collision suffix from article_id and source_document.

    The pipe separator preserves the boundary between the optional article_id and
    source_document so different value pairs cannot collapse into the same input string.
    """
    val = f"{article_id or ''}|{source_document}"
    return hashlib.sha256(val.encode("utf-8")).hexdigest()[:16]


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
        "reviewer_notes": obj.get("reviewer_notes", ""),
    }
    # Preserve provenance fields when present.
    for field in PROVENANCE_FIELDS:
        if obj.get(field):
            node[field] = obj[field]
    return node


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export per-article KG JSON and JSON-LD from reviewed objects."
    )
    parser.add_argument("--input", required=True, help="Reviewed objects JSON path.")
    parser.add_argument("--output-dir", required=True, help="Output directory for per-article files.")
    parser.add_argument(
        "--include-status",
        action="append",
        default=None,
        choices=sorted(ALLOWED_STATUS),
        help="Review status to include. Repeatable. Defaults to accepted.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    objects: List[Dict] = json.loads(input_path.read_text(encoding="utf-8"))
    statuses = set(args.include_status or ["accepted"])
    filtered = [o for o in objects if o.get("review_status") in statuses]

    # Group objects by source_document.
    by_article: Dict[str, List[Dict]] = {}
    for obj in filtered:
        src = str(obj.get("source_document", "unknown"))
        by_article.setdefault(src, []).append(obj)

    output_dir.mkdir(parents=True, exist_ok=True)

    article_entries = []
    slug_counts = defaultdict(int)
    for source_document, objs in sorted(by_article.items()):
        if not objs:
            continue
        article_id = objs[0].get("article_id")
        base_slug = article_slug(source_document, article_id)
        slug_counts[base_slug] += 1
        article_entries.append((source_document, objs, article_id, base_slug))

    article_count = 0
    total_objects = 0

    for source_document, objs, article_id, base_slug in article_entries:
        slug = base_slug
        if slug_counts[base_slug] > 1:
            slug = f"{base_slug}-{article_slug_suffix(source_document, article_id)}"

        # Per-article KG JSON (flat list of objects).
        kg_path = output_dir / f"{slug}.kg.json"
        kg_path.write_text(json.dumps(objs, indent=2, ensure_ascii=False), encoding="utf-8")

        # Per-article JSON-LD.
        jsonld_doc = {
            "@context": CONTEXT,
            "@graph": [to_jsonld_node(o) for o in objs],
        }
        jsonld_path = output_dir / f"{slug}.graph.jsonld"
        jsonld_path.write_text(json.dumps(jsonld_doc, indent=2, ensure_ascii=False), encoding="utf-8")

        article_count += 1
        total_objects += len(objs)
        print(f"  Article '{slug}': {len(objs)} objects -> {kg_path.name}, {jsonld_path.name}")

    print(
        f"Exported {total_objects} objects across {article_count} articles to {output_dir}"
        f" (statuses: {sorted(statuses)})"
    )


if __name__ == "__main__":
    main()
