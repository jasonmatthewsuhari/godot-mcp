# Release Checklist

Use this checklist before shipping.

## Ship Gates
- [ ] Unit/contract tests pass
  - Command: `python -m pytest -q`
- [ ] Integration suite passes OR waiver documented
  - Command: `python -m pytest -q tests_integration -m godot_integration`
  - Waiver must include: date, owner, failing tests, risk acceptance.
- [ ] Stdio smoke pass
  - Verify `initialize`, `tools/list`, and at least one `tools/call` success.
- [ ] Wave 2 parity audit pass
  - Confirm scene/uid/render bridge routes are present and tested.
- [ ] Bridge auth/local bind verified
  - Bridge only listens on `127.0.0.1`.
  - Bearer token auth enforced on all routes.
- [ ] Docs examples validated
  - Run README tool examples against a live project and confirm responses.
- [ ] Demo script validated
  - Run through `docs/product-demo-script.md` once end-to-end.

## Sign-off
- Release owner: Jason (pending final approval)
- Date: 2026-02-28
- Commit SHA: `7ca538f`
- Notes/Waivers:
  - Integration waiver recorded (latest run after bridge TCP-read fix, with `ENABLE_GODOT_INTEGRATION=1` + real `GODOT_PATH`).
  - Result: `1 failed, 3 passed` (reproduced).
  - Failing test: `tests_integration/test_godot_runtime_integration.py::test_scene_uid_render_end_to_end`.
  - Failure reason: bridge health timeout (`Bridge did not become healthy within 45.0s`).
  - `WinError 5` process launch failure appears resolved (editor/run launch tests pass).
  - Risk acceptance required before ship: render/bridge readiness in live editor startup path is not guaranteed.
