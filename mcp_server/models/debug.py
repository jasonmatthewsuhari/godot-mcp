"""Pydantic schemas for debug and feedback loop tools."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ParsedError(BaseModel):
    """A structured error parsed from debug output."""

    file: str
    line: int
    error_type: str
    message: str
    stack_trace: list[str] | None = None


class GodotGetErrorsRequest(BaseModel):
    """Input schema for getting structured errors from debug output."""

    session_id: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


class GodotGetErrorsResponse(BaseModel):
    """Output schema for structured error retrieval."""

    errors: list[ParsedError]
    total_errors: int


class SignalWatchRequest(BaseModel):
    """Input schema for watching signals on a node."""

    project_path: str = Field(min_length=1)
    scene_path: str = Field(min_length=1)
    node_path: str = Field(min_length=1)
    signals: list[str] = Field(min_length=1)


class SignalWatchResponse(BaseModel):
    """Output schema for signal watch setup."""

    watching: list[str]
    node_path: str


class SignalPollRequest(BaseModel):
    """Input schema for polling watched signals."""

    project_path: str = Field(min_length=1)
    limit: int = Field(default=100, ge=1, le=1000)


class SignalEmission(BaseModel):
    """A recorded signal emission."""

    signal_name: str
    node_path: str
    timestamp: str
    args: list[object] | None = None


class SignalPollResponse(BaseModel):
    """Output schema for signal polling."""

    emissions: list[SignalEmission]
    total: int
