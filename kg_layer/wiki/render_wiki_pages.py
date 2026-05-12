import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def render_template(template: str, obj: Dict) -> str:
    out = template
    for k, v in obj.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Render wiki markdown pages from accepted reviewed objects.")
    parser.add_argument("--input", required=True, help="Reviewed objects JSON path.")
    parser.add_argument("--output-dir", required=True, help="Output wiki directory.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    objs: List[Dict] = json.loads(input_path.read_text(encoding="utf-8"))
    accepted = [o for o in objs if o.get("review_status") == "accepted"]

    base_dir = Path(__file__).resolve().parent
    concept_tpl = (base_dir / "templates" / "concept_page.md").read_text(encoding="utf-8")
    claim_tpl = (base_dir / "templates" / "claim_page.md").read_text(encoding="utf-8")

    output_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for obj in accepted:
        t = obj.get("type")
        if t == "Concept":
            tpl = concept_tpl
        elif t == "Claim":
            tpl = claim_tpl
        else:
            # Skip non-wiki-mapped types in the minimal pilot.
            continue

        page = render_template(tpl, obj)
        fname = f"{slugify(str(obj.get('id', 'item')))}.md"
        (output_dir / fname).write_text(page, encoding="utf-8")
        count += 1

    print(f"Rendered {count} wiki pages to {output_dir}")


if __name__ == "__main__":
    main()
