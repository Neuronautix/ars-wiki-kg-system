import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List

ALL_STATUSES = ["pending", "in_review", "accepted", "rejected", "needs_revision"]
DRAFT_STATUSES = ["pending", "in_review", "accepted", "needs_revision"]


def run_cmd(args: List[str]) -> None:
    subprocess.run(args, check=True)


def resolve_publish_statuses(mode: str, explicit_statuses: List[str]) -> List[str]:
    if explicit_statuses:
        return explicit_statuses
    if mode == "accepted":
        return ["accepted"]
    if mode == "draft":
        return DRAFT_STATUSES
    return ALL_STATUSES


def auto_accept(validated_path: Path, reviewed_path: Path) -> None:
    objects = json.loads(validated_path.read_text(encoding="utf-8"))
    for obj in objects:
        obj["review_status"] = "accepted"
        obj["reviewer_notes"] = obj.get("reviewer_notes") or "Auto-accepted by pipeline run."
        obj["reviewer"] = obj.get("reviewer", "auto_pipeline")
        obj["reviewed_at"] = obj.get("reviewed_at", "")
    reviewed_path.parent.mkdir(parents=True, exist_ok=True)
    reviewed_path.write_text(json.dumps(objects, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Auto-accepted {len(objects)} validated objects -> {reviewed_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full KG layer pipeline in one command.")
    parser.add_argument("--input-dir", default="kg_layer/data/raw", help="Input markdown directory.")
    parser.add_argument("--data-root", default="kg_layer/data", help="Base data directory for outputs.")
    parser.add_argument("--reviews", default="kg_layer/review/reviews.json", help="Review decisions JSON file.")
    parser.add_argument("--include-glob", action="append", default=[], help="Optional extraction include glob. Repeatable.")
    parser.add_argument("--exclude-glob", action="append", default=[], help="Optional extraction exclude glob. Repeatable.")
    parser.add_argument(
        "--publish-mode",
        choices=["accepted", "draft", "all"],
        default="accepted",
        help="Status policy for export/wiki when --publish-status is not provided.",
    )
    parser.add_argument(
        "--publish-status",
        action="append",
        default=[],
        choices=ALL_STATUSES,
        help="Explicit status to publish (repeatable). Overrides --publish-mode.",
    )
    parser.add_argument("--skip-review-apply", action="store_true", help="Skip apply_review and publish validated objects directly.")
    parser.add_argument("--auto-accept-validated", action="store_true", help="Set all validated objects to accepted before publishing.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    data_root = (repo_root / args.data_root).resolve()
    input_dir = (repo_root / args.input_dir).resolve()
    reviews_path = (repo_root / args.reviews).resolve()

    candidates_path = data_root / "normalized" / "candidates.json"
    validated_path = data_root / "normalized" / "candidates.validated.json"
    reviewed_path = data_root / "reviewed" / "reviewed.json"
    jsonld_path = data_root / "published" / "graph.jsonld"
    wiki_dir = data_root / "published" / "wiki"

    extract_script = repo_root / "kg_layer" / "extraction" / "extract_candidates.py"
    validate_script = repo_root / "kg_layer" / "validation" / "validate_candidates.py"
    review_script = repo_root / "kg_layer" / "review" / "apply_review.py"
    export_script = repo_root / "kg_layer" / "exports" / "export_jsonld.py"
    wiki_script = repo_root / "kg_layer" / "wiki" / "render_wiki_pages.py"

    extract_cmd = [sys.executable, str(extract_script), "--input-dir", str(input_dir), "--output", str(candidates_path)]
    for glob_value in args.include_glob:
        extract_cmd.extend(["--include-glob", glob_value])
    for glob_value in args.exclude_glob:
        extract_cmd.extend(["--exclude-glob", glob_value])
    run_cmd(extract_cmd)

    run_cmd([sys.executable, str(validate_script), "--input", str(candidates_path), "--output", str(validated_path)])

    if args.auto_accept_validated:
        auto_accept(validated_path, reviewed_path)
    elif args.skip_review_apply:
        reviewed_path.parent.mkdir(parents=True, exist_ok=True)
        reviewed_path.write_text(validated_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Skipped review apply; copied validated objects -> {reviewed_path}")
    else:
        run_cmd(
            [
                sys.executable,
                str(review_script),
                "--objects",
                str(validated_path),
                "--reviews",
                str(reviews_path),
                "--output",
                str(reviewed_path),
            ]
        )

    statuses = resolve_publish_statuses(args.publish_mode, args.publish_status)
    export_cmd = [sys.executable, str(export_script), "--input", str(reviewed_path), "--output", str(jsonld_path)]
    wiki_cmd = [sys.executable, str(wiki_script), "--input", str(reviewed_path), "--output-dir", str(wiki_dir)]
    for status in statuses:
        export_cmd.extend(["--include-status", status])
        wiki_cmd.extend(["--include-status", status])

    run_cmd(export_cmd)
    run_cmd(wiki_cmd)
    print("KG pipeline completed.")


if __name__ == "__main__":
    main()
