"""3D world building tool handlers (bridge-mediated)."""

from __future__ import annotations

from ..models import (
    AnimationAddKeyframeRequest,
    AnimationAddKeyframeResponse,
    AnimationCreateRequest,
    AnimationCreateResponse,
    CsgOperationsRequest,
    CsgOperationsResponse,
    EnvironmentSetupRequest,
    EnvironmentSetupResponse,
    GridmapPlaceRequest,
    GridmapPlaceResponse,
    MaterialApplyRequest,
    MaterialApplyResponse,
    MaterialCreateRequest,
    MaterialCreateResponse,
    TilemapPaintRequest,
    TilemapPaintResponse,
)
from .definitions import ToolDefinition


class WorldToolsMixin:
    """Mixin providing 3D world building tools."""

    def _get_world_definitions(self) -> dict[str, ToolDefinition]:
        return {
            "tilemap_paint": ToolDefinition(
                name="tilemap_paint",
                description="Paint cells on a TileMap node in a scene.",
                request_model=TilemapPaintRequest,
                response_model=TilemapPaintResponse,
                handler=self.tilemap_paint,
            ),
            "gridmap_place": ToolDefinition(
                name="gridmap_place",
                description="Place items in a GridMap node in a scene.",
                request_model=GridmapPlaceRequest,
                response_model=GridmapPlaceResponse,
                handler=self.gridmap_place,
            ),
            "material_create": ToolDefinition(
                name="material_create",
                description="Create a material resource in a Godot project.",
                request_model=MaterialCreateRequest,
                response_model=MaterialCreateResponse,
                handler=self.material_create,
            ),
            "material_apply": ToolDefinition(
                name="material_apply",
                description="Apply a material to a mesh node in a scene.",
                request_model=MaterialApplyRequest,
                response_model=MaterialApplyResponse,
                handler=self.material_apply,
            ),
            "environment_setup": ToolDefinition(
                name="environment_setup",
                description="Configure a 3D environment in a scene.",
                request_model=EnvironmentSetupRequest,
                response_model=EnvironmentSetupResponse,
                handler=self.environment_setup,
            ),
            "csg_operations": ToolDefinition(
                name="csg_operations",
                description="Add CSG shapes with boolean operations to a scene.",
                request_model=CsgOperationsRequest,
                response_model=CsgOperationsResponse,
                handler=self.csg_operations,
            ),
            "animation_create": ToolDefinition(
                name="animation_create",
                description="Create an animation on an AnimationPlayer node.",
                request_model=AnimationCreateRequest,
                response_model=AnimationCreateResponse,
                handler=self.animation_create,
            ),
            "animation_add_keyframe": ToolDefinition(
                name="animation_add_keyframe",
                description="Add a keyframe to an animation track.",
                request_model=AnimationAddKeyframeRequest,
                response_model=AnimationAddKeyframeResponse,
                handler=self.animation_add_keyframe,
            ),
        }

    async def tilemap_paint(self, request: TilemapPaintRequest) -> TilemapPaintResponse:
        payload = self._validate_bridge_payload("tilemap_paint", request)
        response = await self._bridge_call("tilemap_paint", self.bridge_client.tilemap_paint, payload)
        return self._parse_bridge_response("tilemap_paint", TilemapPaintResponse, response)

    async def gridmap_place(self, request: GridmapPlaceRequest) -> GridmapPlaceResponse:
        payload = self._validate_bridge_payload("gridmap_place", request)
        response = await self._bridge_call("gridmap_place", self.bridge_client.gridmap_place, payload)
        return self._parse_bridge_response("gridmap_place", GridmapPlaceResponse, response)

    async def material_create(self, request: MaterialCreateRequest) -> MaterialCreateResponse:
        payload = self._validate_bridge_payload("material_create", request)
        response = await self._bridge_call("material_create", self.bridge_client.material_create, payload)
        return self._parse_bridge_response("material_create", MaterialCreateResponse, response)

    async def material_apply(self, request: MaterialApplyRequest) -> MaterialApplyResponse:
        payload = self._validate_bridge_payload("material_apply", request)
        response = await self._bridge_call("material_apply", self.bridge_client.material_apply, payload)
        return self._parse_bridge_response("material_apply", MaterialApplyResponse, response)

    async def environment_setup(self, request: EnvironmentSetupRequest) -> EnvironmentSetupResponse:
        payload = self._validate_bridge_payload("environment_setup", request)
        response = await self._bridge_call("environment_setup", self.bridge_client.environment_setup, payload)
        return self._parse_bridge_response("environment_setup", EnvironmentSetupResponse, response)

    async def csg_operations(self, request: CsgOperationsRequest) -> CsgOperationsResponse:
        payload = self._validate_bridge_payload("csg_operations", request)
        response = await self._bridge_call("csg_operations", self.bridge_client.csg_operations, payload)
        return self._parse_bridge_response("csg_operations", CsgOperationsResponse, response)

    async def animation_create(self, request: AnimationCreateRequest) -> AnimationCreateResponse:
        payload = self._validate_bridge_payload("animation_create", request)
        response = await self._bridge_call("animation_create", self.bridge_client.animation_create, payload)
        return self._parse_bridge_response("animation_create", AnimationCreateResponse, response)

    async def animation_add_keyframe(self, request: AnimationAddKeyframeRequest) -> AnimationAddKeyframeResponse:
        payload = self._validate_bridge_payload("animation_add_keyframe", request)
        response = await self._bridge_call("animation_add_keyframe", self.bridge_client.animation_add_keyframe, payload)
        return self._parse_bridge_response("animation_add_keyframe", AnimationAddKeyframeResponse, response)
