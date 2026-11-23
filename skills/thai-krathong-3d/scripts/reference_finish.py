"""Portable materials and a separate Blender look-development stage.

Import from build_reference.py under Blender 3.6+ (tested with 4.3.2):
    apply_materials(asset_collection)
    setup_scene(asset_collection, resolution=640, samples=24)
    paths = render_views(output_dir, asset_collection)

Original deterministic pixel textures are connected DIRECTLY to Principled
Base Color, packed in the blend and embedded by GLB export. Roughness and
metallic are scalar factors. Fine procedural bump and subsurface are Blender
look-development additions, NOT baked normal/SSS maps and NOT promised in glTF.
Only export selected asset_collection meshes: the render stage is separate.
"""

from array import array
from pathlib import Path
import math

import bpy
from mathutils import Vector


OWNER = "thai_krathong_reference_finish_v1"
STAGE_NAME = "Krathong_Render_Stage"
EXPORT_CAVEAT = (
    "GLB carries original packed base-color images and scalar roughness/metallic. "
    "Blender-only procedural bump and subsurface are not baked and may be omitted "
    "or differ in glTF viewers. Render-stage floor, lights and cameras are excluded "
    "when exporting only the asset collection."
)

# Palette values are sRGB. Low specular, broad roughness and tiny bump avoid a
# hard plastic appearance. Orange craft petals are smoother than bread crumb.
SPECS = {
    "leaf": ((0.24, 0.43, 0.070), 0.52, 0.035, 0.00010),
    "leaf_dark": ((0.14, 0.29, 0.037), 0.57, 0.025, 0.00009),
    "petal_white": ((0.98, 0.955, 0.82), 0.43, 0.07, 0.000025),
    "petal_pink": ((0.98, 0.91, 0.75), 0.46, 0.06, 0.000025),
    "petal_orange": ((0.94, 0.57, 0.12), 0.57, 0.015, 0.000065),
    "bread": ((0.79, 0.56, 0.28), 0.82, 0.015, 0.00022),
    "bread_crumb": ((0.92, 0.84, 0.66), 0.86, 0.015, 0.00022),
    "bread_crust": ((0.60, 0.31, 0.095), 0.76, 0.01, 0.00013),
    "clay": ((0.48, 0.255, 0.135), 0.84, 0.0, 0.00018),
    "clay_rim": ((0.64, 0.37, 0.19), 0.78, 0.0, 0.00012),
    "clay_outer": ((0.30, 0.145, 0.075), 0.85, 0.0, 0.00016),
    "stem": ((0.74, 0.71, 0.43), 0.76, 0.015, 0.00016),
    "center": ((0.91, 0.76, 0.33), 0.64, 0.035, 0.00008),
    "wax": ((0.96, 0.94, 0.85), 0.36, 0.085, 0.000015),
    "flame": ((1.0, 0.62, 0.11), 0.5, 0.0, 0.0),
    "incense": ((0.39, 0.14, 0.063), 0.86, 0.0, 0.00004),
    "flower_yellow": ((0.96, 0.68, 0.075), 0.65, 0.055, 0.00004),
    "flower_purple": ((0.54, 0.14, 0.42), 0.64, 0.04, 0.00004),
}


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def _mix(a, b, t):
    return tuple(x * (1.0 - t) + y * t for x, y in zip(a, b))


