"""Bake a separate web mesh/UV atlas and embedded GLB from a krathong BLEND.

Run in isolated background Blender with --python-exit-code 1. Refuses live
scenes, source overwrites and nonempty output directories. Original input is
never saved. No decimation, automatic retopology or high-to-low projection.
"""
import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bmesh
import bpy
from mesh_uv_qa import inspect, uv_islands


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")


def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def prepare_web(collection, resolution, margin, angle_limit=66):
    """Work on evaluated copies; retain source UV for sampling and new bake UV."""
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    copies, material_copies = [], {}
    web = bpy.data.collections.new("Krathong_Web")
    scene.collection.children.link(web)
    for source in collection.all_objects:
        if source.type != "MESH":
            continue
        mesh = bpy.data.meshes.new_from_object(source.evaluated_get(depsgraph), depsgraph=depsgraph)
        obj = bpy.data.objects.new(source.name+"_web", mesh)
        obj.matrix_world = source.matrix_world.copy()
        web.objects.link(obj)
        if mesh.uv_layers.active is None:
            raise ValueError("Source is missing UV: "+source.name)
        original_uv = mesh.uv_layers.active.name
        if any(layer.active_render and layer.name != original_uv for layer in mesh.uv_layers):
            raise ValueError("Source active and render UV must match: "+source.name)
        # Only this pipeline's source contract is accepted: explicit UV source,
        # no Generated/Object coordinates that would change after joining.
        mesh.uv_layers.active.name = "SourceUV"
        for layer in list(mesh.uv_layers):
            if layer.name != "SourceUV":
                mesh.uv_layers.remove(layer)
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
                raise ValueError("Source requires node materials: "+source.name)
            material_key = (mat.name, original_uv)
            if material_key not in material_copies:
                copy = mat.copy()
                for node in list(copy.node_tree.nodes):
                    if node.type == "GROUP":
                        raise ValueError("Nested source node groups unsupported; flatten on an authorized copy first")
                    if node.type in {"OBJECT_INFO", "NEW_GEOMETRY", "TEX_ENVIRONMENT", "TEX_SKY", "TEX_POINTDENSITY"}:
                        if any(output.is_linked for output in node.outputs):
                            raise ValueError("Non-UV source coordinate domain unsupported: "+node.name)
                    if node.type.startswith("TEX_") and "Vector" in node.inputs and node.type != "TEX_IMAGE":
                        if not node.inputs["Vector"].is_linked:
                            raise ValueError("Procedural source textures require explicit UV coordinates: "+node.name)
                    if node.type == "TEX_COORD":
                        for output in node.outputs:
                            if output.name != "UV" and output.is_linked:
                                raise ValueError("Only UV-based source coordinates supported")
                        uv = copy.node_tree.nodes.new("ShaderNodeUVMap")
                        uv.uv_map = "SourceUV"
                        for link in list(node.outputs["UV"].links):
                            copy.node_tree.links.new(uv.outputs["UV"], link.to_socket)
                    if node.type == "UVMAP":
                        if node.uv_map and node.uv_map != original_uv:
                            raise ValueError("Source material references another UV set: "+node.uv_map)
                        node.uv_map = "SourceUV"
                    if node.type == "TEX_IMAGE" and not node.inputs["Vector"].is_linked:
                        uv = copy.node_tree.nodes.new("ShaderNodeUVMap")
                        uv.uv_map = "SourceUV"
                        copy.node_tree.links.new(uv.outputs["UV"], node.inputs["Vector"])
                material_copies[material_key] = copy
            slot.material = material_copies[material_key]
        copies.append(obj)
    if not copies:
        raise ValueError("No asset meshes in collection")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in copies:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = "Krathong_WebMesh"
    # Join transforms to active space; explicitly apply the remaining transform.
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    uv = obj.data.uv_layers.new(name="BakeUV")
    obj.data.uv_layers.active = uv
    uv.active_render = True
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle_limit), island_margin=0,
                             margin_method="FRACTION", area_weight=0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    # Source cannot contribute to AO/shadows or appear in an exported/rendered asset.
    for other in list(scene.objects):
        if other != obj:
            bpy.data.objects.remove(other, do_unlink=True)
    return obj, web


