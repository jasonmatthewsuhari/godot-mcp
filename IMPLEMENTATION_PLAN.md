# Plan: Godot MCP Server for Mistral Vibe (Windows-first, Godot 4.4+)

## Summary
Build a real MCP server (Python, `stdio`) that controls Godot projects and scenes through a local Godot addon bridge (`HTTP JSON + token`).
V1 will support all required features, plus on-demand rendered-scene screenshots and basic interaction (`mouse click`, `key press`, `camera orbit`).

## Scope and Architecture
1. Replace current Minecraft-protocol scaffold with an MCP-native tool server.
2. Split into three layers:
   - `mcp_server`: MCP tool definitions, validation, orchestration, process lifecycle.
   - `godot_bridge`: local HTTP client for talking to Godot addon.
   - `godot_addon`: Godot 4.4+ plugin exposing scene/resource/render operations safely via engine APIs.
3. Runtime model:
   - MCP server starts/stops Godot editor/game processes.
   - For scene/render/UID operations, MCP ensures addon bridge is reachable in target project.
   - Debug logs captured from process stdout/stderr with ring buffer + optional cursor pagination.

## Public Interfaces (MCP Tools)
1. `godot_get_version() -> {version, path}`
2. `godot_list_projects(root_path) -> {projects:[{name,path,project_file}]}`
3. `godot_launch_editor(project_path, headless=false) -> {session_id,pid,status}`
4. `godot_run_project(project_path, debug=true, scene_override?) -> {session_id,pid,status}`
5. `godot_stop_execution(session_id?) -> {stopped,exit_code}`
6. `godot_get_debug_output(session_id?, limit=200, cursor?) -> {entries,next_cursor}`
7. `godot_analyze_project(project_path) -> {scenes,scripts,resources,autoloads,plugins,main_scene}`

8. `scene_create(project_path, scene_path, root_node_type, options?) -> {scene_path,uid?}`
9. `scene_add_node(project_path, scene_path, parent_node_path, node_type, node_name, properties?) -> {node_path}`
10. `scene_load_sprite(project_path, scene_path, sprite_node_path, texture_path, import_if_needed=true) -> {sprite_node_path,texture_uid?}`
11. `scene_export_mesh_library(project_path, source_scene_path, mesh_library_path, options?) -> {mesh_library_path,item_count}`
12. `scene_save(project_path, scene_path, variant_name?, make_inherited=false) -> {saved_path,uid?}`

13. `uid_get(project_path, resource_path) -> {uid}`
14. `uid_refresh_references(project_path, paths?) -> {updated_count,updated_paths}`

15. `render_capture(project_path, scene_path?, camera_path?, width=1280, height=720, mode="editor|running") -> {image_path,width,height,timestamp}`
16. `render_interact(project_path, mode, payload) -> {ok,details}`
   - `mode=mouse_click` payload: `{x,y,button}`
   - `mode=key_press` payload: `{keycode,mods?}`
   - `mode=camera_orbit` payload: `{dx,dy,sensitivity?}`

## Godot Addon Bridge API (Internal)
1. `GET /health`
2. `POST /scene/create`
3. `POST /scene/add_node`
4. `POST /scene/load_sprite`
5. `POST /scene/export_mesh_library`
6. `POST /scene/save`
7. `POST /uid/get`
8. `POST /uid/refresh`
9. `POST /render/capture`
10. `POST /render/interact`
11. All endpoints require local token auth and only bind to `127.0.0.1`.

## Implementation Plan (Decision-Complete)
1. **Foundation refactor**
   - Replace current server entrypoint with MCP `stdio` server.
   - Add strict Pydantic schemas for tool inputs/outputs.
   - Add centralized error model (`code`, `message`, `details`).
2. **Godot process control**
   - Implement Godot executable discovery (explicit env var override + PATH + common install paths).
   - Add session registry keyed by `session_id` with PID, project path, mode, start time.
   - Implement stdout/stderr async capture with bounded ring buffer and cursors.
3. **Project discovery and analysis**
   - Recursive `project.godot` search from explicit root path only.
   - Parse project config for key metadata and list asset classes.
4. **Addon bridge bootstrap**
   - Ship `godot_addon/` folder with plugin and bridge script.
   - Add MCP helper to verify/install addon into project if missing.
   - Handshake validation: version compatibility, token, port availability.
5. **Scene and UID operations**
   - Implement all scene mutations through addon APIs (no direct `.tscn` string surgery).
   - Use Godot `ResourceSaver/ResourceLoader` and UID APIs (4.4+) for consistency.
6. **Render visibility + interaction**
   - Implement on-demand screenshot capture from editor viewport or running scene.
   - Implement injected interaction commands via addon (`mouse/key/orbit`).
   - Return filesystem path + image metadata; keep recent capture index per project.
7. **Hardening**
   - Path normalization + project-root confinement checks.
   - Process orphan cleanup.
   - Timeout/retry behavior for bridge calls.
8. **Docs**
   - Update `README.md` with install, required Godot version, MCP client config, tool catalog, and troubleshooting.

## Test Cases and Acceptance Criteria
1. Unit:
   - Tool schema validation for each MCP tool.
   - Godot path resolution and session lifecycle.
   - Output buffer cursor pagination.
2. Integration:
   - Start editor for sample project, verify version and process alive.
   - Run project in debug, capture logs, stop execution cleanly.
   - Scene create/add/save and reload succeeds in Godot.
   - UID get/refresh updates references correctly on renamed resource.
   - Render capture returns valid image file dimensions.
   - Render interact modifies viewport/camera state (assert observable frame delta).
3. Failure scenarios:
   - Missing Godot binary.
   - Invalid project path.
   - Bridge unavailable/token mismatch.
   - Scene path not found/invalid node path.
4. Done criteria:
   - All required user-listed features exposed as MCP tools.
   - End-to-end demo script passes on Windows with Godot 4.4+.

## Execution Delegation Protocol
For every implementation task:
1. Subagent A prompt: primary implementation slice.
2. Subagent B prompt: parallel validation/tests/docs slice.
3. Integrate both and resolve conflicts centrally.

## Assumptions and Defaults
1. Host OS priority: Windows.
2. Godot target: 4.4+ only in v1.
3. MCP transport: Python `stdio` primary.
4. Project listing uses explicit root input, no home-wide scan.
5. Scene operations use addon RPC bridge, not direct text manipulation.
6. Render feature v1 is on-demand screenshot plus basic input actions, not streaming.
7. Security scope is local-machine usage with loopback bind + token auth.
