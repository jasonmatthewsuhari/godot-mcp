"""Auto-installer for the Godot MCP bridge addon."""

from __future__ import annotations

import shutil
from pathlib import Path


class AddonInstaller:
    ADDON_DIR_NAME = "mistral_mcp_bridge"

    def __init__(self, addon_source: Path | None = None) -> None:
        self._source = addon_source or (
            Path(__file__).parent.parent / "godot_addon" / "addons" / self.ADDON_DIR_NAME
        )

    def is_installed(self, project_path: Path) -> bool:
        return (project_path / "addons" / self.ADDON_DIR_NAME / "bridge_entry.gd").is_file()

    def install(self, project_path: Path) -> Path:
        target = project_path / "addons" / self.ADDON_DIR_NAME
        if target.exists():
            shutil.rmtree(str(target))
        shutil.copytree(str(self._source), str(target))
        return target

    def ensure_installed(self, project_path: Path) -> bool:
        if self.is_installed(project_path):
            return False
        self.install(project_path)
        return True
