# Troubleshooting

## Godot Path Discovery Failures
- Symptom: `GODOT_NOT_FOUND` or integration setup fails when opt-in is enabled.
- Fix:
  - Set `GODOT_PATH` explicitly to the Godot executable path.
  - Verify binary exists and is executable:
    - PowerShell: `Test-Path $env:GODOT_PATH`
    - PowerShell: `& $env:GODOT_PATH --version`

## Bridge Token Mismatch
- Symptom: bridge responses return unauthorized/token errors.
- Fix:
  - Ensure project setting `mistral_mcp/bridge_token` matches `GODOT_BRIDGE_TOKEN`.
  - Verify client sends `Authorization: Bearer <token>`.

## Port `19110` Conflicts
- Symptom: bridge health checks timeout or bind failures in Godot logs.
- Fix:
  - Stop other local bridge/editor instances using port `19110`.
  - Check listeners: `Get-NetTCPConnection -LocalPort 19110 -ErrorAction SilentlyContinue`
  - Keep bridge URL and addon bind port aligned.

## Integration Tests Skipped Unexpectedly
- Symptom: `tests_integration` show skipped when you expected execution.
- Fix:
  - Confirm `ENABLE_GODOT_INTEGRATION=1` in the same shell session.
  - Confirm marker invocation:
    - `python -m pytest -q tests_integration -m godot_integration`

## `render_capture` / `render_interact` Runtime Failures
- Symptom: capture fails (`capture_failed`, image path missing) or interaction fails (`node_not_found` camera).
- Fix:
  - Launch editor/run session before calling render tools.
  - Wait for bridge `/health` before invoking render operations.
  - Ensure active viewport/camera exists for target mode.
  - Validate payload keys/types for `mouse_click`, `key_press`, `camera_orbit`.

