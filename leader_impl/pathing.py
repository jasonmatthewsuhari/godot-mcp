from __future__ import annotations

import os

from .errors import ToolError


def normalize_path(path: str) -> str:
    return os.path.normcase(os.path.abspath(os.path.expanduser(path)))


def ensure_dir_exists(path: str, field_name: str) -> str:
    normalized = normalize_path(path)
    if not os.path.isdir(normalized):
        raise ToolError(
            code="invalid_path",
            message=f"{field_name} is not a directory",
            details={"field": field_name, "path": path},
        )
    return normalized


def ensure_project_path(project_path: str) -> str:
    normalized = ensure_dir_exists(project_path, "project_path")
    project_file = os.path.join(normalized, "project.godot")
    if not os.path.isfile(project_file):
        raise ToolError(
            code="invalid_project",
            message="project.godot not found",
            details={"project_path": project_path},
        )
    return normalized

