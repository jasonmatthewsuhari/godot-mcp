from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .errors import ToolError


class GodotBridgeClient:
    def __init__(self, port: int = 8799, token: str | None = None, timeout_seconds: float = 8.0) -> None:
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self.token = token
        self.timeout_seconds = timeout_seconds

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=f"{self.base_url}{path}",
            data=body,
            method=method,
            headers=self._build_headers(),
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise ToolError(
                code="bridge_http_error",
                message=f"Bridge returned HTTP {exc.code}",
                details={"status": exc.code, "body": details},
            ) from exc
        except urllib.error.URLError as exc:
            raise ToolError(
                code="bridge_unavailable",
                message="Could not reach Godot bridge",
                details={"url": f"{self.base_url}{path}", "error": str(exc)},
            ) from exc

        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ToolError(
                code="bridge_invalid_response",
                message="Bridge returned invalid JSON",
                details={"body": raw[:400]},
            ) from exc

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def scene_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/scene/create", payload)

    def scene_add_node(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/scene/add_node", payload)

    def scene_load_sprite(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/scene/load_sprite", payload)

    def scene_export_mesh_library(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/scene/export_mesh_library", payload)

    def scene_save(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/scene/save", payload)

    def uid_get(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/uid/get", payload)

    def uid_refresh(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/uid/refresh", payload)

    def render_capture(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/render/capture", payload)

    def render_interact(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/render/interact", payload)

