"""Parser for extracting structured errors from Godot debug output."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ParsedError:
    """A structured error parsed from debug output."""

    file: str
    line: int
    error_type: str
    message: str
    stack_trace: list[str]


_ERROR_PATTERNS = [
    re.compile(
        r'(?P<type>ERROR|WARNING|SCRIPT ERROR):\s*(?P<message>.+?)\s+at:\s+(?P<file>\S+):(?P<line>\d+)'
    ),
    re.compile(
        r'(?P<file>res://\S+):(?P<line>\d+)\s*-\s*(?P<type>Parse Error|Error):\s*(?P<message>.*)'
    ),
    re.compile(
        r'(?P<type>GDScript error)\s*\((?P<file>[^:]+):(?P<line>\d+)\):\s*(?P<message>.*)'
    ),
]

_STACK_TRACE_RE = re.compile(r'^\s+at\s+(.+)$')


def parse_errors(lines: list[str]) -> list[ParsedError]:
    """Parse Godot debug output lines into structured errors."""
    errors: list[ParsedError] = []
    current_error: ParsedError | None = None

    for line in lines:
        matched = False
        for pattern in _ERROR_PATTERNS:
            match = pattern.search(line)
            if match:
                if current_error:
                    errors.append(current_error)
                current_error = ParsedError(
                    file=match.group("file"),
                    line=int(match.group("line")),
                    error_type=match.group("type"),
                    message=match.group("message").strip(),
                    stack_trace=[],
                )
                matched = True
                break

        if not matched and current_error:
            trace_match = _STACK_TRACE_RE.match(line)
            if trace_match:
                current_error.stack_trace.append(trace_match.group(1))
            elif line.strip() and not line.startswith(" "):
                errors.append(current_error)
                current_error = None

    if current_error:
        errors.append(current_error)

    return errors
