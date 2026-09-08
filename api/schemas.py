"""Pydantic v2 request and response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SingleLogIngestRequest(BaseModel):
    log: str = Field(min_length=1)
    source_hint: str | None = None


class BatchLogIngestRequest(BaseModel):
    logs: list[str] = Field(min_length=1)


class EventResponse(BaseModel):
    event_id: str
    timestamp: str
    actor: dict[str, Any]
    event: dict[str, Any]
    source: dict[str, Any]
    processing: dict[str, Any]
    raw_event: str


class EventDetailResponse(EventResponse):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_type: str
    severity: str
    processing_method: str
    mapping_version: str
    created_at: datetime


class MappingRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    signature_hash: str
    format_type: str
    field_mapping: dict[str, str]
    confidence: float
    is_approved: bool
    created_at: datetime
    updated_at: datetime


class MappingRuleUpdate(BaseModel):
    field_mapping: dict[str, str]
    confidence: float = Field(ge=0.0, le=1.0)
    is_approved: bool = True


class PaginatedEventsResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[EventResponse]


class BatchIngestResponse(BaseModel):
    processed: int
    failed: int
    sample_event_ids: list[str]


class AuthRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class SignupRequest(AuthRequest):
    display_name: str = Field(min_length=2, max_length=120)


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
