"""In-memory store loaded from the JSON seed. Mutations live until process restart."""
from __future__ import annotations

import json
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(name: str) -> list | dict:
    path = DATA_DIR / name
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


class Store:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.tenants: dict[str, dict] = {t["id"]: t for t in _load("tenants.json")}
        self.users: dict[str, dict] = {u["id"]: u for u in _load("users.json")}
        self.facilities: dict[str, dict] = {f["id"]: f for f in _load("facilities.json")}
        self.products: dict[str, dict] = {p["id"]: p for p in _load("products.json")}
        self.ingredients: dict[str, dict] = {i["id"]: i for i in _load("ingredients.json")}
        self.spec_cards: list[dict] = list(_load("spec_cards.json"))
        self.sample_notes: dict[str, str] = dict(_load("sample_notes.json"))
        self.screenings: dict[str, dict] = {}
        self.idempotency: dict[tuple[str, str], str] = {}
        self.meter_events: list[dict] = []

    def get_user(self, user_id: str) -> dict | None:
        return deepcopy(self.users.get(user_id))

    def user_by_email(self, email: str) -> dict | None:
        needle = email.strip().lower()
        for user in self.users.values():
            if user["email"].lower() == needle:
                return deepcopy(user)
        return None

    def demo_users(self) -> list[dict]:
        out = []
        for user in self.users.values():
            tenant = self.tenants[user["tenant_id"]]
            out.append(
                {
                    "email": user["email"],
                    "name": user["name"],
                    "title": user["title"],
                    "role": user["role"],
                    "tenant_id": user["tenant_id"],
                    "tenant_name": tenant["name"],
                    "tenant_slug": tenant["slug"],
                }
            )
        return out

    def tenant(self, tenant_id: str) -> dict:
        t = self.tenants.get(tenant_id)
        if t is None:
            raise HTTPException(status_code=401, detail="Unknown tenant")
        return t

    def usage(self, tenant_id: str) -> dict:
        t = self.tenant(tenant_id)
        events = [e for e in self.meter_events if e["tenant_id"] == tenant_id]
        return {
            "tenant_id": tenant_id,
            "plan": t["plan"],
            "inference_budget": t["inference_budget"],
            "inference_used": t["inference_used"],
            "inference_remaining": round(t["inference_budget"] - t["inference_used"], 4),
            "events": events[-20:],
        }

    def charge(self, tenant_id: str, cost: float, meter_event: str, ref: str | None = None) -> None:
        with self._lock:
            t = self.tenants[tenant_id]
            remaining = t["inference_budget"] - t["inference_used"]
            if cost > remaining:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        f"Inference budget exceeded for tenant {tenant_id}: "
                        f"{remaining:.1f} remaining, this call costs {cost}. "
                        "Metering is the margin guardrail — the client must surface this, not retry blindly."
                    ),
                )
            t["inference_used"] = round(t["inference_used"] + cost, 4)
            self.meter_events.append(
                {
                    "at": _now(),
                    "tenant_id": tenant_id,
                    "event": meter_event,
                    "cost": cost,
                    "ref": ref,
                    "used_after": t["inference_used"],
                }
            )

    def _scoped(self, table: dict[str, dict], tenant_id: str) -> list[dict]:
        return [deepcopy(v) for v in table.values() if v["tenant_id"] == tenant_id]

    def list_facilities(self, tenant_id: str) -> list[dict]:
        return self._scoped(self.facilities, tenant_id)

    def list_products(self, tenant_id: str) -> list[dict]:
        return self._scoped(self.products, tenant_id)

    def list_ingredients(self, tenant_id: str) -> list[dict]:
        return self._scoped(self.ingredients, tenant_id)

    def get_facility(self, tenant_id: str, facility_id: str) -> dict:
        row = self.facilities.get(facility_id)
        if row is None or row["tenant_id"] != tenant_id:
            raise HTTPException(status_code=404, detail="Facility not found")
        return deepcopy(row)

    def get_product(self, tenant_id: str, product_id: str) -> dict:
        row = self.products.get(product_id)
        if row is None or row["tenant_id"] != tenant_id:
            raise HTTPException(status_code=404, detail="Product not found")
        return deepcopy(row)

    def get_ingredient(self, tenant_id: str, ingredient_id: str) -> dict:
        row = self.ingredients.get(ingredient_id)
        if row is None or row["tenant_id"] != tenant_id:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        return deepcopy(row)

    def product_bundle(self, tenant_id: str, product_id: str) -> dict:
        product = self.get_product(tenant_id, product_id)
        facility = self.get_facility(tenant_id, product["facility_id"])
        ingredients = [self.get_ingredient(tenant_id, line["ingredient_id"]) for line in product["recipe"]]
        return {"product": product, "facility": facility, "ingredients": ingredients}

    def apply_fields(self, table: dict[str, dict], tenant_id: str, entity_id: str, fields: dict[str, Any]) -> dict:
        with self._lock:
            row = table.get(entity_id)
            if row is None or row["tenant_id"] != tenant_id:
                raise HTTPException(status_code=404, detail="Entity not found")
            now = _now()
            for name, patch in fields.items():
                existing = row.setdefault("fields", {}).get(name, {})
                tier = patch.tier or "A"
                row["fields"][name] = {
                    "value": patch.value,
                    "tier": tier,
                    "source": patch.source,
                    "retrieved_at": now,
                    "gap": False,
                    "defaulted": False,
                    "previous_tier": existing.get("tier"),
                    "previous_source": existing.get("source"),
                }
            return deepcopy(row)

    def patch_facility(self, tenant_id: str, facility_id: str, fields: dict) -> dict:
        return self.apply_fields(self.facilities, tenant_id, facility_id, fields)

    def patch_product(self, tenant_id: str, product_id: str, fields: dict) -> dict:
        return self.apply_fields(self.products, tenant_id, product_id, fields)

    def patch_ingredient(self, tenant_id: str, ingredient_id: str, fields: dict) -> dict:
        return self.apply_fields(self.ingredients, tenant_id, ingredient_id, fields)

    def put_screening(self, run: dict) -> dict:
        with self._lock:
            self.screenings[run["run_id"]] = run
            return deepcopy(run)

    def get_screening(self, tenant_id: str, run_id: str) -> dict:
        run = self.screenings.get(run_id)
        if run is None or run["tenant_id"] != tenant_id:
            raise HTTPException(status_code=404, detail="Screening run not found")
        return deepcopy(run)

    def list_screenings(self, tenant_id: str, product_id: str | None = None) -> list[dict]:
        rows = [deepcopy(r) for r in self.screenings.values() if r["tenant_id"] == tenant_id]
        if product_id:
            rows = [r for r in rows if r.get("product_id") == product_id]
        rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return rows

    def remember_idempotency(self, tenant_id: str, key: str, run_id: str) -> None:
        with self._lock:
            self.idempotency[(tenant_id, key)] = run_id

    def lookup_idempotency(self, tenant_id: str, key: str) -> str | None:
        return self.idempotency.get((tenant_id, key))

    def search_cards(self, query: str, limit: int = 4) -> list[dict]:
        tokens = {t for t in query.lower().replace("/", " ").replace("-", " ").split() if len(t) > 2}
        scored: list[tuple[int, dict]] = []
        for card in self.spec_cards:
            hay = " ".join([card["id"], card["title"], " ".join(card["tags"]), card["body"]]).lower()
            score = sum(1 for t in tokens if t in hay)
            if score:
                scored.append((score, card))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [deepcopy(c) for _, c in scored[:limit]] or [deepcopy(c) for c in self.spec_cards[:2]]


_STORE: Store | None = None


def get_store() -> Store:
    global _STORE
    if _STORE is None:
        _STORE = Store()
    return _STORE
