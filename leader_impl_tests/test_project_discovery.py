from __future__ import annotations

import os
import tempfile
import unittest

from leader_impl.project_discovery import analyze_project, list_projects


class ProjectDiscoveryTests(unittest.TestCase):
    def test_list_projects_finds_project_godot(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            p1 = os.path.join(root, "game_a")
            p2 = os.path.join(root, "nested", "game_b")
            os.makedirs(p1, exist_ok=True)
            os.makedirs(p2, exist_ok=True)
            with open(os.path.join(p1, "project.godot"), "w", encoding="utf-8") as f:
                f.write("[application]\nconfig/name=\"A\"\n")
            with open(os.path.join(p2, "project.godot"), "w", encoding="utf-8") as f:
                f.write("[application]\nconfig/name=\"B\"\n")

            projects = list_projects(root)
            self.assertEqual(len(projects), 2)
            self.assertEqual(sorted([p.name for p in projects]), ["game_a", "game_b"])

    def test_analyze_project_extracts_main_scene_and_autoload(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            project = os.path.join(root, "game")
            os.makedirs(os.path.join(project, "scenes"), exist_ok=True)
            os.makedirs(os.path.join(project, "scripts"), exist_ok=True)

            with open(os.path.join(project, "project.godot"), "w", encoding="utf-8") as f:
                f.write(
                    "[application]\n"
                    "run/main_scene=\"res://scenes/main.tscn\"\n\n"
                    "[autoload]\n"
                    "GameState=\"*res://scripts/game_state.gd\"\n"
                )
            with open(os.path.join(project, "scenes", "main.tscn"), "w", encoding="utf-8") as f:
                f.write("[gd_scene format=3]\n")
            with open(os.path.join(project, "scripts", "game_state.gd"), "w", encoding="utf-8") as f:
                f.write("extends Node\n")

            info = analyze_project(project)
            self.assertEqual(info.main_scene, "res://scenes/main.tscn")
            self.assertIn("GameState", info.autoloads)
            self.assertIn("scenes/main.tscn", info.scenes)
            self.assertIn("scripts/game_state.gd", info.scripts)


if __name__ == "__main__":
    unittest.main()

