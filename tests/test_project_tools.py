"""Tests for project scaffolding and scene diffing tools."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from mcp_server.errors import MCPError
from mcp_server.models import (
    AssetImportRequest,
    ProjectCreateFromTemplateRequest,
    ProjectGetDependenciesRequest,
    SceneDiffRequest,
)
from mcp_server.tools import GodotToolService


class FakeBridgeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.responses: dict[str, dict[str, Any]] = {}

    def _call(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((name, payload))
        return self.responses.get(name, {"ok": True})

    def scene_create(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("scene_create", p)
    def scene_add_node(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("scene_add_node", p)
    def scene_load_sprite(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("scene_load_sprite", p)
    def scene_export_mesh_library(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("scene_export_mesh_library", p)
    def scene_save(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("scene_save", p)
    def uid_get(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("uid_get", p)
    def uid_refresh_references(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("uid_refresh_references", p)
    def render_capture(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("render_capture", p)
    def render_interact(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("render_interact", p)
    def script_attach(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("script_attach", p)
    def script_validate(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("script_validate", p)
    def scene_inspect(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("scene_inspect", p)
    def node_get_properties(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("node_get_properties", p)
    def asset_import(self, p: dict[str, Any]) -> dict[str, Any]: return self._call("asset_import", p)


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


def test_project_create_from_template(service: tuple[GodotToolService, FakeBridgeClient, Path], tmp_path: Path) -> None:
    srv, _, _ = service
    template = tmp_path / "template"
    template.mkdir()
    (template / "project.godot").write_text('config/name="{{project_name}}"\n', encoding="utf-8")
    (template / "main.gd").write_text("extends Node\n", encoding="utf-8")

    result = asyncio.run(
        srv.project_create_from_template(
            ProjectCreateFromTemplateRequest(
                template_path=str(template),
                target_path=str(tmp_path / "output"),
                project_name="MyGame",
            )
        )
    )
    assert Path(result.project_path).is_dir()
    assert result.files_created == 2
    godot_file = Path(result.project_path) / "project.godot"
    assert 'config/name="MyGame"' in godot_file.read_text(encoding="utf-8")


def test_project_create_template_not_found(service: tuple[GodotToolService, FakeBridgeClient, Path], tmp_path: Path) -> None:
    srv, _, _ = service
    with pytest.raises(MCPError) as exc:
        asyncio.run(
            srv.project_create_from_template(
                ProjectCreateFromTemplateRequest(
                    template_path=str(tmp_path / "nonexistent"),
                    target_path=str(tmp_path),
                    project_name="MyGame",
                )
            )
        )
    assert exc.value.code == "TEMPLATE_NOT_FOUND"


def test_project_get_dependencies(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, project = service
    scenes = project / "scenes"
    scenes.mkdir()
    (scenes / "main.tscn").write_text(
        '[gd_scene format=3]\n'
        '[ext_resource type="Script" path="res://scripts/main.gd" id="1"]\n'
        '[ext_resource type="Texture" path="res://art/icon.png" id="2"]\n'
        '[node name="Root" type="Node2D"]\n',
        encoding="utf-8",
    )

    result = asyncio.run(
        srv.project_get_dependencies(
            ProjectGetDependenciesRequest(project_path=str(project))
        )
    )
    assert result.total_resources == 1
    assert len(result.dependencies) == 1
    assert "res://scripts/main.gd" in result.dependencies[0].depends_on


def test_asset_import_copies_file(service: tuple[GodotToolService, FakeBridgeClient, Path], tmp_path: Path) -> None:
    srv, _, project = service
    source = tmp_path / "source_icon.png"
    source.write_bytes(b"PNG_DATA")

    result = asyncio.run(
        srv.asset_import(
            AssetImportRequest(
                project_path=str(project),
                source_path=str(source),
                target_path="res://art/icon.png",
                scan_after=False,
            )
        )
    )
    imported = Path(result.imported_path)
    assert imported.is_file()
    assert imported.read_bytes() == b"PNG_DATA"


def test_asset_import_source_not_found(service: tuple[GodotToolService, FakeBridgeClient, Path], tmp_path: Path) -> None:
    srv, _, project = service
    with pytest.raises(MCPError) as exc:
        asyncio.run(
            srv.asset_import(
                AssetImportRequest(
                    project_path=str(project),
                    source_path=str(tmp_path / "missing.png"),
                    target_path="art/icon.png",
                )
            )
        )
    assert exc.value.code == "SOURCE_NOT_FOUND"


def test_scene_diff(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, project = service
    scenes = project / "scenes"
    scenes.mkdir()
    (scenes / "a.tscn").write_text(
        '[gd_scene format=3]\n'
        '[node name="Root" type="Node2D"]\n'
        '[node name="Player" type="Sprite2D" parent="."]\n',
        encoding="utf-8",
    )
    (scenes / "b.tscn").write_text(
        '[gd_scene format=3]\n'
        '[node name="Root" type="Node2D"]\n'
        '[node name="Enemy" type="Sprite2D" parent="."]\n',
        encoding="utf-8",
    )

    result = asyncio.run(
        srv.scene_diff(
            SceneDiffRequest(
                project_path=str(project),
                scene_path_a="scenes/a.tscn",
                scene_path_b="scenes/b.tscn",
            )
        )
    )
    assert "Enemy" in result.added_nodes
    assert "Player" in result.removed_nodes


def test_phase2_tools_in_definitions(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, _ = service
    defs = srv.get_definitions()
    for name in ["project_create_from_template", "project_get_dependencies", "asset_import", "scene_diff"]:
        assert name in defs, f"{name} not in definitions"
