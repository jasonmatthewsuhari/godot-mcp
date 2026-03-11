"""Tests for the .tscn scene parser."""

from __future__ import annotations

from mcp_server.scene_parser import diff_scenes, parse_tscn


SAMPLE_TSCN = """\
[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/main.gd" id="1_abc"]

[node name="Root" type="Node2D"]

[node name="Player" type="CharacterBody2D" parent="."]
position = Vector2(100, 200)
speed = 300

[node name="Sprite" type="Sprite2D" parent="Player"]
"""


def test_parse_nodes() -> None:
    scene = parse_tscn(SAMPLE_TSCN)
    assert len(scene.nodes) == 3
    paths = scene.node_paths()
    assert "Root" in paths
    assert "Player" in paths
    assert "Player/Sprite" in paths


def test_parse_ext_resources() -> None:
    scene = parse_tscn(SAMPLE_TSCN)
    assert len(scene.resources) == 1
    assert scene.resources[0].path == "res://scripts/main.gd"
    assert scene.resources[0].type == "Script"


def test_parse_properties() -> None:
    scene = parse_tscn(SAMPLE_TSCN)
    player = scene.node_by_path("Player")
    assert player is not None
    assert player.properties["position"] == "Vector2(100, 200)"
    assert player.properties["speed"] == "300"


def test_diff_scenes_added_removed() -> None:
    scene_a = parse_tscn("""\
[gd_scene format=3]
[node name="Root" type="Node2D"]
[node name="Player" type="Sprite2D" parent="."]
""")
    scene_b = parse_tscn("""\
[gd_scene format=3]
[node name="Root" type="Node2D"]
[node name="Enemy" type="Sprite2D" parent="."]
""")
    result = diff_scenes(scene_a, scene_b)
    assert "Enemy" in result["added_nodes"]
    assert "Player" in result["removed_nodes"]


def test_diff_scenes_changed_properties() -> None:
    scene_a = parse_tscn("""\
[gd_scene format=3]
[node name="Root" type="Node2D"]
position = Vector2(0, 0)
""")
    scene_b = parse_tscn("""\
[gd_scene format=3]
[node name="Root" type="Node2D"]
position = Vector2(100, 200)
""")
    result = diff_scenes(scene_a, scene_b)
    assert len(result["changed_properties"]) == 1
    assert result["changed_properties"][0]["property"] == "Root.position"
