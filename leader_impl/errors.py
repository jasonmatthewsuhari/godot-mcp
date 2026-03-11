from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolError(Exception):
    code: str
    message: str
    details: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details is not None:
            payload["details"] = self.details
        return payload

