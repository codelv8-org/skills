"""Blender mesh/UV diagnostics. Read-only; explicit bake UV policy, no silent repair."""
import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import bmesh
import bpy


def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def intersection_area(a, b):
    """Exact convex triangle clipping; touching edges have zero area."""
    polygon = list(a)
    sign = 1 if cross(*b) >= 0 else -1
    for q, r in zip(b, b[1:]+b[:1]):
        source, polygon = polygon, []
        if not source:
            break
        for s, t in zip(source, source[1:]+source[:1]):
            ds, dt = sign*cross(q, r, s), sign*cross(q, r, t)
            if ds >= 0:
                polygon.append(s)
            if (ds >= 0) != (dt >= 0):
                f = ds/(ds-dt)
                polygon.append((s[0]+f*(t[0]-s[0]), s[1]+f*(t[1]-s[1])))
    return abs(sum(p[0]*q[1]-q[0]*p[1] for p, q in zip(polygon, polygon[1:]+polygon[:1])))*.5


def point_segment_distance(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    t = max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/max(dx*dx+dy*dy, 1e-30)))
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)


def overlap_pairs(triangles, islands=None, min_gap=0):
    bins = defaultdict(list)
    grid = min(512, max(16, int(math.sqrt(len(triangles))*2)))
    overlaps, total, padding_pairs, overlap_ids = [], 0.0, [], set()
    for i, tri in enumerate(triangles):
        if tri is None:
            continue
        lo = [min(p[k] for p in tri)-min_gap for k in (0, 1)]
        hi = [max(p[k] for p in tri)+min_gap for k in (0, 1)]
        # Out-of-range UV is diagnosed separately; clamp grid keys to bound memory.
        cells = [(x, y) for x in range(max(0, min(grid-1, int(lo[0]*grid))), max(0, min(grid-1, int(hi[0]*grid)))+1)
                 for y in range(max(0, min(grid-1, int(lo[1]*grid))), max(0, min(grid-1, int(hi[1]*grid)))+1)]
        seen = set()
        for cell in cells:
            for j in bins[cell]:
                if j in seen:
                    continue
                seen.add(j)
                other = triangles[j]
                if any(max(p[k] for p in tri)+min_gap < min(p[k] for p in other) or
                       max(p[k] for p in other)+min_gap < min(p[k] for p in tri) for k in (0, 1)):
                    continue
                area = intersection_area(triangles[j], tri)
                if area > 1e-10:
                    total += area
                    overlap_ids.update((j, i))
                    if len(overlaps) < 20:
                        overlaps.append([j, i, area])
                if min_gap and islands[j] != islands[i]:
                    other = triangles[j]
                    distance = min(point_segment_distance(p, a, b) for pts, edges in ((tri, other), (other, tri))
                                   for p in pts for a, b in zip(edges, edges[1:]+edges[:1]))
                    if distance < min_gap-1e-6 and len(padding_pairs) < 20:
                        padding_pairs.append([j, i, distance])
            bins[cell].append(i)
    return {"overlap_examples": overlaps, "overlap_area_pair_sum": total,
            "overlap_triangle_ids": sorted(overlap_ids),
            "overlap_detected": bool(overlaps), "padding_violation_examples": padding_pairs,
            "padding_violations_detected": bool(padding_pairs), "required_island_gap_uv": min_gap,
            "method": "triangle clipping and cross-island edge distance with spatial bins; area tolerance 1e-10 UV units"}


