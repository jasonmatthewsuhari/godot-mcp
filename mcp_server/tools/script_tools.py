"""Script and scene introspection tool handlers."""

from __future__ import annotations

import os
from pathlib import Path

from ..errors import MCPError
from ..models import (
    NodeGetPropertiesRequest,
    NodeGetPropertiesResponse,
    SceneInspectRequest,
    SceneInspectResponse,
    ScriptAttachRequest,
    ScriptAttachResponse,
    ScriptCreateRequest,
    ScriptCreateResponse,
    ScriptEditRequest,
    ScriptEditResponse,
    ScriptValidateRequest,
    ScriptValidateResponse,
)
from ..pathing import ensure_project_directory
from .definitions import ToolDefinition


class ScriptToolsMixin:
    """Mixin providing script editing and scene introspection tools."""

    def _get_script_definitions(self) -> dict[str, ToolDefinition]:
        return {
            "script_create": ToolDefinition(
                name="script_create",
                description="Create a GDScript file with content in a Godot project.",
                request_model=ScriptCreateRequest,
                response_model=ScriptCreateResponse,
                handler=self.script_create,
            ),
            "script_edit": ToolDefinition(
                name="script_edit",
                description="Edit a GDScript file via line-based operations.",
                request_model=ScriptEditRequest,
                response_model=ScriptEditResponse,
                handler=self.script_edit,
            ),
            "script_attach": ToolDefinition(
                name="script_attach",
                description="Attach a GDScript to a node in a scene via bridge.",
                request_model=ScriptAttachRequest,
                response_model=ScriptAttachResponse,
                handler=self.script_attach,
            ),
            "script_validate": ToolDefinition(
                name="script_validate",
                description="Validate GDScript syntax via bridge.",
                request_model=ScriptValidateRequest,
                response_model=ScriptValidateResponse,
                handler=self.script_validate,
            ),
            "scene_inspect": ToolDefinition(
                name="scene_inspect",
                description="Walk scene tree and return node hierarchy with types and properties.",
                request_model=SceneInspectRequest,
                response_model=SceneInspectResponse,
                handler=self.scene_inspect,
            ),
            "node_get_properties": ToolDefinition(
                name="node_get_properties",
                description="Get all properties of a specific node in a scene.",
                request_model=NodeGetPropertiesRequest,
                response_model=NodeGetPropertiesResponse,
                handler=self.node_get_properties,
            ),
        }

    async def script_create(self, request: ScriptCreateRequest) -> ScriptCreateResponse:
        project_dir = ensure_project_directory(request.project_path)
        script_path = _resolve_script_path(project_dir, request.script_path)

        script_path.parent.mkdir(parents=True, exist_ok=True)

        content = request.content
        if request.class_name:
            if not content.startswith("class_name"):
                content = f"class_name {request.class_name}\n\n{content}"

        script_path.write_text(content, encoding="utf-8")
        return ScriptCreateResponse(script_path=str(script_path))

    async def script_edit(self, request: ScriptEditRequest) -> ScriptEditResponse:
        project_dir = ensure_project_directory(request.project_path)
        script_path = _resolve_script_path(project_dir, request.script_path)

        if not script_path.is_file():
            raise MCPError(
                code="SCRIPT_NOT_FOUND",
                message="Script file not found.",
                details={"script_path": str(script_path)},
            )

        lines = script_path.read_text(encoding="utf-8").splitlines(keepends=True)

        for op in sorted(request.operations, key=lambda o: o.start, reverse=True):
            if op.op != "replace_lines":
                raise MCPError(
                    code="INVALID_OPERATION",
                    message=f"Unsupported operation: {op.op}",
                    details={"op": op.op},
                )
            start_idx = op.start - 1
            end_idx = op.end
            if start_idx < 0 or end_idx > len(lines) or start_idx > end_idx:
                raise MCPError(
                    code="INVALID_RANGE",
                    message="Line range out of bounds.",
                    details={"start": op.start, "end": op.end, "total_lines": len(lines)},
                )
            new_lines = op.content.splitlines(keepends=True)
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines[-1] += "\n"
            lines[start_idx:end_idx] = new_lines

        script_path.write_text("".join(lines), encoding="utf-8")
        return ScriptEditResponse(script_path=str(script_path), line_count=len(lines))

    async def script_attach(self, request: ScriptAttachRequest) -> ScriptAttachResponse:
        payload = self._validate_bridge_payload("script_attach", request)
        response = await self._bridge_call("script_attach", self.bridge_client.script_attach, payload)
        return self._parse_bridge_response("script_attach", ScriptAttachResponse, response)

    async def script_validate(self, request: ScriptValidateRequest) -> ScriptValidateResponse:
        payload = self._validate_bridge_payload("script_validate", request)
        response = await self._bridge_call("script_validate", self.bridge_client.script_validate, payload)
        return self._parse_bridge_response("script_validate", ScriptValidateResponse, response)

    async def scene_inspect(self, request: SceneInspectRequest) -> SceneInspectResponse:
        payload = self._validate_bridge_payload("scene_inspect", request)
        response = await self._bridge_call("scene_inspect", self.bridge_client.scene_inspect, payload)
        return self._parse_bridge_response("scene_inspect", SceneInspectResponse, response)

    async def node_get_properties(self, request: NodeGetPropertiesRequest) -> NodeGetPropertiesResponse:
        payload = self._validate_bridge_payload("node_get_properties", request)
        response = await self._bridge_call("node_get_properties", self.bridge_client.node_get_properties, payload)
        return self._parse_bridge_response("node_get_properties", NodeGetPropertiesResponse, response)


def _resolve_script_path(project_dir: Path, raw_path: str) -> Path:
    """Resolve a script path relative to the project directory."""
    clean = raw_path.strip()
    if clean.startswith("res://"):
        clean = clean[6:]
    resolved = (project_dir / clean).resolve()
    if not str(resolved).startswith(str(project_dir.resolve())):
        raise MCPError(
            code="PATH_TRAVERSAL",
            message="Script path must be within the project directory.",
            details={"script_path": raw_path, "project_path": str(project_dir)},
        )
    if not clean.endswith(".gd"):
        resolved = resolved.with_suffix(".gd")
    return resolved
