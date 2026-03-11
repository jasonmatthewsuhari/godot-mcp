"""External asset source adapters."""

from .base import AssetSearchResult, AssetSourceAdapter
from .kenney import KenneyAdapter
from .opengameart import OpenGameArtAdapter
from .sketchfab import SketchfabAdapter

__all__ = [
    "AssetSearchResult",
    "AssetSourceAdapter",
    "KenneyAdapter",
    "OpenGameArtAdapter",
    "SketchfabAdapter",
]
