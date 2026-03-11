"""Pydantic schemas for UID tool inputs and outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UidGetRequest(BaseModel):
    """Input schema for uid lookup."""

    project_path: str = Field(min_length=1)
    resource_path: str = Field(min_length=1)


class UidGetResponse(BaseModel):
    """Output schema for uid lookup."""

    uid: str


class UidRefreshReferencesRequest(BaseModel):
    """Input schema for uid reference refresh."""

    project_path: str = Field(min_length=1)
    paths: list[str] | None = None


class UidRefreshReferencesResponse(BaseModel):
    """Output schema for uid reference refresh."""

    updated_count: int
    updated_paths: list[str]
