"""Warm Godot process pool (stub for future implementation)."""

from __future__ import annotations

from .process_registry import ProcessSession


class WarmPool:
    """Placeholder warm pool for pre-spawned Godot processes."""

    def __init__(self, max_size: int = 2) -> None:
        self.max_size = max_size

    async def acquire(self, project_path: str, mode: str) -> ProcessSession | None:
        return None

    async def release(self, session: ProcessSession) -> None:
        pass

    async def shutdown(self) -> None:
        pass
