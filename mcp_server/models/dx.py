"""Pydantic schemas for developer experience tools."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GodotQuickStartRequest(BaseModel):
    """Input schema for Godot quick-start setup."""

    project_path: str = Field(min_length=1)


class GodotQuickStartResponse(BaseModel):
    """Output schema for Godot quick-start setup."""

    godot_path: str
    addon_installed: bool
    bridge_port: int
    token: str
