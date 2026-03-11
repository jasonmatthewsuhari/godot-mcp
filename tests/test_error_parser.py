"""Tests for the Godot error parser."""

from __future__ import annotations

from mcp_server.error_parser import parse_errors


def test_parse_standard_error() -> None:
    lines = [
        'ERROR: Something went wrong at: res://scripts/player.gd:42',
    ]
    errors = parse_errors(lines)
    assert len(errors) == 1
    assert errors[0].file == "res://scripts/player.gd"
    assert errors[0].line == 42
    assert errors[0].error_type == "ERROR"
    assert "Something went wrong" in errors[0].message


def test_parse_script_error() -> None:
    lines = [
        'res://scripts/main.gd:10 - Parse Error: Unexpected token',
    ]
    errors = parse_errors(lines)
    assert len(errors) == 1
    assert errors[0].file == "res://scripts/main.gd"
    assert errors[0].line == 10
    assert "Unexpected token" in errors[0].message


def test_parse_warning() -> None:
    lines = [
        'WARNING: Unused variable at: res://scripts/enemy.gd:5',
    ]
    errors = parse_errors(lines)
    assert len(errors) == 1
    assert errors[0].error_type == "WARNING"


def test_parse_multiple_errors() -> None:
    lines = [
        'ERROR: First error at: res://a.gd:1',
        'some other output',
        'ERROR: Second error at: res://b.gd:2',
    ]
    errors = parse_errors(lines)
    assert len(errors) == 2


def test_parse_no_errors() -> None:
    lines = [
        'Godot Engine v4.4.stable',
        'Loading project...',
        'Scene loaded successfully',
    ]
    errors = parse_errors(lines)
    assert len(errors) == 0


def test_parse_with_stack_trace() -> None:
    lines = [
        'ERROR: Null instance at: res://scripts/player.gd:42',
        '   at res://scripts/player.gd:42 in func _ready()',
        '   at res://scripts/main.gd:10 in func _process()',
        'next line',
    ]
    errors = parse_errors(lines)
    assert len(errors) == 1
    assert len(errors[0].stack_trace) == 2
