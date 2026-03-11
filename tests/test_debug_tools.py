"""Tests for debug and feedback loop tools."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from mcp_server.models import (
    GodotGetErrorsRequest,
    SignalPollRequest,
    SignalWatchRequest,
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


def test_signal_watch_bridge_wiring(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["signal_watch"] = {"watching": ["pressed", "released"], "node_path": "Root/Button"}
    result = asyncio.run(
        srv.signal_watch(
            SignalWatchRequest(
                project_path=str(project),
                scene_path="res://main.tscn",
                node_path="Root/Button",
                signals=["pressed", "released"],
            )
        )
    )
    assert result.watching == ["pressed", "released"]
    assert result.node_path == "Root/Button"
    assert bridge.calls[0][0] == "signal_watch"


def test_signal_poll_bridge_wiring(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, bridge, project = service
    bridge.responses["signal_poll"] = {
        "emissions": [
            {"signal_name": "pressed", "node_path": "Root/Button", "timestamp": "2026-01-01T00:00:00Z"},
        ],
        "total": 1,
    }
    result = asyncio.run(
        srv.signal_poll(
            SignalPollRequest(project_path=str(project))
        )
    )
    assert result.total == 1
    assert result.emissions[0].signal_name == "pressed"


def test_debug_tools_in_definitions(service: tuple[GodotToolService, FakeBridgeClient, Path]) -> None:
    srv, _, _ = service
    defs = srv.get_definitions()
    for name in ["godot_get_errors", "signal_watch", "signal_poll"]:
        assert name in defs, f"{name} not in definitions"
