"""Run the deterministic screening engine against seeded products (no LLM)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.screening import run_screening  # noqa: E402
from app.store import Store  # noqa: E402


def main() -> None:
    store = Store()
    for product_id, tenant_id in (
        ("prd_granola", "tnt_northwind"),
        ("prd_trail_bar", "tnt_northwind"),
        ("prd_kids_pouch", "tnt_northwind"),
        ("prd_tahini_cups", "tnt_harbor"),
    ):
        result = run_screening(store.product_bundle(tenant_id, product_id))
        print(
            json.dumps(
                {
                    "product_id": product_id,
                    "grade": result["grade"],
                    "tier_a_pct": result["weight_coverage"]["tier_a_pct"],
                    "gap_count": len(result["gaps"]),
                    "blocking_gaps": [g["field"] for g in result["gaps"] if g.get("blocking")],
                    "peanut": next(r for r in result["allergen_matrix"] if r["allergen"] == "peanut"),
                    "tree_nut": next(r for r in result["allergen_matrix"] if r["allergen"] == "tree_nut"),
                },
                indent=2,
            )
        )
        print("---")


if __name__ == "__main__":
    main()
