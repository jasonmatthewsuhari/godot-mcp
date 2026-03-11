"""Batch execution tool handler."""

from __future__ import annotations

from typing import Any

from ..errors import MCPError
from ..models.batch import BatchExecuteRequest, BatchExecuteResponse
from .definitions import ToolDefinition, parse_arguments


class BatchToolsMixin:
    """Mixin providing batch tool execution."""

    def _get_batch_definitions(self) -> dict[str, ToolDefinition]:
        return {
            "batch_execute": ToolDefinition(
                name="batch_execute",
                description="Execute multiple tool calls in a single request.",
                request_model=BatchExecuteRequest,
                response_model=BatchExecuteResponse,
                handler=self.batch_execute,
            ),
        }

    async def batch_execute(self, request: BatchExecuteRequest) -> BatchExecuteResponse:
        definitions = self.get_definitions()
        results: list[dict[str, Any]] = []
        succeeded = 0
        failed = 0

        for op in request.operations:
            tool_name = op.get("tool_name")
            arguments = op.get("arguments", {})

            if not tool_name or tool_name not in definitions:
                entry: dict[str, Any] = {
                    "tool_name": tool_name or "",
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                }
                results.append(entry)
                failed += 1
                if request.atomic:
                    break
                continue

            defn = definitions[tool_name]
            try:
                parsed = parse_arguments(defn.request_model, arguments)
                response = await defn.handler(parsed)
                entry = {
                    "tool_name": tool_name,
                    "success": True,
                    "result": response.model_dump(),
                }
                results.append(entry)
                succeeded += 1
            except Exception as exc:
                error_msg = exc.message if isinstance(exc, MCPError) else str(exc)
                entry = {
                    "tool_name": tool_name,
                    "success": False,
                    "error": error_msg,
                }
                results.append(entry)
                failed += 1
                if request.atomic:
                    break

        return BatchExecuteResponse(
            results=results,
            total=len(results),
            succeeded=succeeded,
            failed=failed,
        )
