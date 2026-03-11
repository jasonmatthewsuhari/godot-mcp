"""Parser for Godot .tscn text scene format."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TscnNode:
    """A node parsed from a .tscn file."""

    name: str
    type: str = ""
    parent: str = ""
    properties: dict[str, str] = field(default_factory=dict)

    @property
    def full_path(self) -> str:
        if not self.parent:
            return self.name
        if self.parent == ".":
            return self.name
        return f"{self.parent}/{self.name}"


@dataclass
class TscnResource:
    """An external resource reference in a .tscn file."""

    path: str
    type: str
    id: str


@dataclass
class TscnScene:
    """A parsed .tscn scene file."""

    resources: list[TscnResource] = field(default_factory=list)
    nodes: list[TscnNode] = field(default_factory=list)

    def node_paths(self) -> set[str]:
        return {node.full_path for node in self.nodes}

    def node_by_path(self, path: str) -> TscnNode | None:
        for node in self.nodes:
            if node.full_path == path:
                return node
        return None


_SECTION_RE = re.compile(r'^\[(\w+)(.*?)\]\s*$')
_KV_RE = re.compile(r'^(\w+)\s*=\s*(.*)')
_ATTR_RE = re.compile(r'(\w+)="([^"]*)"')


def parse_tscn(text: str) -> TscnScene:
    """Parse a .tscn text format into a TscnScene structure."""
    scene = TscnScene()
    current_section: str | None = None
    current_attrs: dict[str, str] = {}
    current_props: dict[str, str] = {}

    def _flush() -> None:
        nonlocal current_section, current_attrs, current_props
        if current_section == "ext_resource":
            scene.resources.append(
                TscnResource(
                    path=current_attrs.get("path", ""),
                    type=current_attrs.get("type", ""),
                    id=current_attrs.get("id", ""),
                )
            )
        elif current_section == "node":
            scene.nodes.append(
                TscnNode(
                    name=current_attrs.get("name", ""),
                    type=current_attrs.get("type", ""),
                    parent=current_attrs.get("parent", ""),
                    properties=dict(current_props),
                )
            )
        current_section = None
        current_attrs = {}
        current_props = {}

    for line in text.splitlines():
        section_match = _SECTION_RE.match(line)
        if section_match:
            _flush()
            current_section = section_match.group(1)
            attr_str = section_match.group(2)
            current_attrs = dict(_ATTR_RE.findall(attr_str))
            continue

        kv_match = _KV_RE.match(line)
        if kv_match and current_section:
            current_props[kv_match.group(1)] = kv_match.group(2)

    _flush()
    return scene


def parse_tscn_file(path: Path) -> TscnScene:
    """Parse a .tscn file from disk."""
    return parse_tscn(path.read_text(encoding="utf-8"))


def diff_scenes(scene_a: TscnScene, scene_b: TscnScene) -> dict[str, Any]:
    """Compute differences between two parsed scenes."""
    paths_a = scene_a.node_paths()
    paths_b = scene_b.node_paths()

    added = sorted(paths_b - paths_a)
    removed = sorted(paths_a - paths_b)

    changed: list[dict[str, str]] = []
    for path in sorted(paths_a & paths_b):
        node_a = scene_a.node_by_path(path)
        node_b = scene_b.node_by_path(path)
        if node_a is None or node_b is None:
            continue
        all_keys = set(node_a.properties.keys()) | set(node_b.properties.keys())
        for key in sorted(all_keys):
            val_a = node_a.properties.get(key, "")
            val_b = node_b.properties.get(key, "")
            if val_a != val_b:
                changed.append({
                    "property": f"{path}.{key}",
                    "old_value": val_a,
                    "new_value": val_b,
                })

    return {
        "added_nodes": added,
        "removed_nodes": removed,
        "changed_properties": changed,
    }
