"""Import a GLB in a fresh Blender scene and report structural round-trip QA.

Run:
  blender -b --factory-startup --python-exit-code 1 \
    --python scripts/check_reference_model.py -- \
    --input output/krathong.glb --out output/roundtrip.json

This checks importability, finite geometry, materials and texture availability.
It does not certify visual similarity, watertightness, flotation or web speed.
Warnings (scale, degenerate faces, missing UV) do not cause a failure status.
Exit 1 is reserved for corrupt/unreadable input or missing required mesh/image
data; usage errors exit 2. Use --python-exit-code 1 for Blender script errors.
"""

import argparse
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy
from mathutils import Vector


LIMITATIONS = [
    "Structural import round-trip only; this is not a visual similarity score.",
    "Does not prove watertightness, self-intersection freedom or physical flotation.",
    "Does not benchmark Three.js frame rate or GPU memory use.",
    "Blender-only procedural bump/subsurface may differ from GLB materials.",
    "Import may split vertices at UV/normal seams; source vertex counts need not match.",
]


def _read_glb(path):
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError("GLB is shorter than its header and JSON chunk")
    magic, version, length = struct.unpack_from("<4sII", data)
    if magic != b"glTF" or version != 2:
        raise ValueError("Expected glTF 2.0 binary GLB")
    if length != len(data):
        raise ValueError("GLB header byte length does not match file size")
    offset, doc, bin_size = 12, None, 0
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError("Truncated GLB chunk header")
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        if chunk_length % 4 or offset + chunk_length > len(data):
            raise ValueError("Invalid GLB chunk length")
        content = data[offset:offset + chunk_length]
        if chunk_type == 0x4E4F534A:
            if doc is not None:
                raise ValueError("GLB contains more than one JSON chunk")
            doc = json.loads(content.decode("utf-8").rstrip("\x00 \t\r\n"))
        elif chunk_type == 0x004E4942:
            bin_size += chunk_length
        offset += chunk_length
    if doc is None:
        raise ValueError("GLB has no JSON chunk")
    return doc, len(data), bin_size


def _source_stats(doc, byte_count, bin_size):
    meshes, materials, images = doc.get("meshes", []), doc.get("materials", []), doc.get("images", [])
    return {"file_bytes": byte_count, "binary_chunk_bytes": bin_size,
            "mesh_definitions": len(meshes),
            "mesh_primitives": sum(len(m.get("primitives", [])) for m in meshes),
            "mesh_nodes": sum("mesh" in node for node in doc.get("nodes", [])),
            "material_definitions": len(materials), "image_definitions": len(images),
            "embedded_images": sum("bufferView" in img or img.get("uri", "").startswith("data:") for img in images),
            "base_color_textured_materials": sum("baseColorTexture" in mat.get("pbrMetallicRoughness", {}) for mat in materials),
            "camera_definitions": len(doc.get("cameras", [])),
            "light_definitions": len(doc.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])),
            "named_stage_objects": [node.get("name") for node in doc.get("nodes", [])
                                    if str(node.get("name", "")).startswith("STAGE_")],
            "extensions_used": doc.get("extensionsUsed", [])}


def web_pbr_errors(doc):
    """Enforce a portable, embedded core PBR contract; no scalar-only fallback."""
    errors = []
    materials = doc.get("materials", [])
    if not materials:
        errors.append("Web PBR requires materials")
    if doc.get("cameras") or doc.get("extensions", {}).get("KHR_lights_punctual"):
        errors.append("Web asset must not contain render-stage cameras/lights")
    for i, mat in enumerate(materials):
        pbr = mat.get("pbrMetallicRoughness", {})
        maps = {"BaseColor": pbr.get("baseColorTexture"), "Normal": mat.get("normalTexture"),
                "ORM": pbr.get("metallicRoughnessTexture"), "AO": mat.get("occlusionTexture")}
        for name, info in maps.items():
            if not isinstance(info, dict) or "index" not in info:
                errors.append(f"Material {i} missing required {name} texture")
                continue
            textures = doc.get("textures", [])
            ti = info["index"]
            if not isinstance(ti, int) or not 0 <= ti < len(textures):
                errors.append(f"Material {i} invalid {name} texture index")
                continue
            image_index = textures[ti].get("source", -1)
            images = doc.get("images", [])
            if not isinstance(image_index, int) or not 0 <= image_index < len(images):
                errors.append(f"Material {i} invalid {name} image index")
            elif "bufferView" not in images[image_index] or images[image_index].get("mimeType") != "image/png":
                errors.append(f"Material {i} requires embedded PNG for {name}")
        if maps["ORM"] and maps["AO"] and maps["ORM"].get("index") != maps["AO"].get("index"):
            errors.append(f"Material {i} AO/roughness/metallic must share packed ORM texture")
        if mat.get("alphaMode", "OPAQUE") != "OPAQUE":
            errors.append(f"Material {i} alpha requires a separately validated workflow")
    for mesh in doc.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            attributes = primitive.get("attributes", {})
            for name in ("POSITION", "NORMAL", "TANGENT", "TEXCOORD_0"):
                if name not in attributes:
                    errors.append("Web primitive missing "+name)
            if primitive.get("mode", 4) != 4:
                errors.append("Web primitive must be triangulated")
            mi = primitive.get("material", -1)
            if not 0 <= mi < len(materials):
                errors.append("Web primitive missing valid material")
                continue
            mat = materials[mi]
            pbr = mat.get("pbrMetallicRoughness", {})
            for info in (pbr.get("baseColorTexture"), pbr.get("metallicRoughnessTexture"), mat.get("normalTexture"), mat.get("occlusionTexture")):
                if info and "TEXCOORD_"+str(info.get("texCoord", 0)) not in attributes:
                    errors.append("Texture references absent UV set")
    return errors