def _smooth(a, b, x):
    t = _clamp((x - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def _hash(x, y, seed=0):
    # Integer hash: deterministic across platforms, independent of random state.
    n = (int(x) * 374761393 + int(y) * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFFFF) / 4294967295.0


def _noise(u, v, freq=8, seed=0):
    x, y = u * freq, v * freq
    ix, iy = math.floor(x), math.floor(y)
    a, b = x - ix, y - iy
    a, b = a * a * (3 - 2 * a), b * b * (3 - 2 * b)
    low = _hash(ix, iy, seed) * (1 - a) + _hash(ix + 1, iy, seed) * a
    high = _hash(ix, iy + 1, seed) * (1 - a) + _hash(ix + 1, iy + 1, seed) * a
    return low * (1 - b) + high * b


def _srgb_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgba_linear(rgb):
    return tuple(_srgb_linear(_clamp(x)) for x in rgb) + (1.0,)


def _pixel(role, u, v, x, y):
    base = SPECS[role][0]
    grain = _hash(x, y, 71) - 0.5
    cloud = _noise(u, v, 7, 9) - 0.5
    fine = _noise(u, v, 31, 27) - 0.5
    if role.startswith("leaf"):
        # Longitudinal banana-leaf fibers, secondary veins and a soft midrib.
        bend = 0.006 * math.sin(v * 11.0) + 0.003 * math.sin(v * 37.0)
        strand = math.sin((u + bend) * math.tau * 73.0)
        broad = math.sin((u + bend) * math.tau * 17.0)
        vein = math.exp(-((abs(u - 0.5) / 0.014) ** 2))
        side_vein = max(0.0, math.cos((v + 0.16 * abs(u - 0.5)) * math.tau * 23)) ** 18
        factor = 0.96 + 0.065 * strand + 0.065 * broad + 0.16 * cloud + 0.025 * grain
        color = tuple(c * factor for c in base)
        return _mix(color, (0.54, 0.62, 0.20), 0.12 * vein + 0.035 * side_vein)
    if role in {"petal_white", "petal_pink"}:
        # UV v runs from root to tip; u runs across the broad curved petal.
        root = _mix((0.78, 0.84, 0.48), base, _smooth(0.0, 0.30, v))
        tip = _smooth(0.54, 0.98, v)
        edge = _smooth(0.33, 0.50, abs(u - 0.5))
        amount = (0.62 * tip + 0.10 * edge * v) if role == "petal_pink" else 0.055 * tip
        color = _mix(root, (0.80, 0.28, 0.43), amount)
        flow = u + 0.022 * math.sin(v * 7.0) * abs(u - 0.5)
        veins = max(0.0, math.cos(flow * math.tau * 21.0)) ** 12
        factor = 1.0 - veins * 0.028 + cloud * 0.025 + grain * 0.008
        return tuple(c * factor for c in color)
    if role == "petal_orange":
        color = _mix((0.98, 0.76, 0.30), base, _smooth(0.03, 0.54, v))
        tip = _smooth(0.68, 1.0, v)
        lip = _smooth(0.34, 0.50, abs(u - 0.5)) * _smooth(0.2, 0.7, v)
        color = _mix(color, (0.67, 0.245, 0.025), 0.42 * tip + 0.20 * lip)
        return tuple(c * (1.0 + 0.055 * cloud + 0.018 * fine + 0.006 * grain) for c in color)
    if role == "bread_crumb":
        pore = _smooth(0.64, 0.90, _noise(u, v, 55, 13))
        color = _mix(base, (0.58, 0.40, 0.19), pore * 0.48)
        return tuple(c * (1.0 + 0.055 * cloud + 0.025 * fine + 0.01 * grain) for c in color)
    if role in {"bread", "bread_crust"}:
        # Irregular crumb/toasting, never a perfectly uniform orange plastic.
        color = _mix(base, (0.98, 0.74, 0.32), 0.12 + 0.12 * cloud if role == "bread_crust" else 0.30 + 0.30 * cloud)
        toast = _smooth(0.52, 0.91, _noise(u, v, 5, 81))
        color = _mix(color, (0.54, 0.245, 0.060), toast * 0.38)
        pore = _smooth(0.72, 0.92, _noise(u, v, 66, 13))
        if role == "bread":
            color = _mix(color, (0.93, 0.82, 0.58), 0.28)
        return tuple(c * (1.0 + 0.08 * fine - 0.22 * pore + 0.018 * grain) for c in color)
    if role.startswith("clay"):
        speck = max(0.0, (grain - 0.28) / 0.22)
        wheel = math.sin(v * math.tau * 63) * 0.012
        return tuple(c * (1.0 + cloud * 0.20 + fine * 0.08 - speck * 0.17 + wheel) for c in base)
    if role == "stem":
        pore = _smooth(0.64, 0.86, _noise(u, v, 43, 17))
        fibers = math.sin(u * math.tau * 52) * 0.035
        return tuple(c * (1 + 0.14 * cloud + fibers - 0.17 * pore) for c in base)
    factor = 1.0 + 0.06 * cloud + 0.022 * grain
    if role == "incense":
        factor += 0.055 * math.sin(u * math.tau * 20)
    return tuple(c * factor for c in base)


def _image_for(role):
    name = "KR_Original_" + role + "_Albedo"
    old = bpy.data.images.get(name)
    if old and old.get("krathong_owner") == OWNER:
        return old
    width, height = (256, 256) if role.startswith("leaf") else ((128, 256) if role.startswith("petal") else (128, 128))
    img = bpy.data.images.new(name, width=width, height=height, alpha=True, float_buffer=False)
    img["krathong_owner"] = OWNER
    img["source"] = "Original deterministic pixel synthesis; no reference photo pixels used"
    img.colorspace_settings.name = "sRGB"
    pixels = array("f")
    # Byte image pixel access stores encoded sRGB values; the Image Texture node
    # performs the sRGB-to-linear conversion. Do not double-convert this buffer.
    for y in range(height):
        v = y / (height - 1)
        for x in range(width):
            rgb = _pixel(role, x / (width - 1), v, x, y)
            pixels.extend(tuple(_clamp(c) for c in rgb) + (1.0,))
    img.pixels.foreach_set(pixels)
    img.update()
    img.file_format = "PNG"
    img.pack()
    return img


def _socket(node, names, value):
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return


def _material_for(role):
    name = "KR_" + role
    old = bpy.data.materials.get(name)
    if old and old.get("krathong_owner") == OWNER:
        return old
    mat = bpy.data.materials.new(name)
    mat["krathong_owner"] = OWNER
    mat["krathong_role"] = role
    mat["export_caveat"] = EXPORT_CAVEAT
    base, roughness, sss, bump_distance = SPECS[role]
    mat.diffuse_color = _rgba_linear(base)
    mat.roughness = roughness
    mat.metallic = 0.0
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (720, 80)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (410, 80)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0
    _socket(bsdf, ("Specular IOR Level", "Specular"), 0.28)
    _socket(bsdf, ("Subsurface Weight", "Subsurface"), sss)
    _socket(bsdf, ("Subsurface Scale",), 0.0012)
    _socket(bsdf, ("Subsurface Radius",), (1.0, 0.45, 0.2))
    _socket(bsdf, ("Coat Weight", "Clearcoat"), 0.0)
    if role == "flame":
        _socket(bsdf, ("Emission Color", "Emission"), _rgba_linear((1.0, 0.64, 0.13)))
        _socket(bsdf, ("Emission Strength",), 3.0)
    image = nodes.new("ShaderNodeTexImage")
    image.name = "EXPORT_BaseColor_OriginalPixels"
    image.label = "Portable original albedo (packed PNG)"
    image.location = (-390, 260)
    image.image = _image_for(role)
    image.interpolation = "Linear"
    image.extension = "EXTEND" if role.startswith("petal") else "REPEAT"
    uv = nodes.new("ShaderNodeTexCoord")
    uv.location = (-820, 0)
    links.new(uv.outputs["UV"], image.inputs["Vector"])
    links.new(image.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    # The following chain is intentionally lookdev-only. There is no normal
    # image and therefore no false claim that Blender shader nodes were baked.
    noise = nodes.new("ShaderNodeTexNoise")
    noise.name = "BLENDER_ONLY_MicroSurface"
    noise.label = "Blender-only micro surface; not baked"
    noise.location = (-380, -190)
    noise.inputs["Scale"].default_value = 105.0 if role.startswith("petal") else 68.0
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.64
    mapping = nodes.new("ShaderNodeVectorMath")
    mapping.operation = "MULTIPLY"
    mapping.location = (-620, -180)
    mapping.inputs[1].default_value = (3.8, 0.38, 1.0) if role.startswith("leaf") else (1.0, 1.0, 1.0)
    links.new(uv.outputs["UV"], mapping.inputs[0])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.name = "BLENDER_ONLY_Bump"
    bump.location = (130, -180)
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = bump_distance
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _asset_meshes(asset_collection):
    if isinstance(asset_collection, str):
        asset_collection = bpy.data.collections.get(asset_collection)
    if asset_collection is None:
        raise ValueError("Asset collection does not exist")
    return [o for o in asset_collection.all_objects if o.type == "MESH"]


def _fallback_uv(obj):
    """Stable planar UV for incidental primitives; preserve authored petal UV."""
    mesh = obj.data
    if mesh.uv_layers or not mesh.vertices:
        return False
    uv = mesh.uv_layers.new(name="UVMap")
    ranges = []
    for axis in range(3):
        values = [v.co[axis] for v in mesh.vertices]
        ranges.append((min(values), max(values)))
    axes = sorted(range(3), key=lambda i: ranges[i][1] - ranges[i][0], reverse=True)[:2]
    for loop in mesh.loops:
        point = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = tuple(
            (point[a] - ranges[a][0]) / max(ranges[a][1] - ranges[a][0], 1e-9)
            for a in axes
        )
    obj["krathong_uv_fallback"] = "planar: authored UV recommended for directional detail"
    return True


def apply_materials(asset_collection):
    """Assign one portable role material to each source mesh and pack albedo."""
    meshes = _asset_meshes(asset_collection)
    used, fallback, unknown = {}, [], []
    for obj in meshes:
        role = str(obj.get("krathong_material", "leaf"))
        if role == "bread" and obj.get("krathong_bread_surface") in {"crumb", "crust"}:
            role += "_" + obj["krathong_bread_surface"]
        if role == "clay" and obj.get("krathong_clay_surface") in {"rim", "outer"}:
            role += "_" + obj["krathong_clay_surface"]
        if role == "wax" and obj.get("krathong_detail") == "flame":
            role = "flame"
        if role not in SPECS:
            unknown.append({"object": obj.name, "role": role})
            role = "leaf"
        material = _material_for(role)
        obj.data.materials.clear()
        obj.data.materials.append(material)
        for polygon in obj.data.polygons:
            polygon.material_index = 0
        if _fallback_uv(obj):
            fallback.append(obj.name)
        used[role] = material.name
    report = {"materials": used, "object_count": len(meshes),
              "fallback_uv_objects": fallback, "unknown_roles": unknown,
              "export_caveat": EXPORT_CAVEAT}
    bpy.context.scene["krathong_export_caveat"] = EXPORT_CAVEAT
    return report


def _bounds(asset_collection):
    bpy.context.view_layer.update()
    points = [obj.matrix_world @ Vector(corner)
              for obj in _asset_meshes(asset_collection) for corner in obj.bound_box]
    if not points:
        raise ValueError("No mesh bounds in asset collection")
    if not all(math.isfinite(value) for p in points for value in p):
        raise ValueError("Nonfinite asset bounds")
    lo = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return lo, hi, points


def _aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def _new_stage():
    old = bpy.data.collections.get(STAGE_NAME)
    if old and old.get("krathong_owner") == OWNER:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    stage = bpy.data.collections.new(STAGE_NAME)
    stage["krathong_owner"] = OWNER
    stage["purpose"] = "Preview only; exclude from GLB export"
    bpy.context.scene.collection.children.link(stage)
    return stage


def _add_light(stage, name, position, target, power, size, color):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy, data.shape, data.size, data.color = power, "DISK", size, color
    obj = bpy.data.objects.new(name, data)
    stage.objects.link(obj)
    obj.location = position
    _aim(obj, target)
    return obj


def _floor(stage, center, span, bottom):
    z = bottom - max(0.0008, span * 0.003)
    size = span * 15.0
    mesh = bpy.data.meshes.new("KR_Stage_Surface_Mesh")
    mesh.from_pydata([(-size, -size, z), (size, -size, z), (size, size, z), (-size, size, z)], [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new("STAGE_Dark_Water_Surface", mesh)
    obj.location.x, obj.location.y = center.x, center.y
    obj["exclude_from_asset_export"] = True
    stage.objects.link(obj)
    mat = bpy.data.materials.new("STAGE_Cool_Water")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.008, 0.013, 0.024, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.42
    bsdf.inputs["Metallic"].default_value = 0.0
    _socket(bsdf, ("Specular IOR Level", "Specular"), 0.19)
    noise = mat.node_tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 25.0 / span
    noise.inputs["Detail"].default_value = 2.0
    coords = mat.node_tree.nodes.new("ShaderNodeTexCoord")
    stretch = mat.node_tree.nodes.new("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (0.35, 2.0, 1.0)
    bump = mat.node_tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    bump.inputs["Distance"].default_value = span * 0.0015
    links = mat.node_tree.links
    links.new(coords.outputs["Object"], stretch.inputs[0])
    links.new(stretch.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    mesh.materials.append(mat)
    return obj


def _fit_camera(camera, target, direction, points, span):
    direction = Vector(direction).normalized()
    camera.location = Vector(target) + direction * span * 4.0
    _aim(camera, target)
    # Fit projected asset corners independently for every view. Tall incense
    # and broad petals therefore remain inside the same image margins.
    inverse = camera.rotation_euler.to_matrix().transposed()
    projected = [inverse @ (p - Vector(target)) for p in points]
    min_x, max_x = min(p.x for p in projected), max(p.x for p in projected)
    min_y, max_y = min(p.y for p in projected), max(p.y for p in projected)
    width, height = max_x - min_x, max_y - min_y
    camera.location += camera.rotation_euler.to_matrix() @ Vector(((min_x + max_x) * 0.5, (min_y + max_y) * 0.5, 0.0))
    scene = bpy.context.scene
    aspect = scene.render.resolution_x / scene.render.resolution_y
    camera.data.ortho_scale = max(height, width / aspect) * 1.17
    camera.data.clip_start = max(0.001, span * 0.005)
    camera.data.clip_end = span * 100.0


def setup_scene(asset_collection, resolution=640, samples=24):
    """Set EEVEE studio lighting; preserve asset geometry and collection links."""
    if resolution < 64 or samples < 1:
        raise ValueError("resolution must be >= 64 and samples >= 1")
    scene = bpy.context.scene
    lo, hi, points = _bounds(asset_collection)
    target = (lo + hi) * 0.5
    span = max(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, 0.01)
    stage = _new_stage()
    scene.render.engine = "BLENDER_EEVEE_NEXT" if bpy.app.version >= (4, 2, 0) else "BLENDER_EEVEE"
    if hasattr(scene, "eevee"):
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = samples
        if hasattr(scene.eevee, "taa_samples"):
            scene.eevee.taa_samples = samples
        if hasattr(scene.eevee, "use_gtao"):
            scene.eevee.use_gtao = bpy.app.version < (4, 2, 0)
        if hasattr(scene.eevee, "gtao_distance"):
            scene.eevee.gtao_distance = span * 0.12
        if hasattr(scene.eevee, "gtao_factor"):
            scene.eevee.gtao_factor = 1.15
        # The new renderer's default screen-space GI thickness is large beside
        # millimetre petal shells and can produce mottled overlap shadows. Use
        # stable direct lighting here; retain physically present cast shadows.
        if hasattr(scene.eevee, "use_fast_gi"):
            scene.eevee.use_fast_gi = False
        if hasattr(scene.eevee, "shadow_ray_count"):
            scene.eevee.shadow_ray_count = 4
        if hasattr(scene.eevee, "shadow_step_count"):
            scene.eevee.shadow_step_count = 12
    scene.render.resolution_x = scene.render.resolution_y = int(resolution)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.image_settings.color_depth = "8"
    scene.render.use_file_extension = True
    scene.view_settings.view_transform = "AgX" if bpy.app.version >= (4, 0, 0) else "Filmic"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    try:
        scene.view_settings.look = "AgX - Medium High Contrast" if bpy.app.version >= (4, 0, 0) else "Medium High Contrast"
    except TypeError:
        pass
    scene.world = bpy.data.worlds.new("KR_Cool_Studio_World")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.045, 0.07, 0.12, 1.0)
    background.inputs["Strength"].default_value = 0.32
    floor = _floor(stage, target, span, lo.z)
    scale_squared = (span / 0.26) ** 2
    _add_light(stage, "STAGE_Key_Soft", target + Vector((-0.85, -1.20, 1.7)) * span,
               target, 4.0 * scale_squared, span * 1.45, (1.0, 0.94, 0.83))
    _add_light(stage, "STAGE_Fill_Soft", target + Vector((1.0, -0.65, 0.85)) * span,
               target, 1.7 * scale_squared, span * 1.8, (0.74, 0.84, 1.0))
    _add_light(stage, "STAGE_Rim_Warm", target + Vector((0.25, 1.2, 1.35)) * span,
               target, 3.0 * scale_squared, span * 0.95, (1.0, 0.66, 0.34))
    data = bpy.data.cameras.new("STAGE_Orthographic_Camera")
    data.type = "ORTHO"
    camera = bpy.data.objects.new("STAGE_Orthographic_Camera", data)
    stage.objects.link(camera)
    scene.camera = camera
    _fit_camera(camera, target, (1.2, -1.75, 1.65), points, span)
    scene["krathong_stage_collection"] = stage.name
    scene["krathong_renderer"] = scene.render.engine
    scene["krathong_requested_samples"] = samples
    return {"stage_collection": stage.name, "camera": camera.name,
            "bounds_min": list(lo), "bounds_max": list(hi),
            "floor_z": floor.data.vertices[0].co.z, "renderer": scene.render.engine,
            "export_caveat": EXPORT_CAVEAT}


def render_views(output_dir, asset_collection):
    """Render actual Blender PNGs in iso/front/top order; return path mapping."""
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    if scene.camera is None or scene.camera.name not in bpy.data.objects:
        setup_scene(asset_collection)
    camera = scene.camera
    lo, hi, points = _bounds(asset_collection)
    target, span = (lo + hi) * 0.5, max(hi[i] - lo[i] for i in range(3))
    views = {"iso": (1.2, -1.75, 1.65), "front": (0.0, -1.0, 0.0), "top": (0.0, 0.0, 1.0)}
    saved = camera.location.copy(), camera.rotation_euler.copy(), camera.data.ortho_scale, scene.render.filepath
    paths = {}
    try:
        for name, direction in views.items():
            _fit_camera(camera, target, direction, points, span)
            scene.render.filepath = str(output_dir / ("render_" + name + ".png"))
            bpy.context.view_layer.update()
            bpy.ops.render.render(write_still=True)
            path = Path(scene.render.filepath)
            if not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError("Blender did not write render: " + str(path))
            paths[name] = str(path)
    finally:
        camera.location, camera.rotation_euler, camera.data.ortho_scale, scene.render.filepath = saved
        bpy.context.view_layer.update()
    return paths
