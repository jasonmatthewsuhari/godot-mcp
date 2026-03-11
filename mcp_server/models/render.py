"""Pydantic schemas for render tool inputs and outputs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


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
