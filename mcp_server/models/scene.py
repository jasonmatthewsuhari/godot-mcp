"""Pydantic schemas for scene tool inputs and outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SceneCreateRequest(BaseModel):
    """Input schema for scene creation."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    root_node_type: str = Field(min_length=1)
    options: dict[str, object] | None = None


class SceneCreateResponse(BaseModel):
    """Output schema for scene creation."""

    scene_path: str
    uid: str | None = None


class SceneAddNodeRequest(BaseModel):
    """Input schema for adding a node to a scene."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    parent_node_path: str = Field(min_length=1)
    node_type: str = Field(min_length=1)
    node_name: str = Field(min_length=1)
    properties: dict[str, object] | None = None


class SceneAddNodeResponse(BaseModel):
    """Output schema for adding a scene node."""

    node_path: str


class SceneLoadSpriteRequest(BaseModel):
    """Input schema for loading sprite texture in a scene."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    sprite_node_path: str = Field(min_length=1)
    texture_path: str = Field(min_length=1)
    import_if_needed: bool = True


class SceneLoadSpriteResponse(BaseModel):
    """Output schema for sprite load operation."""

    sprite_node_path: str
    texture_uid: str | None = None


class SceneExportMeshLibraryRequest(BaseModel):
    """Input schema for mesh library export."""

    project_path: str = Field(min_length=1)
    source_scene_path: str = Field(min_length=1)
    mesh_library_path: str = Field(min_length=1)
    options: dict[str, object] | None = None


class SceneExportMeshLibraryResponse(BaseModel):
    """Output schema for mesh library export."""

    mesh_library_path: str
    item_count: int


class SceneSaveRequest(BaseModel):
    """Input schema for saving a scene variant."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    variant_name: str | None = None
    make_inherited: bool = False


class SceneSaveResponse(BaseModel):
    """Output schema for scene save operation."""

    saved_path: str
    uid: str | None = None
