"""Debug and feedback loop tool handlers."""

from __future__ import annotations

from ..error_parser import parse_errors as _parse_error_lines
from ..models import (
    GodotGetErrorsRequest,
    GodotGetErrorsResponse,
    SignalPollRequest,
    SignalPollResponse,
    SignalWatchRequest,
    SignalWatchResponse,
)
from .definitions import ToolDefinition


class DebugToolsMixin:
    """Mixin providing debug and feedback loop tools."""

    def _get_debug_definitions(self) -> dict[str, ToolDefinition]:
        return {
            "godot_get_errors": ToolDefinition(
                name="godot_get_errors",
                description="Parse structured errors from Godot debug output.",
                request_model=GodotGetErrorsRequest,
                response_model=GodotGetErrorsResponse,
                handler=self.godot_get_errors,
            ),
            "signal_watch": ToolDefinition(
                name="signal_watch",
                description="Start watching signals on a scene node via bridge.",
                request_model=SignalWatchRequest,
                response_model=SignalWatchResponse,
                handler=self.signal_watch,
            ),
            "signal_poll": ToolDefinition(
                name="signal_poll",
                description="Poll recorded signal emissions via bridge.",
                request_model=SignalPollRequest,
                response_model=SignalPollResponse,
                handler=self.signal_poll,
            ),
        }

    async def godot_get_errors(self, request: GodotGetErrorsRequest) -> GodotGetErrorsResponse:
        entries, _ = self.process_registry.get_output(
            session_id=request.session_id,
            limit=1000,
            cursor=None,
        )
        lines = [entry.message for entry in entries if entry.stream in ("stderr", "stdout")]
        parsed = _parse_error_lines(lines)
        limited = parsed[:request.limit]
        return GodotGetErrorsResponse(
            errors=[
                {
                    "file": e.file,
                    "line": e.line,
                    "error_type": e.error_type,
                    "message": e.message,
                    "stack_trace": e.stack_trace or None,
                }
                for e in limited
            ],
            total_errors=len(parsed),
        )

    async def signal_watch(self, request: SignalWatchRequest) -> SignalWatchResponse:
        payload = self._validate_bridge_payload("signal_watch", request)
        response = await self._bridge_call("signal_watch", self.bridge_client.signal_watch, payload)
        return self._parse_bridge_response("signal_watch", SignalWatchResponse, response)

    async def signal_poll(self, request: SignalPollRequest) -> SignalPollResponse:
        payload = self._validate_bridge_payload("signal_poll", request)
        response = await self._bridge_call("signal_poll", self.bridge_client.signal_poll, payload)
        return self._parse_bridge_response("signal_poll", SignalPollResponse, response)
