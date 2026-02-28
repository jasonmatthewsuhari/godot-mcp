"""Validate parity of tool names across server, contracts, and manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp_server.stdio_server import StdioMCPServer
from mcp_server.tool_contracts import TOOL_SCHEMAS

MANIFEST_PATH = Path("MACHINE_READABLE_TOOL_MANIFEST.json")


def _names_from_server() -> set[str]:
    return set(StdioMCPServer().tools.keys())


def _names_from_contracts() -> set[str]:
    return set(TOOL_SCHEMAS.keys())


def _names_from_manifest(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    tools = payload.get("tools")
    if not isinstance(tools, list):
        raise RuntimeError("Manifest 'tools' must be an array.")
    names: set[str] = set()
    for item in tools:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise RuntimeError("Each manifest tool must include a string 'name'.")
        names.add(item["name"])
    return names


def build_report() -> dict[str, Any]:
    server = _names_from_server()
    contracts = _names_from_contracts()
    manifest = _names_from_manifest(MANIFEST_PATH)
    return {
        "ok": server == contracts == manifest,
        "server_count": len(server),
        "contracts_count": len(contracts),
        "manifest_count": len(manifest),
        "server_only": sorted(server - contracts - manifest),
        "contracts_only": sorted(contracts - server - manifest),
        "manifest_only": sorted(manifest - server - contracts),
        "missing_in_server": sorted((contracts | manifest) - server),
        "missing_in_contracts": sorted((server | manifest) - contracts),
        "missing_in_manifest": sorted((server | contracts) - manifest),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate tool name parity.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"ok: {report['ok']}")
        print(f"server_count: {report['server_count']}")
        print(f"contracts_count: {report['contracts_count']}")
        print(f"manifest_count: {report['manifest_count']}")
        if not report["ok"]:
            print(f"missing_in_server: {report['missing_in_server']}")
            print(f"missing_in_contracts: {report['missing_in_contracts']}")
            print(f"missing_in_manifest: {report['missing_in_manifest']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
