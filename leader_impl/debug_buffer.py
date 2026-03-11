from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock


@dataclass
class DebugItem:
    index: int
    timestamp: str
    stream: str
    message: str


class DebugBuffer:
    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max_size
        self._items: deque[DebugItem] = deque()
        self._start_index = 0
        self._next_index = 0
        self._lock = Lock()

    @property
    def next_index(self) -> int:
        with self._lock:
            return self._next_index

    def append(self, stream: str, message: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._items.append(
                DebugItem(
                    index=self._next_index,
                    timestamp=now,
                    stream=stream,
                    message=message.rstrip("\n"),
                )
            )
            self._next_index += 1
            while len(self._items) > self.max_size:
                self._items.popleft()
                self._start_index += 1

    def read(self, limit: int = 200, cursor: str | None = None) -> tuple[list[DebugItem], str]:
        with self._lock:
            if cursor is None:
                start = max(self._start_index, self._next_index - limit)
            else:
                try:
                    start = max(self._start_index, int(cursor))
                except ValueError:
                    start = self._start_index

            selected = [item for item in self._items if item.index >= start][:limit]
            if selected:
                next_cursor = str(selected[-1].index + 1)
            else:
                next_cursor = str(start)
            return selected, next_cursor

