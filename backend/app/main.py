"""Lotwise Core API — frozen take-home contract the candidate UI consumes."""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import openai
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import agent, config, extract, screening
from app.auth import current_principal, idempotency_key, issue_token, require_perm
from app.models import (
    AgentAskRequest,
    EntityPatchRequest,
    ExtractRequest,
    ScreeningGenerateRequest,
    SpecsQueryRequest,
    TokenRequest,
    TokenResponse,
)
from app.store import Store, get_store

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lotwise Core API",
    version=config.ENGINE_VERSION,
    description=(
        "Mock screening-grade allergen & spec-gap API for the Product Lead take-home. "
        "Auth is a passwordless stand-in. Screening is deterministic. "
        "The LLM is used only on /v1/extract, /v1/specs:query (synthesize) and /v1/agent:ask."
    ),
    openapi_url="/v1/openapi.json",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "title": user["title"],
        "role": user["role"],
        "tenant_id": user["tenant_id"],
    }


def _llm_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, openai.APITimeoutError):
        return HTTPException(
            status_code=502,
            detail="The local model did not respond before the request timeout. Confirm Ollama has available memory and retry after the model is warm.",
        )
    if isinstance(exc, openai.APIConnectionError):
        return HTTPException(
            status_code=502,
            detail=(
                f"Could not reach the LLM backend at {config.OLLAMA_BASE_URL}. "
                f"Is Ollama running and is '{config.OLLAMA_MODEL}' pulled?"
            ),
        )
    if isinstance(exc, openai.APIStatusError):
        return HTTPException(status_code=502, detail=f"LLM backend rejected the request: {exc.message}")
    logger.exception("LLM call failed")
    return HTTPException(status_code=500, detail=f"Unexpected LLM error: {exc}")


@app.get("/v1/health")
def health(store: Store = Depends(get_store)) -> dict:
    return {
        "status": "ok",
        "engine": config.ENGINE_VERSION,
        "model": config.OLLAMA_MODEL,
        "tenants_loaded": len(store.tenants),
    }


@app.get("/v1/version")
def version() -> dict:
    return {
        "engine": config.ENGINE_VERSION,
        "card_set": config.CARD_SET_VERSION,
        "taxonomy": config.TAXONOMY_VERSION,
        "api": "v1",
        "additive_only": True,
    }


@app.get("/v1/meta/demo-users")
def demo_users(store: Store = Depends(get_store)) -> dict:
    return {
        "note": "Take-home convenience. A real product would never list accounts unauthenticated.",
        "users": store.demo_users(),
    }


@app.get("/v1/meta/sample-notes")
def sample_notes(store: Store = Depends(get_store)) -> dict:
    return store.sample_notes


@app.post("/v1/auth/token", response_model=TokenResponse)
def issue_dev_token(body: TokenRequest, store: Store = Depends(get_store)) -> TokenResponse:
    user = store.user_by_email(body.email)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Unknown email. Use GET /v1/meta/demo-users for the take-home accounts.",
        )
    token = issue_token(user)
    return TokenResponse(
        access_token=token,
        expires_in=config.JWT_TTL_SECONDS,
        user=_public_user(user),
    )


@app.get("/v1/me")
def me(principal: dict = Depends(current_principal), store: Store = Depends(get_store)) -> dict:
    tenant = store.tenant(principal["tenant_id"])
    return {
        "user": _public_user(principal["user"]),
        "tenant": {
            "id": tenant["id"],
            "slug": tenant["slug"],
            "name": tenant["name"],
            "plan": tenant["plan"],
            "home_region": tenant["home_region"],
        },
        "permissions": sorted(principal["perms"]),
    }


@app.get("/v1/usage")
def usage(principal: dict = Depends(require_perm("profiles:read")), store: Store = Depends(get_store)) -> dict:
    return store.usage(principal["tenant_id"])


@app.get("/v1/facilities")
def list_facilities(principal: dict = Depends(require_perm("profiles:read")), store: Store = Depends(get_store)) -> dict:
    return {"items": store.list_facilities(principal["tenant_id"])}


@app.get("/v1/facilities/{facility_id}")
def get_facility(
    facility_id: str,
    principal: dict = Depends(require_perm("profiles:read")),
    store: Store = Depends(get_store),
) -> dict:
    return store.get_facility(principal["tenant_id"], facility_id)


@app.patch("/v1/facilities/{facility_id}")
def patch_facility(
    facility_id: str,
    body: EntityPatchRequest,
    principal: dict = Depends(require_perm("profiles:write")),
    store: Store = Depends(get_store),
) -> dict:
    return store.patch_facility(principal["tenant_id"], facility_id, body.fields)


@app.get("/v1/products")
def list_products(principal: dict = Depends(require_perm("profiles:read")), store: Store = Depends(get_store)) -> dict:
    return {"items": store.list_products(principal["tenant_id"])}


@app.get("/v1/products/{product_id}")
def get_product(
    product_id: str,
    principal: dict = Depends(require_perm("profiles:read")),
    store: Store = Depends(get_store),
) -> dict:
    return store.product_bundle(principal["tenant_id"], product_id)


@app.patch("/v1/products/{product_id}")
def patch_product(
    product_id: str,
    body: EntityPatchRequest,
    principal: dict = Depends(require_perm("profiles:write")),
    store: Store = Depends(get_store),
) -> dict:
    return store.patch_product(principal["tenant_id"], product_id, body.fields)