def web_vector_errors(path, doc):
    """Inspect actual exported float data, not just presence of attribute names."""
    data = path.read_bytes()
    offset, binary = 12, b""
    while offset < len(data):
        length, kind = struct.unpack_from('<II', data, offset)
        offset += 8
        if kind == 0x004E4942:
            binary = data[offset:offset+length]
        offset += length
    errors, cache = [], {}
    def values(index, size):
        if index not in cache:
            a = doc['accessors'][index]
            if a.get('componentType') != 5126 or a.get('type') != 'VEC'+str(size) or 'sparse' in a:
                raise ValueError('Web vector audit requires dense uncompressed float attributes')
            v = doc['bufferViews'][a['bufferView']]
            start = v.get('byteOffset', 0)+a.get('byteOffset', 0)
            stride = v.get('byteStride', size*4)
            cache[index] = [struct.unpack_from('<'+'f'*size, binary, start+i*stride) for i in range(a['count'])]
        return cache[index]
    for mesh in doc.get('meshes', []):
        for primitive in mesh.get('primitives', []):
            attrs = primitive.get('attributes', {})
            for name, size in (('POSITION', 3), ('NORMAL', 3), ('TANGENT', 4), ('TEXCOORD_0', 2)):
                if name not in attrs:
                    continue  # missing attributes already diagnosed by web_pbr_errors
                vectors = values(attrs[name], size)
                if any(not all(math.isfinite(x) for x in v) for v in vectors):
                    errors.append('Nonfinite exported '+name)
                if name in {'NORMAL', 'TANGENT'}:
                    bad = [i for i, v in enumerate(vectors) if abs(sum(x*x for x in v[:3])-1) > 2e-3]
                    if bad:
                        errors.append('Non-unit exported '+name+' at vertices '+str(bad[:10]))
                if name == 'TANGENT' and any(abs(abs(v[3])-1) > 1e-5 for v in vectors):
                    errors.append('Invalid tangent handedness')
    return errors


