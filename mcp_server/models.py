"""Pydantic schemas for MCP tool inputs and outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class GodotGetVersionRequest(BaseModel):
    """Input schema for version lookup."""


class GodotGetVersionResponse(BaseModel):
    """Output schema for version lookup."""

    version: str
    path: str


class ProjectInfo(BaseModel):
    """Godot project metadata."""

    name: str
    path: str
    project_file: str


class GodotListProjectsRequest(BaseModel):
    """Input schema for recursive project discovery."""

    root_path: str = Field(min_length=1)


class GodotListProjectsResponse(BaseModel):
    """Output schema for project discovery."""

    projects: list[ProjectInfo]


class GodotLaunchEditorRequest(BaseModel):
    """Input schema for launching Godot editor."""

    project_path: str = Field(min_length=1)
    headless: bool = False


class GodotLaunchEditorResponse(BaseModel):
    """Output schema for launching Godot editor."""

    session_id: str
    pid: int
    status: Literal["running", "exited"]


class GodotRunProjectRequest(BaseModel):
    """Input schema for running a Godot project."""

    project_path: str = Field(min_length=1)
    debug: bool = True
    scene_override: str | None = None


class GodotRunProjectResponse(BaseModel):
    """Output schema for running a project."""

    session_id: str
    pid: int
    status: Literal["running", "exited"]


class GodotStopExecutionRequest(BaseModel):
    """Input schema for stopping running Godot processes."""

    session_id: str | None = None


class GodotStopExecutionResponse(BaseModel):
    """Output schema for process stop results."""

    stopped: bool
    exit_code: int | None = None


class DebugOutputEntry(BaseModel):
    """One captured log line from a managed process."""

    cursor: int
    timestamp: str
    stream: Literal["stdout", "stderr", "system"]
    message: str


class GodotGetDebugOutputRequest(BaseModel):
    """Input schema for debug output retrieval."""

    session_id: str | None = None
    limit: int = Field(default=200, ge=1, le=1000)
    cursor: int | None = Field(default=None, ge=0)


class GodotGetDebugOutputResponse(BaseModel):
    """Output schema for debug output retrieval."""

    entries: list[DebugOutputEntry]
    next_cursor: int | None = None


class GodotAnalyzeProjectRequest(BaseModel):
    """Input schema for project analysis."""

    project_path: str = Field(min_length=1)


class GodotAnalyzeProjectResponse(BaseModel):
    """Output schema for project analysis."""

    scenes: list[str]
    scripts: list[str]
    resources: list[str]
    autoloads: dict[str, str]
    plugins: list[str]
    main_scene: str | None = None

    @field_validator("scenes", "scripts", "resources", "plugins")
    @classmethod
    def sort_paths(cls, values: list[str]) -> list[str]:
        """Normalize deterministic ordering."""
        return sorted(values)


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


class UidGetRequest(BaseModel):
    """Input schema for uid lookup."""

    project_path: str = Field(min_length=1)
    resource_path: str = Field(min_length=1)


class UidGetResponse(BaseModel):
    """Output schema for uid lookup."""

    uid: str


class UidRefreshReferencesRequest(BaseModel):
    """Input schema for uid reference refresh."""

    project_path: str = Field(min_length=1)
    paths: list[str] | None = None


class UidRefreshReferencesResponse(BaseModel):
    """Output schema for uid reference refresh."""

    updated_count: int
    updated_paths: list[str]


class RenderCaptureRequest(BaseModel):
    """Input schema for capture requests through bridge."""

    project_path: str = Field(min_length=1)
    scene_path: str | None = None
    camera_path: str | None = None
    width: int = Field(default=1280, gt=0)
    height: int = Field(default=720, gt=0)
    mode: Literal["editor", "running"] = "editor"


class RenderCaptureResponse(BaseModel):
    """Output schema for render capture."""

    image_path: str
    width: int
    height: int
    timestamp: str


class RenderInteractRequest(BaseModel):
    """Input schema for interaction requests against render bridge."""

    project_path: str = Field(min_length=1)
    mode: Literal["mouse_click", "key_press", "camera_orbit"]
    payload: dict[str, object]

    @model_validator(mode="after")
    def validate_mode_payload(self) -> "RenderInteractRequest":
        payload_keys = set(self.payload.keys())
        if self.mode == "mouse_click":
            required = {"x", "y", "button"}
            self._ensure_required(payload_keys, required)
            self._ensure_allowed(payload_keys, required)
        elif self.mode == "key_press":
            required = {"keycode"}
            allowed = {"keycode", "mods"}
            self._ensure_required(payload_keys, required)
            self._ensure_allowed(payload_keys, allowed)
        elif self.mode == "camera_orbit":
            required = {"dx", "dy"}
            allowed = {"dx", "dy", "sensitivity"}
            self._ensure_required(payload_keys, required)
            self._ensure_allowed(payload_keys, allowed)
        return self

    @staticmethod
    def _ensure_required(keys: set[str], required: set[str]) -> None:
        missing = sorted(required - keys)
        if missing:
            raise ValueError(f"Missing required payload fields: {', '.join(missing)}")

    @staticmethod
    def _ensure_allowed(keys: set[str], allowed: set[str]) -> None:
        extra = sorted(keys - allowed)
        if extra:
            raise ValueError(f"Unexpected payload fields: {', '.join(extra)}")


class RenderInteractResponse(BaseModel):
    """Output schema for render interaction."""

    ok: bool
    details: dict[str, object] | None = None
