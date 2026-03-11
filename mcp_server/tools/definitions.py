"""Tool definition dataclass and argument parsing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from pydantic import BaseModel, ValidationError

from ..errors import MCPError


@dataclass(slots=True)
class ToolDefinition:
    """Metadata and implementation wiring for an MCP tool."""

    name: str
    description: str
    request_model: type[BaseModel]
    response_model: type[BaseModel]
    handler: Callable[[BaseModel], Coroutine[Any, Any, BaseModel]]


def parse_arguments(model: type[BaseModel], arguments: dict[str, Any] | None) -> BaseModel:
    """Validate tool arguments and raise MCPError on validation failure."""
    payload = arguments or {}
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise MCPError(
            code="VALIDATION_ERROR",
            message="Invalid tool arguments.",
            details={"errors": exc.errors()},
        ) from exc