def pack_atlas_boxes(obj, resolution, margin):
    """Deterministic uniform-scale shelf pack; never place islands into holes."""
    mesh, layer = obj.data, obj.data.uv_layers["BakeUV"]
    mesh.calc_loop_triangles()
    groups = {}
    for ti, group in enumerate(uv_islands(mesh, layer)):
        groups.setdefault(group, set()).update(mesh.loop_triangles[ti].loops)
    boxes = []
    for loops in groups.values():
        points = [layer.data[i].uv for i in loops]
        lo = [min(p[k] for p in points) for k in (0, 1)]
        hi = [max(p[k] for p in points) for k in (0, 1)]
        boxes.append((loops, lo, hi[0]-lo[0], hi[1]-lo[1]))
    boxes.sort(key=lambda b: (-b[3], -b[2]))
    border, gap = margin/resolution, (2*margin+4)/resolution
    def layout(scale):
        x, y, row, positions = border, border, 0.0, []
        for _, _, w, h in boxes:
            w, h = w*scale, h*scale
            if x+w > 1-border:
                x, y, row = border, y+row+gap, 0.0
            if w > 1-2*border or y+h > 1-border:
                return None
            positions.append((x, y))
            x += w+gap
            row = max(row, h)
        return positions
    low, high = 0.0, 1.0
    while high < 65536 and layout(high) is not None:
        high *= 2
    for _ in range(32):
        middle = (low+high)*.5
        if layout(middle) is None:
            high = middle
        else:
            low = middle
    positions = layout(low)
    if positions is None or low < 1e-8:
        raise ValueError("Island padding cannot fit; increase resolution or reduce margin")
    for (loops, lo, _, _), (x, y) in zip(boxes, positions):
        for li in loops:
            p = layer.data[li].uv.copy()
            layer.data[li].uv = ((p.x-lo[0])*low+x, (p.y-lo[1])*low+y)
    return {"islands": len(boxes), "uniform_scale": low, "packing": "deterministic bounding-box shelf"}


def finish_atlas(obj, resolution, margin):
    """Split only projection-overlapping triangles; one bounded repair pass.

    A curved island can fold over itself under Smart Project. Split the
    demonstrated offending triangles into metric planar UVs, then repack all
    islands. This modifies BakeUV only; it never changes mesh or SourceUV.
    """
    initial = inspect([obj], uv_name="BakeUV", resolution=resolution, bake=True)
    record = {"method": "split projection overlaps once, metric triangle projection, repack", "split_triangles": 0}
    r = initial["objects"][0]
    if r["errors"] and set(r["errors"]) <= {"uv_overlap", "uv_stretch_limit", "uv_density_ratio_limit"}:
        ids = r["uv"].get("overlap_triangle_ids", [])
        if ids:
            obj.data.calc_loop_triangles()
            layer = obj.data.uv_layers["BakeUV"]
            density = math.sqrt(max(r["uv"]["summed_triangle_area"], 1e-12)/
                                max(sum(t.area for t in obj.data.loop_triangles), 1e-12))
            for ti in ids:
                tri = obj.data.loop_triangles[ti]
                a, b, c = [obj.data.vertices[vi].co for vi in tri.vertices]
                axis = (b-a).normalized()
                local = [(0, 0), ((b-a).length*density, 0),
                         ((c-a).dot(axis)*density, (c-a).cross(axis).length*density)]
                # Different translations prevent accidental reconnection at a
                # shared UV edge; the subsequent pack removes these offsets.
                offset = ((ti*.61803398875)%1, (ti*.41421356237)%1)
                for li, p in zip(tri.loops, local):
                    layer.data[li].uv = (p[0]+offset[0], p[1]+offset[1])
            record["split_triangles"] = len(ids)
    if not r["errors"] or set(r["errors"]) <= {"uv_overlap", "uv_stretch_limit", "uv_density_ratio_limit"}:
        record.update(pack_atlas_boxes(obj, resolution, margin))
    return record


