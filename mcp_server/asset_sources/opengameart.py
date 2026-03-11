"""OpenGameArt asset source adapter (stub)."""

from __future__ import annotations

import os

from .base import AssetSearchResult, AssetSourceAdapter


class OpenGameArtAdapter(AssetSourceAdapter):
    """Stub adapter for OpenGameArt. Requires OPENGAMEART_API_KEY env var."""

    source_name: str = "opengameart"

    def __init__(self) -> None:
        self._api_key = os.getenv("OPENGAMEART_API_KEY", "")

    async def search(self, query: str, limit: int = 10) -> list[AssetSearchResult]:
        return []

    async def download(self, url: str, target_path: str) -> str:
        return ""
