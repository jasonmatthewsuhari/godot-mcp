"""Project scaffolding and scene diffing tool handlers."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..errors import MCPError
from ..models import (
    AssetImportRequest,
    AssetImportResponse,
    ProjectCreateFromTemplateRequest,
    ProjectCreateFromTemplateResponse,
    ProjectGetDependenciesRequest,
    ProjectGetDependenciesResponse,
    SceneDiffRequest,
    SceneDiffResponse,
)
from ..pathing import ensure_project_directory
from ..scene_parser import diff_scenes, parse_tscn_file
from .definitions import ToolDefinition

_EXT_RESOURCE_PATTERN = "[ext_resource"


class ProjectToolsMixin:
    """Mixin providing project scaffolding and scene diffing tools."""

    def _get_project_definitions(self) -> dict[str, ToolDefinition]:
        return {
            "project_create_from_template": ToolDefinition(
                name="project_create_from_template",
                description="Create a new Godot project from a template directory.",
                request_model=ProjectCreateFromTemplateRequest,
                response_model=ProjectCreateFromTemplateResponse,
                handler=self.project_create_from_template,
            ),
            "project_get_dependencies": ToolDefinition(
                name="project_get_dependencies",
                description="Parse scene/resource files for external resource dependencies.",
                request_model=ProjectGetDependenciesRequest,
                response_model=ProjectGetDependenciesResponse,
                handler=self.project_get_dependencies,
            ),
            "asset_import": ToolDefinition(
                name="asset_import",
                description="Copy an asset file into a Godot project and trigger re-scan.",
                request_model=AssetImportRequest,
                response_model=AssetImportResponse,
                handler=self.asset_import,
            ),
            "scene_diff": ToolDefinition(
                name="scene_diff",
                description="Diff two .tscn scene files and return structural changes.",
                request_model=SceneDiffRequest,
                response_model=SceneDiffResponse,
                handler=self.scene_diff,
            ),
        }

    async def project_create_from_template(
        self, request: ProjectCreateFromTemplateRequest
    ) -> ProjectCreateFromTemplateResponse:
        template = Path(request.template_path).resolve()
        if not template.is_dir():
            raise MCPError(
                code="TEMPLATE_NOT_FOUND",
                message="Template directory not found.",
                details={"template_path": str(template)},
            )

        target = Path(request.target_path).resolve() / request.project_name
        if target.exists():
            raise MCPError(
                code="TARGET_EXISTS",
                message="Target project directory already exists.",
                details={"target_path": str(target)},
            )

        shutil.copytree(str(template), str(target))

        replacements = request.replacements or {}
        replacements.setdefault("project_name", request.project_name)

        files_created = 0
        for file_path in target.rglob("*"):
            if file_path.is_file():
                files_created += 1
                if file_path.suffix in {".godot", ".cfg", ".tscn", ".tres", ".gd", ".txt", ".md"}:
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        for key, value in replacements.items():
                            content = content.replace(f"{{{{{key}}}}}", value)
                        file_path.write_text(content, encoding="utf-8")
                    except (UnicodeDecodeError, PermissionError):
                        pass

        return ProjectCreateFromTemplateResponse(
            project_path=str(target),
            files_created=files_created,
        )

    async def project_get_dependencies(
        self, request: ProjectGetDependenciesRequest
    ) -> ProjectGetDependenciesResponse:
        project_dir = ensure_project_directory(request.project_path)
        deps: list[dict[str, object]] = []
        total = 0

        for ext in ("*.tscn", "*.tres"):
            for file_path in project_dir.rglob(ext):
                total += 1
                resource_deps = _extract_ext_resources(file_path)
                if resource_deps:
                    rel = str(file_path.relative_to(project_dir))
                    deps.append({"source": f"res://{rel}", "depends_on": resource_deps})

        return ProjectGetDependenciesResponse(
            dependencies=deps,
            total_resources=total,
        )

    async def asset_import(self, request: AssetImportRequest) -> AssetImportResponse:
        project_dir = ensure_project_directory(request.project_path)
        source = Path(request.source_path).resolve()
        if not source.is_file():
            raise MCPError(
                code="SOURCE_NOT_FOUND",
                message="Source asset file not found.",
                details={"source_path": str(source)},
            )

        target_rel = request.target_path.strip()
        if target_rel.startswith("res://"):
            target_rel = target_rel[6:]
        target = (project_dir / target_rel).resolve()

        if not str(target).startswith(str(project_dir.resolve())):
            raise MCPError(
                code="PATH_TRAVERSAL",
                message="Target path must be within the project directory.",
                details={"target_path": request.target_path},
            )

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(target))

        if request.scan_after and self.bridge_client:
            try:
                payload = {"project_path": str(project_dir)}
                await self._bridge_call("asset_import", self.bridge_client.asset_import, payload)
            except MCPError:
                pass

        return AssetImportResponse(imported_path=str(target))

    async def scene_diff(self, request: SceneDiffRequest) -> SceneDiffResponse:
        project_dir = ensure_project_directory(request.project_path)

        path_a = _resolve_scene_path(project_dir, request.scene_path_a)
        path_b = _resolve_scene_path(project_dir, request.scene_path_b)

        if not path_a.is_file():
            raise MCPError(
                code="SCENE_NOT_FOUND",
                message="Scene A not found.",
                details={"scene_path": str(path_a)},
            )
        if not path_b.is_file():
            raise MCPError(
                code="SCENE_NOT_FOUND",
                message="Scene B not found.",
                details={"scene_path": str(path_b)},
            )

        scene_a = parse_tscn_file(path_a)
        scene_b = parse_tscn_file(path_b)
        result = diff_scenes(scene_a, scene_b)

        return SceneDiffResponse(
            added_nodes=result["added_nodes"],
            removed_nodes=result["removed_nodes"],
            changed_properties=result["changed_properties"],
        )


def _extract_ext_resources(file_path: Path) -> list[str]:
    """Extract external resource paths from a .tscn/.tres file."""
    resources: list[str] = []
    try:
        for line in file_path.read_text(encoding="utf-8").splitlines():
            if _EXT_RESOURCE_PATTERN in line:
                start = line.find('path="')
                if start != -1:
                    start += 6
                    end = line.find('"', start)
                    if end != -1:
                        resources.append(line[start:end])
    except (UnicodeDecodeError, PermissionError):
        pass
    return resources


def _resolve_scene_path(project_dir: Path, raw_path: str) -> Path:
    """Resolve a scene path relative to the project directory."""
    clean = raw_path.strip()
    if clean.startswith("res://"):
        clean = clean[6:]
    return (project_dir / clean).resolve()
