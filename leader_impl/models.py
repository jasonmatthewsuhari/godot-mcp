from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetVersionRequest(StrictModel):
    pass


class GetVersionResponse(StrictModel):
    version: str
    path: str


class ProjectEntry(StrictModel):
    name: str
    path: str
    project_file: str


class ListProjectsRequest(StrictModel):
    root_path: str


class ListProjectsResponse(StrictModel):
    projects: list[ProjectEntry]


class LaunchEditorRequest(StrictModel):
    project_path: str
    headless: bool = False


class RunProjectRequest(StrictModel):
    project_path: str
    debug: bool = True
    scene_override: str | None = None


class SessionResponse(StrictModel):
    session_id: str
    pid: int
    status: str


class StopExecutionRequest(StrictModel):
    session_id: str | None = None


class StopExecutionResponse(StrictModel):
    stopped: bool
    exit_code: int | None = None


class DebugOutputRequest(StrictModel):
    session_id: str | None = None
    limit: int = Field(default=200, ge=1, le=1000)
    cursor: str | None = None


class DebugEntry(StrictModel):
    index: int
    timestamp: str
    stream: str
    message: str


class DebugOutputResponse(StrictModel):
    entries: list[DebugEntry]
    next_cursor: str | None = None


class AnalyzeProjectRequest(StrictModel):
    project_path: str


class AnalyzeProjectResponse(StrictModel):
    path: str
    name: str
    scenes: list[str]
    scripts: list[str]
    resources: list[str]
    plugins: list[str]
    autoloads: dict[str, str]
    main_scene: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class SceneCreateRequest(StrictModel):
    project_path: str
    scene_path: str
    root_node_type: str = "Node2D"
    options: dict[str, Any] | None = None


class SceneCreateResponse(StrictModel):
    scene_path: str
    uid: str | None = None


class SceneAddNodeRequest(StrictModel):
    project_path: str
    scene_path: str
    parent_node_path: str
    node_type: str
    node_name: str
    properties: dict[str, Any] | None = None


class SceneAddNodeResponse(StrictModel):
    node_path: str


class SceneLoadSpriteRequest(StrictModel):
    project_path: str
    scene_path: str
    sprite_node_path: str
    texture_path: str
    import_if_needed: bool = True


class SceneLoadSpriteResponse(StrictModel):
    sprite_node_path: str
    texture_uid: str | None = None


class SceneExportMeshLibraryRequest(StrictModel):
    project_path: str
    source_scene_path: str
    mesh_library_path: str
    options: dict[str, Any] | None = None


class SceneExportMeshLibraryResponse(StrictModel):
    mesh_library_path: str
    item_count: int


class SceneSaveRequest(StrictModel):
    project_path: str
    scene_path: str
    variant_name: str | None = None
    make_inherited: bool = False


class SceneSaveResponse(StrictModel):
    saved_path: str
    uid: str | None = None


class UIDGetRequest(StrictModel):
    project_path: str
    resource_path: str


class UIDGetResponse(StrictModel):
    uid: str


class UIDRefreshRequest(StrictModel):
    project_path: str
    paths: list[str] | None = None


class UIDRefreshResponse(StrictModel):
    updated_count: int
    updated_paths: list[str]


class RenderCaptureRequest(StrictModel):
    project_path: str
    scene_path: str | None = None
    camera_path: str | None = None
    width: int = Field(default=1280, ge=1, le=8192)
    height: int = Field(default=720, ge=1, le=8192)
    mode: Literal["editor", "running"] = "editor"


class RenderCaptureResponse(StrictModel):
    image_path: str
    width: int
    height: int
    timestamp: str


class RenderInteractRequest(StrictModel):
    project_path: str
    mode: Literal["mouse_click", "key_press", "camera_orbit"]
    payload: dict[str, Any]

    @model_validator(mode="after")
    def validate_payload(self) -> "RenderInteractRequest":
        data = self.payload
        if self.mode == "mouse_click":
            required = {"x", "y", "button"}
        elif self.mode == "key_press":
            required = {"keycode"}
        else:
            required = {"dx", "dy"}

        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"payload missing required fields: {', '.join(sorted(missing))}")
        return self


class RenderInteractResponse(StrictModel):
    ok: bool
    details: dict[str, Any] | None = None
