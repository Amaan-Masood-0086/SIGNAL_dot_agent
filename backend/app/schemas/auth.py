"""Pydantic schemas — every endpoint MUST have schema validation (backend
development contract #1)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field


class TokenRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(ge=0, description="seconds")


class CurrentStaffOut(BaseModel):
    staff_id: uuid.UUID
    institution_id: uuid.UUID
    role: str
