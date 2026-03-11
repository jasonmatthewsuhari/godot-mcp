"""Tests for batch execution tool."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from mcp_server.models import BatchExecuteRequest
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


def test_batch_execute_multiple_success(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["scene_create"] = {"scene_path": "res://a.tscn", "uid": "uid://a"}
    bridge.responses["scene_save"] = {"saved_path": "res://a.tscn"}

    request = BatchExecuteRequest(
        operations=[
            {
                "tool_name": "scene_create",
                "arguments": {
                    "project_path": str(project),
                    "scene_path": "res://a.tscn",
                    "root_node_type": "Node2D",
                },
            },
            {
                "tool_name": "scene_save",
                "arguments": {
                    "project_path": str(project),
                    "scene_path": "res://a.tscn",
                },
            },
        ],
        atomic=True,
    )
    result = asyncio.run(srv.batch_execute(request))
    assert result.total == 2
    assert result.succeeded == 2
    assert result.failed == 0
    assert result.results[0]["success"] is True
    assert result.results[1]["success"] is True


def test_batch_execute_atomic_stops_on_error(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["scene_create"] = {"scene_path": "res://a.tscn", "uid": "uid://a"}
    bridge.responses["scene_save"] = {"saved_path": "res://a.tscn"}

    request = BatchExecuteRequest(
        operations=[
            {
                "tool_name": "scene_create",
                "arguments": {
                    "project_path": str(project),
                    "scene_path": "res://a.tscn",
                    "root_node_type": "Node2D",
                },
            },
            {
                "tool_name": "nonexistent_tool",
                "arguments": {},
            },
            {
                "tool_name": "scene_save",
                "arguments": {
                    "project_path": str(project),
                    "scene_path": "res://a.tscn",
                },
            },
        ],
        atomic=True,
    )
    result = asyncio.run(srv.batch_execute(request))
    assert result.succeeded == 1
    assert result.failed == 1
    assert result.total == 2
    assert result.results[1]["success"] is False
    assert "Unknown tool" in result.results[1]["error"]


def test_batch_execute_in_definitions(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, _ = service
    defs = srv.get_definitions()
    assert "batch_execute" in defs
