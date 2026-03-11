"""UID tool handlers (bridge-mediated)."""

from __future__ import annotations

from ..models import (
    UidGetRequest,
    UidGetResponse,
    UidRefreshReferencesRequest,
    UidRefreshReferencesResponse,
)
from .definitions import ToolDefinition


class UidToolsMixin:
    """Mixin providing UID tool handlers."""

    def _get_uid_definitions(self) -> dict[str, ToolDefinition]:
        return {
            "uid_get": ToolDefinition(
                name="uid_get",
                description="Get a Godot resource UID through the local addon bridge.",
                request_model=UidGetRequest,
                response_model=UidGetResponse,
                handler=self.uid_get,
            ),
            "uid_refresh_references": ToolDefinition(
                name="uid_refresh_references",
                description="Refresh UID references through the local addon bridge.",
                request_model=UidRefreshReferencesRequest,
                response_model=UidRefreshReferencesResponse,
                handler=self.uid_refresh_references,
            ),
        }

    async def uid_get(self, request: UidGetRequest) -> UidGetResponse:
        payload = self._validate_bridge_payload("uid_get", request)
        response = await self._bridge_call("uid_get", self.bridge_client.uid_get, payload)
        return self._parse_bridge_response("uid_get", UidGetResponse, response)

    async def uid_refresh_references(self, request: UidRefreshReferencesRequest) -> UidRefreshReferencesResponse:
        payload = self._validate_bridge_payload("uid_refresh_references", request)
        response = await self._bridge_call("uid_refresh_references", self.bridge_client.uid_refresh_references, payload)
        return self._parse_bridge_response("uid_refresh_references", UidRefreshReferencesResponse, response)
