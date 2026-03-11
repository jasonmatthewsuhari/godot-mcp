"""GodotToolService — main service class combining all tool mixins."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from ..bridge_client import GodotBridgeClient
from ..errors import MCPError
from ..pathing import ensure_project_directory
from ..process_registry import ProcessRegistry
from ..tool_contracts import validate_tool_payload
from .definitions import ToolDefinition
from ..lock_manager import LockManager
from .asset_tools import AssetToolsMixin
from .batch import BatchToolsMixin
from .concurrency_tools import ConcurrencyToolsMixin
from .dx_tools import DxToolsMixin
from .debug_tools import DebugToolsMixin
from .local_tools import LocalToolsMixin
from .project_tools import ProjectToolsMixin
from .render_tools import RenderToolsMixin
from .scene_tools import SceneToolsMixin
from .script_tools import ScriptToolsMixin
from .uid_tools import UidToolsMixin
from .world_tools import WorldToolsMixin


class GodotToolService(
    LocalToolsMixin,
    SceneToolsMixin,
    UidToolsMixin,
    RenderToolsMixin,
    ScriptToolsMixin,
    ProjectToolsMixin,
    WorldToolsMixin,
    DebugToolsMixin,
    BatchToolsMixin,
    ConcurrencyToolsMixin,
    AssetToolsMixin,
    DxToolsMixin,
):
    """Stateful service backing MCP tool handlers."""

    def __init__(self, bridge_client: GodotBridgeClient | None = None) -> None:
        self.process_registry = ProcessRegistry()
        self.lock_manager = LockManager()
        self.bridge_client = bridge_client or GodotBridgeClient(
            base_url=os.getenv("GODOT_BRIDGE_URL", "http://127.0.0.1:19110"),
            token=os.getenv("GODOT_BRIDGE_TOKEN", ""),
            timeout_s=float(os.getenv("GODOT_BRIDGE_TIMEOUT_S", "5.0")),
        )

    def get_definitions(self) -> dict[str, ToolDefinition]:
        """Return registry of supported tools for MCP exposure."""
        defs: dict[str, ToolDefinition] = {}
        defs.update(self._get_local_definitions())
        defs.update(self._get_scene_definitions())
        defs.update(self._get_uid_definitions())
        defs.update(self._get_render_definitions())
        defs.update(self._get_script_definitions())
        defs.update(self._get_project_definitions())
        defs.update(self._get_world_definitions())
        defs.update(self._get_debug_definitions())
        defs.update(self._get_batch_definitions())
        defs.update(self._get_concurrency_definitions())
        defs.update(self._get_asset_definitions())
        defs.update(self._get_dx_definitions())
        return defs

    def _validate_bridge_payload(self, tool_name: str, request: BaseModel) -> dict[str, Any]:
        payload = request.model_dump(exclude_none=True)
        project_path = payload.get("project_path")
        if isinstance(project_path, str):
            ensure_project_directory(project_path)
        return validate_tool_payload(tool_name, payload)

    async def _bridge_call(
        self,
        tool_name: str,
        method: Callable[[dict[str, Any]], dict[str, Any]],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            response = await asyncio.to_thread(method, payload)
        except MCPError:
            raise
        except Exception as exc:
            raise MCPError(
                code="BRIDGE_CALL_FAILED",
                message=f"Bridge call failed for {tool_name}.",
                details={"tool_name": tool_name, "reason": str(exc)},
            ) from exc

        if not isinstance(response, dict):
            raise MCPError(
                code="BRIDGE_BAD_RESPONSE",
                message="Bridge response must be an object.",
                details={"tool_name": tool_name, "response_type": type(response).__name__},
            )

        bridge_error = response.get("error")
        if isinstance(bridge_error, dict):
            raise MCPError(
                code=str(bridge_error.get("code", "BRIDGE_ERROR")),
                message=str(bridge_error.get("message", "Bridge call failed.")),
                details=bridge_error.get("details") if isinstance(bridge_error.get("details"), dict) else {},
            )

        if response.get("ok") is False:
            raise MCPError(
                code="BRIDGE_ERROR",
                message="Bridge call failed.",
                details={"tool_name": tool_name, "response": response},
            )
        return response

    def _parse_bridge_response(
        self,
        tool_name: str,
        response_model: type[BaseModel],
        payload: dict[str, Any],
    ) -> BaseModel:
        try:
            return response_model.model_validate(payload)
        except ValidationError as exc:
            raise MCPError(
                code="BRIDGE_BAD_RESPONSE",
                message="Bridge response did not match expected schema.",
                details={"tool_name": tool_name, "errors": exc.errors()},
            ) from exc
