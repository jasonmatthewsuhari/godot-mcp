"""Tests for Phase 7: External Assets & DX tools."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from mcp_server.addon_installer import AddonInstaller
from mcp_server.bridge_client import GodotBridgeClient
from mcp_server.bridge_registry import BridgeRegistry
from mcp_server.tools import GodotToolService


# ---------------------------------------------------------------------------
# AddonInstaller
# ---------------------------------------------------------------------------


class TestAddonInstaller:
    def test_is_installed_false_when_missing(self, tmp_path: Path) -> None:
        installer = AddonInstaller(addon_source=tmp_path / "src_addon")
        assert installer.is_installed(tmp_path) is False

    def test_install_copies_addon(self, tmp_path: Path) -> None:
        source = tmp_path / "src_addon"
        source.mkdir()
        (source / "bridge_entry.gd").write_text("# stub", encoding="utf-8")

        installer = AddonInstaller(addon_source=source)
        target = installer.install(tmp_path)

        assert target == tmp_path / "addons" / AddonInstaller.ADDON_DIR_NAME
        assert (target / "bridge_entry.gd").is_file()

    def test_is_installed_true_after_install(self, tmp_path: Path) -> None:
        source = tmp_path / "src_addon"
        source.mkdir()
        (source / "bridge_entry.gd").write_text("# stub", encoding="utf-8")

        installer = AddonInstaller(addon_source=source)
        installer.install(tmp_path)
        assert installer.is_installed(tmp_path) is True

    def test_ensure_installed_skips_when_present(self, tmp_path: Path) -> None:
        source = tmp_path / "src_addon"
        source.mkdir()
        (source / "bridge_entry.gd").write_text("# stub", encoding="utf-8")

        installer = AddonInstaller(addon_source=source)
        installer.install(tmp_path)

        assert installer.ensure_installed(tmp_path) is False

    def test_ensure_installed_installs_when_missing(self, tmp_path: Path) -> None:
        source = tmp_path / "src_addon"
        source.mkdir()
        (source / "bridge_entry.gd").write_text("# stub", encoding="utf-8")

        installer = AddonInstaller(addon_source=source)
        assert installer.ensure_installed(tmp_path) is True
        assert installer.is_installed(tmp_path) is True


# ---------------------------------------------------------------------------
# BridgeRegistry
# ---------------------------------------------------------------------------


class TestBridgeRegistry:
    def _make_client(self) -> GodotBridgeClient:
        return GodotBridgeClient(
            base_url="http://127.0.0.1:19110",
            token="test",
        )

    def test_register_and_get(self) -> None:
        registry = BridgeRegistry()
        client = self._make_client()
        registry.register("/projects/demo", client)
        assert registry.get("/projects/demo") is client

    def test_get_returns_none_for_unknown(self) -> None:
        registry = BridgeRegistry()
        assert registry.get("/projects/missing") is None

    def test_unregister_removes_entry(self) -> None:
        registry = BridgeRegistry()
        client = self._make_client()
        registry.register("/projects/demo", client)
        assert registry.unregister("/projects/demo") is True
        assert registry.get("/projects/demo") is None

    def test_unregister_returns_false_for_unknown(self) -> None:
        registry = BridgeRegistry()
        assert registry.unregister("/projects/missing") is False

    def test_list_projects(self) -> None:
        registry = BridgeRegistry()
        c1 = self._make_client()
        c2 = self._make_client()
        registry.register("/a", c1)
        registry.register("/b", c2)
        assert sorted(registry.list_projects()) == ["/a", "/b"]


# ---------------------------------------------------------------------------
# Tool definitions include asset and dx tools
# ---------------------------------------------------------------------------


class TestAssetDxDefinitions:
    def test_asset_tools_in_definitions(self) -> None:
        service = GodotToolService.__new__(GodotToolService)
        defs = service._get_asset_definitions()
        assert "asset_search_online" in defs
        assert "asset_download_3d" in defs

    def test_dx_tools_in_definitions(self) -> None:
        service = GodotToolService.__new__(GodotToolService)
        defs = service._get_dx_definitions()
        assert "godot_quick_start" in defs

    def test_all_definitions_include_new_tools(self) -> None:
        service = GodotToolService(
            bridge_client=GodotBridgeClient(
                base_url="http://127.0.0.1:19110",
                token="test",
            )
        )
        defs = service.get_definitions()
        assert "asset_search_online" in defs
        assert "asset_download_3d" in defs
        assert "godot_quick_start" in defs
