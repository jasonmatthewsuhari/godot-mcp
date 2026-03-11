from __future__ import annotations

import os
import shutil
import subprocess
from typing import Iterable


COMMON_WINDOWS_PATHS = (
    r"C:\Program Files\Godot\Godot_v4.4-stable_win64.exe",
    r"C:\Program Files\Godot Engine\godot.exe",
    r"C:\Program Files\Godot Engine\godot4.exe",
)


def _first_existing(paths: Iterable[str]) -> str | None:
    for p in paths:
        if p and os.path.isfile(p):
            return p
    return None


def find_godot_executable() -> str | None:
    env_path = os.environ.get("GODOT_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    for name in ("godot.exe", "godot4.exe", "godot"):
        resolved = shutil.which(name)
        if resolved:
            return resolved

    return _first_existing(COMMON_WINDOWS_PATHS)


def get_godot_version(godot_path: str) -> str:
    try:
        result = subprocess.run(
            [godot_path, "--version"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except OSError:
        return "unknown"
    return (result.stdout or result.stderr).strip() or "unknown"

