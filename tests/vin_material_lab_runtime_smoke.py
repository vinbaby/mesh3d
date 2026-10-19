"""Headless Blender smoke test for the standalone VIN Material Lab add-on."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import bpy


def main() -> None:
    addon_path = Path(__file__).parents[1] / "blender_addon" / "vin_material_lab.py"
    spec = importlib.util.spec_from_file_location("vin_material_lab", addon_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load VIN Material Lab add-on")
    addon = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = addon
    spec.loader.exec_module(addon)
    addon.register()

    settings = bpy.context.scene.vinmat_settings
    settings.palette = "NEON_PRISM"
    settings.surface_finish = "BLACK_CHROME"
    settings.texture_pattern = "NOISE_RAMP"
    settings.seed = 307
    settings.texture_scale = 3.2
    settings.texture_detail = 4
    settings.ramp_contrast = 0.22
    settings.accent_strength = 0.55
    settings.bump_strength = 0.18
    settings.bump_distance = 0.06
    settings.glow_strength = 0.0

    cube_mesh = bpy.data.meshes.new("VIN Material Test Cube Mesh")
    cube_mesh.from_pydata(
        [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
         (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)],
        [],
        [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],
    )
    cube_mesh.update()
    cube = bpy.data.objects.new("VIN Material Test Cube", cube_mesh)
    bpy.context.scene.collection.objects.link(cube)

    sphere_mesh = bpy.data.meshes.new("VIN Material Test Sphere Mesh")
    sphere_mesh.from_pydata(
        [(0,0,1),(1,0,0),(0,1,0),(-1,0,0),(0,-1,0),(0,0,-1)],
        [],
        [(0,2,1),(0,3,2),(0,4,3),(0,1,4),(5,1,2),(5,2,3),(5,3,4),(5,4,1)],
    )
    sphere_mesh.update()
    sphere = bpy.data.objects.new("VIN Material Test Sphere", sphere_mesh)
    sphere.location.x = 3.0
    bpy.context.scene.collection.objects.link(sphere)

    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    cube.select_set(True)
    sphere.select_set(True)
    bpy.context.view_layer.objects.active = cube
    result = bpy.ops.vinmat.apply_selected()
    if "FINISHED" not in result:
        raise AssertionError(f"VIN Material Lab failed to apply: {result}")

    materials = []
    for obj in (cube, sphere):
        if len(obj.data.materials) != 1 or obj.data.materials[0] is None:
            raise AssertionError(f"{obj.name} does not have one generated material")
        material = obj.data.materials[0]
        materials.append(material)
        if not material.use_nodes:
            raise AssertionError(f"{obj.name} material does not use shader nodes")
        nodes = {node.bl_idname for node in material.node_tree.nodes}
        required = {
            "ShaderNodeOutputMaterial",
            "ShaderNodeBsdfPrincipled",
            "ShaderNodeTexCoord",
            "ShaderNodeMapping",
            "ShaderNodeValToRGB",
            "ShaderNodeBump",
        }
        if not required.issubset(nodes):
            raise AssertionError(f"{obj.name} material missing nodes: {required - nodes}")
        if len(material.node_tree.links) < 7:
            raise AssertionError(f"{obj.name} material graph has too few links")
        if material.get("vinmat_palette") != "NEON_PRISM":
            raise AssertionError(f"{obj.name} material palette metadata is wrong")
        if material.get("vinmat_node_count") != len(material.node_tree.nodes):
            raise AssertionError(f"{obj.name} node count metadata is wrong")
    if materials[0].as_pointer() == materials[1].as_pointer():
        raise AssertionError("Selected objects should receive independent materials/node trees")
    print(f"[OK] Apply selected: {len(materials)} independent materials with Noise/Color Ramp/Bump nodes")

    patterns = (
        "CLEAN",
        "BRUSHED",
        "NOISE_RAMP",
        "CARBON_FIBER",
        "HEX_CELLS",
        "PITTED",
        "CIRCUIT_LINES",
        "FABRIC_WEAVE",
        "WOOD_GRAIN",
        "SPECKLED_STONE",
        "MICRO_SCRATCHES",
        "WATER_DROPLETS",
    )
    for pattern in patterns:
        settings.texture_pattern = pattern
        settings.palette = "CYBER_AMBER"
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube
        result = bpy.ops.vinmat.apply_selected()
        if "FINISHED" not in result:
            raise AssertionError(f"Material pattern {pattern} failed to build: {result}")
        material = cube.data.materials[0]
        if material.get("vinmat_texture") != pattern:
            raise AssertionError(f"Material pattern metadata mismatch for {pattern}")
        nodes = {node.bl_idname for node in material.node_tree.nodes}
        if "ShaderNodeValToRGB" not in nodes or "ShaderNodeBump" not in nodes:
            raise AssertionError(f"{pattern} lacks Color Ramp or Bump nodes")
        if pattern in {"CLEAN", "NOISE_RAMP", "PITTED", "CIRCUIT_LINES", "WOOD_GRAIN", "SPECKLED_STONE", "MICRO_SCRATCHES"} and "ShaderNodeTexNoise" not in nodes:
            raise AssertionError(f"{pattern} lacks Noise Texture")
        if pattern in {"BRUSHED", "CARBON_FIBER", "CIRCUIT_LINES", "FABRIC_WEAVE", "WOOD_GRAIN", "MICRO_SCRATCHES"} and "ShaderNodeTexWave" not in nodes:
            raise AssertionError(f"{pattern} lacks Wave Texture")
        if pattern == "CARBON_FIBER" and not any(node.bl_idname == "ShaderNodeMath" for node in material.node_tree.nodes):
            raise AssertionError("Carbon Fiber graph lacks a weave combination node")
        if pattern in {"HEX_CELLS", "PITTED"} and "ShaderNodeTexVoronoi" not in nodes:
            raise AssertionError(f"{pattern} graph lacks Voronoi Texture")
        print(f"[OK] Material texture {pattern}: {len(nodes)} node types, {len(material.node_tree.links)} links")

    settings.palette = "MONO_GOLD"
    settings.texture_pattern = "BRUSHED"
    settings.surface_finish = "PORCELAIN"
    settings.glow_strength = 0.3
    previous_materials = {material.as_pointer() for material in bpy.data.materials}
    result = bpy.ops.vinmat.create_material()
    if "FINISHED" not in result:
        raise AssertionError(f"Create standalone node material failed: {result}")
    templates = [
        material for material in bpy.data.materials
        if material.get("vinmat_version") == "0.2.0"
        and material.as_pointer() not in previous_materials
    ]
    if len(templates) != 1:
        raise AssertionError(f"Create Node Material should add one new standalone material, got {len(templates)}")
    if templates[0].get("vinmat_palette") != "MONO_GOLD":
        raise AssertionError("Standalone node material did not use the selected palette")
    if templates[0].get("vinmat_texture") != "BRUSHED":
        raise AssertionError("Standalone node material did not use the selected texture pattern")
    print(f"[OK] Standalone node material: {templates[0].name}")

    finishes = (
        "TITANIUM", "BLACK_CHROME", "PORCELAIN", "CARBON_COMPOSITE",
        "ALIEN_POROUS", "ENERGY_CERAMIC", "CLEAR_GLASS", "FROSTED_GLASS",
        "CLEAR_PLASTIC", "MATTE_PLASTIC", "RUBBER", "FABRIC", "LEATHER",
        "WOOD", "STONE", "PAPER",
    )
    for finish in finishes:
        settings.surface_finish = finish
        settings.texture_pattern = "NOISE_RAMP"
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube
        result = bpy.ops.vinmat.apply_selected()
        if "FINISHED" not in result:
            raise AssertionError(f"Surface finish {finish} failed to build: {result}")
        material = cube.data.materials[0]
        shader = material.node_tree.nodes.get("VINMAT · Principled Surface")
        if shader is None:
            raise AssertionError(f"{finish} lacks Principled Surface")
        if material.get("vinmat_finish") != finish:
            raise AssertionError(f"{finish} finish metadata mismatch")
        transmission = shader.inputs.get("Transmission Weight") or shader.inputs.get("Transmission")
        if finish in {"CLEAR_GLASS", "FROSTED_GLASS", "CLEAR_PLASTIC"}:
            if transmission is None or transmission.default_value <= 0.0:
                raise AssertionError(f"{finish} should configure transmission")
        if finish == "RUBBER" and shader.inputs["Roughness"].default_value < 0.75:
            raise AssertionError("Rubber should be very rough")
        if finish == "FABRIC":
            sheen = shader.inputs.get("Sheen Weight") or shader.inputs.get("Sheen")
            if sheen is not None and sheen.default_value < 0.2:
                raise AssertionError("Fabric should configure visible sheen")
        print(f"[OK] Surface finish {finish}: {len(material.node_tree.nodes)} nodes")

    for palette in (
        "CYBER_AMBER", "MONO_GOLD", "NEON_PRISM", "TITANIUM_SUNSET",
        "PORCELAIN_CHAMPAGNE", "VOID_EMBER", "EARTH_NATURAL",
        "SOFT_PASTEL", "OCEAN_COAST", "FOREST_MOSS", "CANDY_POP",
        "CLAY_TERRACOTTA",
    ):
        settings.palette = palette
        result = bpy.ops.vinmat.create_material()
        if "FINISHED" not in result:
            raise AssertionError(f"Palette {palette} could not create a material")
    print("[OK] All 12 color palettes create editable materials.")
    print("VIN Material Lab Blender runtime smoke test passed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VIN Material Lab Blender runtime smoke test failed: {exc}", file=sys.stderr)
        raise
