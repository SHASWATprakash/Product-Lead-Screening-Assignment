"""Extraction response handling without a live Ollama dependency."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from app.extract import extract_notes
from app.store import Store


class ExtractNotesTests(unittest.TestCase):
    def test_requests_json_mode_and_leaves_profiles_unchanged_for_review(self) -> None:
        store = Store()
        response = {
            "summary": "Supplier evidence is incomplete.",
            "patches": [],
            "unresolved": ["Await supplier specifications."],
            "warnings": ["Do not reuse the previous oil specification."],
        }

        with patch("app.extract.llm_client.chat", return_value={"content": json.dumps(response)}) as chat:
            result = extract_notes(
                store,
                "tnt_northwind",
                "Supplier specifications are pending.",
                "prd_trail_bar",
                apply=False,
            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["proposals"], [])
        self.assertEqual(result["unresolved"], ["Await supplier specifications."])
        self.assertEqual(result["warnings"], ["Do not reuse the previous oil specification."])
        self.assertTrue(chat.call_args.kwargs["json_mode"])
        self.assertEqual(chat.call_args.kwargs["max_tokens"], 1400)
        self.assertEqual(chat.call_args.kwargs["timeout"], 120)

    def test_ignores_metadata_that_the_model_places_inside_fields(self) -> None:
        store = Store()
        response = {
            "summary": "Honey evidence requires review.",
            "patches": [{
                "target": "ingredient",
                "id": "ing_honey",
                "fields": {
                    "supplier_name": {"value": "Meadowbrook Apiaries", "source": "Supplier QA email"},
                    "needs_human_confirm": {"value": True},
                    "confidence": {"value": "medium"},
                },
                "confidence": "medium",
                "needs_human_confirm": True,
            }],
            "unresolved": [],
            "warnings": [],
        }

        with patch("app.extract.llm_client.chat", return_value={"content": json.dumps(response)}):
            result = extract_notes(store, "tnt_northwind", "Honey supplier changed.", "prd_trail_bar", apply=False)

        self.assertEqual(result["proposals"][0]["fields"], {"supplier_name": {"value": "Meadowbrook Apiaries", "source": "Supplier QA email"}})
        self.assertIn("Ignored unsupported extracted fields: confidence, needs_human_confirm.", result["warnings"])

    def test_rejects_empty_arrays_that_are_only_inferred_from_missing_evidence(self) -> None:
        store = Store()
        response = {
            "summary": "Sunflower oil specification is pending.",
            "patches": [{
                "target": "ingredient",
                "id": "ing_sunflower_oil",
                "fields": {"process_aids": {"value": [], "source": "No process aids mentioned for this ingredient."}},
                "confidence": "low",
                "needs_human_confirm": True,
            }],
            "unresolved": ["Sunflower oil specification pending."],
            "warnings": [],
        }

        with patch("app.extract.llm_client.chat", return_value={"content": json.dumps(response)}):
            result = extract_notes(store, "tnt_northwind", "Sunflower oil spec pending.", "prd_trail_bar", apply=False)

        self.assertEqual(result["proposals"], [])
        self.assertIn("Ignored unsupported extracted fields: process_aids.", result["warnings"])


if __name__ == "__main__":
    unittest.main()
