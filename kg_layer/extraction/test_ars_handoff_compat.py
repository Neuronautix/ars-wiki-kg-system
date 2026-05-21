import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from kg_layer.extraction.ars_handoff_adapter import adapt_handoff
from kg_layer.extraction.ingest_structured import ingest_file


def item(item_id: str, item_type: str, review_status: str = "pending") -> dict:
    return {
        "id": item_id,
        "type": item_type,
        "source_document": "article.md",
        "source_section": "Results",
        "supporting_quote_or_span": "Source span.",
        "confidence": 0.8,
        "extraction_method": "ars_hitl",
        "review_status": review_status,
    }


class TestArsHandoffCompatibility(unittest.TestCase):
    def test_adapt_handoff_maps_ars_verdict_statuses_and_reverse_contradiction_edges(self) -> None:
        payload = {
            "schema_version": "1.0.0",
            "article_id": "article-123",
            "run_id": "run-001",
            "items": [
                item("claim:article-123:c001", "Claim", "MAJOR_DISTORTION"),
                item("evidence:article-123:e001", "Evidence", "UNVERIFIABLE_ACCESS"),
            ],
            "links": [
                {
                    "id": "link-001",
                    "from_id": "claim:article-123:c001",
                    "to_id": "evidence:article-123:e001",
                    "relation_type": "claim_contradicted_by_evidence",
                    "polarity": "contradiction",
                    "confidence": 0.91,
                    "rationale": "Evidence contradicts the claim.",
                }
            ],
        }

        adapted = adapt_handoff(payload)
        claim = adapted["items"][0]
        evidence = adapted["items"][1]

        self.assertEqual(claim["review_status"], "rejected")
        self.assertEqual(evidence["review_status"], "in_review")
        self.assertIn(
            {
                "target_id": "evidence:article-123:e001",
                "relation_type": "contradicts",
                "confidence": 0.91,
                "source_link_id": "link-001",
                "polarity": "contradiction",
                "rationale": "Evidence contradicts the claim.",
            },
            claim["relation_edges"],
        )
        self.assertIn(
            {
                "target_id": "claim:article-123:c001",
                "relation_type": "contradicts",
                "confidence": 0.91,
                "source_link_id": "link-001",
                "polarity": "contradiction",
                "rationale": "Evidence contradicts the claim.",
            },
            evidence["relation_edges"],
        )

    def test_ingest_accepts_status_and_relation_aliases_from_newer_ars_payloads(self) -> None:
        payload = {
            "schema_version": "1.1.0",
            "contract_version": "1.1",
            "article_id": "article-123",
            "source_document": "article.md",
            "items": [
                {
                    **item("claim:article-123:c001", "Claim", "VERIFIED"),
                    "relation_edges": [
                        {
                            "target_id": "concept:article-123:qa",
                            "relation_type": "related_to_concept",
                            "confidence": 0.77,
                        }
                    ],
                },
                item("concept:article-123:qa", "Concept", "MINOR_DISTORTION"),
            ],
        }

        with TemporaryDirectory() as tmp_name:
            path = Path(tmp_name) / "article-123.kg_candidates.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            ingested = ingest_file(path)

        claim = next(obj for obj in ingested if obj["type"] == "Claim")
        concept = next(obj for obj in ingested if obj["type"] == "Concept")

        self.assertEqual(claim["review_status"], "accepted")
        self.assertEqual(claim["relation_edges"][0]["relation_type"], "relates_to_concept")
        self.assertEqual(concept["review_status"], "needs_revision")

    def test_ingest_accepts_current_ars_main_statuses_and_relation_types(self) -> None:
        payload = {
            "schema_version": "1.1.0",
            "contract_version": "1.1",
            "article_id": "article-123",
            "source_document": "article.md",
            "items": [
                {
                    **item("claim:article-123:c001", "Claim", "evidence_supported"),
                    "relation_edges": [
                        {
                            "target_id": "evidence:article-123:e001",
                            "relation_type": "reports_finding",
                            "confidence": 0.81,
                        },
                        {
                            "target_id": "concept:article-123:system",
                            "relation_type": "uses_system",
                            "confidence": 0.75,
                        },
                    ],
                },
                item("evidence:article-123:e001", "Evidence", "human_reviewed"),
                item("concept:article-123:system", "Concept", "superseded"),
            ],
        }

        with TemporaryDirectory() as tmp_name:
            path = Path(tmp_name) / "article-123.kg_candidates.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            ingested = ingest_file(path)

        statuses = {obj["id"]: obj["review_status"] for obj in ingested}
        self.assertEqual(statuses["claim:article-123:c001"], "evidence_supported")
        self.assertEqual(statuses["evidence:article-123:e001"], "human_reviewed")
        self.assertEqual(statuses["concept:article-123:system"], "superseded")

        claim = next(obj for obj in ingested if obj["type"] == "Claim")
        relation_types = {edge["relation_type"] for edge in claim["relation_edges"]}
        self.assertEqual(relation_types, {"reports_finding", "uses_system"})


if __name__ == "__main__":
    unittest.main()
