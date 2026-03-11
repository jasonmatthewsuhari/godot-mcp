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


def _as_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise make_error("validation_error", f"'{field_name}' must be an array")
    return value


def _as_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise make_error("validation_error", f"'{field_name}' must be a string")
    return value


def _as_operation_list(value: Any, field_name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) == 0:
        raise make_error("validation_error", f"'{field_name}' must be a non-empty array")
    result = []
    for i, item in enumerate(value):
        if not isinstance(item, dict):
            raise make_error("validation_error", f"'{field_name}[{i}]' must be an object")
        result.append(item)
    return result


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
    "script_create": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "script_path": (True, lambda v: _as_non_empty_str(v, "script_path")),
        "content": (True, lambda v: _as_str(v, "content")),
        "class_name": (False, lambda v: _as_optional_non_empty_str(v, "class_name")),
    },
    "script_edit": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "script_path": (True, lambda v: _as_non_empty_str(v, "script_path")),
        "operations": (True, lambda v: _as_operation_list(v, "operations")),
    },
    "script_attach": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "node_path": (True, lambda v: _as_non_empty_str(v, "node_path")),
        "script_path": (True, lambda v: _as_non_empty_str(v, "script_path")),
    },
    "script_validate": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "script_path": (True, lambda v: _as_non_empty_str(v, "script_path")),
    },
    "scene_inspect": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "max_depth": (False, lambda v: _as_positive_int(v, "max_depth")),
    },
    "node_get_properties": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "node_path": (True, lambda v: _as_non_empty_str(v, "node_path")),
    },
    "project_create_from_template": {
        "template_path": (True, lambda v: str(Path(_as_non_empty_str(v, "template_path")))),
        "target_path": (True, lambda v: str(Path(_as_non_empty_str(v, "target_path")))),
        "project_name": (True, lambda v: _as_non_empty_str(v, "project_name")),
        "replacements": (False, lambda v: _as_dict(v, "replacements")),
    },
    "project_get_dependencies": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
    },
    "asset_import": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "source_path": (True, lambda v: str(Path(_as_non_empty_str(v, "source_path")))),
        "target_path": (True, lambda v: _as_non_empty_str(v, "target_path")),
        "scan_after": (False, lambda v: _as_bool(v, "scan_after")),
    },
    "scene_diff": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path_a": (True, lambda v: _as_non_empty_str(v, "scene_path_a")),
        "scene_path_b": (True, lambda v: _as_non_empty_str(v, "scene_path_b")),
    },
    "tilemap_paint": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "tilemap_node_path": (True, lambda v: _as_non_empty_str(v, "tilemap_node_path")),
        "cells": (True, lambda v: _as_list(v, "cells")),
        "layer": (False, lambda v: _as_int(v, "layer")),
    },
    "gridmap_place": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "gridmap_node_path": (True, lambda v: _as_non_empty_str(v, "gridmap_node_path")),
        "placements": (True, lambda v: _as_list(v, "placements")),
    },
    "material_create": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "material_path": (True, lambda v: _as_non_empty_str(v, "material_path")),
        "material_type": (False, lambda v: _as_non_empty_str(v, "material_type")),
        "properties": (False, lambda v: _as_dict(v, "properties")),
    },
    "material_apply": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "node_path": (True, lambda v: _as_non_empty_str(v, "node_path")),
        "material_path": (True, lambda v: _as_non_empty_str(v, "material_path")),
        "surface_index": (False, lambda v: _as_int(v, "surface_index")),
    },
    "environment_setup": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "background_mode": (False, lambda v: _as_non_empty_str(v, "background_mode")),
        "ambient_light_color": (False, lambda v: _as_optional_non_empty_str(v, "ambient_light_color")),
        "fog_enabled": (False, lambda v: _as_bool(v, "fog_enabled")),
        "tonemap_mode": (False, lambda v: _as_optional_non_empty_str(v, "tonemap_mode")),
    },
    "csg_operations": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "parent_node_path": (True, lambda v: _as_non_empty_str(v, "parent_node_path")),
        "operation": (True, lambda v: _as_non_empty_str(v, "operation")),
        "shape_type": (True, lambda v: _as_non_empty_str(v, "shape_type")),
        "shape_properties": (False, lambda v: _as_dict(v, "shape_properties")),
        "node_name": (True, lambda v: _as_non_empty_str(v, "node_name")),
    },
    "animation_create": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "animation_player_path": (True, lambda v: _as_non_empty_str(v, "animation_player_path")),
        "animation_name": (True, lambda v: _as_non_empty_str(v, "animation_name")),
        "length": (True, lambda v: _as_number(v, "length")),
        "loop": (False, lambda v: _as_bool(v, "loop")),
    },
    "animation_add_keyframe": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "animation_player_path": (True, lambda v: _as_non_empty_str(v, "animation_player_path")),
        "animation_name": (True, lambda v: _as_non_empty_str(v, "animation_name")),
        "track_path": (True, lambda v: _as_non_empty_str(v, "track_path")),
        "time": (True, lambda v: _as_number(v, "time")),
        "value": (False, lambda v: v),
    },
    "godot_get_errors": {
        "session_id": (False, lambda v: _as_optional_non_empty_str(v, "session_id")),
        "limit": (False, lambda v: _as_positive_int(v, "limit")),
    },
    "signal_watch": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "scene_path": (True, lambda v: _as_non_empty_str(v, "scene_path")),
        "node_path": (True, lambda v: _as_non_empty_str(v, "node_path")),
        "signals": (True, lambda v: _as_optional_string_list(v, "signals")),
    },
    "signal_poll": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "limit": (False, lambda v: _as_positive_int(v, "limit")),
    },
    "batch_execute": {
        "operations": (True, lambda v: _as_list(v, "operations")),
        "atomic": (False, lambda v: _as_bool(v, "atomic")),
    },
    "lock_acquire": {
        "resource": (True, lambda v: _as_non_empty_str(v, "resource")),
        "owner": (True, lambda v: _as_non_empty_str(v, "owner")),
        "ttl_seconds": (False, lambda v: _as_number(v, "ttl_seconds")),
    },
    "lock_release": {
        "resource": (True, lambda v: _as_non_empty_str(v, "resource")),
        "owner": (True, lambda v: _as_non_empty_str(v, "owner")),
    },
    "lock_list": {},
    "journal_read": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "limit": (False, lambda v: _as_positive_int(v, "limit")),
    },
    "asset_search_online": {
        "query": (True, lambda v: _as_non_empty_str(v, "query")),
        "sources": (False, lambda v: _as_optional_string_list(v, "sources")),
        "limit": (False, lambda v: _as_positive_int(v, "limit")),
    },
    "asset_download_3d": {
        "url": (True, lambda v: _as_non_empty_str(v, "url")),
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
        "target_path": (True, lambda v: _as_non_empty_str(v, "target_path")),
    },
    "godot_quick_start": {
        "project_path": (True, lambda v: str(Path(_as_non_empty_str(v, "project_path")))),
    },
}


DEFAULTS: dict[str, dict[str, Any]] = {
    "godot_launch_editor": {"headless": False},
    "godot_run_project": {"debug": True},
    "godot_get_debug_output": {"limit": 200},
    "scene_load_sprite": {"import_if_needed": True},
    "scene_save": {"make_inherited": False},
    "render_capture": {"width": 1280, "height": 720, "mode": "editor"},
    "scene_inspect": {"max_depth": 10},
    "asset_import": {"scan_after": True},
    "tilemap_paint": {"layer": 0},
    "material_create": {"material_type": "standard"},
    "material_apply": {"surface_index": 0},
    "environment_setup": {"background_mode": "sky", "fog_enabled": False},
    "animation_create": {"loop": False},
    "godot_get_errors": {"limit": 50},
    "signal_poll": {"limit": 100},
    "batch_execute": {"atomic": True},
    "lock_acquire": {"ttl_seconds": 300.0},
    "journal_read": {"limit": 100},
    "asset_search_online": {"limit": 10},
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
