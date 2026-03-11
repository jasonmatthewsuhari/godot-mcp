"""Render tool handlers (bridge-mediated)."""

from __future__ import annotations

from ..models import (
    RenderCaptureRequest,
    RenderCaptureResponse,
    RenderInteractRequest,
    RenderInteractResponse,
)
from .definitions import ToolDefinition


class RenderToolsMixin:
    """Mixin providing render tool handlers."""

    def _get_render_definitions(self) -> dict[str, ToolDefinition]:
        return {
            "render_capture": ToolDefinition(
                name="render_capture",
                description="Capture rendered output through the local addon bridge.",
                request_model=RenderCaptureRequest,
                response_model=RenderCaptureResponse,
                handler=self.render_capture,
            ),
            "render_interact": ToolDefinition(
                name="render_interact",
                description="Send interaction input through the local addon bridge.",
                request_model=RenderInteractRequest,
                response_model=RenderInteractResponse,
                handler=self.render_interact,
            ),
        }

    async def render_capture(self, request: RenderCaptureRequest) -> RenderCaptureResponse:
        payload = self._validate_bridge_payload("render_capture", request)
        response = await self._bridge_call("render_capture", self.bridge_client.render_capture, payload)
        return self._parse_bridge_response("render_capture", RenderCaptureResponse, response)

    async def render_interact(self, request: RenderInteractRequest) -> RenderInteractResponse:
        payload = self._validate_bridge_payload("render_interact", request)
        response = await self._bridge_call("render_interact", self.bridge_client.render_interact, payload)
        return self._parse_bridge_response("render_interact", RenderInteractResponse, response)
