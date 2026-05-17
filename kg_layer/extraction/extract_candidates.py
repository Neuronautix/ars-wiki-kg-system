import argparse
import json
import re
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List, Tuple

CITATION_RE = re.compile(r"\(([^\)]+,\s*\d{4}[a-z]?)\)|\[[A-Z]?\d+\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def split_sections(text: str) -> List[Tuple[str, str]]:
    sections: List[Tuple[str, str]] = []
    current_heading = "Document"
    current_lines: List[str] = []

    for line in text.splitlines():
        m = HEADING_RE.match(line.strip())
        if m:
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines).strip()))
                current_lines = []
            current_heading = m.group(2).strip()
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    return sections


def sentence_split(block: str) -> List[str]:
    raw = re.split(r"(?<=[.!?])\s+", block)
    return [s.strip() for s in raw if s.strip()]


def build_object(object_type: str, object_id: str, source_document: str, source_section: str, span: str, confidence: float, method: str) -> Dict:
    return {
        "type": object_type,
        "id": object_id,
        "source_document": source_document,
        "source_section": source_section,
        "supporting_quote_or_span": span,
        "confidence": confidence,
        "extraction_method": method,
        "review_status": "pending",
        "reviewer_notes": ""
    }


def extract_from_file(path: Path) -> List[Dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    objs: List[Dict] = []

    paper_id = f"paper:{path.stem}"
    objs.append(
        build_object(
            "Paper",
            paper_id,
            str(path),
            "Document",
            f"Source document {path.name}",
            1.0,
            "file_ingestion"
        )
    )

    claim_idx = 1
    evidence_idx = 1
    concept_idx = 1

    sections = split_sections(text)
    seen_concepts = set()

    for section, content in sections:
        if not content:
            continue

        for sentence in sentence_split(content):
            if CITATION_RE.search(sentence):
                claim_id = f"claim:{path.stem}:{claim_idx}"
                claim_idx += 1
                objs.append(
                    build_object(
                        "Claim",
                        claim_id,
                        str(path),
                        section,
                        sentence[:1200],
                        0.7,
                        "regex_citation_sentence"
                    )
                )

                ev_id = f"evidence:{path.stem}:{evidence_idx}"
                evidence_idx += 1
                objs.append(
                    build_object(
                        "Evidence",
                        ev_id,
                        str(path),
                        section,
                        sentence[:1200],
                        0.65,
                        "sentence_as_evidence_proxy"
                    )
                )

        # Lightweight concept capture from title-case multiword spans.
        for match in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b", content):
            concept = match.group(1).strip()
            if len(concept.split()) < 2:
                continue
            key = concept.lower()
            if key in seen_concepts:
                continue
            seen_concepts.add(key)
            c_id = f"concept:{path.stem}:{concept_idx}"
            concept_idx += 1
            objs.append(
                build_object(
                    "Concept",
                    c_id,
                    str(path),
                    section,
                    concept,
                    0.5,
                    "title_case_phrase_heuristic"
                )
            )

    return objs


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract minimal candidate objects from markdown artifacts.")
    parser.add_argument("--input-dir", required=True, help="Directory containing markdown artifacts.")
    parser.add_argument("--output", required=True, help="Output JSON path for extracted candidates.")
    parser.add_argument(
        "--include-glob",
        action="append",
        default=[],
        help="Optional relative-path glob filter. Repeatable (e.g., --include-glob '*article*.md').",
    )
    parser.add_argument(
        "--exclude-glob",
        action="append",
        default=[],
        help="Optional relative-path glob exclusion. Repeatable.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output = Path(args.output)

    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")

    files = sorted([*input_dir.rglob("*.md"), *input_dir.rglob("*.markdown")])

    def rel_path(path: Path) -> str:
        return path.relative_to(input_dir).as_posix()

    def matches_any(path: Path, globs: List[str]) -> bool:
        rel = rel_path(path)
        return any(fnmatch(rel, g) for g in globs)

    if args.include_glob:
        files = [p for p in files if matches_any(p, args.include_glob)]
    if args.exclude_glob:
        files = [p for p in files if not matches_any(p, args.exclude_glob)]

    if not files:
        raise SystemExit("No markdown files found in input directory.")

    all_objs: List[Dict] = []
    for file_path in files:
        all_objs.extend(extract_from_file(file_path))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(all_objs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(all_objs)} objects to {output}")


if __name__ == "__main__":
    main()
