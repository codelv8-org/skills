#!/usr/bin/env python3
"""Procedural, editable-by-part Thai krathong .glb generator.

Requirements: pip install numpy trimesh
Output glTF uses +Y up for Three.js, meters, centered on ground.
This is a stylized geometric baseline, not an image-to-3D reconstruction engine.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

PALETTE = {
    "pith": "#C7DAB4", "leaf_band": "#286C3C", "leaf_dark": "#1E5734",
    "leaf_mid": "#317C47", "leaf_light": "#4B9855", "leaf_vein": "#84AE63",
    "marigold_core": "#E9A51F", "marigold_deep": "#E9780C",
    "marigold_gold": "#F2B820", "marigold_light": "#FFCE36",
    "purple": "#9B248E", "purple_light": "#C447AA", "purple_dark": "#711B69",
    "lotus_pale": "#F6B5CD", "lotus_pink": "#DE5899", "lotus_rose": "#B93B7B",
    "lotus_yellow": "#F7D859", "wax": "#F9E5AD", "wick": "#32251D",
    "incense": "#98622F", "incense_tip": "#463935",
    "flame_outer": "#FF9C16", "flame_inner": "#FFE78A",
}
DEFAULTS = {
    "name": "Thai Traditional Krathong", "diameter_m": 0.26,
    "flower_style": "marigold", "flower_count": 8, "amaranth_count": 8,
    "outer_leaf_count": 20, "inner_leaf_count": 16,
    "candle": True, "candle_lit": False, "incense_count": 3,
    "quality": "medium", "seed": 2026,
}
QUALITY = {
    "low": {"circle": 24, "leaf_steps": 6, "flower_florets": 38},
    "medium": {"circle": 40, "leaf_steps": 9, "flower_florets": 82},
    "high": {"circle": 64, "leaf_steps": 13, "flower_florets": 150},
}
STAGES = ["base", "leaves", "flowers", "ceremonial", "complete"]


def rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def material(name):
    kwargs = dict(name=name, baseColorFactor=rgb(PALETTE[name]) + [255],
                  metallicFactor=0.0, roughnessFactor=0.85,
                  doubleSided=True)
    if name.startswith("flame"):
        kwargs["roughnessFactor"] = 0.45
        kwargs["emissiveFactor"] = [x / 255 * 0.7 for x in rgb(PALETTE[name])]
    return PBRMaterial(**kwargs)


def norm(v):
    v = np.asarray(v, dtype=float)
    return v / max(float(np.linalg.norm(v)), 1e-9)


def cylinder(radius, height, center, sections):
    m = trimesh.creation.cylinder(radius=float(radius), height=float(height), sections=int(sections))
    m.apply_translation(center)
    return m


def ball(radius, center, detail=1):
    m = trimesh.creation.icosphere(subdivisions=detail, radius=float(radius))
    m.apply_translation(center)
    return m


def line_tube(start, end, radius, sections=6):
    return trimesh.creation.cylinder(radius=float(radius), segment=np.asarray([start, end]), sections=sections)


def flat_band(r_in, r_out, z_min, z_max, segments):
    """Closed thin annular leaf sleeve, outer radial band."""
    vertices = []
    for radius in [r_in, r_out]:
        for z in [z_min, z_max]:
            for i in range(segments):
                a = 2 * math.pi * i / segments
                vertices.append((radius * math.cos(a), radius * math.sin(a), z))
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        # Surface all four edges of the annular sleeve.
        for l1, l2 in [(0, 1), (1, 3), (3, 2), (2, 0)]:
            aa = l1 * segments + i
            bb = l2 * segments + i
            cc = l2 * segments + j
            dd = l1 * segments + j
            faces.extend([[aa, bb, cc], [aa, cc, dd]])
    return trimesh.Trimesh(vertices=vertices, faces=faces, process=False)


def folded_leaf(theta, r0, z0, width, height, tilt, steps, crease=0.010):
    """Closed folded leaf: thin shell with a longitudinal central ridge."""
    verts = []
    across = 6
    for side in [0, 1]:
        for j in range(steps + 1):
            v = j / steps
            half_width = width * 0.5 * (0.10 + 0.90 * math.sin(math.pi * v) ** 0.68)
            if j == steps:
                half_width = width * 0.012
            for k in range(across + 1):
                u = -1 + 2 * k / across
                rr = (r0 + tilt * v + 0.003 * math.sin(math.pi * v)
                      + crease * (1 - abs(u)) * math.sin(math.pi * (0.20 + 0.80 * v))
                      + (-0.0011 if side else 0.0011))
                xy = np.array([math.cos(theta), math.sin(theta)]) * rr
                xy += np.array([-math.sin(theta), math.cos(theta)]) * (half_width * u)
                zz = z0 + height * v + 0.0020 * (1 - u * u) * math.sin(math.pi * v)
                verts.append([float(xy[0]), float(xy[1]), zz])
    n = (steps + 1) * (across + 1)
    faces = []
    for side in [0, 1]:
        off = side * n
        for j in range(steps):
            for k in range(across):
                a = off + j * (across + 1) + k
                b, c, d = a + 1, a + (across + 1), a + (across + 2)
                faces.extend(([a, c, d], [a, d, b]) if side == 0 else ([a, d, c], [a, b, d]))
    # close the shell along the four perimeter edges
    for j in range(steps):
        for k in [0, across]:
            a, b = j * (across + 1) + k, (j + 1) * (across + 1) + k
            faces.extend([[a, b, b + n], [a, b + n, a + n]])
    for j in [0, steps]:
        for k in range(across):
            a, b = j * (across + 1) + k, j * (across + 1) + k + 1
            faces.extend([[a, b, b + n], [a, b + n, a + n]])
    return trimesh.Trimesh(vertices=verts, faces=faces, process=False)


def lotus_petal(cx, cy, theta, root_radius, length, rise, width, z0, steps):
    verts, faces = [], []
    across = 6
    for side in [0, 1]:
        for j in range(steps + 1):
            v = j / steps
            petal_half = width * (0.03 + 0.97 * math.sin(math.pi * v) ** 0.67) * 0.5
            if j == steps:
                petal_half = width * 0.015
            for k in range(across + 1):
                u = -1.0 + 2.0 * k / across
                rad = root_radius + length * v - 0.005 * v * v
                # Cup petal toward its centerline
                rad += 0.005 * (1-u*u) * math.sin(math.pi*v)
                rad += 0.0005 if side == 0 else -0.0005
                xy = np.array([cx, cy], dtype=float)
                xy += rad * np.array([math.cos(theta), math.sin(theta)])
                xy += u * petal_half * np.array([-math.sin(theta), math.cos(theta)])
                zz = z0 + rise * (v - 0.15 * v*v) - 0.006 * abs(u) * math.sin(math.pi*v)
                verts.append([float(xy[0]), float(xy[1]), zz])
    n = (steps+1) * (across+1)
    for side in [0, 1]:
        off = side * n
        for j in range(steps):
            for k in range(across):
                a = off + j * (across+1) + k
                b, c, d = a+1, a+(across+1), a+(across+2)
                faces.extend([[a, c, d], [a, d, b]] if not side else [[a, d, c], [a, b, d]])
    for j in range(steps):
        for k in [0, across]:
            a, b = j*(across+1)+k, (j+1)*(across+1)+k
            faces.extend([[a,b,b+n],[a,b+n,a+n]])
    for j in [0, steps]:
        for k in range(across):
            a, b = j*(across+1)+k, j*(across+1)+k+1
            faces.extend([[a,b,b+n],[a,b+n,a+n]])
    return trimesh.Trimesh(vertices=verts, faces=faces, process=False)


def tiny_floret(center, direction, length, width, angle=0.0):
    """Double-sided, ruffled pointed marigold floret made of 4 triangles."""
    direction = norm(direction)
    helper = np.array([0., 0., 1.]) if abs(direction[2]) < 0.93 else np.array([1., 0., 0.])
    p = norm(np.cross(direction, helper))
    q = norm(np.cross(direction, p))
    p, q = math.cos(angle)*p + math.sin(angle)*q, -math.sin(angle)*p + math.cos(angle)*q
    c = np.asarray(center, dtype=float)
    start = c + direction*0.010
    mid = c + direction*(0.010+length*0.47) + q*width*0.08
    tip = c + direction*(0.010+length) + q*width*0.31
    v = [start, mid-p*width*0.48, mid+q*width*0.4, mid+p*width*0.48, tip]
    f = [[0,1,2],[0,2,3],[1,4,2],[2,4,3], [2,1,0],[3,2,0],[2,4,1],[3,4,2]]
    return trimesh.Trimesh(vertices=v, faces=f, process=False)


def flame_shape(center, height, width):
    x,y,z = center
    verts = [(x,y,z),(x+width,y,z+height*0.25),(x,y,z+height),
             (x-width,y,z+height*0.25),(x,y+width,z+height*0.25),
             (x,y-width,z+height*0.25)]
    faces = [[0,1,2],[0,2,3],[0,4,2],[0,2,5],
             [2,1,0],[3,2,0],[2,4,0],[5,2,0]]
    return trimesh.Trimesh(vertices=verts, faces=faces, process=False)


class Builder:
    def __init__(self, config):
        self.cfg = config
        self.q = QUALITY[config["quality"]]
        self.rng = random.Random(int(config["seed"]))
        self.pieces = defaultdict(list)
        self.count = Counter()
        self.radius = float(config["diameter_m"]) / 2
        self.scale = self.radius / 0.13

    def put(self, label, mat, mesh):
        self.pieces[(label, mat)].append(mesh)

    def build_base(self):
        s, r = self.scale, self.radius
        self.put("01_banana_stem_core", "pith", cylinder(r*0.976, .038*s, (0,0,.019*s), self.q["circle"]))
        # Top banana-leaf sheet hides the pith and gives flowers a natural green bed.
        self.put("01_banana_leaf_top_cap", "leaf_mid", cylinder(r*0.947, .0016*s, (0,0,.039*s), self.q["circle"]))
        self.put("01_banana_leaf_wrapping", "leaf_band", flat_band(r*.962, r*.99, .006*s, .043*s, self.q["circle"]))
        self.put("01_banana_leaf_wrapping", "leaf_dark", flat_band(r*.993, r*.998, .005*s, .010*s, self.q["circle"]))
        # Visible horizontal folded overlap band
        self.put("01_banana_leaf_wrapping", "leaf_light", flat_band(r*.999, r*1.005, .026*s, .030*s, self.q["circle"]))
        self.count["base"] += 1

    def leaf_ring(self, ring, quantity, r0, z0, width, height, tilt):
        s = self.scale
        if not quantity:
            return
        for i in range(quantity):
            theta = (i + (0.5 if ring == "inner" else 0.0)) * 2*math.pi/quantity
            variation = 0.94 + .09*self.rng.random()
            m = folded_leaf(theta, r0*s, z0*s, width*s*variation,
                            height*s*variation, tilt*s, self.q["leaf_steps"])
            mat = ["leaf_dark", "leaf_mid", "leaf_light"][i%3]
            self.put("02_banana_leaf_petals_" + ring, mat, m)
            # Central fold/vein, subtle and not a separate leaf object.
            start = np.array([r0*math.cos(theta), r0*math.sin(theta), z0]) * s
            end_rad = (r0 + tilt) * s
            end = np.array([end_rad*math.cos(theta), end_rad*math.sin(theta), (z0+height)*s])
            self.put("02_folded_leaf_rib_" + ring, "leaf_vein", line_tube(start, end, .00055*s, 5))
        self.count[ring + "_leaves"] += quantity

    def build_leaves(self):
        self.leaf_ring("outer", int(self.cfg["outer_leaf_count"]),
                       .115, .030, .054, .081, .012)
        self.leaf_ring("inner", int(self.cfg["inner_leaf_count"]),
                       .083, .042, .045, .077, .014)

    def marigold(self, center):
        s = self.scale
        center = np.array(center) * s
        self.put("03_marigold_heads", "marigold_core", ball(.013*s, center, 1))
        self.put("03_marigold_calyx", "leaf_dark", ball(.008*s, center - np.array([0,0,.012*s]), 1))
        n = self.q["flower_florets"]
        golden_angle = math.pi * (3 - math.sqrt(5))
        for i in range(n):
            h = 1 - 2*(i+0.5)/n
            angle = golden_angle*i
            rr = math.sqrt(max(0, 1-h*h))
            direction = np.array([math.cos(angle)*rr, math.sin(angle)*rr, h])
            length = (.007 + .006*self.rng.random()) * s
            width = (.005 + .002*self.rng.random()) * s
            petal = tiny_floret(center, direction, length, width, angle=self.rng.random()*math.pi)
            self.put("03_marigold_ruffled_florets", ["marigold_gold", "marigold_light", "marigold_deep"][i%3], petal)
        self.count["marigolds"] += 1

    def amaranth(self, center):
        s = self.scale
        center = np.asarray(center) * s
        self.put("03_globe_amaranth_heads", "purple", ball(.009*s, center, 1))
        n = 30 if self.cfg["quality"] != "low" else 18
        for i in range(n):
            h = 1 - 2*(i+.5)/n
            a = math.pi*(3-math.sqrt(5))*i
            d = np.array([math.sqrt(1-h*h)*math.cos(a),math.sqrt(1-h*h)*math.sin(a),h])
            self.put("03_globe_amaranth_florets", "purple_light" if i%3==0 else "purple_dark",
                     tiny_floret(center, d, .003*s, .0032*s, a))
        self.count["amaranths"] += 1

    def lotus(self, center):
        s = self.scale
        cx,cy = center
        for layer, n, rad, length, rise, width, z, mat in [
            ("outer", 12, .006, .043, .039, .024, .053, "lotus_pale"),
            ("middle", 10, .005, .029, .050, .021, .056, "lotus_pink"),
            ("inner", 7, .003, .018, .047, .015, .064, "lotus_rose")]:
            for i in range(n):
                t = 2*math.pi*(i+.5*(layer=="middle"))/n
                m = lotus_petal(cx*s,cy*s,t,rad*s,length*s,rise*s,width*s,z*s,self.q["leaf_steps"])
                self.put("03_lotus_petals_" + layer, mat, m)
                self.count["lotus_petals"] += 1
        self.put("03_lotus_seed_center", "lotus_yellow", ball(.008*s, (cx*s,cy*s,.092*s),1))
        self.count["lotus"] += 1

    def build_flowers(self):
        style = self.cfg["flower_style"]
        s = self.scale
        if style not in {"marigold", "lotus", "mixed", "none"}:
            raise ValueError("flower_style must be marigold, lotus, mixed or none")
        flower_count = int(self.cfg["flower_count"])
        if style == "lotus":
            self.lotus((0, -.008))
            flower_count = min(flower_count, 5)
        elif style == "mixed":
            self.lotus((0, -.008))
            flower_count = min(flower_count, 6)
        elif style == "none":
            flower_count = 0
        for i in range(flower_count):
            theta = 2*math.pi*i/max(flower_count,1) + .12
            r = .070 if style == "marigold" else .079
            self.marigold((r*math.cos(theta),r*math.sin(theta),.066))
        if style != "none":
            for i in range(int(self.cfg["amaranth_count"])):
                a = 2*math.pi*(i+.5)/max(1,int(self.cfg["amaranth_count"]))
                self.amaranth((.094*math.cos(a),.094*math.sin(a),.075))

    def build_ceremonial(self):
        s = self.scale
        style = self.cfg["flower_style"]
        separate = style in {"lotus", "mixed"}
        candle_x,candle_y = (.054,.032) if separate else (.016,0.0)
        if self.cfg["candle"]:
            self.put("04_candle_wax", "wax", cylinder(.0070*s,.071*s,(candle_x*s,candle_y*s,.120*s),14))
            self.put("04_candle_wick", "wick", line_tube((candle_x*s,candle_y*s,.155*s),
                                                         (candle_x*s,candle_y*s,.163*s),.0009*s))
            if self.cfg["candle_lit"]:
                self.put("04_candle_flame", "flame_outer", flame_shape((candle_x*s,candle_y*s,.163*s),.023*s,.007*s))
                self.put("04_candle_flame", "flame_inner", flame_shape((candle_x*s,candle_y*s,.164*s),.015*s,.0035*s))
            self.count["candles"] += 1
        n = int(self.cfg["incense_count"])
        base_x,base_y = (-.050,.025) if separate else (-.026,.003)
        for i in range(n):
            x = base_x + .006*i
            y = base_y + .002*((i%2)*2-1)
            top = .215 + .007*(i%2)
            self.put("04_incense_sticks", "incense", cylinder(.00155*s,(top-.083)*s,
                      (x*s,y*s,((top+.083)/2)*s),8))
            self.put("04_incense_burnt_tips", "incense_tip", cylinder(.00160*s,.015*s,
                      (x*s,y*s,(top-.0075)*s),8))
            self.count["incense_sticks"] += 1

    def export(self, output, stage):
        scene = trimesh.Scene()
        for (name, mat), parts in sorted(self.pieces.items()):
            if not parts:
                continue
            mesh = trimesh.util.concatenate(parts)
            mesh.visual = trimesh.visual.TextureVisuals(material=material(mat))
            scene.add_geometry(mesh, geom_name=f"{name}_{mat}", node_name=f"{name}_{mat}")
        # Convert world +Z up to glTF-native +Y up for Three.js / Babylon.js.
        rotate = trimesh.transformations.rotation_matrix(-math.pi/2, [1,0,0])
        scene.apply_transform(rotate)
        output.parent.mkdir(parents=True, exist_ok=True)
        glb = scene.export(file_type="glb")
        output.write_bytes(glb)
        tri = sum(len(m.faces) for m in scene.geometry.values())
        report = {
            "generator": "thai-krathong-3d", "stage": stage,
            "name": self.cfg["name"], "units": "meters", "glb_up": "+Y",
            "config": self.cfg, "component_counts": dict(self.count),
            "mesh_groups": len(scene.geometry), "triangles": int(tri),
            "glb_bytes": len(glb),
            "bounds_y_up_m": np.asarray(scene.bounds).round(5).tolist(),
            "format": "glb",
            "limitations": "Stylized procedural starter; photo fidelity and functional float stability are not certified."
        }
        output.with_suffix(".report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report


def validate_config(cfg):
    if cfg["quality"] not in QUALITY:
        raise ValueError("quality must be low/medium/high")
    if not (.12 <= float(cfg["diameter_m"]) <= .50):
        raise ValueError("diameter_m must be between 0.12 and 0.50 meters")
    for name, upper in [("outer_leaf_count",64),("inner_leaf_count",64),
                        ("flower_count",24),("amaranth_count",32),("incense_count",12)]:
        v = cfg[name]
        if isinstance(v, bool) or int(v) != v or not (0 <= v <= upper):
            raise ValueError(f"{name} must be an integer from 0 to {upper}")
    if not cfg["outer_leaf_count"] and not cfg["inner_leaf_count"]:
        raise ValueError("At least one leaf ring is required")
    if not isinstance(cfg["candle"],bool) or not isinstance(cfg["candle_lit"],bool):
        raise ValueError("candle and candle_lit must be boolean")
    if cfg["flower_style"] not in {"marigold","lotus","mixed","none"}:
        raise ValueError("Unsupported flower_style")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preset", type=Path, help="JSON preset bundled with the Skill")
    p.add_argument("--config", type=Path, help="Optional JSON overrides (whitelisted keys only)")
    p.add_argument("--out", required=True, type=Path, help="Destination .glb")
    p.add_argument("--stage", choices=STAGES, default="complete")
    p.add_argument("--seed", type=int, help="Override random seed")
    args = p.parse_args()
    if args.out.suffix.lower() != ".glb":
        p.error("--out must end in .glb")
    cfg = dict(DEFAULTS)
    for path in [args.preset,args.config]:
        if path:
            data = json.loads(path.read_text(encoding="utf-8"))
            unknown = set(data) - set(DEFAULTS)
            if unknown:
                p.error(f"Unknown config parameters: {sorted(unknown)}")
            cfg.update(data)
    if args.seed is not None:
        cfg["seed"] = args.seed
    validate_config(cfg)
    b = Builder(cfg)
    b.build_base()
    if STAGES.index(args.stage)>=STAGES.index("leaves"):
        b.build_leaves()
    if STAGES.index(args.stage)>=STAGES.index("flowers"):
        b.build_flowers()
    if STAGES.index(args.stage)>=STAGES.index("ceremonial"):
        b.build_ceremonial()
    report = b.export(args.out,args.stage)
    print(json.dumps({"path":str(args.out),"triangles":report["triangles"],
                      "counts":report["component_counts"],"bytes":report["glb_bytes"]},
                     ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
