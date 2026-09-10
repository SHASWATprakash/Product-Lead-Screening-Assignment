"""Regression coverage for screening generation idempotency."""
from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.store import Store, get_store


class ScreeningIdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store()
        app.dependency_overrides[get_store] = lambda: self.store
        self.client = TestClient(app)
        token_response = self.client.post("/v1/auth/token", json={"email": "maya@northwind.example"})
        self.assertEqual(token_response.status_code, 200)
        self.headers = {"Authorization": f"Bearer {token_response.json()['access_token']}"}

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.client.close()

    def test_repeated_key_returns_the_original_run_without_another_charge(self) -> None:
        before = self.client.get("/v1/usage", headers=self.headers).json()
        headers = {**self.headers, "Idempotency-Key": "idempotency-verification-key"}
        body = {"product_id": "prd_trail_bar"}

        first = self.client.post("/v1/screenings:generate", headers=headers, json=body)
        second = self.client.post("/v1/screenings:generate", headers=headers, json=body)
        after = self.client.get("/v1/usage", headers=self.headers).json()

        self.assertEqual(first.status_code, 202)
        self.assertEqual(second.status_code, 202)
        self.assertEqual(second.json()["run_id"], first.json()["run_id"])
        self.assertEqual(after["inference_used"], before["inference_used"] + 1)
        events = [event for event in after["events"] if event["event"] == "screenings:generate"]
        self.assertEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main()
