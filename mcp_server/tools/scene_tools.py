"""Scene tool handlers (bridge-mediated)."""

from __future__ import annotations

from ..models import (
    SceneAddNodeRequest,
    SceneAddNodeResponse,
    SceneCreateRequest,
    SceneCreateResponse,
    SceneExportMeshLibraryRequest,
    SceneExportMeshLibraryResponse,
    SceneLoadSpriteRequest,
    SceneLoadSpriteResponse,
    SceneSaveRequest,
    SceneSaveResponse,
)
from .definitions import ToolDefinition


class SceneToolsMixin:
    """Mixin providing scene tool handlers."""

    def _get_scene_definitions(self) -> dict[str, ToolDefinition]:
        return {
            "scene_create": ToolDefinition(
                name="scene_create",
                description="Create a scene through the local Godot addon bridge.",
                request_model=SceneCreateRequest,
                response_model=SceneCreateResponse,
                handler=self.scene_create,
            ),
            "scene_add_node": ToolDefinition(
                name="scene_add_node",
                description="Add a node to a scene through the local Godot addon bridge.",
                request_model=SceneAddNodeRequest,
                response_model=SceneAddNodeResponse,
                handler=self.scene_add_node,
            ),
            "scene_load_sprite": ToolDefinition(
                name="scene_load_sprite",
                description="Load a sprite texture through the local Godot addon bridge.",
                request_model=SceneLoadSpriteRequest,
                response_model=SceneLoadSpriteResponse,
                handler=self.scene_load_sprite,
            ),
            "scene_export_mesh_library": ToolDefinition(
                name="scene_export_mesh_library",
                description="Export a mesh library through the local Godot addon bridge.",
                request_model=SceneExportMeshLibraryRequest,
                response_model=SceneExportMeshLibraryResponse,
                handler=self.scene_export_mesh_library,
            ),
            "scene_save": ToolDefinition(
                name="scene_save",
                description="Save a scene through the local Godot addon bridge.",
                request_model=SceneSaveRequest,
                response_model=SceneSaveResponse,
                handler=self.scene_save,
            ),
        }

    async def scene_create(self, request: SceneCreateRequest) -> SceneCreateResponse:
        payload = self._validate_bridge_payload("scene_create", request)
        response = await self._bridge_call("scene_create", self.bridge_client.scene_create, payload)
        return self._parse_bridge_response("scene_create", SceneCreateResponse, response)

    async def scene_add_node(self, request: SceneAddNodeRequest) -> SceneAddNodeResponse:
        payload = self._validate_bridge_payload("scene_add_node", request)
        response = await self._bridge_call("scene_add_node", self.bridge_client.scene_add_node, payload)
        return self._parse_bridge_response("scene_add_node", SceneAddNodeResponse, response)

    async def scene_load_sprite(self, request: SceneLoadSpriteRequest) -> SceneLoadSpriteResponse:
        payload = self._validate_bridge_payload("scene_load_sprite", request)
        response = await self._bridge_call("scene_load_sprite", self.bridge_client.scene_load_sprite, payload)
        return self._parse_bridge_response("scene_load_sprite", SceneLoadSpriteResponse, response)

    async def scene_export_mesh_library(self, request: SceneExportMeshLibraryRequest) -> SceneExportMeshLibraryResponse:
        payload = self._validate_bridge_payload("scene_export_mesh_library", request)
        response = await self._bridge_call("scene_export_mesh_library", self.bridge_client.scene_export_mesh_library, payload)
        return self._parse_bridge_response("scene_export_mesh_library", SceneExportMeshLibraryResponse, response)

    async def scene_save(self, request: SceneSaveRequest) -> SceneSaveResponse:
        payload = self._validate_bridge_payload("scene_save", request)
        response = await self._bridge_call("scene_save", self.bridge_client.scene_save, payload)
        return self._parse_bridge_response("scene_save", SceneSaveResponse, response)
