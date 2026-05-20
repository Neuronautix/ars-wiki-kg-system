import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
EXPORTER = REPO_ROOT / "kg_layer" / "ars_export" / "export_kg_candidates.py"
LOCAL_VALIDATOR = REPO_ROOT / "kg_layer" / "validation" / "validate_ars_handoff.py"
ARS_V1_VALIDATOR = REPO_ROOT / "vendor" / "academic-research-skills" / "scripts" / "check_kg_handoff.py"


class TestExportKgCandidates(unittest.TestCase):
    def write_article(self, tmp: Path) -> Path:
        article = tmp / "article.md"
        article.write_text(
            "# Demo Article\n\n"
            "## Discussion\n\n"
            "AI-assisted formative assessment improved completion outcomes.\n",
            encoding="utf-8",
        )
        return article

    def write_claim_report_json(self, tmp: Path) -> Path:
        report = tmp / "claim_verification_report.json"
        report.write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "report_id": "cvr-001",
                    "article_id": "article-123",
                    "run_id": "run-001",
                    "mode": "pre-review",
                    "generated_at": "2026-05-19T18:10:00Z",
                    "summary": {
                        "total_claims_checked": 1,
                        "verdict_counts": {
                            "VERIFIED": 1,
                            "MINOR_DISTORTION": 0,
                            "MAJOR_DISTORTION": 0,
                            "UNVERIFIABLE": 0,
                            "UNVERIFIABLE_ACCESS": 0,
                        },
                        "overall_verdict": "PASS",
                    },
                    "claims": [
                        {
                            "claim_id": "claim:article-123:c001",
                            "claim_registry_row": 1,
                            "claim_text": "AI-assisted formative assessment improved completion outcomes.",
                            "section": "Discussion",
                            "source_anchor": "sec:discussion:p1",
                            "cited_source_ids": ["S02"],
                            "verdict": "VERIFIED",
                            "severity": "NONE",
                            "confidence": 0.91,
                            "rationale": "Source and manuscript numbers align.",
                            "kg_review_update": {
                                "kg_item_id": "claim:article-123:c001",
                                "old_status": "in_review",
                                "new_status": "accepted",
                                "reviewer_notes": "Verified.",
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return report

    def write_claim_report_markdown(self, tmp: Path) -> Path:
        report = tmp / "claim_verification_report.md"
        report.write_text(
            "| Claim | Section | Source | Verdict | Detail |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| Markdown claim remains supported. | Discussion | https://example.org/source | VERIFIED | Source aligns. |\n",
            encoding="utf-8",
        )
        return report

    def run_exporter(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(EXPORTER), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )

    def test_json_claim_report_exports_legacy_handoff_with_v1_fields(self) -> None:
        with TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            output_dir = tmp / "out"
            result = self.run_exporter(
                "--article",
                str(self.write_article(tmp)),
                "--claim-verification-report",
                str(self.write_claim_report_json(tmp)),
                "--output-dir",
                str(output_dir),
                "--article-id",
                "article-123",
                "--run-id",
                "run-001",
                "--reviewed-at",
                "2026-05-19T18:10:00Z",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            output = output_dir / "article-123.kg_candidates.json"
            payload = json.loads(output.read_text(encoding="utf-8"))
            claim = next(item for item in payload["items"] if item["type"] == "Claim")
            evidence = next(item for item in payload["items"] if item["type"] == "Evidence")

            self.assertEqual(payload["schema_version"], "1.1.0")
            self.assertEqual(claim["id"], "claim:article-123:c001")
            self.assertEqual(claim["review_status"], "accepted")
            self.assertEqual(claim["source_anchor"], "sec:discussion:p1")
            self.assertEqual(claim["source_citation_id"], "S02")
            self.assertEqual(claim["cited_source_ids"], ["S02"])
            self.assertNotIn("citation_ids", claim)
            self.assertEqual(claim["related_evidence_ids"], [evidence["id"]])
            self.assertIn("Verified.", claim["reviewer_notes"])

            validation = subprocess.run(
                [sys.executable, str(LOCAL_VALIDATOR), str(output)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(validation.returncode, 0, msg=validation.stdout + validation.stderr)

    def test_markdown_claim_report_still_exports_legacy_handoff(self) -> None:
        with TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            output_dir = tmp / "out"
            result = self.run_exporter(
                "--article",
                str(self.write_article(tmp)),
                "--claim-verification-report",
                str(self.write_claim_report_markdown(tmp)),
                "--output-dir",
                str(output_dir),
                "--article-id",
                "markdown-article",
                "--run-id",
                "run-001",
                "--reviewed-at",
                "2026-05-19T18:10:00Z",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            output = output_dir / "markdown-article.kg_candidates.json"
            payload = json.loads(output.read_text(encoding="utf-8"))
            claim = next(item for item in payload["items"] if item["type"] == "Claim")

            self.assertEqual(payload["schema_version"], "1.1.0")
            self.assertEqual(claim["supporting_quote_or_span"], "Markdown claim remains supported.")
            self.assertEqual(claim["review_status"], "accepted")
            self.assertEqual(claim["source_citation"], "https://example.org/source")

            validation = subprocess.run(
                [sys.executable, str(LOCAL_VALIDATOR), str(output)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(validation.returncode, 0, msg=validation.stdout + validation.stderr)

    def test_json_claim_report_exports_ars_v1_handoff(self) -> None:
        with TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            output_dir = tmp / "out"
            result = self.run_exporter(
                "--article",
                str(self.write_article(tmp)),
                "--claim-verification-report",
                str(self.write_claim_report_json(tmp)),
                "--output-dir",
                str(output_dir),
                "--article-id",
                "article-123",
                "--run-id",
                "run-001",
                "--reviewed-at",
                "2026-05-19T18:10:00Z",
                "--handoff-schema",
                "ars_v1",
                "--ars-version",
                "v3.7.0",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            output = output_dir / "article-123.kg_candidates.json"
            payload = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(payload["schema_version"], "1.0.0")
            self.assertEqual(payload["run_metadata"]["pipeline_stage"], "2.5")
            self.assertEqual(payload["links"][0]["relation_type"], "claim_supported_by_evidence")
            claim = next(item for item in payload["items"] if item["type"] == "Claim")
            self.assertEqual(claim["source_anchor"], "sec:discussion:p1")
            self.assertEqual(claim["source_citation_id"], "S02")
            self.assertEqual(claim["confidence_rationale"], "Source and manuscript numbers align.")
            self.assertEqual(claim["review_decision"]["rationale"], "Verified.")

            validation = subprocess.run(
                [sys.executable, str(ARS_V1_VALIDATOR), str(output)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(validation.returncode, 0, msg=validation.stdout + validation.stderr)


if __name__ == "__main__":
    unittest.main()
