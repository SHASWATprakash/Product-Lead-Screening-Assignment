"""Unstructured-notes extractor. The LLM proposes patches; apply is explicit."""
from __future__ import annotations

import json
import re
from typing import Any

from app import llm_client
from app.store import Store

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

EXTRACT_SYSTEM = """You extract structured allergen/spec claims from messy operations notes \
for a food co-manufacturer. You do not invent facts.

Return ONLY a JSON object with this shape:
{
  "summary": "one paragraph of what you understood",
  "patches": [
    {
      "target": "ingredient" | "facility" | "product",
      "id": "use an id from the provided catalogue if you can match it, else null",
      "name_hint": "the name as it appears in the notes",
      "fields": {
        "field_name": {"value": ..., "source": "short quote or paraphrase from the notes"}
      },
      "confidence": "high" | "medium" | "low",
      "needs_human_confirm": true
    }
  ],
  "unresolved": ["anything you could not map to a catalogue entity"],
  "warnings": ["liability or overclaim risks, e.g. a requested peanut-free claim"]
}

Allowed field names:
- ingredient: declared_allergens, cross_contact_allergens, process_aids, spec_sheet_date, supplier_name
- facility: validated_changeover_sop_id, allergen_control_plan_id, shared_line_allergens
- product: label_claims, intended_market

Allergen values must be from: milk, egg, fish, shellfish, tree_nut, peanut, wheat, soy, sesame.
Process-aid values are free text slugs like sulfites, ascorbic_acid.
declared_allergens / cross_contact_allergens / process_aids / shared_line_allergens / label_claims are arrays.
If a spec was promised but not received, do NOT fill declared_allergens as empty — put it in unresolved.
Do not copy an old supplier's statement onto a new supplier.
"""


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).rstrip("`").strip()
    match = _JSON_RE.search(text)
    if not match:
        raise ValueError("Model did not return JSON")
    return json.loads(match.group(0))


def _match_entity(store: Store, tenant_id: str, patch: dict, product: dict | None) -> dict | None:
    target = patch.get("target")
    if patch.get("id"):
        try:
            if target == "ingredient":
                return store.get_ingredient(tenant_id, patch["id"])
            if target == "facility":
                return store.get_facility(tenant_id, patch["id"])
            if target == "product":
                return store.get_product(tenant_id, patch["id"])
        except Exception:
            pass
    hint = (patch.get("name_hint") or "").lower()
    if not hint:
        return None
    if target == "ingredient":
        for ing in store.list_ingredients(tenant_id):
            if ing["name"].lower() in hint or hint in ing["name"].lower() or (ing.get("supplier_name") or "").lower() in hint:
                return ing
    if target == "facility" and product:
        return store.get_facility(tenant_id, product["facility_id"])
    if target == "product" and product:
        return product
    return None


def extract_notes(
    store: Store,
    tenant_id: str,
    notes: str,
    product_id: str | None,
    apply: bool,
) -> dict[str, Any]:
    product = store.get_product(tenant_id, product_id) if product_id else None
    facility = store.get_facility(tenant_id, product["facility_id"]) if product else None
    ingredients = []
    if product:
        ingredients = [store.get_ingredient(tenant_id, line["ingredient_id"]) for line in product["recipe"]]
    else:
        ingredients = store.list_ingredients(tenant_id)

    catalogue = {
        "product": {"id": product["id"], "name": product["name"]} if product else None,
        "facility": {"id": facility["id"], "name": facility["name"]} if facility else None,
        "ingredients": [
            {"id": i["id"], "name": i["name"], "supplier_name": i.get("supplier_name")} for i in ingredients
        ],
    }
    cards = store.search_cards(notes, limit=4)

    user = (
        "Catalogue (only attach patches to these ids):\n"
        + json.dumps(catalogue, indent=2)
        + "\n\nRelevant spec cards:\n"
        + json.dumps(cards, indent=2)
        + "\n\nNotes:\n"
        + notes
    )
    raw = llm_client.chat(
        [
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": user},
        ]
    )
    try:
        parsed = _parse_json(raw.get("content") or "")
    except (ValueError, json.JSONDecodeError) as exc:
        return {
            "status": "parse_failed",
            "error": str(exc),
            "raw": raw.get("content"),
            "proposals": [],
            "applied": [],
        }

    proposals = []
    applied = []
    for patch in parsed.get("patches") or []:
        entity = _match_entity(store, tenant_id, patch, product)
        proposal = {
            **patch,
            "matched_id": entity["id"] if entity else None,
            "matched_name": entity.get("name") if entity else None,
        }
        proposals.append(proposal)
        if apply and entity and patch.get("fields"):
            from app.models import FieldPatch

            fields = {}
            for name, spec in patch["fields"].items():
                if not isinstance(spec, dict) or "value" not in spec:
                    continue
                fields[name] = FieldPatch(
                    value=spec["value"],
                    source=spec.get("source") or "extracted from notes (unconfirmed)",
                    tier="B",
                )
            if not fields:
                continue
            if patch.get("target") == "ingredient":
                row = store.patch_ingredient(tenant_id, entity["id"], fields)
            elif patch.get("target") == "facility":
                row = store.patch_facility(tenant_id, entity["id"], fields)
            else:
                row = store.patch_product(tenant_id, entity["id"], fields)
            applied.append({"id": entity["id"], "target": patch.get("target"), "fields": list(fields)})
            proposal["applied_snapshot"] = row.get("fields")

    return {
        "status": "ok",
        "summary": parsed.get("summary"),
        "warnings": parsed.get("warnings") or [],
        "unresolved": parsed.get("unresolved") or [],
        "proposals": proposals,
        "applied": applied,
        "cards_consulted": [c["id"] for c in cards],
        "note": (
            "Proposals are Tier B (extracted, unconfirmed) when applied. "
            "The UI should let a human confirm and re-PATCH as Tier A with a primary source."
        ),
    }
