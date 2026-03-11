from __future__ import annotations

import os

from .models import AnalyzeProjectResponse, ProjectEntry
from .pathing import ensure_dir_exists, ensure_project_path


SCENE_EXTENSIONS = {".tscn", ".scn"}
SCRIPT_EXTENSIONS = {".gd", ".cs", ".gdshader", ".gdextension"}
RESOURCE_EXTENSIONS = {".res", ".tres", ".import", ".png", ".jpg", ".jpeg", ".webp"}


def list_projects(root_path: str) -> list[ProjectEntry]:
    root = ensure_dir_exists(root_path, "root_path")
    projects: list[ProjectEntry] = []
    for current_root, _, files in os.walk(root):
        if "project.godot" in files:
            projects.append(
                ProjectEntry(
                    name=os.path.basename(current_root),
                    path=current_root,
                    project_file=os.path.join(current_root, "project.godot"),
                )
            )
    projects.sort(key=lambda p: p.path.lower())
    return projects


def _parse_project_file(project_file: str) -> tuple[dict[str, str], dict[str, str], str | None]:
    config: dict[str, str] = {}
    autoloads: dict[str, str] = {}
    section = ""
    with open(project_file, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith(";"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1].strip().lower()
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"')
            full_key = f"{section}.{key}" if section else key
            config[full_key] = value
            if section == "autoload":
                autoloads[key] = value

    main_scene = config.get("application.run/main_scene") or config.get("application.main_scene")
    return config, autoloads, main_scene


def analyze_project(project_path: str) -> AnalyzeProjectResponse:
    project = ensure_project_path(project_path)
    project_file = os.path.join(project, "project.godot")
    config, autoloads, main_scene = _parse_project_file(project_file)

    scenes: list[str] = []
    scripts: list[str] = []
    resources: list[str] = []
    plugins: list[str] = []

    for current_root, _, files in os.walk(project):
        for file_name in files:
            ext = os.path.splitext(file_name)[1].lower()
            full_path = os.path.join(current_root, file_name)
            rel_path = os.path.relpath(full_path, project).replace("\\", "/")

            if ext in SCENE_EXTENSIONS:
                scenes.append(rel_path)
            elif ext in SCRIPT_EXTENSIONS:
                scripts.append(rel_path)
            elif ext in RESOURCE_EXTENSIONS:
                resources.append(rel_path)

            if file_name.endswith(".gdextension") or "plugin" in file_name.lower():
                plugins.append(rel_path)

    scenes.sort()
    scripts.sort()
    resources.sort()
    plugins.sort()

    return AnalyzeProjectResponse(
        path=project,
        name=os.path.basename(project),
        scenes=scenes,
        scripts=scripts,
        resources=resources,
        plugins=plugins,
        autoloads=autoloads,
        main_scene=main_scene,
        config=config,
    )

