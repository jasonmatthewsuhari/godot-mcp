"""Scene locking for concurrent agent safety."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .errors import MCPError


@dataclass
class LockEntry:
    """A single resource lock held by an owner."""

    resource: str
    owner: str
    acquired_at: float
    ttl_seconds: float = 300.0

    @property
    def is_expired(self) -> bool:
        return time.time() - self.acquired_at > self.ttl_seconds


class LockManager:
    """In-memory resource lock manager with TTL-based expiry."""

    def __init__(self) -> None:
        self._locks: dict[str, LockEntry] = {}

    def acquire(self, resource: str, owner: str, ttl_seconds: float = 300.0) -> LockEntry:
        self._cleanup_expired()
        existing = self._locks.get(resource)
        if existing and not existing.is_expired and existing.owner != owner:
            raise MCPError(
                code="LOCK_HELD",
                message=f"Resource locked by {existing.owner}",
                details={
                    "resource": resource,
                    "held_by": existing.owner,
                    "acquired_at": existing.acquired_at,
                },
            )
        entry = LockEntry(
            resource=resource,
            owner=owner,
            acquired_at=time.time(),
            ttl_seconds=ttl_seconds,
        )
        self._locks[resource] = entry
        return entry

    def release(self, resource: str, owner: str) -> bool:
        existing = self._locks.get(resource)
        if not existing or existing.owner != owner:
            return False
        del self._locks[resource]
        return True

    def list_locks(self) -> list[LockEntry]:
        self._cleanup_expired()
        return list(self._locks.values())

    def _cleanup_expired(self) -> None:
        expired = [k for k, v in self._locks.items() if v.is_expired]
        for k in expired:
            del self._locks[k]
