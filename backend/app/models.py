from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Tier = Literal["A", "B", "C"]
AllergenStatus = Literal["present", "possible_cross_contact", "not_detected", "unknown"]
Grade = Literal["screening-ready", "indicative"]
RunStatus = Literal["queued", "running", "completed", "failed"]


class ProvenancedValue(BaseModel):
    value: Any = None
    tier: Tier | None = None
    source: str | None = None
    retrieved_at: str | None = None
    gap: bool = False
    defaulted: bool = False


class FieldPatch(BaseModel):
    value: Any
    source: str = Field(..., min_length=1)
    tier: Tier | None = None


class EntityPatchRequest(BaseModel):
    fields: dict[str, FieldPatch]


class TokenRequest(BaseModel):
    email: str = Field(..., min_length=3)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class ScreeningGenerateRequest(BaseModel):
    product_id: str = Field(..., min_length=1)


class ExtractRequest(BaseModel):
    notes: str = Field(..., min_length=8)
    product_id: str | None = None
    apply: bool = False


class SpecsQueryRequest(BaseModel):
    query: str = Field(..., min_length=3)
    synthesize: bool = True


class AgentAskRequest(BaseModel):
    question: str = Field(..., min_length=3)
    product_id: str | None = None
