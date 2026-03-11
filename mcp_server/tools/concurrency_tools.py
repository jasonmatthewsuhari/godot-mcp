"""Concurrency safety tool handlers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ..journal import OperationJournal
from ..models.concurrency import (
    JournalReadRequest,
    JournalReadResponse,
    LockAcquireRequest,
    LockAcquireResponse,
    LockListRequest,
    LockListResponse,
    LockReleaseRequest,
    LockReleaseResponse,
)
from .definitions import ToolDefinition


class ConcurrencyToolsMixin:
    """Mixin providing concurrency safety tools."""

    def _get_concurrency_definitions(self) -> dict[str, ToolDefinition]:
        return {
            "lock_acquire": ToolDefinition(
                name="lock_acquire",
                description="Acquire an exclusive lock on a resource (scene, script, etc.).",
                request_model=LockAcquireRequest,
                response_model=LockAcquireResponse,
                handler=self.lock_acquire,
            ),
            "lock_release": ToolDefinition(
                name="lock_release",
                description="Release a previously acquired resource lock.",
                request_model=LockReleaseRequest,
                response_model=LockReleaseResponse,
                handler=self.lock_release,
            ),
            "lock_list": ToolDefinition(
                name="lock_list",
                description="List all active resource locks.",
                request_model=LockListRequest,
                response_model=LockListResponse,
                handler=self.lock_list,
            ),
            "journal_read": ToolDefinition(
                name="journal_read",
                description="Read recent entries from the operation journal.",
                request_model=JournalReadRequest,
                response_model=JournalReadResponse,
                handler=self.journal_read,
            ),
        }

    async def lock_acquire(self, request: LockAcquireRequest) -> LockAcquireResponse:
        entry = self.lock_manager.acquire(
            resource=request.resource,
            owner=request.owner,
            ttl_seconds=request.ttl_seconds,
        )
        acquired_dt = datetime.fromtimestamp(entry.acquired_at, tz=timezone.utc)
        expires_dt = datetime.fromtimestamp(
            entry.acquired_at + entry.ttl_seconds, tz=timezone.utc
        )
        return LockAcquireResponse(
            resource=entry.resource,
            owner=entry.owner,
            acquired_at=acquired_dt.isoformat(),
            expires_at=expires_dt.isoformat(),
        )

    async def lock_release(self, request: LockReleaseRequest) -> LockReleaseResponse:
        released = self.lock_manager.release(
            resource=request.resource,
            owner=request.owner,
        )
        return LockReleaseResponse(released=released)

    async def lock_list(self, request: LockListRequest) -> LockListResponse:
        locks = self.lock_manager.list_locks()
        return LockListResponse(
            locks=[
                {
                    "resource": lock.resource,
                    "owner": lock.owner,
                    "acquired_at": datetime.fromtimestamp(
                        lock.acquired_at, tz=timezone.utc
                    ).isoformat(),
                    "expires_at": datetime.fromtimestamp(
                        lock.acquired_at + lock.ttl_seconds, tz=timezone.utc
                    ).isoformat(),
                }
                for lock in locks
            ]
        )

    async def journal_read(self, request: JournalReadRequest) -> JournalReadResponse:
        journal_path = Path(request.project_path) / ".godot_mcp" / "journal.jsonl"
        journal = OperationJournal(journal_path)
        entries = journal.read_entries(limit=request.limit)
        return JournalReadResponse(
            entries=[
                {
                    "timestamp": e.timestamp,
                    "tool_name": e.tool_name,
                    "arguments": e.arguments,
                    "result_code": e.result_code,
                }
                for e in entries
            ],
            total=len(entries),
        )
