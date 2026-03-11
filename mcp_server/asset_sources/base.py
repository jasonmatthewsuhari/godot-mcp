"""Base adapter for external asset sources."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AssetSearchResult:
    name: str
    source: str  # "sketchfab", "opengameart", "kenney"
    url: str
    download_url: str | None = None
    license: str = ""
    format: str = ""
    thumbnail_url: str | None = None


class AssetSourceAdapter:
    """Base class for asset source adapters."""

    source_name: str = ""

    async def search(self, query: str, limit: int = 10) -> list[AssetSearchResult]:
        raise NotImplementedError

    async def download(self, url: str, target_path: str) -> str:
        raise NotImplementedError
