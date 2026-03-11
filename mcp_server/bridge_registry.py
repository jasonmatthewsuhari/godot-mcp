"""Multi-project bridge registry for managing multiple Godot connections."""

from __future__ import annotations

from mcp_server.bridge_client import GodotBridgeClient


class BridgeRegistry:
    def __init__(self) -> None:
        self._bridges: dict[str, GodotBridgeClient] = {}

    def register(self, project_path: str, client: GodotBridgeClient) -> None:
        self._bridges[project_path] = client

    def get(self, project_path: str) -> GodotBridgeClient | None:
        return self._bridges.get(project_path)

    def unregister(self, project_path: str) -> bool:
        return self._bridges.pop(project_path, None) is not None

    def list_projects(self) -> list[str]:
        return list(self._bridges.keys())
