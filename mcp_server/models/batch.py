"""Pydantic schemas for batch execution."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BatchExecuteRequest(BaseModel):
    """Input schema for batch tool execution."""

    operations: list[dict[str, Any]] = Field(min_length=1)
    atomic: bool = True


class BatchExecuteResponse(BaseModel):
    """Output schema for batch tool execution."""

    results: list[dict[str, Any]]
    total: int
    succeeded: int
    failed: int
