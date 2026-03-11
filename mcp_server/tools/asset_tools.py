"""Asset search and download tool handlers (Python-only, no bridge)."""

from __future__ import annotations

from ..asset_sources import KenneyAdapter, OpenGameArtAdapter, SketchfabAdapter
from ..models.asset import (
    AssetDownload3dRequest,
    AssetDownload3dResponse,
    AssetSearchOnlineRequest,
    AssetSearchOnlineResponse,
)
from .definitions import ToolDefinition

ADAPTERS = {
    "sketchfab": SketchfabAdapter,
    "opengameart": OpenGameArtAdapter,
    "kenney": KenneyAdapter,
}


class AssetToolsMixin:
    """Mixin providing external asset search and download tools."""

    def _get_asset_definitions(self) -> dict[str, ToolDefinition]:
        return {
            "asset_search_online": ToolDefinition(
                name="asset_search_online",
                description="Search external asset sources (Sketchfab, OpenGameArt, Kenney) for game assets.",
                request_model=AssetSearchOnlineRequest,
                response_model=AssetSearchOnlineResponse,
                handler=self.asset_search_online,
            ),
            "asset_download_3d": ToolDefinition(
                name="asset_download_3d",
                description="Download a 3D asset from an external source into the project.",
                request_model=AssetDownload3dRequest,
                response_model=AssetDownload3dResponse,
                handler=self.asset_download_3d,
            ),
        }

    async def asset_search_online(self, request: AssetSearchOnlineRequest) -> AssetSearchOnlineResponse:
        source_names = request.sources or list(ADAPTERS.keys())
        all_results: list[dict] = []
        for name in source_names:
            adapter_cls = ADAPTERS.get(name)
            if adapter_cls is None:
                continue
            adapter = adapter_cls()
            hits = await adapter.search(request.query, limit=request.limit)
            for hit in hits:
                all_results.append({
                    "name": hit.name,
                    "source": hit.source,
                    "url": hit.url,
                    "download_url": hit.download_url,
                    "license": hit.license,
                    "format": hit.format,
                    "thumbnail_url": hit.thumbnail_url,
                })
        return AssetSearchOnlineResponse(results=all_results, total=len(all_results))

    async def asset_download_3d(self, request: AssetDownload3dRequest) -> AssetDownload3dResponse:
        return AssetDownload3dResponse(imported_path="", format="")
