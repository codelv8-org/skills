#!/usr/bin/env python3
"""Original, reference-informed krathong meshes built directly in Blender.

Run with Blender, not the system Python:
  blender -b --python scripts/build_reference.py -- \
    --preset assets/ref-white-lotus.json --out-dir /absolute/output --render

This is a new implementation informed by the supplied research and screenshots;
it is not the unavailable archive described in the historical research report.
All coordinates are metres, Z up in Blender, Y up in exported glTF.
"""
import argparse
import json
import math
import random
import sys

sys.dont_write_bytecode = True

from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

TAU = 2.0 * math.pi
ROLES = {"leaf", "leaf_dark", "petal_white", "petal_pink", "petal_orange",
         "bread", "clay", "stem", "center", "wax", "incense",
         "flower_yellow", "flower_purple"}
FAMILIES = {"white_lotus", "pink_lotus", "orange_bowl", "banana_classic",
            "tiered_leaf", "diamond_leaf", "bread_flower", "clay_bowl"}


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


class Builder:
    def __init__(self, preset):
        self.cfg = preset
        self.rng = random.Random(int(preset.get("seed", 731)))
        self.collection = bpy.data.collections.new("Krathong_Asset")
        bpy.context.scene.collection.children.link(self.collection)
        self.parts = Counter()
        self.candle_z = 0.025

    def mesh(self, name, vertices, faces, role, uv=None, smooth=False, part=None):
        if role not in ROLES:
            raise ValueError("Unknown material role: " + role)
        mesh = bpy.data.meshes.new(name + "_mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.update(calc_edges=True)
        obj = bpy.data.objects.new(name, mesh)
        self.collection.objects.link(obj)
        obj["krathong_material"] = role
        obj["krathong_part"] = part or name.split("_")[0]
        obj["source_units"] = "metres"
        for polygon in mesh.polygons:
            polygon.use_smooth = smooth
        layer = mesh.uv_layers.new(name="UVMap")
        if uv is None:
            xs = [v[0] for v in vertices]
            ys = [v[1] for v in vertices]
            dx = max(max(xs) - min(xs), 1e-8)
            dy = max(max(ys) - min(ys), 1e-8)
            uv = [((v[0] - min(xs)) / dx, (v[1] - min(ys)) / dy) for v in vertices]
        for polygon in mesh.polygons:
            for li in polygon.loop_indices:
                layer.data[li].uv = uv[mesh.loops[li].vertex_index]
        self.parts[obj["krathong_part"]] += 1
        return obj

    def solid_grid(self, name, surface, uv, rows, cols, thickness, role,
                   smooth=True, normals=None, part=None):
        """Closed double-sided grid, including its narrow perimeter wall."""
        n = len(surface)
        if normals is None:
            normals = [Vector((0, 0, 1))] * n
        verts = []
        for sign in (1, -1):
            for p, normal in zip(surface, normals):
                verts.append(tuple(Vector(p) + normal * (sign * thickness * .5)))
        faces = []
        for j in range(rows - 1):
            for k in range(cols - 1):
                a = j * cols + k
                face = (a, a + cols, a + cols + 1, a + 1)
                faces.append(face)
                faces.append(tuple(i + n for i in reversed(face)))
        boundary = [j * cols for j in range(rows)]
        boundary += [(rows - 1) * cols + k for k in range(1, cols)]
        boundary += [j * cols + cols - 1 for j in range(rows - 2, -1, -1)]
        boundary += [k for k in range(cols - 2, 0, -1)]
        for a, b in zip(boundary, boundary[1:] + boundary[:1]):
            faces.append((a, a + n, b + n, b))
        return self.mesh(name, verts, faces, role, uv + uv, smooth, part)

    def lathe(self, name, profile, role, segments=72, smooth=True, part=None):
        """Revolve a closed radial cross-section; zero-radius rings are poles."""
        verts, uv, rings = [], [], []
        z0 = min(z for _, z in profile)
        dz = max(z for _, z in profile) - z0 or 1.0
        for r, z in profile:
            if r == 0:
                rings.append([len(verts)])
                verts.append((0, 0, z))
                uv.append((.5, (z - z0) / dz))
            else:
                ids = []
                for k in range(segments):
                    a = TAU * k / segments
                    ids.append(len(verts))
                    verts.append((r * math.cos(a), r * math.sin(a), z))
                    uv.append((k / segments, (z - z0) / dz))
                rings.append(ids)
        faces = []
        for aa, bb in zip(rings, rings[1:]):
            for k in range(segments):
                nk = (k + 1) % segments
                if len(aa) == 1:
                    faces.append((aa[0], bb[nk], bb[k]))
                elif len(bb) == 1:
                    faces.append((aa[k], aa[nk], bb[0]))
                else:
                    faces.append((aa[k], aa[nk], bb[nk], bb[k]))
        obj = self.mesh(name, verts, faces, role, uv, smooth, part)
        # Flat caps need planar UVs: cylindrical UVs collapse their area to a line.
        radius = max(r for r, _ in profile) or 1.0
        layer = obj.data.uv_layers.active
        for polygon in obj.data.polygons:
            zs = [obj.data.vertices[k].co.z for k in polygon.vertices]
            if max(zs) - min(zs) < 1e-8:
                for li in polygon.loop_indices:
                    v = obj.data.vertices[obj.data.loops[li].vertex_index].co
                    layer.data[li].uv = (.5 + v.x / (2 * radius), .5 + v.y / (2 * radius))
        return obj

    def disc(self, name, radius, z, height, role, segments=72, bevel=.001, part="base"):
        b = min(bevel, height * .24, radius * .08)
        return self.lathe(name, [(0, z), (radius - b, z), (radius, z + b),
                                (radius, z + height - b), (radius - b, z + height),
                                (0, z + height)], role, segments, True, part)

    def petal(self, name, spec, angle, role, index):
        reach = float(spec["reach"])
        rise = float(spec["rise"])
        width = float(spec["width"])
        r0, z0 = float(spec["radius"]), float(spec["z"])
        variance = float(spec.get("variation", .025))
        width *= 1 + self.rng.uniform(-variance, variance)
        rise *= 1 + self.rng.uniform(-variance, variance)
        cup = float(spec.get("cup", .004))
        ridge = float(spec.get("ridge", .001))
        curl = float(spec.get("edge_curl", .001))
        hook = float(spec.get("tip_hook", .002))
        thickness = float(spec.get("thickness", .0013))
        # Beta envelope gives a pinched attachment and a broad spoon centre.
        alpha, beta = spec.get("width_profile", [.65, .60])
        peak_t = alpha / (alpha + beta)
        peak = peak_t ** alpha * (1 - peak_t) ** beta
        base_normal = Vector((-rise, 0, reach)).normalized()

        def point(s, t):
            envelope = (max(t, 0) ** alpha * max(1 - t, 0) ** beta) / peak
            envelope = .016 + .984 * envelope
            x = r0 + reach * t - hook * smoothstep((t - .76) / .24)
            z = z0 + rise * (.70 * t + .30 * t * t)
            z += float(spec.get("camber", .0015)) * math.sin(math.pi * t)
            z -= float(spec.get("tip_droop", 0)) * smoothstep((t - .8) / .2)
            p = Vector((x, s * width * .5 * envelope, z))
            transverse = cup * abs(s) ** 2.2 * math.sin(math.pi * t) ** .65
            transverse += curl * abs(s) ** 6 * math.sin(math.pi * t)
            transverse += ridge * (1 - s * s) * math.sin(math.pi * t)
            return p + base_normal * transverse

        rows = int(spec.get("length_segments", 22)) + 1
        cols = int(spec.get("width_segments", 12)) + 1
        surface, uv, normals = [], [], []
        for j in range(rows):
            t = (1 - math.cos(math.pi * j / (rows - 1))) * .5
            for k in range(cols):
                s = 2 * k / (cols - 1) - 1
                p = point(s, t)
                dt = point(s, min(t + .0001, 1)) - point(s, max(t - .0001, 0))
                ds = point(min(s + .0001, 1), t) - point(max(s - .0001, -1), t)
                normal = dt.cross(ds).normalized()
                if normal.length < .1:
                    normal = base_normal
                surface.append(tuple(p))
                normals.append(normal)
                uv.append(((s + 1) * .5, t))
        obj = self.solid_grid(name, surface, uv, rows, cols, thickness, role,
                              True, normals, "petal")
        obj.rotation_euler.z = angle
        obj["whorl"] = spec.get("name", "petal")
        obj["petal_index"] = index
        obj["petal_uv"] = "u=cross-width; v=base-to-tip"
        return obj

    def folded_leaf(self, name, spec, angle=0, location=(0, 0, 0)):
        """Thick, faceted folded sheet with a centre crease and side valleys."""
        width, reach, rise = spec["width"], spec["reach"], spec["rise"]
        r0, z0 = spec.get("radius", 0), spec.get("z", 0)
        ridge = spec.get("ridge", .005)
        profile = spec.get("profile", "pointed")
        if profile == "rounded":
            stations = [(0, .70), (.35, 1.0), (.78, .95), (1, .65)]
        else:
            stations = [(0, .60), (.38, 1.0), (.72, .64), (1, .012)]
        cross = [-1, -.62, 0, .62, 1]
        # The centre is a sharp ridge; the off-centre points are valleys.
        folds = [.28, -.14, 1.0, -.14, .28]
        surface, uv = [], []
        for t, w in stations:
            for s, fold in zip(cross, folds):
                zz = z0 + rise * t + ridge * fold * (.55 + .45 * math.sin(math.pi * t))
                surface.append((r0 + reach * t, s * width * w * .5, zz))
                uv.append(((s + 1) * .5, t))
        n = Vector((-rise, 0, reach)).normalized()
        obj = self.solid_grid(name, surface, uv, len(stations), len(cross),
                              spec.get("thickness", .00065), "leaf", False,
                              [n] * len(surface), "folded_leaf")
        obj.rotation_euler.z = angle
        obj.location = location
        obj["fold_type"] = "ridge-valley-sheet"
        # Independent overlapping folded side flaps, not a smoothed blade loft.
        if spec.get("flaps", True):
            for side in (-1, 1):
                flap = [(r0 + .04 * reach, side * .29 * width, z0 + ridge * .16),
                        (r0 + .42 * reach, side * .48 * width, z0 + .42 * rise + ridge * .05),
                        (r0 + .65 * reach, side * .16 * width, z0 + .65 * rise + ridge * .55),
                        (r0 + .12 * reach, side * .07 * width, z0 + .12 * rise + ridge * .92)]
                # A tiny triangular prism makes the overlapping lip visibly thick.
                normal = Vector((-rise, 0, reach)).normalized() * .00035
                vv = [tuple(Vector(p) + normal) for p in flap]
                vv += [tuple(Vector(p) - normal) for p in flap]
                ff = [(0, 1, 2, 3), (7, 6, 5, 4)]
                ff += [(k, k + 4, (k + 1) % 4 + 4, (k + 1) % 4) for k in range(4)]
                if side > 0:
                    ff = [tuple(reversed(f)) for f in ff]
                flap_obj = self.mesh(name + ("_flap_L" if side < 0 else "_flap_R"),
                                     vv, ff, "leaf_dark", smooth=False, part="fold_flap")
                flap_obj.rotation_euler.z = angle
                flap_obj.location = location
        return obj

    def leaf_ring(self, spec, prefix):
        count = int(spec["count"])
        phase = math.radians(spec.get("phase_degrees", 0))
        for k in range(count):
            angle = phase + TAU * k / count
            self.folded_leaf("%s_%02d" % (prefix, k + 1), spec, angle)

    def polygon_slab(self, name, outline, z, height, role, part="base"):
        n = len(outline)
        vv = [(x, y, z) for x, y in outline] + [(x, y, z + height) for x, y in outline]
        ff = [tuple(range(n - 1, -1, -1)), tuple(range(n, n * 2))]
        ff += [(k, (k + 1) % n, (k + 1) % n + n, k + n) for k in range(n)]
        return self.mesh(name, vv, ff, role, smooth=False, part=part)

    def build_lotus(self):
        cfg = self.cfg
        role = cfg["petal_role"]
        base = cfg.get("base", {})
        self.disc("lotus_support", base.get("radius", .056), 0,
                  base.get("height", .010), base.get("role", "stem"))
        for wi, whorl in enumerate(cfg["whorls"]):
            for k in range(int(whorl["count"])):
                angle = TAU * k / whorl["count"] + math.radians(whorl.get("phase_degrees", 0))
                angle += self.rng.uniform(-.012, .012)
                self.petal("lotus_%s_petal_%02d" % (whorl.get("name", str(wi)), k + 1),
                           whorl, angle, role, k + 1)
        center = cfg.get("center", {})
        mode = center.get("mode", "disc")
        z = center.get("z", .022)
        r = center.get("radius", .075)
        if mode == "dome":
            # An independently configured central volume, as in screenshot 214638.
            prof = [(0, z), (r, z)]
            for j in range(1, 13):
                a = math.pi * .5 * j / 12
                prof.append((r * math.cos(a) if j < 12 else 0,
                             z + center.get("height", .030) * math.sin(a)))
            self.lathe("lotus_central_dome", prof, "petal_white", part="center")
            self.candle_z = z + center.get("height", .030)
        elif mode in {"disc", "open"}:
            self.disc("lotus_central_deck", r, z - .004, .004,
                      center.get("role", role), part="center")
            self.candle_z = z
        else:
            raise ValueError("Unknown lotus center mode: " + mode)

    def build_banana(self):
        cfg = self.cfg
        base = cfg["base"]
        self.disc("banana_stem_slice", base["radius"], 0, base["height"], "stem")
        self.disc("banana_wrapped_side", base["radius"] + .0005, base["height"] * .60,
                  base["height"] * .48, "leaf_dark", bevel=.0005)
        for i, ring in enumerate(cfg["rings"]):
            self.leaf_ring(ring, "banana_ring_%d_leaf" % (i + 1))
        deck = cfg["deck"]
        self.disc("banana_leaf_centre_sheet", deck["radius"], deck["z"] - .002,
                  .002, "leaf", bevel=.00035, part="center")
        self.candle_z = deck["z"]
        if cfg.get("bead_border"):
            for k in range(cfg["bead_border"].get("count", 36)):
                a = TAU * k / cfg["bead_border"].get("count", 36)
                rr = deck["radius"] * .97
                self.ellipsoid("pale_border_bead_%02d" % k,
                               (rr * math.cos(a), rr * math.sin(a), deck["z"] + .004),
                               (.004, .0045, .0055), "flower_yellow", "bead")

    def build_tiered(self):
        self.disc("tiered_banana_stem", self.cfg["base"]["radius"], 0,
                  self.cfg["base"]["height"], "stem")
        for i, tier in enumerate(self.cfg["tiers"]):
            self.disc("tier_%d_wrapped_wall" % (i + 1), tier["radius"],
                      tier["z"] - tier["height"], tier["height"], "leaf_dark")
            self.disc("tier_%d_flat_leaf_deck" % (i + 1), tier["radius"],
                      tier["z"] - .0015, .0015, "leaf", bevel=.00025, part="terrace")
            ring = dict(tier["ring"])
            ring["radius"] = tier["radius"] - .006
            ring["z"] = tier["z"] - .003
            self.leaf_ring(ring, "tier_%d_crown_leaf" % (i + 1))
        self.candle_z = self.cfg["tiers"][-1]["z"]

    def build_diamond(self):
        cfg = self.cfg
        rx, front, back = cfg.get("half_width", .112), cfg.get("front", .143), cfg.get("back", .113)
        outline = [(0, -front), (rx, 0), (0, back), (-rx, 0)]
        self.polygon_slab("diamond_cut_stem", outline, 0, .014, "stem")
        self.polygon_slab("diamond_wrapped_side", [(x * 1.005, y * 1.005) for x, y in outline],
                          .010, .007, "leaf_dark")
        for ri, ring in enumerate(cfg["rings"]):
            scale = ring.get("scale", 1.0)
            corners = [Vector((x * scale, y * scale, 0)) for x, y in outline]
            nside = int(ring.get("leaves_per_side", 5))
            for edge in range(4):
                a, b = corners[edge], corners[(edge + 1) % 4]
                normal = Vector((b.y - a.y, -(b.x - a.x), 0)).normalized()
                angle = math.atan2(normal.y, normal.x)
                for k in range(nside):
                    t = (k + .5) / nside
                    p = a.lerp(b, t) - normal * .006
                    spec = dict(ring)
                    spec["radius"] = 0
                    self.folded_leaf("diamond_ring_%d_edge_%d_leaf_%02d" % (ri + 1, edge + 1, k + 1),
                                     spec, angle, tuple(p))
        deck_scale = cfg.get("deck_scale", .85)
        deck_z = cfg.get("deck_z", .034)
        self.polygon_slab("diamond_continuous_leaf_deck",
                          [(x * deck_scale, y * deck_scale) for x, y in outline],
                          deck_z - .002, .002, "leaf", part="center")
        self.candle_z = deck_z

    def bread_slice(self, name, length, width, thickness, location, angle, pores=True):
        nseg = 64
        outline = []
        for k in range(nseg):
            a = TAU * k / nseg
            # Slight asymmetry keeps broad slices from resembling identical ellipses.
            xx = math.cos(a) * length * .5
            yy = math.sin(a) * width * .5 * (1 + .06 * math.cos(a))
            outline.append((xx, yy))
        shell = self.polygon_slab(name + "_crust", outline, 0, thickness, "bread", "bread_slice")
        shell["krathong_bread_surface"] = "crust"
        shell.location, shell.rotation_euler.z = location, angle
        points = [(self.rng.uniform(-.8, .8) * length * .5,
                   self.rng.uniform(-.8, .8) * width * .5,
                   self.rng.uniform(.0012, .0028), self.rng.uniform(.0003, .0010))
                  for _ in range(45 if pores else 0)]
        verts, uv = [(0, 0, thickness + .0008)], [(.5, .5)]
        nr = 17
        for j in range(1, nr + 1):
            rho = j / nr
            for k in range(nseg):
                a = TAU * k / nseg
                x = math.cos(a) * length * .485 * rho
                y = math.sin(a) * width * .485 * rho * (1 + .06 * math.cos(a))
                z = thickness + .0002 + .0015 * (1 - rho * rho)
                for px, py, radius, depth in points:
                    z -= depth * (1 - rho * rho) * math.exp(-((x - px) ** 2 + (y - py) ** 2) / (radius * radius))
                z = max(z, thickness + .0001)
                verts.append((x, y, z))
                uv.append((x / length + .5, y / width + .5))
        faces = []
        for k in range(nseg):
            faces.append((0, 1 + k, 1 + (k + 1) % nseg))
        for j in range(nr - 1):
            start, nxt = 1 + j * nseg, 1 + (j + 1) * nseg
            for k in range(nseg):
                kk = (k + 1) % nseg
                faces.append((start + k, nxt + k, nxt + kk, start + kk))
        # Close the crumb veneer with a bottom cap and narrow side wall.
        boundary = [1 + (nr - 1) * nseg + k for k in range(nseg)]
        bottom = len(verts)
        for k in boundary:
            x, y, _ = verts[k]
            verts.append((x, y, thickness - .0003))
            uv.append(uv[k])
        faces.append(tuple(reversed(range(bottom, bottom + nseg))))
        for k in range(nseg):
            kk = (k + 1) % nseg
            faces.append((boundary[k], bottom + k, bottom + kk, boundary[kk]))
        crumb = self.mesh(name + "_porous_crumb", verts, faces, "bread", uv, True, "bread_crumb")
        crumb["krathong_bread_surface"] = "crumb"
        crumb.location, crumb.rotation_euler.z = location, angle
        return shell, crumb

    def build_bread(self):
        cfg = self.cfg
        base = self.disc("bread_support_loaf", .064, 0, .016, "bread", part="base")
        base["krathong_bread_surface"] = "crust"
        for k in range(cfg.get("slice_count", 8)):
            a = TAU * k / cfg.get("slice_count", 8) + math.pi / 8
            radius = cfg.get("slice_radius", .077)
            self.bread_slice("bread_flower_slice_%02d" % (k + 1),
                             cfg.get("slice_length", .103), cfg.get("slice_width", .052),
                             cfg.get("slice_thickness", .008),
                             (radius * math.cos(a), radius * math.sin(a), .016), a)
        self.bread_slice("bread_central_pedestal", .042, .042, .030, (0, 0, .017), 0)
        for k in range(cfg.get("small_round_count", 8)):
            a = TAU * k / cfg.get("small_round_count", 8)
            self.bread_slice("bread_small_round_%02d" % (k + 1), .018, .018, .016,
                             (.036 * math.cos(a), .036 * math.sin(a), .018), a, pores=False)
        self.candle_z = .0475

    def build_clay(self):
        cfg = self.cfg
        r, h = cfg.get("radius", .13), cfg.get("height", .044)
        # Cross-section walks under the bowl, around the rim, down its inner wall.
        # A cap at rim height would eliminate the cavity and is deliberately absent.
        profile = [(0, 0), (.72 * r, 0), (.84 * r, .06 * h),
                   (.93 * r, .25 * h), (.99 * r, .70 * h), (r, .90 * h),
                   (.992 * r, .98 * h), (.972 * r, h), (.946 * r, .99 * h),
                   (.928 * r, .92 * h), (.918 * r, .78 * h),
                   (.88 * r, .51 * h), (.78 * r, .32 * h),
                   (.60 * r, .22 * h), (.34 * r, .18 * h), (0, .175 * h)]
        obj = self.lathe("terracotta_bowl_true_cavity", profile, "clay", 112, True, "bowl")
        obj["cavity_depth_m"] = h * .825
        self.candle_z = h * .175

    def ellipsoid(self, name, center, scale, role, part, rings=10, segments=20):
        profile = []
        for j in range(rings + 1):
            a = math.pi * j / rings
            rr = math.sin(a) if 0 < j < rings else 0
            profile.append((rr, -math.cos(a)))
        obj = self.lathe(name, profile, role, segments, True, part)
        obj.location = center
        obj.scale = scale
        return obj

    def accessories(self):
        cfg = self.cfg.get("accessories", {})
        if not cfg.get("candle", False):
            return
        z = self.candle_z
        radius, height = cfg.get("candle_radius", .006), cfg.get("candle_height", .052)
        candle = self.disc("ceremonial_wax_candle", radius, z, height, "wax", 40,
                           bevel=.0007, part="candle")
        self.disc("candle_wick", .00045, z + height - .001, .003, "incense", 10,
                  bevel=.0001, part="wick")
        if cfg.get("wax_drips", True):
            for k in range(5):
                a = TAU * k / 5 + .3
                self.ellipsoid("candle_wax_drip_%d" % k,
                               (radius * math.cos(a), radius * math.sin(a), z + height - .0025),
                               (.0008, .0008, .002 + .00035 * (k % 3)), "wax", "wax_drip")
        incense_count = int(cfg.get("incense_count", 3))
        for k in range(incense_count):
            x = (k - (incense_count - 1) * .5) * .0055
            stick = self.disc("ceremonial_incense_%d" % (k + 1), .00065, 0,
                              cfg.get("incense_height", .095), "incense", 12, .0001, "incense")
            stick.location = (x, .008, z)
            stick.rotation_euler.y = (k - (incense_count - 1) * .5) * .035
        if cfg.get("flame", False):
            obj = self.ellipsoid("candle_stylized_flame", (0, 0, z + height + .0045),
                                 (.0022, .0018, .006), "wax", "flame", 12, 20)
            obj["krathong_detail"] = "flame"

    def build(self):
        family = self.cfg["family"]
        if family in {"white_lotus", "pink_lotus", "orange_bowl"}:
            self.build_lotus()
        elif family == "banana_classic":
            self.build_banana()
        elif family == "tiered_leaf":
            self.build_tiered()
        elif family == "diamond_leaf":
            self.build_diamond()
        elif family == "bread_flower":
            self.build_bread()
        elif family == "clay_bowl":
            self.build_clay()
        self.accessories()
        bpy.context.view_layer.update()
        return self.collection


def geometry_report(collection):
    vertices, faces, triangles = 0, 0, 0
    coords, objects, errors = [], [], []
    roles = Counter()
    for obj in collection.all_objects:
        if obj.type != "MESH":
            errors.append("Non-mesh asset object: " + obj.name)
            continue
        mesh = obj.data
        if not mesh.vertices or not mesh.polygons:
            errors.append("Empty mesh: " + obj.name)
        tri_count = sum(len(p.vertices) - 2 for p in mesh.polygons)
        vertices += len(mesh.vertices)
        faces += len(mesh.polygons)
        triangles += tri_count
        role = obj.get("krathong_material", "unknown")
        roles[role] += 1
        for vertex in mesh.vertices:
            p = obj.matrix_world @ vertex.co
            if not all(math.isfinite(c) for c in p):
                errors.append("Non-finite geometry: " + obj.name)
                break
            coords.append(tuple(p))
        objects.append({"name": obj.name, "vertices": len(mesh.vertices),
                        "triangles": tri_count, "material_role": role,
                        "part": obj.get("krathong_part", "unspecified")})
    if not coords:
        raise ValueError("Asset has no finite coordinates")
    lo = [min(p[i] for p in coords) for i in range(3)]
    hi = [max(p[i] for p in coords) for i in range(3)]
    size = [b - a for a, b in zip(lo, hi)]
    if not .12 <= max(size[:2]) <= .50:
        errors.append("Width outside plausible 0.12–0.50 m interval")
    if not .01 <= size[2] <= .50:
        errors.append("Height outside plausible 0.01–0.50 m interval")
    if lo[2] < -.005:
        errors.append("Asset extends more than 5 mm below its nominal base")
    return {"status": "passed" if not errors else "failed", "errors": errors,
            "mesh_objects": len(objects), "vertices": vertices, "polygons": faces,
            "triangles": triangles, "bounds_m": {"min": lo, "max": hi, "size": size},
            "material_role_counts": dict(roles), "objects": objects,
            "checks": ["finite world-space vertices", "nonempty meshes", "plausible metre-scale bounds"],
            "not_checked": ["watertightness of the complete assembly", "physical buoyancy",
                            "visual reference fidelity", "device-specific WebGL performance"]}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--resolution", type=int, default=640)
    parser.add_argument("--samples", type=int, default=24)
    args = parser.parse_args(argv)
    preset_path = Path(args.preset).expanduser().resolve()
    cfg = json.loads(preset_path.read_text(encoding="utf-8"))
    if cfg.get("family") not in FAMILIES:
        raise ValueError("Unsupported structural family: " + str(cfg.get("family")))
    out = Path(args.out_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.resolution < 64 or args.resolution > 4096 or args.samples < 1:
        raise ValueError("Use resolution 64–4096 and positive render samples")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        if not collection.objects and not collection.children:
            bpy.data.collections.remove(collection)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    builder = Builder(cfg)
    asset = builder.build()
    qa = geometry_report(asset)
    report = {"schema_version": 1, "generator": "build_reference.py", "implementation": "new-original-reference-informed",
              "preset": preset_path.name, "family": cfg["family"], "seed": cfg.get("seed", 731),
              "reference_images": cfg.get("reference_images", []), "preset_configuration": cfg,
              "source_coordinates": "metres, +Z up", "gltf_coordinates": "metres, +Y up",
              "parts": dict(builder.parts), "geometry": qa, "visual_status": "unreviewed",
              "visual_notes": ["Automated structural checks do not establish a reference match.",
                               "Source screenshots are used as design references and are not packaged textures."],
              "renders": []}
    if qa["status"] != "passed":
        (out / "build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        raise ValueError("Structural validation failed: " + "; ".join(qa["errors"]))
    from reference_finish import apply_materials, setup_scene, render_views
    material_info = apply_materials(asset)
    if material_info is not None:
        report["finishing"] = material_info
    bpy.ops.object.select_all(action="DESELECT")
    for obj in asset.all_objects:
        if obj.type == "MESH":
            obj.select_set(True)
    bpy.context.view_layer.objects.active = next(obj for obj in asset.all_objects if obj.type == "MESH")
    blend_path, glb_path = out / "krathong.blend", out / "krathong.glb"
    # Save the editable asset before constructing temporary render-stage objects.
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_extras=True,
                              export_cameras=False, export_lights=False)
    report["files"] = {"blend": str(blend_path), "glb": str(glb_path)}
    report["file_bytes"] = {"blend": blend_path.stat().st_size, "glb": glb_path.stat().st_size}
    report["export_scope"] = "selected mesh objects in Krathong_Asset only; no stage, lights or cameras"
    report["source_blend_scope"] = "asset collection only; render staging is constructed after saving"
    setup_scene(asset, resolution=args.resolution, samples=args.samples)
    if args.render:
        paths = render_views(str(out), asset)
        report["renders"] = paths
    (out / "build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print("KRATHONG_BUILD_OK " + json.dumps({"family": cfg["family"], "triangles": qa["triangles"],
                                             "bounds_m": qa["bounds_m"]["size"], "visual_status": "unreviewed"}))


if __name__ == "__main__":
    main()
