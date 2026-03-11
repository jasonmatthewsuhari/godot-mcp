"""Pydantic schemas for external asset tools."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AssetSearchOnlineRequest(BaseModel):
    """Input schema for searching external asset sources."""

    query: str = Field(min_length=1)
    sources: list[str] | None = None
    limit: int = 10


class AssetSearchOnlineResponse(BaseModel):
    """Output schema for external asset search."""

    results: list[dict]
    total: int


class AssetDownload3dRequest(BaseModel):
    """Input schema for downloading a 3D asset."""

    url: str = Field(min_length=1)
    project_path: str = Field(min_length=1)
    target_path: str = Field(min_length=1)


class AssetDownload3dResponse(BaseModel):
    """Output schema for 3D asset download."""

    imported_path: str
    format: str
