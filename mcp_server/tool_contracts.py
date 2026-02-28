from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from mcp_server.errors import make_error

Validator = Callable[[Any], Any]


def _as_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise make_error("validation_error", f"'{field_name}' must be a non-empty string")
    return value.strip()


def _as_optional_non_empty_str(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _as_non_empty_str(value, field_name)


def _as_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise make_error("validation_error", f"'{field_name}' must be a boolean")
    return value


def _as_positive_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise make_error("validation_error", f"'{field_name}' must be a positive integer")
    return value


def _as_optional_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int):
        raise make_error("validation_error", f"'{field_name}' must be an integer")
    return value


def _as_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise make_error("validation_error", f"'{field_name}' must be an object")
    return value


def _as_optional_string_list(value: Any, field_name: str) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise make_error("validation_error", f"'{field_name}' must be an array of strings")
    return [_as_non_empty_str(item, f"{field_name}[]") for item in value]


def _as_number(value: Any, field_name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise make_error("validation_error", f"'{field_name}' must be a number")
    return float(value)


def _as_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise make_error("validation_error", f"'{field_name}' must be an integer")
    return value


def _validate_render_capture_mode(value: Any) -> str:
    mode = _as_non_empty_str(value, "mode")
    if mode not in {"editor", "running"}:
        raise make_error("validation_error", "'mode' must be one of: editor, running")
    return mode


def _validate_render_interact_mode(value: Any) -> str:
    mode = _as_non_empty_str(value, "mode")
    if mode not in {"mouse_click", "key_press", "camera_orbit"}:
        raise make_error("validation_error", "'mode' must be one of: mouse_click, key_press, camera_orbit")
    return mode


def _validate_render_interact_payload(mode: str, payload: dict[str, Any]) -> dict[str, Any]:
    if mode == "mouse_click":
        unexpected = sorted(set(payload.keys()) - {"x", "y", "button"})
        if unexpected:
            raise make_error(
                "validation_error",
                "Unexpected field for mode payload",
                {"mode": mode, "fields": unexpected},
            )
        for key in ("x", "y", "button"):
            if key not in payload:
                raise make_error("validation_error", "Missing required field for mode payload", {"mode": mode, "field": key})
        return {
            "x": _as_number(payload["x"], "payload.x"),
            "y": _as_number(payload["y"], "payload.y"),
            "button": _as_int(payload["button"], "payload.button"),
        }
    if mode == "key_press":
        unexpected = sorted(set(payload.keys()) - {"keycode", "mods"})
        if unexpected:
            raise make_error(
                "validation_error",
                "Unexpected field for mode payload",
                {"mode": mode, "fields": unexpected},
            )
        if "keycode" not in payload:
            raise make_error("validation_error", "Missing required field for mode payload", {"mode": mode, "field": "keycode"})
        result: dict[str, Any] = {"keycode": _as_int(payload["keycode"], "payload.keycode")}
        mods = payload.get("mods")
        if mods is not None:
            result["mods"] = _as_dict(mods, "payload.mods")
        return result
    unexpected = sorted(set(payload.keys()) - {"dx", "dy", "sensitivity"})
    if unexpected:
        raise make_error(
            "validation_error",
            "Unexpected field for mode payload",
            {"mode": mode, "fields": unexpected},
        )
    for key in ("dx", "dy"):
        if key not in payload:
            raise make_error("validation_error", "Missing required field for mode payload", {"mode": mode, "field": key})
    result = {"dx": _as_number(payload["dx"], "payload.dx"), "dy": _as_number(payload["dy"], "payload.dy")}
    if "sensitivity" in payload:
        result["sensitivity"] = _as_number(payload["sensitivity"], "payload.sensitivity")
    return result


TOOL_SCHEMAS: dict[str, dict[str, tuple[bool, Validator]]] = {
    "godot_get_version": {},
    "godot_list_projects": {
        "root_path": (True, lambda v: str(Path(_as_non_empty_str(v, "root_path"))))
    },
    "godot_launch_editor": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "headless": (False, lambda v: _as_bool(v, "headless")),
    },
    "godot_run_project": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "debug": (False, lambda v: _as_bool(v, "debug")),
        "scene_override": (False, lambda v: _as_optional_non_empty_str(v, "scene_override")),
    },
    "godot_stop_execution": {
        "session_id": (False, lambda v: _as_optional_non_empty_str(v, "session_id"))
    },
    "godot_get_debug_output": {
        "session_id": (False, lambda v: _as_optional_non_empty_str(v, "session_id")),
        "limit": (False, lambda v: _as_positive_int(v, "limit")),
        "cursor": (False, lambda v: _as_optional_int(v, "cursor")),
    },
    "godot_analyze_project": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path"))))
    },
    "scene_create": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "root_node_type": (True, lambda v: _as_non_empty_str(v, "root_node_type")),
        "options": (False, lambda v: _as_dict(v, "options")),
    },
    "scene_add_node": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "parent_node_path": (True, lambda v: _as_non_empty_str(v, "parent_node_path")),
        "node_type": (True, lambda v: _as_non_empty_str(v, "node_type")),
        "node_name": (True, lambda v: _as_non_empty_str(v, "node_name")),
        "properties": (False, lambda v: _as_dict(v, "properties")),
    },
    "scene_load_sprite": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "sprite_node_path": (True, lambda v: _as_non_empty_str(v, "sprite_node_path")),
        "texture_path": (True, lambda v: _as_non_empty_str(v, "texture_path")),
        "import_if_needed": (False, lambda v: _as_bool(v, "import_if_needed")),
    },
    "scene_export_mesh_library": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "source_scene_path": (True, lambda v: _as_non_empty_str(v, "source_scene_path")),
        "mesh_library_path": (True, lambda v: _as_non_empty_str(v, "mesh_library_path")),
        "options": (False, lambda v: _as_dict(v, "options")),
    },
    "scene_save": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "variant_name": (False, lambda v: _as_optional_non_empty_str(v, "variant_name")),
        "make_inherited": (False, lambda v: _as_bool(v, "make_inherited")),
    },
    "uid_get": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "resource_path": (True, lambda v: _as_non_empty_str(v, "resource_path")),
    },
    "uid_refresh_references": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "paths": (False, lambda v: _as_optional_string_list(v, "paths")),
    },
    "render_capture": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (False, lambda v: _as_optional_non_empty_str(v, "scene_path")),
        "camera_path": (False, lambda v: _as_optional_non_empty_str(v, "camera_path")),
        "width": (False, lambda v: _as_positive_int(v, "width")),
        "height": (False, lambda v: _as_positive_int(v, "height")),
        "mode": (False, _validate_render_capture_mode),
    },
    "render_interact": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "mode": (True, _validate_render_interact_mode),
        "payload": (True, lambda v: _as_dict(v, "payload")),
    },
}


