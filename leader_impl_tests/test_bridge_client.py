from __future__ import annotations

import io
import json
import unittest
from unittest import mock

from leader_impl.bridge_client import GodotBridgeClient
from leader_impl.errors import ToolError


class FakeResponse:
    def __init__(self, payload: dict):
        self._bytes = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._bytes

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class BridgeClientTests(unittest.TestCase):
    def test_health_success(self) -> None:
        client = GodotBridgeClient(port=8799, token="abc")
        with mock.patch("urllib.request.urlopen", return_value=FakeResponse({"ok": True})):
            out = client.health()
        self.assertEqual(out["ok"], True)

    def test_http_error_maps_to_tool_error(self) -> None:
        client = GodotBridgeClient()
        http_error = Exception()
        from urllib.error import HTTPError

        http_error = HTTPError(
            url="http://127.0.0.1:8799/health",
            code=401,
            msg="unauthorized",
            hdrs=None,
            fp=io.BytesIO(b'{"error":"unauthorized"}'),
        )
        with mock.patch("urllib.request.urlopen", side_effect=http_error):
            with self.assertRaises(ToolError) as ctx:
                client.health()
        self.assertEqual(ctx.exception.code, "bridge_http_error")

    def test_invalid_json_maps_to_tool_error(self) -> None:
        client = GodotBridgeClient()

        class BadResponse:
            def read(self) -> bytes:
                return b"not-json"

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with mock.patch("urllib.request.urlopen", return_value=BadResponse()):
            with self.assertRaises(ToolError) as ctx:
                client.health()
        self.assertEqual(ctx.exception.code, "bridge_invalid_response")


if __name__ == "__main__":
    unittest.main()

