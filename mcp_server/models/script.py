"""Pydantic schemas for script and scene introspection tool inputs and outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScriptCreateRequest(BaseModel):
    """Input schema for creating a GDScript file."""

    project_path: str = Field(min_length=1)
    script_path: str = Field(min_length=1)
    content: str
    class_name: str | None = None


class ScriptCreateResponse(BaseModel):
    """Output schema for script creation."""

    script_path: str


class ScriptEditOperation(BaseModel):
    """A single edit operation on a script file."""

    op: str = Field(min_length=1)
    start: int = Field(ge=1)
    end: int = Field(ge=1)
    content: str = ""


class ScriptEditRequest(BaseModel):
    """Input schema for editing a GDScript file."""

    project_path: str = Field(min_length=1)
    script_path: str = Field(min_length=1)
    operations: list[ScriptEditOperation] = Field(min_length=1)


class ScriptEditResponse(BaseModel):
    """Output schema for script editing."""

    script_path: str
    line_count: int


class ScriptAttachRequest(BaseModel):
    """Input schema for attaching a script to a scene node."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    node_path: str = Field(min_length=1)
    script_path: str = Field(min_length=1)


class ScriptAttachResponse(BaseModel):
    """Output schema for script attachment."""

    node_path: str
    script_path: str


class ScriptValidateRequest(BaseModel):
    """Input schema for GDScript syntax validation."""

    project_path: str = Field(min_length=1)
    script_path: str = Field(min_length=1)


class ScriptValidateResponse(BaseModel):
    """Output schema for script validation."""

    valid: bool
    errors: list[str]


class SceneInspectNode(BaseModel):
    """A node in the scene tree inspection result."""

    node_path: str
    type: str
    properties: dict[str, object]
    children: list[SceneInspectNode]


class SceneInspectRequest(BaseModel):
    """Input schema for scene tree inspection."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    max_depth: int = Field(default=10, ge=1, le=50)


class SceneInspectResponse(BaseModel):
    """Output schema for scene tree inspection."""

    root: SceneInspectNode


class NodeGetPropertiesRequest(BaseModel):
    """Input schema for getting node properties."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    node_path: str = Field(min_length=1)


class NodeGetPropertiesResponse(BaseModel):
    """Output schema for node properties."""

    node_path: str
    type: str
    properties: dict[str, object]
