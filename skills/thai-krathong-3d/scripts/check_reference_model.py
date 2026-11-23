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


def check(path):
    path = Path(path).expanduser().resolve()
    report = {"input": str(path), "blender_version": bpy.app.version_string,
              "scope": "GLB import round-trip structural checks", "visual_similarity": "not_assessed",
              "coordinate_system": "meters; Blender Z-up after glTF import", "limitations": LIMITATIONS,
              "errors": [], "warnings": [], "passed": False}
    try:
        doc, byte_count, bin_size = _read_glb(path)
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
        report["passed"] = not report["errors"]
    except Exception as error:
        report["errors"].append(type(error).__name__ + ": " + str(error))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", nargs="?", help="GLB path (or use --input)")
    parser.add_argument("--input", dest="input_path")
    parser.add_argument("--out", help="JSON report path; default INPUT.roundtrip.json")
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(arguments)
    source = args.input_path or args.model
    if not source:
        parser.error("provide a GLB path or --input")
    report = check(source)
    out = Path(args.out).expanduser().resolve() if args.out else Path(source).expanduser().resolve().with_suffix(".roundtrip.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "report": str(out),
                      "errors": report["errors"], "warnings": report["warnings"]}, ensure_ascii=False))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
