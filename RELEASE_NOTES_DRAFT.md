# Release Notes Draft - v0.1.0

## Delivered Summary
- Wave 1 foundation:
  - Replaced legacy protocol scaffold with stdio MCP server transport.
  - Added typed Pydantic contracts for core Godot process and project tools.
  - Added Windows-first Godot executable discovery and process session registry with cursor-based debug buffer retrieval.
  - Added project discovery and static project analysis support.
- Wave 2 tooling:
  - Wired scene, UID, and render tools end-to-end through localhost token-auth bridge client.
  - Added strict validation for `render_interact` mode payloads.
  - Standardized failure mapping to canonical `MCPError` shape (`code`, `message`, `details`).
- Wave 3 scaffolding:
  - Added CI quality gate workflow with smoke + audit + unittest checks and tool-list artifact publication.
  - Added optional integration CI job and artifact capture for integration logs.
  - Added machine-readable tool manifest and parity validation script.

## Known Limitations
- Integration tests require a real Godot 4.4+ runtime and local bridge setup; they are opt-in.
- Bridge operations depend on addon availability and token configuration in target project.
- CI default job validates API surface and stdio behavior but does not prove full engine/runtime behavior without integration gating enabled.
- Manifest is committed artifact and should be regenerated when tool signatures or names change.

## Minimum Runtime Requirements
- Python 3.11+
- `pydantic` installed in runtime environment
- Godot 4.4+ for runtime process/bridge operations
- MCP client capable of stdio JSON-RPC framing (`Content-Length` transport)

