"""Developer experience tool handlers (Python-only, no bridge)."""

from __future__ import annotations

import os
from pathlib import Path

from ..addon_installer import AddonInstaller
from ..errors import MCPError
from ..godot_discovery import discover_godot_executable
from ..models.dx import GodotQuickStartRequest, GodotQuickStartResponse
from .definitions import ToolDefinition


class DxToolsMixin:
    """Mixin providing developer experience tools."""

    def _get_dx_definitions(self) -> dict[str, ToolDefinition]:
        return {
            "godot_quick_start": ToolDefinition(
                name="godot_quick_start",
                description="Detect Godot, install the MCP bridge addon, and return configuration info.",
                request_model=GodotQuickStartRequest,
                response_model=GodotQuickStartResponse,
                handler=self.godot_quick_start,
            ),
        }

    async def godot_quick_start(self, request: GodotQuickStartRequest) -> GodotQuickStartResponse:
        project_path = Path(request.project_path)
        if not (project_path / "project.godot").is_file():
            raise MCPError(
                code="NOT_A_GODOT_PROJECT",
                message="No project.godot found at the given path.",
                details={"project_path": str(project_path)},
            )

        godot_path = discover_godot_executable()

        installer = AddonInstaller()
        addon_installed = installer.ensure_installed(project_path)

        bridge_port = int(os.getenv("GODOT_BRIDGE_PORT", "19110"))
        token = os.getenv("GODOT_BRIDGE_TOKEN", "")

        return GodotQuickStartResponse(
            godot_path=godot_path,
            addon_installed=addon_installed,
            bridge_port=bridge_port,
            token=token,
        )