def uv_islands(mesh, layer):
    """Triangle components connected by a shared mesh edge with matching UVs."""
    parent = list(range(len(mesh.loop_triangles)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    edges = {}
    for i, tri in enumerate(mesh.loop_triangles):
        corners = [(tuple(round(float(v), 7) for v in mesh.vertices[vi].co),
                    tuple(round(float(v), 7) for v in layer.data[li].uv)) for vi, li in zip(tri.vertices, tri.loops)]
        for a, b in zip(corners, corners[1:]+corners[:1]):
            edge = tuple(sorted((a, b)))
            if edge in edges:
                parent[find(i)] = find(edges[edge])
            else:
                edges[edge] = i
    return [find(i) for i in range(len(parent))]


def percentile(values, fraction):
    return sorted(values)[min(len(values)-1, int((len(values)-1)*fraction))] if values else None


def inspect_object(obj, uv_name=None, resolution=1024, bake=False, require_closed=False,
                   max_stretch=20.0, max_density_ratio=8.0, min_gap_px=0, min_texels_per_cm=0):
    mesh = obj.data
    mesh.calc_loop_triangles()
    errors, warnings = [], []
    bm = bmesh.new()
    bm.from_mesh(mesh)
    topology = {"vertices": len(bm.verts), "edges": len(bm.edges), "polygons": len(bm.faces),
                "triangles": len(mesh.loop_triangles), "loose_vertices": sum(not v.link_faces for v in bm.verts),
                "wire_edges": sum(not e.link_faces for e in bm.edges),
                "boundary_edges": sum(e.is_boundary for e in bm.edges),
                "nonmanifold_edges": sum(len(e.link_faces) > 2 for e in bm.edges),
                "inconsistent_winding_edges": sum(e.is_manifold and not e.is_contiguous for e in bm.edges)}
    unseen, inward = set(bm.faces), 0
    while unseen:
        todo, component = [unseen.pop()], []
        while todo:
            face = todo.pop()
            component.append(face)
            for edge in face.edges:
                for neighbor in edge.link_faces:
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        todo.append(neighbor)
        if all(len(e.link_faces) == 2 for f in component for e in f.edges):
            volume = 0.0
            for face in component:
                pts = [v.co for v in face.verts]
                volume += sum(pts[0].dot(pts[i].cross(pts[i+1]))/6 for i in range(1, len(pts)-1))
            inward += volume < -1e-18
    topology["inward_closed_components"] = inward
    bm.free()
    topology["nonfinite_vertices"] = sum(not all(math.isfinite(c) for c in obj.matrix_world @ v.co) for v in mesh.vertices)
    keys = [tuple(sorted(p.vertices)) for p in mesh.polygons]
    topology["duplicate_faces"] = len(keys)-len(set(keys))
    if not mesh.polygons:
        errors.append("empty_mesh")
    for key in ("nonfinite_vertices", "loose_vertices", "wire_edges", "nonmanifold_edges", "inconsistent_winding_edges", "inward_closed_components", "duplicate_faces"):
        if topology[key]:
            errors.append(key)
    if topology["boundary_edges"]:
        (errors if require_closed else warnings).append("boundary_edges: open craft parts allowed only under open-surface policy")
    if obj.matrix_world.to_3x3().determinant() <= 0:
        errors.append("negative_or_singular_transform: apply and verify normals on a working copy")
    if obj.modifiers:
        errors.append("unevaluated_modifiers: evaluate on a copy before release QA")
    layer = mesh.uv_layers.get(uv_name) if uv_name else mesh.uv_layers.active
    uv_report = {"layer": layer.name if layer else None, "degenerate_triangles": 0,
                 "nonfinite_loops": 0, "out_of_tile_loops": 0, "mirrored_triangles": 0}
    if not layer:
        errors.append("missing_uv")
    else:
        for loop in layer.data:
            values = tuple(loop.uv)
            if not all(math.isfinite(v) for v in values):
                uv_report["nonfinite_loops"] += 1
            elif any(v < -1e-6 or v > 1+1e-6 for v in values):
                uv_report["out_of_tile_loops"] += 1
    areas, densities, stretches, triangles = [], [], [], []
    topology["degenerate_triangles"] = 0
    for tri in mesh.loop_triangles:
        a, b, c = [obj.matrix_world @ mesh.vertices[v].co for v in tri.vertices]
        e, f = b-a, c-a
        area = e.cross(f).length*.5
        if not math.isfinite(area) or area <= 1e-14:
            topology["degenerate_triangles"] += 1
        if not layer:
            continue
        points = [tuple(layer.data[l].uv) for l in tri.loops]
        finite = all(math.isfinite(v) for p in points for v in p)
        signed = cross(*points)*.5 if finite else 0
        ua = abs(signed)
        triangles.append(points if finite and ua > 1e-12 else None)
        if not finite or ua <= 1e-12:
            uv_report["degenerate_triangles"] += 1
        if signed < 0:
            uv_report["mirrored_triangles"] += 1
        if not math.isfinite(area) or area <= 1e-14 or ua <= 1e-12 or not finite:
            continue
        areas.append(ua)
        densities.append(math.sqrt(ua/area)*resolution/100)  # pixels per centimetre
        # Singular-value ratio of triangle's 3D-to-UV Jacobian: 1 is isotropic.
        x, y = e.length, f.dot(e.normalized())
        z = max(0, f.length_squared-y*y)**.5
        if z <= 1e-12:
            continue
        du, dv = points[1][0]-points[0][0], points[1][1]-points[0][1]
        fu, fv = points[2][0]-points[0][0], points[2][1]-points[0][1]
        j0, j1, j2, j3 = du/x, (fu-du*y/x)/z, dv/x, (fv-dv*y/x)/z
        trace = j0*j0+j1*j1+j2*j2+j3*j3
        det = (j0*j3-j1*j2)**2
        disc = math.sqrt(max(0, trace*trace-4*det))
        largest, smallest = (trace+disc)*.5, (trace-disc)*.5
        stretches.append(math.sqrt(largest/max(smallest, 1e-30)))
    if topology["degenerate_triangles"]:
        errors.append("degenerate_mesh_triangles")
    if layer:
        for key in ("nonfinite_loops", "degenerate_triangles"):
            if uv_report[key]:
                errors.append("uv_"+key)
        if uv_report["out_of_tile_loops"]:
            (errors if bake else warnings).append("uv_outside_0_1")
        uv_report.update({"resolution": resolution, "summed_triangle_area": sum(areas),
                          "tile_border_min_px": min((min(float(v), 1-float(v))*resolution
                                                     for l in layer.data for v in l.uv if math.isfinite(v)), default=None),
                          "texels_per_cm_p05": percentile(densities, .05), "texels_per_cm_p95": percentile(densities, .95),
                          "stretch_p95": percentile(stretches, .95), "stretch_max": max(stretches, default=None)})
        uv_report["subpixel_triangles"] = sum(area*resolution*resolution < 1 for area in areas)
        low, high = percentile(densities, .05), percentile(densities, .95)
        ratio = high/low if low else None
        uv_report["density_p95_p05_ratio"] = ratio
        if bake and min_texels_per_cm and (low is None or low < min_texels_per_cm):
            errors.append("uv_absolute_texel_density_limit")
        if bake and not any(uv_report[k] for k in ("nonfinite_loops", "degenerate_triangles", "out_of_tile_loops")):
            islands = uv_islands(mesh, layer)
            uv_report["islands"] = len(set(islands))
            uv_report.update(overlap_pairs(triangles, islands, min_gap_px/resolution))
            if uv_report["overlap_detected"]:
                errors.append("uv_overlap")
            if uv_report["padding_violations_detected"]:
                errors.append("uv_island_padding")
            if max(stretches, default=0) > max_stretch:
                errors.append("uv_stretch_limit")
            if ratio and ratio > max_density_ratio:
                errors.append("uv_density_ratio_limit")
        elif bake:
            uv_report["overlap_check"] = "not_run: invalid/degenerate/out-of-tile UV must be repaired first"
        else:
            uv_report["overlap_check"] = "not_run: source UV may deliberately tile/reuse; bake atlas must use bake policy"
    return {"object": obj.name, "passed": not errors, "errors": errors, "warnings": warnings,
            "mesh": topology, "uv": uv_report}


def inspect(objects, **options):
    results = [inspect_object(o, **options) for o in objects if o.type == "MESH"]
    return {"schema_version": 1, "passed": bool(results) and all(r["passed"] for r in results),
            "blender_version": bpy.app.version_string, "policy": options, "objects": results,
            "not_checked": ["self-intersections between surfaces/objects", "reference likeness", "physical buoyancy",
                            "mip bleed at all LODs/view distances; inspect baked gutters and target-device appearance"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="BLEND or GLB; run in isolated background Blender")
    parser.add_argument("--out", required=True)
    parser.add_argument("--collection", default="Krathong_Asset")
    parser.add_argument("--uv-layer")
    parser.add_argument("--bake-uv", action="store_true")
    parser.add_argument("--require-closed", action="store_true")
    parser.add_argument("--resolution", type=int, default=1024)
    parser.add_argument("--min-gap-px", type=float, default=0, help="Bake island gap at --resolution; zero checks overlap only")
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    if not bpy.app.background:
        raise RuntimeError("Use background Blender to protect the live scene")
    path = Path(args.input).resolve()
    if path.suffix.lower() == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(path))
        col = bpy.data.collections.get(args.collection)
        if not col:
            raise ValueError("Missing asset collection: "+args.collection)
        objects = list(col.all_objects)
    elif path.suffix.lower() == ".glb":
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(path))
        objects = list(bpy.context.scene.objects)
    else:
        raise ValueError("Only .blend and .glb inputs supported")
    if args.resolution < 1 or args.min_gap_px < 0:
        parser.error("resolution must be positive and min-gap-px nonnegative")
    report = inspect(objects, uv_name=args.uv_layer, resolution=args.resolution, bake=args.bake_uv,
                     require_closed=args.require_closed, min_gap_px=args.min_gap_px)
    out = Path(args.out).resolve()
    if out == path:
        raise ValueError("Report must not overwrite input")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("MESH_UV_QA", report["passed"], str(out))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
