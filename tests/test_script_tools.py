"""Tests for script editing and scene introspection tools."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from mcp_server.errors import MCPError
from mcp_server.models import (
    NodeGetPropertiesRequest,
    SceneInspectRequest,
    ScriptAttachRequest,
    ScriptCreateRequest,
    ScriptEditOperation,
    ScriptEditRequest,
    ScriptValidateRequest,
)
from mcp_server.tools import GodotToolService


class FakeBridgeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.responses: dict[str, dict[str, Any]] = {}

    def _call(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((name, payload))
        return self.responses[name]

    def scene_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("scene_create", payload)

    def scene_add_node(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("scene_add_node", payload)

    def scene_load_sprite(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("scene_load_sprite", payload)

    def scene_export_mesh_library(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("scene_export_mesh_library", payload)

    def scene_save(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("scene_save", payload)

    def uid_get(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("uid_get", payload)

    def uid_refresh_references(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("uid_refresh_references", payload)

    def render_capture(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("render_capture", payload)

    def render_interact(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("render_interact", payload)

    def script_attach(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("script_attach", payload)

    def script_validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("script_validate", payload)

    def scene_inspect(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("scene_inspect", payload)

    def node_get_properties(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._call("node_get_properties", payload)


def _create_project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    project.mkdir()
    (project / "project.godot").write_text("[application]\n", encoding="utf-8")
    return project


@pytest.fixture
def service(tmp_path: Path) -> tuple[GodotToolService, FakeBridgeClient, Path]:
    bridge = FakeBridgeClient()
    srv = GodotToolService(bridge_client=bridge)
    project = _create_project(tmp_path)
    return srv, bridge, project


def test_script_create_writes_file(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, project = service
    result = asyncio.run(
        srv.script_create(
            ScriptCreateRequest(
                project_path=str(project),
                script_path="scripts/player.gd",
                content="extends CharacterBody2D\n\nfunc _ready():\n\tpass\n",
            )
        )
    )
    assert result.script_path.endswith("player.gd")
    script_file = Path(result.script_path)
    assert script_file.is_file()
    assert "extends CharacterBody2D" in script_file.read_text(encoding="utf-8")


def test_script_create_with_class_name(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, project = service
    result = asyncio.run(
        srv.script_create(
            ScriptCreateRequest(
                project_path=str(project),
                script_path="scripts/player.gd",
                content="extends Node2D\n",
                class_name="Player",
            )
        )
    )
    content = Path(result.script_path).read_text(encoding="utf-8")
    assert content.startswith("class_name Player")
    assert "extends Node2D" in content


def test_script_create_with_res_path(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, project = service
    result = asyncio.run(
        srv.script_create(
            ScriptCreateRequest(
                project_path=str(project),
                script_path="res://scripts/enemy.gd",
                content="extends Node\n",
            )
        )
    )
    assert Path(result.script_path).is_file()


def test_script_edit_replace_lines(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, project = service
    script_file = project / "test.gd"
    script_file.write_text("line1\nline2\nline3\nline4\n", encoding="utf-8")

    result = asyncio.run(
        srv.script_edit(
            ScriptEditRequest(
                project_path=str(project),
                script_path="test.gd",
                operations=[
                    ScriptEditOperation(op="replace_lines", start=2, end=3, content="new_line2\nnew_line3\n"),
                ],
            )
        )
    )
    assert result.line_count == 4
    content = script_file.read_text(encoding="utf-8")
    assert "new_line2" in content
    assert "new_line3" in content
    assert "line1" in content
    assert "line4" in content


def test_script_edit_file_not_found(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, project = service
    with pytest.raises(MCPError) as exc:
        asyncio.run(
            srv.script_edit(
                ScriptEditRequest(
                    project_path=str(project),
                    script_path="nonexistent.gd",
                    operations=[
                        ScriptEditOperation(op="replace_lines", start=1, end=1, content="x\n"),
                    ],
                )
            )
        )
    assert exc.value.code == "SCRIPT_NOT_FOUND"


def test_script_edit_invalid_op(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, project = service
    script_file = project / "test.gd"
    script_file.write_text("line1\n", encoding="utf-8")

    with pytest.raises(MCPError) as exc:
        asyncio.run(
            srv.script_edit(
                ScriptEditRequest(
                    project_path=str(project),
                    script_path="test.gd",
                    operations=[
                        ScriptEditOperation(op="delete", start=1, end=1, content=""),
                    ],
                )
            )
        )
    assert exc.value.code == "INVALID_OPERATION"


def test_script_attach_bridge_wiring(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["script_attach"] = {"node_path": "Root/Player", "script_path": "res://scripts/player.gd"}
    result = asyncio.run(
        srv.script_attach(
            ScriptAttachRequest(
                project_path=str(project),
                scene_path="res://main.tscn",
                node_path="Root/Player",
                script_path="res://scripts/player.gd",
            )
        )
    )
    assert result.node_path == "Root/Player"
    assert result.script_path == "res://scripts/player.gd"
    assert bridge.calls[0][0] == "script_attach"


def test_script_validate_bridge_wiring(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["script_validate"] = {"valid": True, "errors": []}
    result = asyncio.run(
        srv.script_validate(
            ScriptValidateRequest(
                project_path=str(project),
                script_path="res://scripts/player.gd",
            )
        )
    )
    assert result.valid is True
    assert result.errors == []
    assert bridge.calls[0][0] == "script_validate"


def test_scene_inspect_bridge_wiring(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["scene_inspect"] = {
        "root": {
            "node_path": "Root",
            "type": "Node2D",
            "properties": {},
            "children": [
                {"node_path": "Root/Sprite", "type": "Sprite2D", "properties": {}, "children": []},
            ],
        }
    }
    result = asyncio.run(
        srv.scene_inspect(
            SceneInspectRequest(
                project_path=str(project),
                scene_path="res://main.tscn",
            )
        )
    )
    assert result.root.type == "Node2D"
    assert len(result.root.children) == 1
    assert result.root.children[0].type == "Sprite2D"
    assert bridge.calls[0][0] == "scene_inspect"


def test_node_get_properties_bridge_wiring(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["node_get_properties"] = {
        "node_path": "Root/Sprite",
        "type": "Sprite2D",
        "properties": {"position": {"x": 100, "y": 200}},
    }
    result = asyncio.run(
        srv.node_get_properties(
            NodeGetPropertiesRequest(
                project_path=str(project),
                scene_path="res://main.tscn",
                node_path="Root/Sprite",
            )
        )
    )
    assert result.type == "Sprite2D"
    assert result.properties["position"] == {"x": 100, "y": 200}
    assert bridge.calls[0][0] == "node_get_properties"


def test_script_create_prevents_path_traversal(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, project = service
    with pytest.raises(MCPError) as exc:
        asyncio.run(
            srv.script_create(
                ScriptCreateRequest(
                    project_path=str(project),
                    script_path="../../etc/evil.gd",
                    content="extends Node\n",
                )
            )
        )
    assert exc.value.code == "PATH_TRAVERSAL"


def test_new_tools_appear_in_definitions(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, _ = service
    defs = srv.get_definitions()
    expected_tools = [
        "script_create",
        "script_edit",
        "script_attach",
        "script_validate",
        "scene_inspect",
        "node_get_properties",
    ]
    for tool_name in expected_tools:
        assert tool_name in defs, f"{tool_name} not in definitions"
