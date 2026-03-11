"""Pydantic schemas for concurrency tools."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LockAcquireRequest(BaseModel):
    """Input schema for acquiring a resource lock."""

    resource: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    ttl_seconds: float = Field(default=300.0, gt=0)


class LockAcquireResponse(BaseModel):
    """Output schema for a successful lock acquisition."""

    resource: str
    owner: str
    acquired_at: str
    expires_at: str


class LockReleaseRequest(BaseModel):
    """Input schema for releasing a resource lock."""

    resource: str = Field(min_length=1)
    owner: str = Field(min_length=1)


class LockReleaseResponse(BaseModel):
    """Output schema for lock release."""

    released: bool


class LockListRequest(BaseModel):
    """Input schema for listing active locks."""


class LockListResponse(BaseModel):
    """Output schema for listing active locks."""

    locks: list[dict]


class JournalReadRequest(BaseModel):
    """Input schema for reading the operation journal."""

    project_path: str = Field(min_length=1)
    limit: int = Field(default=100, ge=1, le=1000)


class JournalReadResponse(BaseModel):
    """Output schema for journal entries."""

    entries: list[dict]
    total: int
