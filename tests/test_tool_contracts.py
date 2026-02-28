import pytest

from mcp_server.errors import MCPError
from mcp_server.tool_contracts import validate_tool_payload


def test_godot_run_project_contract_defaults() -> None:
    payload = validate_tool_payload("godot_run_project", {"project_path": "C:/demo"})
    assert payload["project_path"].endswith("demo")
    assert payload["debug"] is True


def test_scene_add_node_requires_fields() -> None:
    with pytest.raises(MCPError) as exc:
        validate_tool_payload("scene_add_node", {"project_path": "C:/demo"})
    assert exc.value.code == "validation_error"
    assert exc.value.details["field"] == "scene_path"


def test_unknown_field_rejected() -> None:
    with pytest.raises(MCPError) as exc:
        validate_tool_payload("render_capture", {"project_path": "C:/demo", "unknown": 1})
    assert exc.value.code == "validation_error"


def test_uid_refresh_paths_must_be_string_list() -> None:
    with pytest.raises(MCPError) as exc:
        validate_tool_payload("uid_refresh_references", {"project_path": "C:/demo", "paths": "bad"})
    assert exc.value.code == "validation_error"


def test_render_interact_mouse_click_requires_button() -> None:
    with pytest.raises(MCPError) as exc:
        validate_tool_payload(
            "render_interact",
            {"project_path": "C:/demo", "mode": "mouse_click", "payload": {"x": 1, "y": 2}},
        )
    assert exc.value.code == "validation_error"
    assert exc.value.details["field"] == "button"


def test_render_interact_key_press_rejects_unknown_payload_fields() -> None:
    with pytest.raises(MCPError) as exc:
        validate_tool_payload(
            "render_interact",
            {"project_path": "C:/demo", "mode": "key_press", "payload": {"keycode": 65, "x": 1}},
        )
    assert exc.value.code == "validation_error"
    assert "fields" in exc.value.details


def test_render_interact_camera_orbit_requires_dx_dy() -> None:
    with pytest.raises(MCPError) as exc:
        validate_tool_payload(
            "render_interact",
            {"project_path": "C:/demo", "mode": "camera_orbit", "payload": {"dy": 1.0}},
        )
    assert exc.value.code == "validation_error"
    assert exc.value.details["field"] == "dx"


def test_render_capture_mode_must_be_supported() -> None:
    with pytest.raises(MCPError) as exc:
        validate_tool_payload("render_capture", {"project_path": "C:/demo", "mode": "vr"})
    assert exc.value.code == "validation_error"


def test_render_interact_mouse_click_payload_is_validated() -> None:
    payload = validate_tool_payload(
        "render_interact",
        {
            "project_path": "C:/demo",
            "mode": "mouse_click",
            "payload": {"x": 10.5, "y": 20, "button": 1},
        },
    )
    assert payload["payload"] == {"x": 10.5, "y": 20.0, "button": 1}


def test_render_interact_rejects_missing_mode_fields() -> None:
    with pytest.raises(MCPError) as exc:
        validate_tool_payload(
            "render_interact",
            {"project_path": "C:/demo", "mode": "camera_orbit", "payload": {"dx": 1.0}},
        )
    assert exc.value.code == "validation_error"
    assert exc.value.details["field"] == "dy"
