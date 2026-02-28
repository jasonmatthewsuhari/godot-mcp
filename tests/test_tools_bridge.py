import asyncio
from pathlib import Path
from typing import Any

import pytest

from mcp_server.errors import MCPError
from mcp_server.models import (
    RenderCaptureRequest,
    RenderInteractRequest,
    SceneAddNodeRequest,
    SceneCreateRequest,
    SceneExportMeshLibraryRequest,
    SceneLoadSpriteRequest,
    SceneSaveRequest,
    UidGetRequest,
    UidRefreshReferencesRequest,
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


def test_scene_create_bridge_wiring(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["scene_create"] = {"scene_path": "res://scenes/new.tscn", "uid": "uid://123"}
    result = asyncio.run(
        srv.scene_create(
            SceneCreateRequest(project_path=str(project), scene_path="res://scenes/new.tscn", root_node_type="Node2D")
        )
    )
    assert result.scene_path.endswith("new.tscn")
    assert bridge.calls[0][0] == "scene_create"


def test_all_wave2_tools_call_expected_bridge_method(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    cases = [
        (
            "scene_add_node",
            SceneAddNodeRequest(
                project_path=str(project),
                scene_path="res://a.tscn",
                parent_node_path=".",
                node_type="Sprite2D",
                node_name="Sprite",
            ),
            {"node_path": "Node2D/Sprite"},
            srv.scene_add_node,
        ),
        (
            "scene_load_sprite",
            SceneLoadSpriteRequest(
                project_path=str(project),
                scene_path="res://a.tscn",
                sprite_node_path="Node2D/Sprite",
                texture_path="res://art/sprite.png",
            ),
            {"sprite_node_path": "Node2D/Sprite", "texture_uid": "uid://tex"},
            srv.scene_load_sprite,
        ),
        (
            "scene_export_mesh_library",
            SceneExportMeshLibraryRequest(
                project_path=str(project),
                source_scene_path="res://src.tscn",
                mesh_library_path="res://lib.meshlib",
            ),
            {"mesh_library_path": "res://lib.meshlib", "item_count": 2},
            srv.scene_export_mesh_library,
        ),
        (
            "scene_save",
            SceneSaveRequest(project_path=str(project), scene_path="res://a.tscn"),
            {"saved_path": "res://a.tscn", "uid": "uid://scene"},
            srv.scene_save,
        ),
        (
            "uid_get",
            UidGetRequest(project_path=str(project), resource_path="res://a.tscn"),
            {"uid": "uid://abc"},
            srv.uid_get,
        ),
        (
            "uid_refresh_references",
            UidRefreshReferencesRequest(project_path=str(project), paths=["res://a.tscn"]),
            {"updated_count": 1, "updated_paths": ["res://a.tscn"]},
            srv.uid_refresh_references,
        ),
        (
            "render_capture",
            RenderCaptureRequest(project_path=str(project)),
            {"image_path": "C:/tmp/a.png", "width": 1280, "height": 720, "timestamp": "2026-02-28T00:00:00Z"},
            srv.render_capture,
        ),
        (
            "render_interact",
            RenderInteractRequest(project_path=str(project), mode="key_press", payload={"keycode": 65}),
            {"ok": True, "details": {"accepted": True}},
            srv.render_interact,
        ),
    ]
    for name, request, response, handler in cases:
        bridge.responses[name] = response
        asyncio.run(handler(request))
    called = [call[0] for call in bridge.calls]
    assert called == [case[0] for case in cases]


def test_bridge_error_maps_to_mcperror_shape(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["scene_save"] = {"error": {"code": "BRIDGE_TIMEOUT", "message": "Timed out", "details": {"op": "save"}}}
    with pytest.raises(MCPError) as exc:
        asyncio.run(srv.scene_save(SceneSaveRequest(project_path=str(project), scene_path="res://a.tscn")))
    assert exc.value.code == "BRIDGE_TIMEOUT"
    assert exc.value.details["op"] == "save"