def prepare_tangents(obj):
    """Prevent zero MikkTSpace tangents before baking/exporting normal maps."""
    mesh = obj.data
    mesh.calc_tangents(uvmap="BakeUV")
    bad = {l.index for l in mesh.loops if not all(math.isfinite(v) for v in l.tangent) or abs(l.tangent.length-1) > 1e-3}
    faces = [p for p in mesh.polygons if any(li in bad for li in p.loop_indices)]
    for p in faces:
        p.use_smooth = False
    if faces:
        mesh.update()
        mesh.calc_tangents(uvmap="BakeUV")
    if any(abs(l.tangent.length-1) > 1e-3 for l in mesh.loops):
        raise ValueError("Invalid tangent basis remains; inspect UV/sliver geometry before baking")
    return {"flat_shaded_web_faces": [p.index for p in faces], "unit_tangents": True}


def new_image(name, resolution, color=False):
    img = bpy.data.images.new(name, width=resolution, height=resolution, alpha=False, float_buffer=True)
    img.colorspace_settings.name = "sRGB" if color else "Non-Color"
    return img


def save_image(img, out):
    img.file_format = "PNG"
    img.filepath_raw = str(out)
    # Image.save avoids view-transform/lighting being baked into color data.
    img.save()
    if not out.is_file() or out.stat().st_size == 0:
        raise RuntimeError("Missing baked image: "+str(out))
    img.pack()


