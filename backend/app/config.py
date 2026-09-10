"""Lotwise Core API — take-home mock for the Product Lead screening."""

from __future__ import annotations

import os

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:4b")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "ollama")
LLM_REQUEST_TIMEOUT_SECONDS = float(os.environ.get("LLM_REQUEST_TIMEOUT_SECONDS", "600"))
JWT_SECRET = os.environ.get("JWT_SECRET", "lotwise-takehome-not-a-real-secret")
JWT_TTL_SECONDS = int(os.environ.get("JWT_TTL_SECONDS", "86400"))
JWT_ALGORITHM = "HS256"

ENGINE_VERSION = "lotwise-core/1.0.0"
CARD_SET_VERSION = "allergen-cards/2026-06"
TAXONOMY_VERSION = "big9+process-aids/1"

SCREENING_COST = 1.0
EXTRACT_COST = 3.0
SPECS_QUERY_COST = 2.0
AGENT_ASK_COST = 4.0

MAX_AGENT_STEPS = int(os.environ.get("MAX_AGENT_STEPS", "6"))
SCREENING_DELAY_SECONDS = float(os.environ.get("SCREENING_DELAY_SECONDS", "1.2"))

TIER_A_WEIGHT_THRESHOLD = 0.80

BIG9 = (
    "milk",
    "egg",
    "fish",
    "shellfish",
    "tree_nut",
    "peanut",
    "wheat",
    "soy",
    "sesame",
)

ROLE_PERMS: dict[str, frozenset[str]] = {
    "ops_lead": frozenset(
        {
            "profiles:read",
            "profiles:write",
            "screenings:run",
            "extract:run",
            "agent:ask",
            "export:read",
        }
    ),
    "qa": frozenset(
        {
            "profiles:read",
            "profiles:write",
            "screenings:run",
            "extract:run",
            "agent:ask",
            "export:read",
        }
    ),
    "viewer": frozenset({"profiles:read", "export:read"}),
}
