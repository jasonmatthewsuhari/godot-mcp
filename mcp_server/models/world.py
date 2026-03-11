"""Pydantic schemas for 3D world building tools."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TilemapPaintRequest(BaseModel):
    """Input schema for painting tilemap cells."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    tilemap_node_path: str = Field(min_length=1)
    cells: list[dict[str, int]] = Field(min_length=1)
    layer: int = 0


class TilemapPaintResponse(BaseModel):
    """Output schema for tilemap painting."""

    painted_count: int


class GridmapPlaceRequest(BaseModel):
    """Input schema for placing items in a GridMap."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    gridmap_node_path: str = Field(min_length=1)
    placements: list[dict[str, object]] = Field(min_length=1)


class GridmapPlaceResponse(BaseModel):
    """Output schema for GridMap placement."""

    placed_count: int


class MaterialCreateRequest(BaseModel):
    """Input schema for creating a material resource."""

    project_path: str = Field(min_length=1)
    material_path: str = Field(min_length=1)
    material_type: Literal["standard", "orm", "unshaded"] = "standard"
    properties: dict[str, object] | None = None


class MaterialCreateResponse(BaseModel):
    """Output schema for material creation."""

    material_path: str
    uid: str | None = None


class MaterialApplyRequest(BaseModel):
    """Input schema for applying a material to a node."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    node_path: str = Field(min_length=1)
    material_path: str = Field(min_length=1)
    surface_index: int = 0


class MaterialApplyResponse(BaseModel):
    """Output schema for material application."""

    node_path: str
    material_path: str


class EnvironmentSetupRequest(BaseModel):
    """Input schema for configuring a 3D environment."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    background_mode: str = "sky"
    ambient_light_color: str | None = None
    fog_enabled: bool = False
    tonemap_mode: str | None = None


class EnvironmentSetupResponse(BaseModel):
    """Output schema for environment setup."""

    environment_path: str


class CsgOperationsRequest(BaseModel):
    """Input schema for CSG boolean operations."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    parent_node_path: str = Field(min_length=1)
    operation: Literal["union", "intersection", "subtraction"]
    shape_type: str = Field(min_length=1)
    shape_properties: dict[str, object] | None = None
    node_name: str = Field(min_length=1)


class CsgOperationsResponse(BaseModel):
    """Output schema for CSG operations."""

    node_path: str


class AnimationCreateRequest(BaseModel):
    """Input schema for creating an animation resource."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    animation_player_path: str = Field(min_length=1)
    animation_name: str = Field(min_length=1)
    length: float = Field(gt=0)
    loop: bool = False


class AnimationCreateResponse(BaseModel):
    """Output schema for animation creation."""

    animation_name: str


class AnimationAddKeyframeRequest(BaseModel):
    """Input schema for adding a keyframe to an animation."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    animation_player_path: str = Field(min_length=1)
    animation_name: str = Field(min_length=1)
    track_path: str = Field(min_length=1)
    time: float = Field(ge=0)
    value: object = None


class AnimationAddKeyframeResponse(BaseModel):
    """Output schema for adding a keyframe."""

    track_path: str
    time: float
    track_index: int
