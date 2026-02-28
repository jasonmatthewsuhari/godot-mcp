"""MCP tool implementations for Godot workflows."""

from __future__ import annotations

import asyncio
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Coroutine

from pydantic import BaseModel, ValidationError

from .bridge_client import GodotBridgeClient
from .errors import MCPError
from .godot_discovery import discover_godot_executable
from .models import (
    GodotAnalyzeProjectRequest,
    GodotAnalyzeProjectResponse,
    GodotGetDebugOutputRequest,
    GodotGetDebugOutputResponse,
    GodotGetVersionRequest,
    GodotGetVersionResponse,
    GodotLaunchEditorRequest,
    GodotLaunchEditorResponse,
    GodotListProjectsRequest,
    GodotListProjectsResponse,
    GodotRunProjectRequest,
    GodotRunProjectResponse,
    GodotStopExecutionRequest,
    GodotStopExecutionResponse,
    RenderCaptureRequest,
    RenderCaptureResponse,
    RenderInteractRequest,
    RenderInteractResponse,
    SceneAddNodeRequest,
    SceneAddNodeResponse,
    SceneCreateRequest,
    SceneCreateResponse,
    SceneExportMeshLibraryRequest,
    SceneExportMeshLibraryResponse,
    SceneLoadSpriteRequest,
    SceneLoadSpriteResponse,
    SceneSaveRequest,
    SceneSaveResponse,
    UidGetRequest,
    UidGetResponse,
    UidRefreshReferencesRequest,
    UidRefreshReferencesResponse,
)
from .pathing import ensure_project_directory
from .process_registry import ProcessRegistry
from .project_analysis import analyze_project, list_projects
from .tool_contracts import validate_tool_payload


@dataclass(slots=True)
class ToolDefinition:
    """Metadata and implementation wiring for an MCP tool."""

    name: str
    description: str
    request_model: type[BaseModel]
    response_model: type[BaseModel]
    handler: Callable[[BaseModel], Coroutine[Any, Any, BaseModel]]


