from __future__ import annotations

import os
import subprocess
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from .debug_buffer import DebugBuffer
from .errors import ToolError


@dataclass
class SessionRecord:
    session_id: str
    process: subprocess.Popen[str]
    project_path: str
    mode: str
    started_at: str
    buffer: DebugBuffer
    status: str = "running"
    exit_code: int | None = None

    @property
    def pid(self) -> int:
        return int(self.process.pid)


class SessionManager:
    def __init__(self, max_buffer_size: int = 1000) -> None:
        self._sessions: dict[str, SessionRecord] = {}
        self._lock = threading.Lock()
        self._max_buffer_size = max_buffer_size

    def _spawn(self, cmd: list[str], project_path: str, mode: str) -> SessionRecord:
        try:
            process = subprocess.Popen(
                cmd,
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError as exc:
            raise ToolError(code="spawn_failed", message="Failed to start Godot process", details=str(exc)) from exc

        session = SessionRecord(
            session_id=str(uuid.uuid4()),
            process=process,
            project_path=project_path,
            mode=mode,
            started_at=datetime.now(timezone.utc).isoformat(),
            buffer=DebugBuffer(max_size=self._max_buffer_size),
        )
        with self._lock:
            self._sessions[session.session_id] = session

        self._start_capture_threads(session)
        return session

    def _start_capture_threads(self, session: SessionRecord) -> None:
        assert session.process.stdout is not None
        assert session.process.stderr is not None
        threading.Thread(target=self._capture_pipe, args=(session, "stdout", session.process.stdout), daemon=True).start()
        threading.Thread(target=self._capture_pipe, args=(session, "stderr", session.process.stderr), daemon=True).start()
        threading.Thread(target=self._watch_process, args=(session,), daemon=True).start()

    def _capture_pipe(self, session: SessionRecord, stream_name: str, pipe) -> None:
        for line in pipe:
            session.buffer.append(stream_name, line)

    def _watch_process(self, session: SessionRecord) -> None:
        exit_code = session.process.wait()
        with self._lock:
            current = self._sessions.get(session.session_id)
            if current is not None:
                current.exit_code = exit_code
                current.status = "exited"

    def launch_editor(self, godot_path: str, project_path: str, headless: bool = False) -> SessionRecord:
        cmd = [godot_path]
        if headless:
            cmd.append("--headless")
        cmd.extend(["--editor", "--path", project_path])
        return self._spawn(cmd, project_path, "editor")

    def run_project(self, godot_path: str, project_path: str, debug: bool = True, scene_override: str | None = None) -> SessionRecord:
        cmd = [godot_path, "--path", project_path]
        if debug:
            cmd.append("--debug")
        if scene_override:
            cmd.extend(["--main-pack", scene_override])
        return self._spawn(cmd, project_path, "run")

    def latest_session_id(self) -> str | None:
        with self._lock:
            if not self._sessions:
                return None
            return next(reversed(self._sessions.keys()))

    def get_session(self, session_id: str | None) -> SessionRecord:
        selected = session_id or self.latest_session_id()
        if not selected:
            raise ToolError(code="no_session", message="No active or historical session found")
        with self._lock:
            session = self._sessions.get(selected)
        if not session:
            raise ToolError(code="session_not_found", message="Session not found", details={"session_id": selected})
        return session

    def stop(self, session_id: str | None = None) -> tuple[bool, int | None]:
        session = self.get_session(session_id)
        proc = session.process
        if proc.poll() is not None:
            return True, proc.returncode
        proc.terminate()
        try:
            exit_code = proc.wait(timeout=5)
            return True, exit_code
        except subprocess.TimeoutExpired:
            proc.kill()
            exit_code = proc.wait(timeout=5)
            return True, exit_code

    def get_output(self, session_id: str | None, limit: int, cursor: str | None):
        session = self.get_session(session_id)
        entries, next_cursor = session.buffer.read(limit=limit, cursor=cursor)
        return entries, next_cursor

