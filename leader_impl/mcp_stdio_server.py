from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Callable

from pydantic import ValidationError

from .errors import ToolError
from .bridge_client import GodotBridgeClient
from .godot_discovery import find_godot_executable, get_godot_version
from .models import (
    AnalyzeProjectRequest,
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
    UIDGetRequest,
    UIDGetResponse,
    UIDRefreshRequest,
    UIDRefreshResponse,
    DebugEntry,
    DebugOutputRequest,
    DebugOutputResponse,
    GetVersionRequest,
    GetVersionResponse,
    LaunchEditorRequest,
    ListProjectsRequest,
    ListProjectsResponse,
    RunProjectRequest,
    SessionResponse,
    StopExecutionRequest,
    StopExecutionResponse,
)
from .pathing import ensure_project_path
from .process_sessions import SessionManager
from .project_discovery import analyze_project, list_projects


LOGGER = logging.getLogger("leader_impl.mcp")


class LeaderMCPServer:
    def __init__(self) -> None:
        self.session_manager = SessionManager()
        self.godot_path = find_godot_executable()
        bridge_port = int(os.environ.get("LEADER_BRIDGE_PORT", "8799"))
        bridge_token = os.environ.get("LEADER_BRIDGE_TOKEN")
        self.bridge = GodotBridgeClient(port=bridge_port, token=bridge_token)

    def _require_godot_path(self) -> str:
        if not self.godot_path:
            raise ToolError(
                code="godot_not_found",
                message="Could not find Godot executable",
                details={"hint": "Set GODOT_PATH or install Godot in PATH"},
            )
        return self.godot_path

    def _tool_get_version(self, arguments: dict[str, Any]) -> dict[str, Any]:
        GetVersionRequest.model_validate(arguments)
        path = self._require_godot_path()
        payload = GetVersionResponse(version=get_godot_version(path), path=path)
        return payload.model_dump()

    def _tool_list_projects(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = ListProjectsRequest.model_validate(arguments)
        projects = list_projects(req.root_path)
        return ListProjectsResponse(projects=projects).model_dump()

    def _tool_launch_editor(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = LaunchEditorRequest.model_validate(arguments)
        path = ensure_project_path(req.project_path)
        session = self.session_manager.launch_editor(self._require_godot_path(), path, headless=req.headless)
        return SessionResponse(session_id=session.session_id, pid=session.pid, status=session.status).model_dump()

    def _tool_run_project(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = RunProjectRequest.model_validate(arguments)
        path = ensure_project_path(req.project_path)
        session = self.session_manager.run_project(
            self._require_godot_path(),
            path,
            debug=req.debug,
            scene_override=req.scene_override,
        )
        return SessionResponse(session_id=session.session_id, pid=session.pid, status=session.status).model_dump()

    def _tool_stop_execution(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = StopExecutionRequest.model_validate(arguments)
        stopped, exit_code = self.session_manager.stop(req.session_id)
        return StopExecutionResponse(stopped=stopped, exit_code=exit_code).model_dump()

    def _tool_get_debug_output(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = DebugOutputRequest.model_validate(arguments)
        entries, next_cursor = self.session_manager.get_output(req.session_id, req.limit, req.cursor)
        payload = DebugOutputResponse(
            entries=[
                DebugEntry(index=e.index, timestamp=e.timestamp, stream=e.stream, message=e.message)
                for e in entries
            ],
            next_cursor=next_cursor,
        )
        return payload.model_dump()

    def _tool_analyze_project(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = AnalyzeProjectRequest.model_validate(arguments)
        return analyze_project(req.project_path).model_dump()

    def _tool_scene_create(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = SceneCreateRequest.model_validate(arguments)
        req.project_path = ensure_project_path(req.project_path)
        raw = self.bridge.scene_create(req.model_dump())
        return SceneCreateResponse.model_validate(raw).model_dump()

    def _tool_scene_add_node(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = SceneAddNodeRequest.model_validate(arguments)
        req.project_path = ensure_project_path(req.project_path)
        raw = self.bridge.scene_add_node(req.model_dump())
        return SceneAddNodeResponse.model_validate(raw).model_dump()

    def _tool_scene_load_sprite(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = SceneLoadSpriteRequest.model_validate(arguments)
        req.project_path = ensure_project_path(req.project_path)
        raw = self.bridge.scene_load_sprite(req.model_dump())
        return SceneLoadSpriteResponse.model_validate(raw).model_dump()

    def _tool_scene_export_mesh_library(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = SceneExportMeshLibraryRequest.model_validate(arguments)
        req.project_path = ensure_project_path(req.project_path)
        raw = self.bridge.scene_export_mesh_library(req.model_dump())
        return SceneExportMeshLibraryResponse.model_validate(raw).model_dump()

    def _tool_scene_save(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = SceneSaveRequest.model_validate(arguments)
        req.project_path = ensure_project_path(req.project_path)
        raw = self.bridge.scene_save(req.model_dump())
        return SceneSaveResponse.model_validate(raw).model_dump()

    def _tool_uid_get(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = UIDGetRequest.model_validate(arguments)
        req.project_path = ensure_project_path(req.project_path)
        raw = self.bridge.uid_get(req.model_dump())
        return UIDGetResponse.model_validate(raw).model_dump()

    def _tool_uid_refresh_references(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = UIDRefreshRequest.model_validate(arguments)
        req.project_path = ensure_project_path(req.project_path)
        raw = self.bridge.uid_refresh(req.model_dump())
        return UIDRefreshResponse.model_validate(raw).model_dump()

    def _tool_render_capture(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = RenderCaptureRequest.model_validate(arguments)
        req.project_path = ensure_project_path(req.project_path)
        raw = self.bridge.render_capture(req.model_dump())
        return RenderCaptureResponse.model_validate(raw).model_dump()

    def _tool_render_interact(self, arguments: dict[str, Any]) -> dict[str, Any]:
        req = RenderInteractRequest.model_validate(arguments)
        req.project_path = ensure_project_path(req.project_path)
        raw = self.bridge.render_interact(req.model_dump())
        return RenderInteractResponse.model_validate(raw).model_dump()

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "godot_get_version": self._tool_get_version,
            "godot_list_projects": self._tool_list_projects,
            "godot_launch_editor": self._tool_launch_editor,
            "godot_run_project": self._tool_run_project,
            "godot_stop_execution": self._tool_stop_execution,
            "godot_get_debug_output": self._tool_get_debug_output,
            "godot_analyze_project": self._tool_analyze_project,
            "scene_create": self._tool_scene_create,
            "scene_add_node": self._tool_scene_add_node,
            "scene_load_sprite": self._tool_scene_load_sprite,
            "scene_export_mesh_library": self._tool_scene_export_mesh_library,
            "scene_save": self._tool_scene_save,
            "uid_get": self._tool_uid_get,
            "uid_refresh_references": self._tool_uid_refresh_references,
            "render_capture": self._tool_render_capture,
            "render_interact": self._tool_render_interact,
        }
        handler = handlers.get(tool_name)
        if not handler:
            raise ToolError(code="unknown_tool", message=f"Unknown tool '{tool_name}'")
        return handler(arguments)

    def handle_jsonrpc(self, payload: dict[str, Any]) -> dict[str, Any]:
        req_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params", {})
        try:
            if method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments") or {}
                if not isinstance(arguments, dict):
                    raise ToolError(code="invalid_arguments", message="arguments must be an object")
                result = self.call_tool(str(tool_name), arguments)
                return {"jsonrpc": "2.0", "id": req_id, "result": result}
            raise ToolError(code="unknown_method", message=f"Unknown method '{method}'")
        except ValidationError as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": "validation_error", "message": "Invalid input", "details": exc.errors()},
            }
        except ToolError as exc:
            return {"jsonrpc": "2.0", "id": req_id, "error": exc.to_dict()}
        except Exception as exc:  # pragma: no cover
            LOGGER.exception("Unhandled error while processing request")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": "internal_error", "message": "Unexpected error", "details": str(exc)},
            }

    def serve_stdio(self) -> None:
        for line in sys.stdin:
            raw = line.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": "invalid_json", "message": "Failed to parse JSON input"},
                }
            else:
                response = self.handle_jsonrpc(payload)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
