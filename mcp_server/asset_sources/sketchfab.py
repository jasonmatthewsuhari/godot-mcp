"""Sketchfab asset source adapter (stub)."""

from __future__ import annotations

import os

from .base import AssetSearchResult, AssetSourceAdapter


class SketchfabAdapter(AssetSourceAdapter):
    """Stub adapter for Sketchfab. Requires SKETCHFAB_API_KEY env var."""

    source_name: str = "sketchfab"

    def __init__(self) -> None:
        self._api_key = os.getenv("SKETCHFAB_API_KEY", "")

    async def search(self, query: str, limit: int = 10) -> list[AssetSearchResult]:
        return []

    async def download(self, url: str, target_path: str) -> str:
        return ""
