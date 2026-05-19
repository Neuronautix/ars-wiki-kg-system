import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List

try:
    from kg_layer.exports.jsonld_utils import DEFAULT_BASE_IRI
except ModuleNotFoundError:
    DEFAULT_BASE_IRI = "https://neuronautix.github.io/ars-wiki-kg-system/kg/"

ALL_STATUSES = ["pending", "in_review", "accepted", "rejected", "needs_revision"]
DRAFT_STATUSES = ["pending", "in_review", "accepted", "needs_revision"]
AUTO_REVIEWER = "pipeline_auto"
KG_SCHEMA_VERSION = "1.1.0"
KG_CONTRACT_VERSION = "1.1"


def add_bool_arg(parser: argparse.ArgumentParser, name: str, default: bool, help_text: str) -> None:
    parser.add_argument(name, dest=name.lstrip("-").replace("-", "_"), action="store_true", help=help_text)
    parser.add_argument(
        f"--no-{name.lstrip('-')}",
        dest=name.lstrip("-").replace("-", "_"),
        action="store_false",
        help=f"Disable: {help_text}",
    )
    parser.set_defaults(**{name.lstrip("-").replace("-", "_"): default})


def run_cmd(args: List[str]) -> None:
    subprocess.run(args, check=True)


def resolve_repo_path(repo_root: Path, path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else (repo_root / path)


def run_handoff_validation(repo_root: Path, structured_input_dir: Path) -> None:
    validate_handoff_script = repo_root / "kg_layer" / "validation" / "validate_ars_handoff.py"
    result = subprocess.run([sys.executable, str(validate_handoff_script), str(structured_input_dir)])
    if result.returncode:
        raise SystemExit(result.returncode)


def run_semantic_validation(repo_root: Path, paths: List[Path]) -> None:
    validate_semantics_script = repo_root / "kg_layer" / "validation" / "validate_semantics.py"
    result = subprocess.run([sys.executable, str(validate_semantics_script), *(str(path) for path in paths)])
    if result.returncode:
        raise SystemExit(result.returncode)


def list_markdown_files(input_dir: Path, include_glob: List[str], exclude_glob: List[str]) -> List[Path]:
    files = sorted([*input_dir.rglob("*.md"), *input_dir.rglob("*.markdown")])

    def rel_path(path: Path) -> str:
        return path.relative_to(input_dir).as_posix()

    def matches_any(path: Path, globs: List[str]) -> bool:
        rel = rel_path(path)
        return any(fnmatch(rel, g) for g in globs)

    if include_glob:
        files = [p for p in files if matches_any(p, include_glob)]
    if exclude_glob:
        files = [p for p in files if not matches_any(p, exclude_glob)]
    return files


def validate_structured_input_dir(structured_input_dir: Path) -> None:
    if not structured_input_dir.exists():
        raise SystemExit(f"Structured input directory not found: {structured_input_dir}")
    if not structured_input_dir.is_dir():
        raise SystemExit(f"Structured input path is not a directory: {structured_input_dir}")


def list_structured_files(structured_input_dir: Path) -> List[Path]:
    """Return all *.kg_candidates.json files in the structured input directory."""
    validate_structured_input_dir(structured_input_dir)
    return sorted(structured_input_dir.glob("*.kg_candidates.json"))


def build_snapshot(
    input_dir: Path,
    include_glob: List[str],
    exclude_glob: List[str],
    reviews_path: Path,
    structured_input_dir: Path = None,
) -> Dict[str, float]:
    snapshot: Dict[str, float] = {}
    for path in list_markdown_files(input_dir, include_glob, exclude_glob):
        try:
            snapshot[str(path)] = path.stat().st_mtime
        except FileNotFoundError:
            continue
    if reviews_path.exists():
        snapshot[str(reviews_path)] = reviews_path.stat().st_mtime
    if structured_input_dir is not None:
        for path in list_structured_files(structured_input_dir):
            try:
                snapshot[str(path)] = path.stat().st_mtime
            except FileNotFoundError:
                continue
    return snapshot


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
    reviewed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    for obj in objects:
        obj["review_status"] = "accepted"
        obj["reviewer_notes"] = obj.get("reviewer_notes") or "Auto-accepted by pipeline run."
        obj["reviewer"] = AUTO_REVIEWER
        obj["reviewed_at"] = reviewed_at
    reviewed_path.parent.mkdir(parents=True, exist_ok=True)
    reviewed_path.write_text(json.dumps(objects, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Auto-accepted {len(objects)} validated objects -> {reviewed_path}")


def run_once(args) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    data_root = resolve_repo_path(repo_root, args.data_root).resolve()
    input_dir = resolve_repo_path(repo_root, args.input_dir).resolve()
    reviews_path = resolve_repo_path(repo_root, args.reviews).resolve()

    structured_input_dir: Path = None
    if args.structured_input_dir:
        structured_input_dir = resolve_repo_path(repo_root, args.structured_input_dir).resolve()

    if args.merge_structured_and_markdown and not structured_input_dir:
        raise SystemExit("--merge-structured-and-markdown requires --structured-input-dir")

    candidates_path = data_root / "normalized" / "candidates.json"
    validated_path = data_root / "normalized" / "candidates.validated.json"
    reviewed_path = data_root / "reviewed" / "reviewed.json"
    review_queue_path = data_root / "review_queue" / "review_queue.json"
    jsonld_path = data_root / "published" / "graph.jsonld"
    strict_jsonld_path = data_root / "published" / "graph.accepted.jsonld"
    draft_jsonld_path = data_root / "published" / "graph.draft.jsonld"
    wiki_dir = data_root / "published" / "wiki"
    per_article_dir = data_root / "published" / "per_article"
    constraints_dir = data_root / "published" / "constraints"
    quality_dir = data_root / "published" / "quality"
    release_metadata_path = quality_dir / "release_metadata.json"
    quality_report_path = quality_dir / "run_quality_report.json"
    trend_report_path = quality_dir / "quality_trends.json"

    extract_script = repo_root / "kg_layer" / "extraction" / "extract_candidates.py"
    ingest_script = repo_root / "kg_layer" / "extraction" / "ingest_structured.py"
    validate_script = repo_root / "kg_layer" / "validation" / "validate_candidates.py"
    review_script = repo_root / "kg_layer" / "review" / "apply_review.py"
    review_queue_script = repo_root / "kg_layer" / "review" / "build_review_queue.py"
    export_script = repo_root / "kg_layer" / "exports" / "export_jsonld.py"
    per_article_script = repo_root / "kg_layer" / "exports" / "export_per_article.py"
    constraints_script = repo_root / "kg_layer" / "exports" / "export_constraints.py"
    wiki_script = repo_root / "kg_layer" / "wiki" / "render_wiki_pages.py"
    quality_script = repo_root / "kg_layer" / "validation" / "quality_report.py"
    semantic_script = repo_root / "kg_layer" / "validation" / "validate_semantics.py"

    previous_reviewed_path = reviewed_path.with_suffix(".previous.json")
    had_previous_reviewed = reviewed_path.exists()
    if had_previous_reviewed:
        previous_reviewed_path.parent.mkdir(parents=True, exist_ok=True)
        previous_reviewed_path.write_text(reviewed_path.read_text(encoding="utf-8"), encoding="utf-8")

    try:
        # ── Extraction step ──────────────────────────────────────────────────
        # Determine whether to use structured input, markdown, or both.
        structured_files = list_structured_files(structured_input_dir) if structured_input_dir else []
        use_structured = bool(structured_files)
        use_markdown = (not use_structured) or args.merge_structured_and_markdown

        if use_structured and structured_input_dir is not None:
            run_handoff_validation(repo_root, structured_input_dir)

        if structured_input_dir and not use_structured:
            print(
                f"No *.kg_candidates.json files found in '{structured_input_dir}'; "
                "falling back to markdown extraction."
            )

        if use_structured and use_markdown:
            print("Merging structured ARS HITL artifacts with markdown extraction.")
        elif use_structured:
            print(f"Using structured ARS HITL artifacts from '{structured_input_dir}'.")
        else:
            print("Using markdown extraction.")

        # Collect candidates from each active source into temp files, then merge.
        candidate_parts: List[Path] = []

        if use_structured:
            structured_candidates = candidates_path.with_name("candidates.structured.json")
            ingest_cmd = [
                sys.executable,
                str(ingest_script),
                "--input-dir",
                str(structured_input_dir),
                "--output",
                str(structured_candidates),
            ]
            run_cmd(ingest_cmd)
            candidate_parts.append(structured_candidates)

        if use_markdown:
            markdown_candidates = candidates_path.with_name("candidates.markdown.json")
            extract_cmd = [
                sys.executable,
                str(extract_script),
                "--input-dir",
                str(input_dir),
                "--output",
                str(markdown_candidates),
            ]
            for glob_value in args.include_glob:
                extract_cmd.extend(["--include-glob", glob_value])
            for glob_value in args.exclude_glob:
                extract_cmd.extend(["--exclude-glob", glob_value])
            run_cmd(extract_cmd)
            candidate_parts.append(markdown_candidates)

        # Merge partial candidate lists into the main candidates file.
        if len(candidate_parts) == 1:
            # No merge needed; rename / copy directly.
            candidates_path.parent.mkdir(parents=True, exist_ok=True)
            candidates_path.write_text(
                candidate_parts[0].read_text(encoding="utf-8"), encoding="utf-8"
            )
        else:
            # Merge: structured first (preferred), then markdown.
            # Deduplicate by id — structured items win on collision.
            merged: List[Dict] = []
            seen_ids = set()
            for part in candidate_parts:
                for obj in json.loads(part.read_text(encoding="utf-8")):
                    obj_id = obj.get("id")
                    if obj_id not in seen_ids:
                        seen_ids.add(obj_id)
                        merged.append(obj)
            candidates_path.parent.mkdir(parents=True, exist_ok=True)
            candidates_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Merged {len(merged)} candidates from {len(candidate_parts)} sources.")

        # Clean up temp files.
        for part in candidate_parts:
            if part != candidates_path:
                part.unlink(missing_ok=True)

        # ── Validation ───────────────────────────────────────────────────────
        run_cmd([sys.executable, str(validate_script), "--input", str(candidates_path), "--output", str(validated_path)])

        # ── Review ───────────────────────────────────────────────────────────
        if args.auto_accept_validated:
            auto_accept(validated_path, reviewed_path)
        elif args.skip_review_apply:
            reviewed_path.parent.mkdir(parents=True, exist_ok=True)
            validated_objects = json.loads(validated_path.read_text(encoding="utf-8"))
            if args.publish_mode == "accepted" and not args.publish_status:
                reviewed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
                for obj in validated_objects:
                    obj["review_status"] = "accepted"
                    obj["reviewer_notes"] = obj.get("reviewer_notes") or "Auto-accepted in skip-review mode."
                    obj["reviewer"] = AUTO_REVIEWER
                    obj["reviewed_at"] = reviewed_at
            reviewed_path.write_text(json.dumps(validated_objects, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Skipped review apply; copied validated objects -> {reviewed_path}")
        else:
            review_cmd = [
                sys.executable,
                str(review_script),
                "--objects",
                str(validated_path),
                "--reviews",
                str(reviews_path),
                "--output",
                str(reviewed_path),
            ]
            if args.carry_forward_accepted and previous_reviewed_path.exists():
                review_cmd.extend(["--previous-reviewed", str(previous_reviewed_path), "--carry-forward-accepted"])
            run_cmd(review_cmd)

        # ── Review queue ─────────────────────────────────────────────────────
        queue_cmd = [
            sys.executable,
            str(review_queue_script),
            "--objects",
            str(reviewed_path),
            "--output",
            str(review_queue_path),
        ]
        if previous_reviewed_path.exists():
            queue_cmd.extend(["--previous-reviewed", str(previous_reviewed_path)])
        run_cmd(queue_cmd)

        # ── Semantic release gate ────────────────────────────────────────────
        run_cmd([sys.executable, str(semantic_script), str(reviewed_path)])

        # ── Quality reporting + release metadata ────────────────────────────
        run_cmd(
            [
                sys.executable,
                str(quality_script),
                "--input",
                str(reviewed_path),
                "--output",
                str(quality_report_path),
                "--trend-file",
                str(trend_report_path),
            ]
        )
        release_metadata = {
            "schema_version": KG_SCHEMA_VERSION,
            "contract_version": KG_CONTRACT_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "base_iri": args.base_iri,
            "publish_statuses": resolve_publish_statuses(args.publish_mode, args.publish_status),
            "quality_report": str(quality_report_path),
            "release_gate": "semantic_validation_passed",
        }
        quality_dir.mkdir(parents=True, exist_ok=True)
        release_metadata_path.write_text(
            json.dumps(release_metadata, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # ── Global export + wiki ─────────────────────────────────────────────
        publish_statuses = resolve_publish_statuses(args.publish_mode, args.publish_status)
        export_cmd = [
            sys.executable,
            str(export_script),
            "--input",
            str(reviewed_path),
            "--output",
            str(jsonld_path),
            "--base-iri",
            args.base_iri,
            "--metadata-file",
            str(release_metadata_path),
        ]
        wiki_cmd = [sys.executable, str(wiki_script), "--input", str(reviewed_path), "--output-dir", str(wiki_dir)]
        for status in publish_statuses:
            export_cmd.extend(["--include-status", status])
            wiki_cmd.extend(["--include-status", status])

        run_cmd(export_cmd)
        run_cmd(wiki_cmd)

        # Always publish strict accepted and draft graph artifacts.
        strict_cmd = [
            sys.executable,
            str(export_script),
            "--input",
            str(reviewed_path),
            "--output",
            str(strict_jsonld_path),
            "--base-iri",
            args.base_iri,
            "--metadata-file",
            str(release_metadata_path),
            "--include-status",
            "accepted",
        ]
        draft_cmd = [
            sys.executable,
            str(export_script),
            "--input",
            str(reviewed_path),
            "--output",
            str(draft_jsonld_path),
            "--base-iri",
            args.base_iri,
            "--metadata-file",
            str(release_metadata_path),
        ]
        for status in DRAFT_STATUSES:
            draft_cmd.extend(["--include-status", status])
        run_cmd(strict_cmd)
        run_cmd(draft_cmd)

        # ── Per-article export ───────────────────────────────────────────────
        per_article_cmd = [
            sys.executable,
            str(per_article_script),
            "--input",
            str(reviewed_path),
            "--output-dir",
            str(per_article_dir),
            "--base-iri",
            args.base_iri,
        ]
        for status in publish_statuses:
            per_article_cmd.extend(["--include-status", status])
        run_cmd(per_article_cmd)

        # ── Constraint artifacts ─────────────────────────────────────────────
        constraint_cmd = [
            sys.executable,
            str(constraints_script),
            "--input",
            str(reviewed_path),
            "--output-dir",
            str(constraints_dir / "selected"),
            "--base-iri",
            args.base_iri,
        ]
        for status in publish_statuses:
            constraint_cmd.extend(["--include-status", status])
        run_cmd(constraint_cmd)

        strict_constraint_cmd = [
            sys.executable,
            str(constraints_script),
            "--input",
            str(reviewed_path),
            "--output-dir",
            str(constraints_dir / "accepted"),
            "--base-iri",
            args.base_iri,
            "--include-status",
            "accepted",
        ]
        run_cmd(strict_constraint_cmd)

        draft_constraint_cmd = [
            sys.executable,
            str(constraints_script),
            "--input",
            str(reviewed_path),
            "--output-dir",
            str(constraints_dir / "draft"),
            "--base-iri",
            args.base_iri,
        ]
        for status in DRAFT_STATUSES:
            draft_constraint_cmd.extend(["--include-status", status])
        run_cmd(draft_constraint_cmd)

        print("KG pipeline completed.")
    finally:
        if had_previous_reviewed and previous_reviewed_path.exists():
            previous_reviewed_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full KG layer pipeline in one command.")
    parser.add_argument("--input-dir", default="kg_layer/data/raw", help="Input markdown directory.")
    parser.add_argument("--data-root", default="kg_layer/data", help="Base data directory for outputs.")
    parser.add_argument("--reviews", default="kg_layer/review/reviews.json", help="Review decisions JSON file.")
    parser.add_argument(
        "--base-iri",
        default=DEFAULT_BASE_IRI,
        help=f"Base IRI for JSON-LD exports. Defaults to {DEFAULT_BASE_IRI}",
    )
    parser.add_argument("--include-glob", action="append", default=[], help="Optional extraction include glob. Repeatable.")
    parser.add_argument("--exclude-glob", action="append", default=[], help="Optional extraction exclude glob. Repeatable.")
    parser.add_argument(
        "--structured-input-dir",
        default=None,
        help=(
            "Directory containing *.kg_candidates.json ARS HITL handoff files. "
            "When present and files exist, structured input is preferred over markdown extraction. "
            "A valid but empty directory falls back to markdown extraction."
        ),
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate --structured-input-dir handoff files and exit before extraction or publishing.",
    )
    parser.add_argument(
        "--semantic-validate-only",
        action="store_true",
        help=(
            "Run ontology-quality semantic validation and exit. Validates --structured-input-dir when set; "
            "otherwise validates the reviewed objects file under --data-root."
        ),
    )
    add_bool_arg(
        parser,
        "--merge-structured-and-markdown",
        default=False,
        help_text=(
            "Merge structured ARS HITL artifacts with markdown extraction instead of preferring one source. "
            "Requires --structured-input-dir."
        ),
    )
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
    add_bool_arg(
        parser,
        "--carry-forward-accepted",
        default=True,
        help_text="Carry forward prior accepted decisions when source spans are unchanged.",
    )
    parser.add_argument("--watch", action="store_true", help="Run continuously and re-run pipeline on input/review changes.")
    parser.add_argument("--poll-seconds", type=int, default=5, help="Polling interval in seconds for --watch mode.")
    review_mode_group = parser.add_mutually_exclusive_group()
    review_mode_group.add_argument(
        "--skip-review-apply",
        action="store_true",
        help="Skip apply_review and publish validated objects directly (auto-accepts when publish mode is accepted).",
    )
    review_mode_group.add_argument(
        "--auto-accept-validated",
        action="store_true",
        help="Set all validated objects to accepted before publishing.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    input_dir = resolve_repo_path(repo_root, args.input_dir).resolve()
    reviews_path = resolve_repo_path(repo_root, args.reviews).resolve()
    structured_input_dir: Path = None
    if args.structured_input_dir:
        structured_input_dir = resolve_repo_path(repo_root, args.structured_input_dir).resolve()

    if args.merge_structured_and_markdown and not structured_input_dir:
        raise SystemExit("--merge-structured-and-markdown requires --structured-input-dir")
    if args.validate_only and not structured_input_dir:
        raise SystemExit("--validate-only requires --structured-input-dir")
    if structured_input_dir:
        validate_structured_input_dir(structured_input_dir)

    if args.validate_only:
        run_handoff_validation(repo_root, structured_input_dir)
        return
    if args.semantic_validate_only:
        semantic_paths = [structured_input_dir] if structured_input_dir else [
            resolve_repo_path(repo_root, args.data_root).resolve() / "reviewed" / "reviewed.json"
        ]
        run_semantic_validation(repo_root, semantic_paths)
        return

    if not args.watch:
        run_once(args)
        return

    if args.poll_seconds < 1:
        raise SystemExit("--poll-seconds must be >= 1")

    print("Starting live KG sidecar mode (watch). Press Ctrl+C to stop.")
    last_snapshot: Dict[str, float] = {}
    while True:
        current_snapshot = build_snapshot(
            input_dir, args.include_glob, args.exclude_glob, reviews_path, structured_input_dir
        )
        if current_snapshot != last_snapshot:
            print("Detected change in ARS artifacts/reviews. Running pipeline...")
            try:
                run_once(args)
                last_snapshot = current_snapshot
            except subprocess.CalledProcessError as exc:
                print(f"Pipeline run failed with exit code {exc.returncode}; waiting for next change.")
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
