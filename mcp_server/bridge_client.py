"""HTTP bridge client used by scene/uid/render MCP tools."""

from __future__ import annotations

from collections.abc import Callable
import json
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from .errors import MCPError


class GodotBridgeClient:
    """HTTP bridge client for local Godot addon bridge calls."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:19110",
        token: str = "",
        timeout_s: float = 2.0,
        transport: Callable[..., dict[str, Any]] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout_s = timeout_s
        self.transport = transport or _default_transport
        self._validate_localhost_url()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health", None)

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

    def uid_refresh_references(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.uid_refresh(payload)

    def render_capture(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/render/capture", payload)

    def render_interact(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/render/interact", payload)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
        try:
            return self.transport(
                method=method,
                url=f"{self.base_url}{path}",
                headers=headers,
                payload=payload,
                timeout_s=self.timeout_s,
            )
        except MCPError:
            raise
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise MCPError(
                code="BRIDGE_REQUEST_FAILED",
                message="Unexpected bridge transport error.",
                details={"path": path, "reason": str(exc)},
            ) from exc

    def _validate_localhost_url(self) -> None:
        parsed = urllib_parse.urlparse(self.base_url)
        host = parsed.hostname or ""
        if host not in {"127.0.0.1", "localhost"}:
            raise MCPError(
                code="INVALID_BRIDGE_URL",
                message="Bridge URL must target localhost.",
                details={"base_url": self.base_url},
            )
        if parsed.scheme not in {"http", "https"}:
            raise MCPError(
                code="INVALID_BRIDGE_URL",
                message="Bridge URL must be http or https.",
                details={"base_url": self.base_url},
            )


def _default_transport(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any] | None,
    timeout_s: float,
) -> dict[str, Any]:
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    request = urllib_request.Request(url=url, data=body, method=method, headers=headers)
    try:
        with urllib_request.urlopen(request, timeout=timeout_s) as response:
            raw = response.read().decode("utf-8")
            if not raw.strip():
                return {}
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise MCPError(
                    code="BRIDGE_BAD_RESPONSE",
                    message="Bridge response must be a JSON object.",
                    details={"url": url},
                )
            return parsed
    except urllib_error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        raise MCPError(
            code="BRIDGE_HTTP_ERROR",
            message="Bridge returned an HTTP error.",
            details={"url": url, "status": exc.code, "body": body_text},
        ) from exc
    except urllib_error.URLError as exc:
        raise MCPError(
            code="BRIDGE_UNREACHABLE",
            message="Failed to connect to Godot bridge.",
            details={"url": url, "reason": str(exc.reason)},
        ) from exc
    except json.JSONDecodeError as exc:
        raise MCPError(
            code="BRIDGE_BAD_RESPONSE",
            message="Bridge returned invalid JSON.",
            details={"url": url, "reason": str(exc)},
        ) from exc