class GodotToolService:
    """Stateful service backing MCP tool handlers."""

    def __init__(self, bridge_client: GodotBridgeClient | None = None) -> None:
        self.process_registry = ProcessRegistry()
        self.bridge_client = bridge_client or GodotBridgeClient(
            base_url=os.getenv("GODOT_BRIDGE_URL", "http://127.0.0.1:19110"),
            token=os.getenv("GODOT_BRIDGE_TOKEN", ""),
            timeout_s=float(os.getenv("GODOT_BRIDGE_TIMEOUT_S", "5.0")),
        )

    def get_definitions(self) -> dict[str, ToolDefinition]:
        """Return registry of supported tools for MCP exposure."""
        return {
            "godot_get_version": ToolDefinition(
                name="godot_get_version",
                description="Get installed Godot version and resolved executable path.",
                request_model=GodotGetVersionRequest,
                response_model=GodotGetVersionResponse,
                handler=self.godot_get_version,
            ),
            "godot_list_projects": ToolDefinition(
                name="godot_list_projects",
                description="Recursively list Godot projects beneath a root directory.",
                request_model=GodotListProjectsRequest,
                response_model=GodotListProjectsResponse,
                handler=self.godot_list_projects,
            ),
            "godot_launch_editor": ToolDefinition(
                name="godot_launch_editor",
                description="Launch Godot editor for a project and return session details.",
                request_model=GodotLaunchEditorRequest,
                response_model=GodotLaunchEditorResponse,
                handler=self.godot_launch_editor,
            ),
            "godot_run_project": ToolDefinition(
                name="godot_run_project",
                description="Run a Godot project and return session details.",
                request_model=GodotRunProjectRequest,
                response_model=GodotRunProjectResponse,
                handler=self.godot_run_project,
            ),
            "godot_stop_execution": ToolDefinition(
                name="godot_stop_execution",
                description="Stop a running Godot process by session_id or latest session.",
                request_model=GodotStopExecutionRequest,
                response_model=GodotStopExecutionResponse,
                handler=self.godot_stop_execution,
            ),
            "godot_get_debug_output": ToolDefinition(
                name="godot_get_debug_output",
                description="Read buffered stdout/stderr from a session with cursor pagination.",
                request_model=GodotGetDebugOutputRequest,
                response_model=GodotGetDebugOutputResponse,
                handler=self.godot_get_debug_output,
            ),
            "godot_analyze_project": ToolDefinition(
                name="godot_analyze_project",
                description="Analyze project scenes/scripts/resources/plugins/autoloads/main scene.",
                request_model=GodotAnalyzeProjectRequest,
                response_model=GodotAnalyzeProjectResponse,
                handler=self.godot_analyze_project,
            ),
            "scene_create": ToolDefinition(
                name="scene_create",
                description="Create a scene through the local Godot addon bridge.",
                request_model=SceneCreateRequest,
                response_model=SceneCreateResponse,
                handler=self.scene_create,
            ),
            "scene_add_node": ToolDefinition(
                name="scene_add_node",
                description="Add a node to a scene through the local Godot addon bridge.",
                request_model=SceneAddNodeRequest,
                response_model=SceneAddNodeResponse,
                handler=self.scene_add_node,
            ),
            "scene_load_sprite": ToolDefinition(
                name="scene_load_sprite",
                description="Load a sprite texture through the local Godot addon bridge.",
                request_model=SceneLoadSpriteRequest,
                response_model=SceneLoadSpriteResponse,
                handler=self.scene_load_sprite,
            ),
            "scene_export_mesh_library": ToolDefinition(
                name="scene_export_mesh_library",
                description="Export a mesh library through the local Godot addon bridge.",
                request_model=SceneExportMeshLibraryRequest,
                response_model=SceneExportMeshLibraryResponse,
                handler=self.scene_export_mesh_library,
            ),
            "scene_save": ToolDefinition(
                name="scene_save",
                description="Save a scene through the local Godot addon bridge.",
                request_model=SceneSaveRequest,
                response_model=SceneSaveResponse,
                handler=self.scene_save,
            ),
            "uid_get": ToolDefinition(
                name="uid_get",
                description="Get a Godot resource UID through the local addon bridge.",
                request_model=UidGetRequest,
                response_model=UidGetResponse,
                handler=self.uid_get,
            ),
            "uid_refresh_references": ToolDefinition(
                name="uid_refresh_references",
                description="Refresh UID references through the local addon bridge.",
                request_model=UidRefreshReferencesRequest,
                response_model=UidRefreshReferencesResponse,
                handler=self.uid_refresh_references,
            ),
            "render_capture": ToolDefinition(
                name="render_capture",
                description="Capture rendered output through the local addon bridge.",
                request_model=RenderCaptureRequest,
                response_model=RenderCaptureResponse,
                handler=self.render_capture,
            ),
            "render_interact": ToolDefinition(
                name="render_interact",
                description="Send interaction input through the local addon bridge.",
                request_model=RenderInteractRequest,
                response_model=RenderInteractResponse,
                handler=self.render_interact,
            ),
        }

    async def godot_get_version(self, request: GodotGetVersionRequest) -> GodotGetVersionResponse:
        del request
        godot_path = discover_godot_executable()

        def _run_version(path: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [str(path), "--version"],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )

        result = await asyncio.to_thread(_run_version, godot_path)
        version = (result.stdout or result.stderr).strip()
        if not version:
            raise MCPError(
                code="GODOT_VERSION_FAILED",
                message="Failed to read Godot version output.",
                details={"path": str(godot_path), "returncode": result.returncode},
            )
        return GodotGetVersionResponse(version=version, path=str(godot_path))

    async def godot_list_projects(self, request: GodotListProjectsRequest) -> GodotListProjectsResponse:
        projects = list_projects(request.root_path)
        return GodotListProjectsResponse(projects=projects)

    async def godot_launch_editor(self, request: GodotLaunchEditorRequest) -> GodotLaunchEditorResponse:
        godot_path = discover_godot_executable()
        project_path = ensure_project_directory(request.project_path)
        session = await self.process_registry.create_session(
            godot_path=godot_path,
            project_path=project_path,
            mode="editor",
            headless=request.headless,
        )
        return GodotLaunchEditorResponse(session_id=session.session_id, pid=session.pid, status=session.status)

    async def godot_run_project(self, request: GodotRunProjectRequest) -> GodotRunProjectResponse:
        godot_path = discover_godot_executable()
        project_path = ensure_project_directory(request.project_path)
        session = await self.process_registry.create_session(
            godot_path=godot_path,
            project_path=project_path,
            mode="run",
            debug=request.debug,
            scene_override=request.scene_override,
        )
        return GodotRunProjectResponse(session_id=session.session_id, pid=session.pid, status=session.status)

    async def godot_stop_execution(self, request: GodotStopExecutionRequest) -> GodotStopExecutionResponse:
        stopped, exit_code = await self.process_registry.stop_session(request.session_id)
        return GodotStopExecutionResponse(stopped=stopped, exit_code=exit_code)

    async def godot_get_debug_output(self, request: GodotGetDebugOutputRequest) -> GodotGetDebugOutputResponse:
        entries, next_cursor = self.process_registry.get_output(
            session_id=request.session_id,
            limit=request.limit,
            cursor=request.cursor,
        )
        return GodotGetDebugOutputResponse(
            entries=[
                {
                    "cursor": item.cursor,
                    "timestamp": item.timestamp,
                    "stream": item.stream,
                    "message": item.message,
                }
                for item in entries
            ],
            next_cursor=next_cursor,
        )

    async def godot_analyze_project(self, request: GodotAnalyzeProjectRequest) -> GodotAnalyzeProjectResponse:
        return analyze_project(request.project_path)

    async def scene_create(self, request: SceneCreateRequest) -> SceneCreateResponse:
        payload = self._validate_bridge_payload("scene_create", request)
        response = await self._bridge_call("scene_create", self.bridge_client.scene_create, payload)
        return self._parse_bridge_response("scene_create", SceneCreateResponse, response)

    async def scene_add_node(self, request: SceneAddNodeRequest) -> SceneAddNodeResponse:
        payload = self._validate_bridge_payload("scene_add_node", request)
        response = await self._bridge_call("scene_add_node", self.bridge_client.scene_add_node, payload)
        return self._parse_bridge_response("scene_add_node", SceneAddNodeResponse, response)

    async def scene_load_sprite(self, request: SceneLoadSpriteRequest) -> SceneLoadSpriteResponse:
        payload = self._validate_bridge_payload("scene_load_sprite", request)
        response = await self._bridge_call("scene_load_sprite", self.bridge_client.scene_load_sprite, payload)
        return self._parse_bridge_response("scene_load_sprite", SceneLoadSpriteResponse, response)

    async def scene_export_mesh_library(self, request: SceneExportMeshLibraryRequest) -> SceneExportMeshLibraryResponse:
        payload = self._validate_bridge_payload("scene_export_mesh_library", request)
        response = await self._bridge_call("scene_export_mesh_library", self.bridge_client.scene_export_mesh_library, payload)
        return self._parse_bridge_response("scene_export_mesh_library", SceneExportMeshLibraryResponse, response)

    async def scene_save(self, request: SceneSaveRequest) -> SceneSaveResponse:
        payload = self._validate_bridge_payload("scene_save", request)
        response = await self._bridge_call("scene_save", self.bridge_client.scene_save, payload)
        return self._parse_bridge_response("scene_save", SceneSaveResponse, response)

    async def uid_get(self, request: UidGetRequest) -> UidGetResponse:
        payload = self._validate_bridge_payload("uid_get", request)
        response = await self._bridge_call("uid_get", self.bridge_client.uid_get, payload)
        return self._parse_bridge_response("uid_get", UidGetResponse, response)

    async def uid_refresh_references(self, request: UidRefreshReferencesRequest) -> UidRefreshReferencesResponse:
        payload = self._validate_bridge_payload("uid_refresh_references", request)
        response = await self._bridge_call("uid_refresh_references", self.bridge_client.uid_refresh_references, payload)
        return self._parse_bridge_response("uid_refresh_references", UidRefreshReferencesResponse, response)

    async def render_capture(self, request: RenderCaptureRequest) -> RenderCaptureResponse:
        payload = self._validate_bridge_payload("render_capture", request)
        response = await self._bridge_call("render_capture", self.bridge_client.render_capture, payload)
        return self._parse_bridge_response("render_capture", RenderCaptureResponse, response)

    async def render_interact(self, request: RenderInteractRequest) -> RenderInteractResponse:
        payload = self._validate_bridge_payload("render_interact", request)
        response = await self._bridge_call("render_interact", self.bridge_client.render_interact, payload)
        return self._parse_bridge_response("render_interact", RenderInteractResponse, response)

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


def parse_arguments(model: type[BaseModel], arguments: dict[str, Any] | None) -> BaseModel:
    """Validate tool arguments and raise MCPError on validation failure."""
    payload = arguments or {}
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise MCPError(
            code="VALIDATION_ERROR",
            message="Invalid tool arguments.",
            details={"errors": exc.errors()},
        ) from exc

