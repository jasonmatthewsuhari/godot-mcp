"""Operation journal for auditing tool invocations."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class JournalEntry:
    """A single recorded operation."""

    timestamp: float
    tool_name: str
    arguments: dict
    result_code: str  # "success" or error code


class OperationJournal:
    """Append-only JSONL journal for recording tool calls."""

    def __init__(self, journal_path: Path) -> None:
        self._path = journal_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: JournalEntry) -> None:
        record = {
            "timestamp": entry.timestamp,
            "tool_name": entry.tool_name,
            "arguments": entry.arguments,
            "result_code": entry.result_code,
        }
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def read_entries(self, limit: int = 100) -> list[JournalEntry]:
        if not self._path.exists():
            return []
        lines = self._path.read_text(encoding="utf-8").strip().splitlines()
        tail = lines[-limit:] if len(lines) > limit else lines
        entries: list[JournalEntry] = []
        for line in tail:
            data = json.loads(line)
            entries.append(
                JournalEntry(
                    timestamp=data["timestamp"],
                    tool_name=data["tool_name"],
                    arguments=data["arguments"],
                    result_code=data["result_code"],
                )
            )
        return entries
