"""Pydantic schemas for project scaffolding and scene diffing tools."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectCreateFromTemplateRequest(BaseModel):
    """Input schema for creating a project from a template."""

    template_path: str = Field(min_length=1)
    target_path: str = Field(min_length=1)
    project_name: str = Field(min_length=1)
    replacements: dict[str, str] | None = None


class ProjectCreateFromTemplateResponse(BaseModel):
    """Output schema for project creation from template."""

    project_path: str
    files_created: int


class ProjectGetDependenciesRequest(BaseModel):
    """Input schema for project dependency analysis."""

    project_path: str = Field(min_length=1)


class DependencyEntry(BaseModel):
    """A dependency relationship between resources."""

    source: str
    depends_on: list[str]


class ProjectGetDependenciesResponse(BaseModel):
    """Output schema for project dependency analysis."""

    dependencies: list[DependencyEntry]
    total_resources: int


class AssetImportRequest(BaseModel):
    """Input schema for importing an asset into a project."""

    project_path: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    target_path: str = Field(min_length=1)
    scan_after: bool = True


class AssetImportResponse(BaseModel):
    """Output schema for asset import."""

    imported_path: str


class SceneDiffNodeChange(BaseModel):
    """A changed property on a node between two scenes."""

    property: str
    old_value: str
    new_value: str


class SceneDiffRequest(BaseModel):
    """Input schema for diffing two scene files."""

    project_path: str = Field(min_length=1)
    scene_path_a: str = Field(min_length=1)
    scene_path_b: str = Field(min_length=1)


class SceneDiffResponse(BaseModel):
    """Output schema for scene diff."""

    added_nodes: list[str]
    removed_nodes: list[str]
    changed_properties: list[SceneDiffNodeChange]