def check(path, web_pbr=False):
    path = Path(path).expanduser().resolve()
    report = {"input": str(path), "blender_version": bpy.app.version_string,
              "scope": "GLB import round-trip structural checks", "visual_similarity": "not_assessed",
              "coordinate_system": "meters; Blender Z-up after glTF import", "limitations": LIMITATIONS,
              "errors": [], "warnings": [], "passed": False}
    try:
        doc, byte_count, bin_size = _read_glb(path)
        if web_pbr:
            report["errors"].extend(web_pbr_errors(doc))
            report["errors"].extend(web_vector_errors(path, doc))
            report["web_pbr_policy"] = "embedded PNG BaseColor + tangent Normal + packed ORM; strict mesh/UV QA"
        report["source_glb"] = _source_stats(doc, byte_count, bin_size)
        if report["source_glb"]["camera_definitions"] or report["source_glb"]["light_definitions"]:
            report["warnings"].append("GLB contains cameras/lights; verify the render stage was excluded")
        if report["source_glb"]["named_stage_objects"]:
            report["warnings"].append("GLB contains objects named STAGE_; verify render scenery was excluded")
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(path))
        bpy.context.view_layer.update()
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        if not meshes:
            report["errors"].append("No mesh objects imported")
        materials, images, positions = {}, {}, []
        counts = {"mesh_objects": len(meshes), "unique_meshes": len({o.data.as_pointer() for o in meshes}),
                  "vertices": 0, "triangles": 0, "nonfinite_vertices": 0,
                  "degenerate_triangles": 0, "objects_missing_uv": 0, "empty_mesh_objects": 0}
        object_reports = []
        for obj in meshes:
            mesh = obj.data
            mesh.calc_loop_triangles()
            world = [obj.matrix_world @ v.co for v in mesh.vertices]
            invalid = sum(not all(math.isfinite(x) for x in p) for p in world)
            degenerate = 0
            if not invalid:
                positions.extend(world)
                for tri in mesh.loop_triangles:
                    a, b, c = (world[i] for i in tri.vertices)
                    if (b - a).cross(c - a).length_squared < 1e-24:
                        degenerate += 1
            counts["vertices"] += len(mesh.vertices)
            counts["triangles"] += len(mesh.loop_triangles)
            counts["nonfinite_vertices"] += invalid
            counts["degenerate_triangles"] += degenerate
            counts["empty_mesh_objects"] += int(not mesh.vertices or not mesh.polygons)
            counts["objects_missing_uv"] += int(not mesh.uv_layers)
            object_reports.append({"name": obj.name, "vertices": len(mesh.vertices),
                                   "triangles": len(mesh.loop_triangles), "material_slots": len(obj.material_slots),
                                   "uv_layers": len(mesh.uv_layers)})
            for slot in obj.material_slots:
                if slot.material:
                    materials[slot.material.name] = slot.material
        for mat in materials.values():
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == "TEX_IMAGE" and node.image:
                        images[node.image.name] = node.image
        missing_images = [name for name, img in images.items()
                          if img.size[0] <= 0 or img.size[1] <= 0 or not img.has_data]
        counts.update({"used_materials": len(materials), "referenced_images": len(images),
                       "missing_images": len(missing_images)})
        report["imported"] = counts
        report["objects"] = object_reports
        report["materials"] = sorted(materials)
        report["images"] = [{"name": img.name, "width": img.size[0], "height": img.size[1],
                              "loaded": bool(img.has_data)} for img in images.values()]
        if positions:
            lo = Vector(tuple(min(p[i] for p in positions) for i in range(3)))
            hi = Vector(tuple(max(p[i] for p in positions) for i in range(3)))
            dims = hi - lo
            report["bounds"] = {"min": list(lo), "max": list(hi), "dimensions_m": list(dims),
                                "horizontal_diameter_m": max(dims.x, dims.y)}
            if not 0.05 <= max(dims.x, dims.y) <= 1.0:
                report["warnings"].append("Horizontal diameter is outside 0.05–1.0 m; confirm intended units/scale")
        if counts["nonfinite_vertices"]:
            report["errors"].append("Imported mesh contains nonfinite vertex positions")
        if meshes and counts["triangles"] == 0:
            report["errors"].append("Imported mesh objects contain no surface triangles")
        if counts["triangles"] and counts["degenerate_triangles"] == counts["triangles"]:
            report["errors"].append("All imported triangles have zero area")
        if missing_images:
            report["errors"].append("Missing or unreadable referenced images: " + ", ".join(missing_images))
        if counts["empty_mesh_objects"]:
            report["warnings"].append("Some imported mesh objects are empty")
        if counts["degenerate_triangles"]:
            report["warnings"].append("Degenerate triangles found; inspect before further optimization")
        if counts["objects_missing_uv"]:
            report["warnings"].append("Some objects have no UV map; verify textured surfaces")
        if report["source_glb"]["base_color_textured_materials"] and not images:
            report["errors"].append("Source declares base-color textures but no images imported")
        if report["source_glb"]["embedded_images"] != report["source_glb"]["image_definitions"]:
            report["warnings"].append("GLB references external images and is not fully self-contained")
        if web_pbr:
            from mesh_uv_qa import inspect
            report["mesh_uv_qa"] = inspect(meshes, bake=True)
            if not report["mesh_uv_qa"]["passed"]:
                report["errors"].append("Strict imported mesh/UV QA failed")
        report["passed"] = not report["errors"]
    except Exception as error:
        report["errors"].append(type(error).__name__ + ": " + str(error))
    return report


def main():
    if not bpy.app.background:
        raise RuntimeError("Use isolated background Blender to protect the live scene")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", nargs="?", help="GLB path (or use --input)")
    parser.add_argument("--input", dest="input_path")
    parser.add_argument("--out", help="JSON report path; default INPUT.roundtrip.json")
    parser.add_argument("--web-pbr", action="store_true", help="Require embedded full PBR maps and strict mesh/UV QA")
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(arguments)
    source = args.input_path or args.model
    if not source:
        parser.error("provide a GLB path or --input")
    report = check(source, web_pbr=args.web_pbr)
    out = Path(args.out).expanduser().resolve() if args.out else Path(source).expanduser().resolve().with_suffix(".roundtrip.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "report": str(out),
                      "errors": report["errors"], "warnings": report["warnings"]}, ensure_ascii=False))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
