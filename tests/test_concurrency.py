"""Tests for concurrent agent safety: locks, journal, version tracker, and tools."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import pytest

from mcp_server.errors import MCPError
from mcp_server.journal import JournalEntry, OperationJournal
from mcp_server.lock_manager import LockManager
from mcp_server.models import (
    LockAcquireRequest,
    LockListRequest,
    LockReleaseRequest,
    JournalReadRequest,
)
from mcp_server.tools import GodotToolService
from mcp_server.version_tracker import VersionTracker


# ---------------------------------------------------------------------------
# LockManager
# ---------------------------------------------------------------------------

class TestLockManager:
    def test_acquire_and_release(self) -> None:
        lm = LockManager()
        entry = lm.acquire("res://main.tscn", "agent-1")
        assert entry.resource == "res://main.tscn"
        assert entry.owner == "agent-1"
        assert not entry.is_expired

        released = lm.release("res://main.tscn", "agent-1")
        assert released is True

    def test_release_wrong_owner_returns_false(self) -> None:
        lm = LockManager()
        lm.acquire("res://main.tscn", "agent-1")
        assert lm.release("res://main.tscn", "agent-2") is False

    def test_release_nonexistent_returns_false(self) -> None:
        lm = LockManager()
        assert lm.release("res://nope.tscn", "agent-1") is False

    def test_conflict_raises_error(self) -> None:
        lm = LockManager()
        lm.acquire("res://main.tscn", "agent-1")
        with pytest.raises(MCPError) as exc_info:
            lm.acquire("res://main.tscn", "agent-2")
        assert exc_info.value.code == "LOCK_HELD"
        assert "agent-1" in exc_info.value.message

    def test_same_owner_can_reacquire(self) -> None:
        lm = LockManager()
        lm.acquire("res://main.tscn", "agent-1")
        entry = lm.acquire("res://main.tscn", "agent-1")
        assert entry.owner == "agent-1"

    def test_expired_lock_allows_reacquisition(self) -> None:
        lm = LockManager()
        entry = lm.acquire("res://main.tscn", "agent-1", ttl_seconds=0.01)
        # Force expiry
        entry.acquired_at = time.time() - 1.0
        new_entry = lm.acquire("res://main.tscn", "agent-2")
        assert new_entry.owner == "agent-2"

    def test_list_locks(self) -> None:
        lm = LockManager()
        lm.acquire("res://a.tscn", "agent-1")
        lm.acquire("res://b.tscn", "agent-2")
        locks = lm.list_locks()
        assert len(locks) == 2
        resources = {lock.resource for lock in locks}
        assert resources == {"res://a.tscn", "res://b.tscn"}

    def test_list_locks_excludes_expired(self) -> None:
        lm = LockManager()
        entry = lm.acquire("res://old.tscn", "agent-1", ttl_seconds=0.01)
        entry.acquired_at = time.time() - 1.0
        lm.acquire("res://new.tscn", "agent-2")
        locks = lm.list_locks()
        assert len(locks) == 1
        assert locks[0].resource == "res://new.tscn"


# ---------------------------------------------------------------------------
# OperationJournal
# ---------------------------------------------------------------------------

class TestOperationJournal:
    def test_append_and_read(self, tmp_path: Path) -> None:
        journal_path = tmp_path / ".godot_mcp" / "journal.jsonl"
        journal = OperationJournal(journal_path)

        entry = JournalEntry(
            timestamp=1000.0,
            tool_name="scene_create",
            arguments={"scene_path": "res://main.tscn"},
            result_code="success",
        )
        journal.append(entry)

        entries = journal.read_entries()
        assert len(entries) == 1
        assert entries[0].tool_name == "scene_create"
        assert entries[0].result_code == "success"
        assert entries[0].timestamp == 1000.0

    def test_read_respects_limit(self, tmp_path: Path) -> None:
        journal_path = tmp_path / "journal.jsonl"
        journal = OperationJournal(journal_path)

        for i in range(10):
            journal.append(
                JournalEntry(
                    timestamp=float(i),
                    tool_name=f"tool_{i}",
                    arguments={},
                    result_code="success",
                )
            )

        entries = journal.read_entries(limit=3)
        assert len(entries) == 3
        assert entries[0].tool_name == "tool_7"
        assert entries[2].tool_name == "tool_9"

    def test_read_empty_journal(self, tmp_path: Path) -> None:
        journal_path = tmp_path / "nonexistent.jsonl"
        journal = OperationJournal(journal_path)
        entries = journal.read_entries()
        assert entries == []


# ---------------------------------------------------------------------------
# VersionTracker
# ---------------------------------------------------------------------------

class TestVersionTracker:
    def test_compute_version(self, tmp_path: Path) -> None:
        f = tmp_path / "test.tscn"
        f.write_text("hello", encoding="utf-8")
        vt = VersionTracker()
        version = vt.compute_version(f)
        assert isinstance(version, str)
        assert len(version) == 16

    def test_track_stores_version(self, tmp_path: Path) -> None:
        f = tmp_path / "test.tscn"
        f.write_text("content", encoding="utf-8")
        vt = VersionTracker()
        version = vt.track(f)
        assert vt.get_version(f) == version

    def test_check_matches(self, tmp_path: Path) -> None:
        f = tmp_path / "test.tscn"
        f.write_text("content", encoding="utf-8")
        vt = VersionTracker()
        version = vt.track(f)
        assert vt.check(f, version) is True

    def test_check_fails_after_modification(self, tmp_path: Path) -> None:
        f = tmp_path / "test.tscn"
        f.write_text("original", encoding="utf-8")
        vt = VersionTracker()
        version = vt.track(f)
        f.write_text("modified", encoding="utf-8")
        assert vt.check(f, version) is False

    def test_get_version_returns_none_for_untracked(self) -> None:
        vt = VersionTracker()
        assert vt.get_version(Path("/nonexistent")) is None

    def test_deterministic_hashing(self, tmp_path: Path) -> None:
        f = tmp_path / "test.tscn"
        f.write_text("same content", encoding="utf-8")
        vt = VersionTracker()
        v1 = vt.compute_version(f)
        v2 = vt.compute_version(f)
        assert v1 == v2


# ---------------------------------------------------------------------------
# ConcurrencyToolsMixin (integration via GodotToolService)
# ---------------------------------------------------------------------------

class FakeBridgeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.responses: dict[str, dict[str, Any]] = {}

    def _call(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((name, payload))
        return self.responses.get(name, {"ok": True})

    def __getattr__(self, name: str) -> Any:
        return lambda p: self._call(name, p)


def _create_project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    project.mkdir()
    (project / "project.godot").write_text("[application]\n", encoding="utf-8")
    return project


@pytest.fixture
def service(tmp_path: Path) -> tuple[GodotToolService, FakeBridgeClient, Path]:
    bridge = FakeBridgeClient()
    srv = GodotToolService(bridge_client=bridge)
    project = _create_project(tmp_path)
    return srv, bridge, project


class TestConcurrencyTools:
    def test_concurrency_tools_in_definitions(
        self, service: tuple[GodotToolService, FakeBridgeClient, Path]
    ) -> None:
        srv, _, _ = service
        defs = srv.get_definitions()
        for name in ["lock_acquire", "lock_release", "lock_list", "journal_read"]:
            assert name in defs, f"{name} not in definitions"

    def test_lock_acquire_tool(
        self, service: tuple[GodotToolService, FakeBridgeClient, Path]
    ) -> None:
        srv, _, _ = service
        result = asyncio.run(
            srv.lock_acquire(
                LockAcquireRequest(resource="res://main.tscn", owner="agent-1")
            )
        )
        assert result.resource == "res://main.tscn"
        assert result.owner == "agent-1"
        assert result.acquired_at
        assert result.expires_at

    def test_lock_release_tool(
        self, service: tuple[GodotToolService, FakeBridgeClient, Path]
    ) -> None:
        srv, _, _ = service
        asyncio.run(
            srv.lock_acquire(
                LockAcquireRequest(resource="res://main.tscn", owner="agent-1")
            )
        )
        result = asyncio.run(
            srv.lock_release(
                LockReleaseRequest(resource="res://main.tscn", owner="agent-1")
            )
        )
        assert result.released is True

    def test_lock_list_tool(
        self, service: tuple[GodotToolService, FakeBridgeClient, Path]
    ) -> None:
        srv, _, _ = service
        asyncio.run(
            srv.lock_acquire(
                LockAcquireRequest(resource="res://a.tscn", owner="agent-1")
            )
        )
        result = asyncio.run(srv.lock_list(LockListRequest()))
        assert len(result.locks) == 1
        assert result.locks[0]["resource"] == "res://a.tscn"

    def test_journal_read_tool(
        self, service: tuple[GodotToolService, FakeBridgeClient, Path]
    ) -> None:
        srv, _, project = service
        journal_path = project / ".godot_mcp" / "journal.jsonl"
        journal = OperationJournal(journal_path)
        journal.append(
            JournalEntry(
                timestamp=1000.0,
                tool_name="scene_create",
                arguments={"path": "res://main.tscn"},
                result_code="success",
            )
        )
        result = asyncio.run(
            srv.journal_read(
                JournalReadRequest(project_path=str(project), limit=10)
            )
        )
        assert result.total == 1
        assert result.entries[0]["tool_name"] == "scene_create"
