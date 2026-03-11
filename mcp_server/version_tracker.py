"""Optimistic concurrency control via content hashing."""

from __future__ import annotations

import hashlib
from pathlib import Path


class VersionTracker:
    """Track file versions using SHA-256 content hashes."""

    def __init__(self) -> None:
        self._versions: dict[str, str] = {}

    def compute_version(self, file_path: Path) -> str:
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()[:16]

    def track(self, file_path: Path) -> str:
        version = self.compute_version(file_path)
        self._versions[str(file_path)] = version
        return version

    def check(self, file_path: Path, expected_version: str) -> bool:
        current = self.compute_version(file_path)
        return current == expected_version

    def get_version(self, file_path: Path) -> str | None:
        return self._versions.get(str(file_path))