DEFAULTS: dict[str, dict[str, Any]] = {
    "godot_launch_editor": {"headless": False},
    "godot_run_project": {"debug": True},
    "godot_get_debug_output": {"limit": 200},
    "scene_load_sprite": {"import_if_needed": True},
    "scene_save": {"make_inherited": False},
    "render_capture": {"width": 1280, "height": 720, "mode": "editor"},
}


def validate_tool_payload(tool_name: str, payload: dict[str, Any] | None) -> dict[str, Any]:
    if tool_name not in TOOL_SCHEMAS:
        raise make_error("validation_error", "Unknown tool", {"tool_name": tool_name})
    payload = payload or {}
    if not isinstance(payload, dict):
        raise make_error("validation_error", "Payload must be an object")

    validated: dict[str, Any] = {}
    schema = TOOL_SCHEMAS[tool_name]

    for field_name in payload:
        if field_name not in schema:
            raise make_error("validation_error", "Unknown field for tool", {"tool_name": tool_name, "field": field_name})

    for field_name, (required, validator) in schema.items():
        if field_name in payload:
            validated[field_name] = validator(payload[field_name])
        elif required:
            raise make_error("validation_error", "Missing required field", {"tool_name": tool_name, "field": field_name})

    for key, value in DEFAULTS.get(tool_name, {}).items():
        validated.setdefault(key, value)

    if tool_name == "render_interact":
        validated["payload"] = _validate_render_interact_payload(validated["mode"], validated["payload"])

    return validated
