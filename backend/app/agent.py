"""Small tool-using agent over tenant-scoped catalogue + spec cards.

Used by POST /v1/agent:ask. Screening itself does not call this.
"""
from __future__ import annotations

import json
from typing import Any, Callable

from app import config, llm_client
from app.store import Store

SYSTEM = """You are a Lotwise spec assistant for one tenant. You answer by calling tools \
and then writing a short, concrete answer. Never invent ids, allergens, or grades.

Rules:
- Call tools until you can answer. Then reply in plain text with no tool call.
- Only state facts that appear in a tool result. If a field is gapped, say it is gapped.
- Do not claim a product is peanut-free unless the screening matrix or source data says not_detected at a named tier.
- Prefer citing ingredient ids, facility ids, and spec card ids.
- If the question asks for a labelled grade, tell the user to run POST /v1/screenings:generate rather than guessing.
"""


def _tools(store: Store, tenant_id: str, default_product_id: str | None) -> tuple[list[dict], dict[str, Callable]]:
    def get_product(product_id: str | None = None) -> dict:
        pid = product_id or default_product_id
        if not pid:
            return {"error": "product_id required"}
        bundle = store.product_bundle(tenant_id, pid)
        return {
            "product": bundle["product"],
            "facility_id": bundle["facility"]["id"],
            "ingredient_ids": [i["id"] for i in bundle["ingredients"]],
        }

    def get_facility(facility_id: str) -> dict:
        return store.get_facility(tenant_id, facility_id)

    def get_ingredient(ingredient_id: str) -> dict:
        return store.get_ingredient(tenant_id, ingredient_id)

    def search_spec_cards(query: str) -> dict:
        return {"cards": store.search_cards(query, limit=4)}

    def list_products() -> dict:
        return {
            "products": [
                {"id": p["id"], "name": p["name"], "sku": p["sku"], "status": p["status"], "facility_id": p["facility_id"]}
                for p in store.list_products(tenant_id)
            ]
        }

    def latest_screening(product_id: str | None = None) -> dict:
        pid = product_id or default_product_id
        rows = store.list_screenings(tenant_id, pid)
        if not rows:
            return {"error": "no screening runs yet; generate one first"}
        run = rows[0]
        return {
            "run_id": run["run_id"],
            "status": run["status"],
            "grade": (run.get("result") or {}).get("grade"),
            "tier_a_pct": ((run.get("result") or {}).get("weight_coverage") or {}).get("tier_a_pct"),
            "gap_count": len((run.get("result") or {}).get("gaps") or []),
        }

    impl = {
        "get_product": get_product,
        "get_facility": get_facility,
        "get_ingredient": get_ingredient,
        "search_spec_cards": search_spec_cards,
        "list_products": list_products,
        "latest_screening": latest_screening,
    }
    schemas = [
        {
            "type": "function",
            "function": {
                "name": "list_products",
                "description": "List this tenant's products (id, name, sku, status).",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_product",
                "description": "Get a product plus facility_id and ingredient ids.",
                "parameters": {
                    "type": "object",
                    "properties": {"product_id": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_facility",
                "description": "Get a facility profile with provenanced fields.",
                "parameters": {
                    "type": "object",
                    "properties": {"facility_id": {"type": "string"}},
                    "required": ["facility_id"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_ingredient",
                "description": "Get an ingredient with provenanced allergen/spec fields.",
                "parameters": {
                    "type": "object",
                    "properties": {"ingredient_id": {"type": "string"}},
                    "required": ["ingredient_id"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_spec_cards",
                "description": "Keyword search over the shared spec-card set (the 'brain' knowledge).",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "latest_screening",
                "description": "Return the latest screening run summary for a product, if any.",
                "parameters": {
                    "type": "object",
                    "properties": {"product_id": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
        },
    ]
    return schemas, impl


def ask(store: Store, tenant_id: str, question: str, product_id: str | None) -> dict[str, Any]:
    schemas, impl = _tools(store, tenant_id, product_id)
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]
    trace: list[dict] = []

    for step in range(1, config.MAX_AGENT_STEPS + 1):
        assistant = llm_client.chat(messages, tools=schemas)
        tool_calls = assistant.get("tool_calls") or []
        if not tool_calls:
            return {
                "answer": assistant.get("content") or "",
                "trace": trace,
                "steps": step,
            }

        messages.append(
            {
                "role": "assistant",
                "content": assistant.get("content"),
                "tool_calls": tool_calls,
            }
        )
        for call in tool_calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
            except json.JSONDecodeError as exc:
                result = {"error": f"invalid json arguments: {exc}"}
                args = {}
            else:
                fn = impl.get(name)
                if fn is None:
                    result = {"error": f"unknown tool {name}"}
                else:
                    try:
                        result = fn(**args)
                    except Exception as exc:  # noqa: BLE001
                        result = {"error": str(exc)}
            trace.append({"step": step, "tool": name, "arguments": args, "result_preview": _preview(result)})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(result, default=str),
                }
            )

    return {
        "answer": "Reached the maximum number of agent steps without a final answer.",
        "trace": trace,
        "steps": config.MAX_AGENT_STEPS,
    }


def _preview(result: Any) -> Any:
    dumped = json.dumps(result, default=str)
    if len(dumped) <= 400:
        return result
    return dumped[:400] + "…"
