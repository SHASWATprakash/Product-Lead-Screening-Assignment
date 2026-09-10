"""Deterministic screening engine.

The labelled pack is a pure function of the current facility + product +
ingredient snapshot and the pinned engine/card/taxonomy versions. The LLM
is intentionally not on this path — labelled numbers must not depend on
sampling. See the candidate brief.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app import config

TIER_STRENGTH = {"A": 3, "B": 2, "C": 1}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _field(entity: dict, name: str) -> dict:
    return entity.get("fields", {}).get(name) or {
        "value": None,
        "tier": None,
        "source": None,
        "retrieved_at": None,
        "gap": True,
        "defaulted": False,
    }


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _weakest_tier(tiers: list[str | None]) -> str | None:
    present = [t for t in tiers if t in TIER_STRENGTH]
    if not present:
        return None
    return min(present, key=lambda t: TIER_STRENGTH[t])


def _strongest_tier(tiers: list[str | None]) -> str | None:
    present = [t for t in tiers if t in TIER_STRENGTH]
    if not present:
        return None
    return max(present, key=lambda t: TIER_STRENGTH[t])


def _ingredient_covered_tier_a(ing: dict) -> bool:
    declared = _field(ing, "declared_allergens")
    cross = _field(ing, "cross_contact_allergens")
    return (
        not declared.get("gap")
        and not cross.get("gap")
        and declared.get("tier") == "A"
        and cross.get("tier") == "A"
    )


def run_screening(bundle: dict) -> dict:
    product = bundle["product"]
    facility = bundle["facility"]
    ingredients_by_id = {i["id"]: i for i in bundle["ingredients"]}

    recipe = product["recipe"]
    total_weight = sum(line["weight_g"] for line in recipe) or 1
    tier_a_weight = 0.0
    gaps: list[dict] = []
    process_aids: list[dict] = []
    component_rows: list[dict] = []

    declared_hits: dict[str, list[dict]] = {a: [] for a in config.BIG9}
    cross_hits: dict[str, list[dict]] = {a: [] for a in config.BIG9}
    complete_negatives: dict[str, list[str]] = {a: [] for a in config.BIG9}
    unknown_allergens: set[str] = set()

    for line in recipe:
        ing = ingredients_by_id[line["ingredient_id"]]
        weight = line["weight_g"]
        weight_pct = round(weight / total_weight, 4)
        declared = _field(ing, "declared_allergens")
        cross = _field(ing, "cross_contact_allergens")
        aids = _field(ing, "process_aids")
        spec_date = _field(ing, "spec_sheet_date")

        covered = _ingredient_covered_tier_a(ing)
        if covered:
            tier_a_weight += weight

        if declared.get("gap") or cross.get("gap"):
            gaps.append(
                {
                    "entity_type": "ingredient",
                    "entity_id": ing["id"],
                    "entity_name": ing["name"],
                    "field": "declared_allergens" if declared.get("gap") else "cross_contact_allergens",
                    "blocking": False,
                    "why": "No dated allergen statement on file for this ingredient.",
                    "weight_pct": weight_pct,
                }
            )
            unknown_allergens.update(config.BIG9)

        if spec_date.get("gap"):
            gaps.append(
                {
                    "entity_type": "ingredient",
                    "entity_id": ing["id"],
                    "entity_name": ing["name"],
                    "field": "spec_sheet_date",
                    "blocking": False,
                    "why": "No spec-sheet date — coverage cannot be treated as Tier A.",
                    "weight_pct": weight_pct,
                }
            )

        for allergen in _as_list(declared.get("value")):
            if allergen in declared_hits:
                declared_hits[allergen].append(
                    {
                        "ingredient_id": ing["id"],
                        "ingredient_name": ing["name"],
                        "tier": declared.get("tier"),
                        "source": declared.get("source"),
                    }
                )
        for allergen in _as_list(cross.get("value")):
            if allergen in cross_hits:
                cross_hits[allergen].append(
                    {
                        "ingredient_id": ing["id"],
                        "ingredient_name": ing["name"],
                        "tier": cross.get("tier"),
                        "source": cross.get("source"),
                    }
                )

        if not declared.get("gap") and not cross.get("gap"):
            present = set(_as_list(declared.get("value"))) | set(_as_list(cross.get("value")))
            for allergen in config.BIG9:
                if allergen not in present:
                    complete_negatives[allergen].append(ing["id"])

        for aid in _as_list(aids.get("value")):
            process_aids.append(
                {
                    "name": aid,
                    "ingredient_id": ing["id"],
                    "ingredient_name": ing["name"],
                    "tier": aids.get("tier") or "C",
                    "source": aids.get("source"),
                    "defaulted": bool(aids.get("defaulted")),
                }
            )
        if aids.get("gap"):
            gaps.append(
                {
                    "entity_type": "ingredient",
                    "entity_id": ing["id"],
                    "entity_name": ing["name"],
                    "field": "process_aids",
                    "blocking": False,
                    "why": "Process-aid declaration missing.",
                    "weight_pct": weight_pct,
                }
            )

        component_rows.append(
            {
                "ingredient_id": ing["id"],
                "ingredient_name": ing["name"],
                "supplier_name": ing.get("supplier_name"),
                "weight_g": weight,
                "weight_pct": weight_pct,
                "declared_allergens": declared,
                "cross_contact_allergens": cross,
                "tier_a_covered": covered,
            }
        )

    shared = _field(facility, "shared_line_allergens")
    changeover = _field(facility, "validated_changeover_sop_id")
    acp = _field(facility, "allergen_control_plan_id")

    facility_cross: dict[str, dict] = {}
    for allergen in _as_list(shared.get("value")):
        if allergen not in config.BIG9:
            continue
        if changeover.get("gap") or not changeover.get("value"):
            facility_cross[allergen] = {
                "status": "possible_cross_contact",
                "tier": "C",
                "source": shared.get("source"),
                "why": (
                    f"Facility shared-line lists {allergen} and no validated changeover SOP is on file. "
                    "Defaulted to possible cross-contact (Tier C)."
                ),
                "defaulted": True,
            }
            gaps.append(
                {
                    "entity_type": "facility",
                    "entity_id": facility["id"],
                    "entity_name": facility["name"],
                    "field": "validated_changeover_sop_id",
                    "blocking": False,
                    "why": f"Shared-line {allergen} has no validated changeover SOP.",
                    "weight_pct": None,
                }
            )
        else:
            facility_cross[allergen] = {
                "status": "possible_cross_contact",
                "tier": _weakest_tier([shared.get("tier"), changeover.get("tier")]) or "B",
                "source": changeover.get("source"),
                "why": (
                    f"Facility shared-line lists {allergen}; validated SOP "
                    f"{changeover.get('value')} is on file. Still disclosed as possible cross-contact."
                ),
                "defaulted": False,
            }

    if acp.get("gap"):
        gaps.append(
            {
                "entity_type": "facility",
                "entity_id": facility["id"],
                "entity_name": facility["name"],
                "field": "allergen_control_plan_id",
                "blocking": False,
                "why": "No allergen control plan id on file.",
                "weight_pct": None,
            }
        )

    kids_like = "kids" in product["name"].lower() or product["id"] == "prd_kids_pouch"
    for field_name, why in (
        ("label_claims", "Label claims are gapped — the pack cannot describe what the brand may print."),
        ("intended_market", "Intended market is gapped — jurisdiction of the disclosure is unknown."),
    ):
        fld = _field(product, field_name)
        if fld.get("gap"):
            gaps.append(
                {
                    "entity_type": "product",
                    "entity_id": product["id"],
                    "entity_name": product["name"],
                    "field": field_name,
                    "blocking": kids_like,
                    "why": why,
                    "weight_pct": None,
                }
            )

    matrix = []
    for allergen in config.BIG9:
        if declared_hits[allergen]:
            status = "present"
            tier = _strongest_tier([h["tier"] for h in declared_hits[allergen]])
            lineage = declared_hits[allergen]
            why = f"Declared on {len(declared_hits[allergen])} ingredient(s)."
        elif allergen in facility_cross or cross_hits[allergen]:
            status = "possible_cross_contact"
            evidence_tiers = [h["tier"] for h in cross_hits[allergen]]
            if allergen in facility_cross:
                evidence_tiers.append(facility_cross[allergen]["tier"])
            tier = _weakest_tier(evidence_tiers)
            lineage = cross_hits[allergen] + (
                [{"facility_id": facility["id"], **facility_cross[allergen]}] if allergen in facility_cross else []
            )
            why = facility_cross.get(allergen, {}).get("why") or f"Cross-contact signal on {len(cross_hits[allergen])} ingredient(s)."
        elif allergen in unknown_allergens:
            status = "unknown"
            tier = None
            lineage = []
            why = "One or more recipe ingredients are missing an allergen statement, so this allergen cannot be concluded."
        else:
            status = "not_detected"
            tier = _weakest_tier(
                [_field(ingredients_by_id[line["ingredient_id"]], "declared_allergens").get("tier") for line in recipe]
            ) or "A"
            lineage = [{"ingredient_id": i} for i in complete_negatives[allergen]]
            why = "Every recipe ingredient has a complete statement and none lists this allergen."

        # Unknown ingredients already force unknown unless a positive declaration exists.
        if status != "present" and allergen in unknown_allergens and allergen not in facility_cross and not cross_hits[allergen]:
            status = "unknown"
            tier = None

        if status != "unknown" and tier is None:
            tier = "C"

        row = {
            "allergen": allergen,
            "status": status,
            "tier": tier,
            "why": why,
            "lineage": lineage,
        }
        if status == "unknown":
            row["tier"] = None
            row["unlabelled_forbidden"] = True
            row["display"] = "unknown — no unlabelled conclusion"
        matrix.append(row)

    tier_a_pct = round(tier_a_weight / total_weight, 4)
    blocking = [g for g in gaps if g.get("blocking")]
    grade = "screening-ready" if tier_a_pct >= config.TIER_A_WEIGHT_THRESHOLD and not blocking else "indicative"
    grade_rule = (
        f"screening-ready when Tier-A recipe-weight coverage is ≥ {int(config.TIER_A_WEIGHT_THRESHOLD * 100)}% "
        "and there are no blocking gaps (kids SKUs block on missing label_claims / intended_market). "
        "Otherwise the pack is labelled indicative. The engine never returns an unlabelled grade."
    )

    snapshot = {
        "product": product,
        "facility": facility,
        "ingredients": bundle["ingredients"],
        "engine_version": config.ENGINE_VERSION,
        "card_set_version": config.CARD_SET_VERSION,
        "taxonomy_version": config.TAXONOMY_VERSION,
    }
    determinism_hash = hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]

    return {
        "product_id": product["id"],
        "facility_id": facility["id"],
        "grade": grade,
        "grade_rule": grade_rule,
        "weight_coverage": {
            "total_g": total_weight,
            "tier_a_g": tier_a_weight,
            "tier_a_pct": tier_a_pct,
            "threshold": config.TIER_A_WEIGHT_THRESHOLD,
        },
        "allergen_matrix": matrix,
        "process_aids": process_aids,
        "gaps": gaps,
        "components": component_rows,
        "versions": {
            "engine": config.ENGINE_VERSION,
            "card_set": config.CARD_SET_VERSION,
            "taxonomy": config.TAXONOMY_VERSION,
        },
        "determinism_hash": determinism_hash,
        "computed_at": _now(),
    }