@app.get("/v1/ingredients")
def list_ingredients(principal: dict = Depends(require_perm("profiles:read")), store: Store = Depends(get_store)) -> dict:
    return {"items": store.list_ingredients(principal["tenant_id"])}


@app.get("/v1/ingredients/{ingredient_id}")
def get_ingredient(
    ingredient_id: str,
    principal: dict = Depends(require_perm("profiles:read")),
    store: Store = Depends(get_store),
) -> dict:
    return store.get_ingredient(principal["tenant_id"], ingredient_id)


@app.patch("/v1/ingredients/{ingredient_id}")
def patch_ingredient(
    ingredient_id: str,
    body: EntityPatchRequest,
    principal: dict = Depends(require_perm("profiles:write")),
    store: Store = Depends(get_store),
) -> dict:
    return store.patch_ingredient(principal["tenant_id"], ingredient_id, body.fields)


def _execute_screening(store: Store, tenant_id: str, run_id: str) -> None:
    run = store.screenings.get(run_id)
    if run is None:
        return
    run["status"] = "running"
    run["started_at"] = _now()
    try:
        time.sleep(config.SCREENING_DELAY_SECONDS)
        bundle = store.product_bundle(tenant_id, run["product_id"])
        result = screening.run_screening(bundle)
        run["status"] = "completed"
        run["result"] = result
        run["completed_at"] = _now()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Screening failed")
        run["status"] = "failed"
        run["error"] = str(exc)
        run["completed_at"] = _now()
    store.put_screening(run)


@app.post("/v1/screenings:generate", status_code=202)
def generate_screening(
    body: ScreeningGenerateRequest,
    background: BackgroundTasks,
    principal: dict = Depends(require_perm("screenings:run")),
    store: Store = Depends(get_store),
    idemp: str | None = Depends(idempotency_key),
) -> dict:
    tenant_id = principal["tenant_id"]
    store.get_product(tenant_id, body.product_id)
    if idemp:
        existing = store.lookup_idempotency(tenant_id, idemp)
        if existing:
            return store.get_screening(tenant_id, existing)

    store.charge(tenant_id, config.SCREENING_COST, "screenings:generate", ref=body.product_id)
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    run = {
        "run_id": run_id,
        "tenant_id": tenant_id,
        "product_id": body.product_id,
        "status": "queued",
        "created_at": _now(),
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None,
        "cost": config.SCREENING_COST,
        "requested_by": principal["user"]["id"],
    }
    store.put_screening(run)
    if idemp:
        store.remember_idempotency(tenant_id, idemp, run_id)
    background.add_task(_execute_screening, store, tenant_id, run_id)
    return {"run_id": run_id, "status": "queued", "poll": f"/v1/screenings/{run_id}"}


@app.get("/v1/screenings")
def list_screenings(
    product_id: str | None = None,
    principal: dict = Depends(require_perm("profiles:read")),
    store: Store = Depends(get_store),
) -> dict:
    return {"items": store.list_screenings(principal["tenant_id"], product_id)}


@app.get("/v1/screenings/{run_id}")
def get_screening(
    run_id: str,
    principal: dict = Depends(require_perm("profiles:read")),
    store: Store = Depends(get_store),
) -> dict:
    return store.get_screening(principal["tenant_id"], run_id)


@app.post("/v1/extract")
def extract_notes(
    body: ExtractRequest,
    principal: dict = Depends(require_perm("extract:run")),
    store: Store = Depends(get_store),
) -> dict:
    if body.apply and "profiles:write" not in principal["perms"]:
        raise HTTPException(status_code=403, detail="Applying extract patches requires profiles:write")
    store.charge(principal["tenant_id"], config.EXTRACT_COST, "extract", ref=body.product_id)
    try:
        return extract.extract_notes(
            store,
            principal["tenant_id"],
            body.notes,
            body.product_id,
            body.apply,
        )
    except Exception as exc:  # noqa: BLE001
        raise _llm_http_error(exc) from exc


@app.post("/v1/specs:query")
def specs_query(
    body: SpecsQueryRequest,
    principal: dict = Depends(require_perm("profiles:read")),
    store: Store = Depends(get_store),
) -> dict:
    cards = store.search_cards(body.query, limit=4)
    payload: dict[str, Any] = {"query": body.query, "cards": cards, "synthesis": None}
    if not body.synthesize:
        return payload
    store.charge(principal["tenant_id"], config.SPECS_QUERY_COST, "specs:query")
    prompt = (
        "Using only the spec cards below, answer the question in 2-4 sentences. "
        "Cite card ids. If the cards are insufficient, say so.\n\n"
        f"Question: {body.query}\n\nCards:\n{cards}"
    )
    try:
        raw = llm_client.chat(
            [
                {"role": "system", "content": "You are a cautious food-spec librarian. No extra claims."},
                {"role": "user", "content": prompt},
            ]
        )
        payload["synthesis"] = raw.get("content")
        return payload
    except Exception as exc:  # noqa: BLE001
        raise _llm_http_error(exc) from exc


@app.post("/v1/agent:ask")
def agent_ask(
    body: AgentAskRequest,
    principal: dict = Depends(require_perm("agent:ask")),
    store: Store = Depends(get_store),
) -> dict:
    store.charge(principal["tenant_id"], config.AGENT_ASK_COST, "agent:ask", ref=body.product_id)
    try:
        return agent.ask(store, principal["tenant_id"], body.question, body.product_id)
    except Exception as exc:  # noqa: BLE001
        raise _llm_http_error(exc) from exc