def bake_map(obj, name, kind, resolution, margin, out):
    image = new_image(name, resolution, name == "BaseColor")
    restores, targets = [], []
    try:
        for mat in obj.data.materials:
            nodes, links = mat.node_tree.nodes, mat.node_tree.links
            outputs = [n for n in nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output]
            if len(outputs) != 1:
                raise ValueError("Expected one active material output")
            output = outputs[0]
            surface_links = list(output.inputs["Surface"].links)
            if len(surface_links) != 1 or surface_links[0].from_node.type != "BSDF_PRINCIPLED":
                raise ValueError("Only direct Principled source surface supported")
            principled = surface_links[0].from_node
            if principled.inputs["Alpha"].is_linked or principled.inputs["Alpha"].default_value < .999:
                raise ValueError("Transparent/alpha sources need a separate bake workflow")
            node = nodes.new("ShaderNodeTexImage")
            node.image = image
            node.name = "BAKE_TARGET_"+name
            for n in nodes:
                n.select = False
            node.select = True
            nodes.active = node
            targets.append((mat, node))
            if name == "Metallic":
                emission = nodes.new("ShaderNodeEmission")
                socket = principled.inputs["Metallic"]
                if socket.is_linked:
                    links.new(socket.links[0].from_socket, emission.inputs["Color"])
                else:
                    v = socket.default_value
                    emission.inputs["Color"].default_value = (v, v, v, 1)
                restores.append((mat, output, surface_links[0].from_socket, emission))
                links.new(emission.outputs[0], output.inputs["Surface"])
        select_only(obj)
        kwargs = {"type": kind, "margin": margin, "margin_type": "EXTEND", "use_clear": True,
                  "use_selected_to_active": False, "uv_layer": "BakeUV"}
        if kind == "DIFFUSE":
            kwargs["pass_filter"] = {"COLOR"}
        if kind == "NORMAL":
            kwargs.update(normal_space="TANGENT", normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")
        bpy.ops.object.bake(**kwargs)
        save_image(image, out/(name+".png"))
    finally:
        for mat, output, socket, emission in restores:
            mat.node_tree.links.new(socket, output.inputs["Surface"])
            mat.node_tree.nodes.remove(emission)
        for mat, node in targets:
            mat.node_tree.nodes.remove(node)
    return image


def pack_orm(images, resolution, out):
    count = resolution*resolution*4
    channels = []
    for key in ("AO", "Roughness", "Metallic"):
        values = array('f', [0])*count
        images[key].pixels.foreach_get(values)
        channels.append(values)
    pixels = array('f', [1])*count
    for i in range(0, count, 4):
        for c in range(3):
            pixels[i+c] = channels[c][i]
    orm = new_image("ORM", resolution)
    orm.pixels.foreach_set(pixels)
    orm.update()
    save_image(orm, out/"ORM.png")
    return orm


def web_material(images):
    mat = bpy.data.materials.new("Krathong_Web_PBR")
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    uv = nodes.new("ShaderNodeUVMap")
    uv.uv_map = "BakeUV"
    tex = {}
    for key in ("BaseColor", "Normal", "ORM"):
        node = nodes.new("ShaderNodeTexImage")
        node.image = images[key]
        links.new(uv.outputs["UV"], node.inputs["Vector"])
        tex[key] = node
    links.new(tex["BaseColor"].outputs["Color"], bsdf.inputs["Base Color"])
    normal = nodes.new("ShaderNodeNormalMap")
    normal.space = "TANGENT"
    normal.uv_map = "BakeUV"
    links.new(tex["Normal"].outputs["Color"], normal.inputs["Color"])
    links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
    separate = nodes.new("ShaderNodeSeparateColor")
    separate.mode = "RGB"
    links.new(tex["ORM"].outputs["Color"], separate.inputs["Color"])
    links.new(separate.outputs["Green"], bsdf.inputs["Roughness"])
    links.new(separate.outputs["Blue"], bsdf.inputs["Metallic"])
    # Recognized Blender glTF exporter hook; AO must stay separate from albedo.
    group = bpy.data.node_groups.get("glTF Material Output")
    if group is None:
        group = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
        group.interface.new_socket(name="Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    occlusion = nodes.new("ShaderNodeGroup")
    occlusion.node_tree = group
    links.new(separate.outputs["Red"], occlusion.inputs["Occlusion"])
    return mat


def run(args, out, report):
    source = Path(args.input).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    col = bpy.data.collections.get(args.collection)
    if col is None:
        raise ValueError("Missing asset collection: "+args.collection)
    report.update(input=str(source), input_sha256=digest, blender_version=bpy.app.version_string,
                  resolution=args.resolution, samples=args.samples, margin_px=args.margin, uv_angle_limit=args.uv_angle_limit,
                  source_qa=inspect(col.all_objects, require_closed=args.require_closed))
    save_json(out/"source-qa.json", report["source_qa"])
    if not report["source_qa"]["passed"]:
        raise ValueError("Source mesh/UV QA failed; repair source explicitly before baking")
    obj, web = prepare_web(col, args.resolution, args.margin, args.uv_angle_limit)
    report["atlas_preparation"] = finish_atlas(obj, args.resolution, args.margin)
    qa = inspect([obj], uv_name="BakeUV", resolution=args.resolution, bake=True,
                 require_closed=args.require_closed, min_gap_px=2*args.margin,
                 min_texels_per_cm=args.min_texels_per_cm)
    report["bake_qa"] = qa
    save_json(out/"bake-qa.json", qa)
    if not qa["passed"]:
        raise ValueError("Bake atlas/mesh QA failed; inspect bake-qa.json. Increase resolution or reduce margin when atlas packing cannot fit; never waive overlap/padding errors")
    report["tangent_preparation"] = prepare_tangents(obj)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    scene.render.bake.use_selected_to_active = False
    scene.render.bake.use_clear = True
    images = {}
    for name, kind in (("BaseColor", "DIFFUSE"), ("Normal", "NORMAL"), ("Roughness", "ROUGHNESS"),
                       ("Metallic", "EMIT"), ("AO", "AO")):
        start = time.monotonic()
        images[name] = bake_map(obj, name, kind, args.resolution, args.margin, out)
        report.setdefault("bakes", []).append({"map": name, "type": kind, "seconds": time.monotonic()-start})
        save_json(out/"web-pbr-report.json", report)
    images["ORM"] = pack_orm(images, args.resolution, out)
    obj.data.materials.clear()
    obj.data.materials.append(web_material(images))
    for p in obj.data.polygons:
        p.material_index = 0
    # Release mesh carries only its atlas; source UV remains in original BLEND.
    obj.data.uv_layers.remove(obj.data.uv_layers["SourceUV"])
    obj.data.uv_layers.active = obj.data.uv_layers["BakeUV"]
    obj.data.uv_layers.active.active_render = True
    select_only(obj)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"krathong-web.blend"), check_existing=False)
    bpy.ops.export_scene.gltf(filepath=str(out/"krathong-web.glb"), export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_texcoords=True, export_normals=True,
                              export_tangents=True, export_cameras=False, export_lights=False)
    from check_reference_model import check
    roundtrip = check(out/"krathong-web.glb", web_pbr=True)
    save_json(out/"roundtrip.json", roundtrip)
    if not roundtrip["passed"]:
        raise ValueError("Strict web PBR GLB roundtrip failed: "+str(roundtrip["errors"]))
    report["roundtrip"] = {"passed": True, "report": "roundtrip.json"}
    if args.render:
        from reference_finish import setup_scene, render_views
        render_col = bpy.data.collections.new("Web_Preview")
        scene = bpy.context.scene
        scene.collection.children.link(render_col)
        for obj in list(scene.objects):
            if obj.type == "MESH":
                render_col.objects.link(obj)
        setup_scene(render_col, resolution=512, samples=16)
        report["renders"] = render_views(str(out), render_col)
    if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise RuntimeError("Source BLEND changed unexpectedly")
    report.update(passed=True, input_unchanged=True, visual_status="unreviewed",
                  files={p.name: {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                         for p in out.iterdir() if p.suffix in {".png", ".glb", ".blend"}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--collection", default="Krathong_Asset")
    parser.add_argument("--resolution", type=int, default=1024)
    parser.add_argument("--samples", type=int, default=32)
    parser.add_argument("--margin", type=int, default=8)
    parser.add_argument("--uv-angle-limit", type=float, default=66, help="Smart UV projection angle in degrees; lower to split curved/folded islands")
    parser.add_argument("--min-texels-per-cm", type=float, default=2, help="Minimum p05 density; increase for close-up art, never waive a visibly under-resolved atlas")
    parser.add_argument("--require-closed", action="store_true")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    source, out = Path(args.input).resolve(), Path(args.out_dir).resolve()
    if not bpy.app.background:
        raise RuntimeError("Use isolated background Blender; live scene is protected")
    if bpy.app.version < (4, 2, 0):
        parser.error("Web baker requires Blender >=4.2; verified runtime is documented separately")
    if source.suffix.lower() != ".blend" or not source.is_file():
        parser.error("--input must be an existing .blend")
    if source.is_relative_to(out) or (out.exists() and any(out.iterdir())):
        parser.error("Output must be a new/empty directory outside the source location")
    if args.resolution not in {128,256,512,1024,2048,4096} or args.samples < 1 or not 1 <= args.margin < args.resolution//8:
        parser.error("Use power-of-two resolution 128–4096, positive samples and margin 1..resolution/8-1")
    if not 5 <= args.uv_angle_limit <= 89:
        parser.error("uv-angle-limit must be 5–89 degrees")
    if not math.isfinite(args.min_texels_per_cm) or args.min_texels_per_cm <= 0:
        parser.error("min-texels-per-cm must be finite and positive")
    out.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "passed": False, "errors": [], "visual_status": "unreviewed",
              "scope": "same-mesh bake with separate atlas; not high-to-low retopology",
              "limitations": ["SSS/transmission/coats/emission are not baked into core metallic-roughness maps",
                              "No automatic self-intersection removal or topology repair",
                              "128/256 smoke-test atlases do not establish production texture quality",
                              "No target-device browser performance or mip-bleed certification"]}
    try:
        run(args, out, report)
    except Exception as error:
        report["errors"].append(type(error).__name__+": "+str(error))
        raise
    finally:
        save_json(out/"web-pbr-report.json", report)


if __name__ == "__main__":
    main()
