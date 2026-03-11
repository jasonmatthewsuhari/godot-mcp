"""Tests for 3D world building tools."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from mcp_server.models import (
    AnimationAddKeyframeRequest,
    AnimationCreateRequest,
    CsgOperationsRequest,
    EnvironmentSetupRequest,
    GridmapPlaceRequest,
    MaterialApplyRequest,
    MaterialCreateRequest,
    TilemapPaintRequest,
)
from mcp_server.tools import GodotToolService


class FakeBridgeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.responses: dict[str, dict[str, Any]] = {}

    def _call(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((name, payload))
        return self.responses.get(name, {"ok": True})

    def __getattr__(self, name: str) -> Any:
        return lambda p: self._call(name, p)


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


def test_tilemap_paint_bridge_wiring(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["tilemap_paint"] = {"painted_count": 3}
    result = asyncio.run(
        srv.tilemap_paint(
            TilemapPaintRequest(
                project_path=str(project),
                scene_path="res://main.tscn",
                tilemap_node_path="Root/TileMap",
                cells=[{"x": 0, "y": 0, "tile": 1}, {"x": 1, "y": 0, "tile": 1}, {"x": 2, "y": 0, "tile": 2}],
            )
        )
    )
    assert result.painted_count == 3
    assert bridge.calls[0][0] == "tilemap_paint"


def test_material_create_bridge_wiring(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["material_create"] = {"material_path": "res://materials/ground.tres", "uid": "uid://mat1"}
    result = asyncio.run(
        srv.material_create(
            MaterialCreateRequest(
                project_path=str(project),
                material_path="res://materials/ground.tres",
                properties={"albedo_color": "#00FF00"},
            )
        )
    )
    assert result.material_path == "res://materials/ground.tres"


def test_csg_operations_bridge_wiring(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["csg_operations"] = {"node_path": "Root/CSGBox"}
    result = asyncio.run(
        srv.csg_operations(
            CsgOperationsRequest(
                project_path=str(project),
                scene_path="res://main.tscn",
                parent_node_path="Root",
                operation="union",
                shape_type="CSGBox3D",
                node_name="CSGBox",
            )
        )
    )
    assert result.node_path == "Root/CSGBox"


def test_animation_create_bridge_wiring(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["animation_create"] = {"animation_name": "walk"}
    result = asyncio.run(
        srv.animation_create(
            AnimationCreateRequest(
                project_path=str(project),
                scene_path="res://main.tscn",
                animation_player_path="Root/AnimationPlayer",
                animation_name="walk",
                length=1.0,
            )
        )
    )
    assert result.animation_name == "walk"


def test_animation_add_keyframe_bridge_wiring(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["animation_add_keyframe"] = {"track_path": "Root/Sprite:position", "time": 0.5, "track_index": 0}
    result = asyncio.run(
        srv.animation_add_keyframe(
            AnimationAddKeyframeRequest(
                project_path=str(project),
                scene_path="res://main.tscn",
                animation_player_path="Root/AnimationPlayer",
                animation_name="walk",
                track_path="Root/Sprite:position",
                time=0.5,
                value={"x": 100, "y": 200},
            )
        )
    )
    assert result.track_path == "Root/Sprite:position"
    assert result.time == 0.5


def test_world_tools_in_definitions(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, _ = service
    defs = srv.get_definitions()
    expected = [
        "tilemap_paint", "gridmap_place", "material_create", "material_apply",
        "environment_setup", "csg_operations", "animation_create", "animation_add_keyframe",
    ]
    for name in expected:
        assert name in defs, f"{name} not in definitions"
