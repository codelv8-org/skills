#!/usr/bin/env python3
"""Validate Thai krathong GLB geometry, content, basic performance budgets."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

REQUIRED_PARTS = {
    "base": ["01_banana_stem_core", "01_banana_leaf_wrapping"],
    "leaves": ["02_banana_leaf_petals_outer", "02_banana_leaf_petals_inner"],
    "flowers": ["03_marigold_", "03_lotus_", "03_globe_amaranth_"],
    "ceremonial": ["04_candle_", "04_incense_"],
}
TRIANGLE_BUDGET = {"low": 30000, "medium": 90000, "high": 190000}


def inspect(path, expect_stage="complete", perf_quality="medium"):
    issues = []
    scene = trimesh.load(str(path), force="scene", process=False)
    geometries = list(scene.geometry.values())
    labels = list(scene.geometry)
    total_faces = sum(len(m.faces) for m in geometries)
    verts = sum(len(m.vertices) for m in geometries)
    geom_ok = all(np.isfinite(m.vertices).all() for m in geometries)
    if not geometries or not total_faces:
        issues.append("Empty scene")
    if not geom_ok:
        issues.append("Non-finite vertex positions")
    bounds = np.asarray(scene.bounds, dtype=float)
    extents = np.asarray(scene.extents, dtype=float)
    if not np.isfinite(bounds).all():
        issues.append("Invalid bounds")
    elif len(extents) != 3 or extents[1] <= 0:
        issues.append("Missing +Y-up height")
    elif bounds[0,1] < -0.015:
        issues.append("Bottom is unexpectedly below y=0 (meters)")
    elif extents[1] < .04 or extents[1] > 1.5:
        issues.append("Unreasonable total height; check axis/unit conversion")
    if abs(extents[0] - extents[2]) > 0.2 * max(extents[0], extents[2]):
        issues.append("Krathong footprint should be approximately circular")
    for prefix in REQUIRED_PARTS["base"]:
        if not any(s.startswith(prefix) for s in labels):
            issues.append("Missing " + prefix)
    if expect_stage in ["leaves", "flowers", "ceremonial", "complete"]:
        if not any("02_banana_leaf_petals_" in s for s in labels):
            issues.append("Missing leaf petals")
    report_path = path.with_suffix(".report.json")
    extra = {}
    if report_path.exists():
        extra = json.loads(report_path.read_text(encoding="utf-8"))
        if extra.get("triangles") != total_faces:
            issues.append("Triangle counts differ between GLB and metadata")
        components = extra.get("component_counts", {})
        cfg = extra.get("config", {})
        if components.get("outer_leaves",0) != cfg.get("outer_leaf_count",0):
            if expect_stage != "base":
                issues.append("Outer leaf count does not match configuration")
        if expect_stage in ["leaves", "flowers", "ceremonial", "complete"]:
            for ring in ("outer", "inner"):
                if components.get(ring+"_leaves", 0) != cfg.get(ring+"_leaf_count", 0):
                    issues.append(f"{ring} leaf count does not match configuration")
                if cfg.get(ring+"_leaf_count", 0) > 0 and not any(
                    s.startswith("02_banana_leaf_petals_"+ring) for s in labels):
                    issues.append(f"Missing leaf ring: {ring}")
        if expect_stage in ["flowers", "ceremonial", "complete"]:
            fs = cfg.get("flower_style", "marigold")
            expected_fl = (0 if fs == "none" else
                           min(cfg.get("flower_count",0), 5 if fs=="lotus" else 6)
                           if fs in ("lotus", "mixed") else cfg.get("flower_count",0))
            if components.get("marigolds",0) != expected_fl:
                issues.append("Marigold count differs from configuration")
            if fs in ("lotus", "mixed") and components.get("lotus",0) != 1:
                issues.append("Lotus bloom missing")
            if expected_fl > 0 and not any(s.startswith("03_marigold_heads_") for s in labels):
                issues.append("Marigold geometry missing")
            expected_am = 0 if fs == "none" else cfg.get("amaranth_count",0)
            if components.get("amaranths",0) != expected_am:
                issues.append("Amaranth count differs from configuration")
        if expect_stage in ["ceremonial","complete"]:
            if components.get("incense_sticks",0) != cfg.get("incense_count",0):
                issues.append("Incense stick count does not match configuration")
            if components.get("candles",0) != int(bool(cfg.get("candle",False))):
                issues.append("Candle count does not match configuration")
            if cfg.get("candle",False) and not any(s.startswith("04_candle_wax_") for s in labels):
                issues.append("Candle geometry missing")
            if cfg.get("incense_count",0) and not any(s.startswith("04_incense_sticks_") for s in labels):
                issues.append("Incense geometry missing")
        d = cfg.get("diameter_m")
        if d and max(extents[0],extents[2]) > d*1.40:
            issues.append("Footprint is oversized vs configured diameter")
    else:
        issues.append("Missing generator sidecar report.json")
    # Zero-area triangles and broken floating point geometry should not pass.
    degenerate = sum(int(np.count_nonzero(m.area_faces < 1e-12)) for m in geometries)
    if degenerate:
        issues.append(f"Degenerate triangle faces detected: {degenerate}")
    if total_faces > TRIANGLE_BUDGET[perf_quality]:
        issues.append(f"Triangle budget exceeded: {total_faces} > {TRIANGLE_BUDGET[perf_quality]}")
    if path.stat().st_size > 8*1024*1024:
        issues.append("GLB is >8 MB; optimize for web")
    return {
        "valid": not issues, "issues": issues, "triangles": total_faces,
        "vertices": verts, "geometry_groups": len(geometries),
        "material_count": len({getattr(getattr(m.visual,'material',None),'name',None) for m in geometries}),
        "bounds_m_y_up": bounds.round(5).tolist(),
        "glb_kb": round(path.stat().st_size / 1024, 1),
        "counts": extra.get("component_counts",{}),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("model", type=Path)
    p.add_argument("--stage", choices=["base", "leaves", "flowers", "ceremonial", "complete"], default="complete")
    p.add_argument("--quality", choices=["low","medium","high"], default="medium")
    a = p.parse_args()
    if not a.model.is_file():
        p.error("Model file missing")
    result=inspect(a.model, a.stage,a.quality)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["valid"] else 2)


if __name__ == "__main__":
    main()
