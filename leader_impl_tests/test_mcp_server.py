from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from leader_impl.mcp_stdio_server import LeaderMCPServer


class MCPServerTests(unittest.TestCase):
    def test_unknown_method(self) -> None:
        server = LeaderMCPServer()
        payload = {"jsonrpc": "2.0", "id": 1, "method": "nope", "params": {}}
        response = server.handle_jsonrpc(payload)
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], "unknown_method")

    def test_unknown_tool(self) -> None:
        server = LeaderMCPServer()
        payload = {
            "jsonrpc": "2.0",
            "id": "abc",
            "method": "tools/call",
            "params": {"name": "not_real", "arguments": {}},
        }
        response = server.handle_jsonrpc(payload)
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], "unknown_tool")

    def test_validation_error(self) -> None:
        server = LeaderMCPServer()
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "godot_list_projects", "arguments": {"root_path": 123}},
        }
        response = server.handle_jsonrpc(payload)
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], "validation_error")

    def test_scene_create_maps_to_bridge(self) -> None:
        server = LeaderMCPServer()
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "project.godot"), "w", encoding="utf-8") as f:
                f.write("[application]\nconfig/name=\"X\"\n")
            with mock.patch.object(
                server.bridge,
                "scene_create",
                return_value={"scene_path": "res://scenes/main.tscn", "uid": "uid://abc"},
            ) as patched:
                payload = {
                    "jsonrpc": "2.0",
                    "id": "s1",
                    "method": "tools/call",
                    "params": {
                        "name": "scene_create",
                        "arguments": {
                            "project_path": root,
                            "scene_path": "res://scenes/main.tscn",
                            "root_node_type": "Node2D",
                        },
                    },
                }
                response = server.handle_jsonrpc(payload)
        self.assertIn("result", response)
        self.assertEqual(response["result"]["scene_path"], "res://scenes/main.tscn")
        patched.assert_called_once()

    def test_render_interact_validation(self) -> None:
        server = LeaderMCPServer()
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "project.godot"), "w", encoding="utf-8") as f:
                f.write("[application]\nconfig/name=\"X\"\n")
            payload = {
                "jsonrpc": "2.0",
                "id": "r1",
                "method": "tools/call",
                "params": {
                    "name": "render_interact",
                    "arguments": {"project_path": root, "mode": "mouse_click", "payload": {"x": 1}},
                },
            }
            response = server.handle_jsonrpc(payload)
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], "validation_error")

    def test_uid_refresh_maps_to_bridge(self) -> None:
        server = LeaderMCPServer()
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "project.godot"), "w", encoding="utf-8") as f:
                f.write("[application]\nconfig/name=\"X\"\n")
            with mock.patch.object(
                server.bridge,
                "uid_refresh",
                return_value={"updated_count": 2, "updated_paths": ["res://a.tscn", "res://b.tres"]},
            ):
                payload = {
                    "jsonrpc": "2.0",
                    "id": "u1",
                    "method": "tools/call",
                    "params": {
                        "name": "uid_refresh_references",
                        "arguments": {"project_path": root, "paths": ["res://a.tscn"]},
                    },
                }
                response = server.handle_jsonrpc(payload)
        self.assertIn("result", response)
        self.assertEqual(response["result"]["updated_count"], 2)


if __name__ == "__main__":
    unittest.main()
