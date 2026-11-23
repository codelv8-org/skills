#!/usr/bin/env python3
"""Approximate character projected height and suggested LOD by camera distance.

Assumes camera upright, character near optical axis, perspective vertical FOV;
not a substitute for real model AABB projection, camera inclination or WebGL QA.
"""
from __future__ import annotations
import argparse
import json
from math import radians, tan


def projected_height_px(character_height_m:float, distance_m:float, fov_vertical_deg:float,
                        viewport_css_height:int) -> float:
    if character_height_m<=0 or distance_m<=0 or viewport_css_height<1 or not 1<fov_vertical_deg<179:
        raise ValueError('Positive height/distance/viewport and vertical FOV in (1,179) required')
    return character_height_m*viewport_css_height/(2*distance_m*tan(radians(fov_vertical_deg)/2))


def lod_tier(height_css_px:float) -> str:
    if height_css_px >= 160:return 'HERO_LOD0'
    if height_css_px >= 60:return 'NPC_LOD1'
    if height_css_px >= 15:return 'CROWD_LOD2'
    return 'DISTANT_IMPOSTOR_OR_CULL'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--height-m',type=float,required=True)
    ap.add_argument('--distances-m',type=float,nargs='+',required=True)
    ap.add_argument('--fov-vertical-deg',type=float,default=50)
    ap.add_argument('--viewport-css-height',type=int,default=900)
    ap.add_argument('--json',type=str)
    args=ap.parse_args()
    result={'assumptions':'central upright perspective object; illustrative CSS-pixel thresholds; use hysteresis in actual LOD implementation',
            'character_height_m':args.height_m,'fov_vertical_deg':args.fov_vertical_deg,
            'viewport_css_height':args.viewport_css_height,'distances':[]}
    for d in args.distances_m:
        px=projected_height_px(args.height_m,d,args.fov_vertical_deg,args.viewport_css_height)
        result['distances'].append({'distance_m':d,'approx_projected_css_px':round(px,1),'initial_tier':lod_tier(px)})
    payload=json.dumps(result,indent=2)+'\n'
    if args.json:
        from pathlib import Path
        dst=Path(args.json);dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(payload)
    print(payload)

if __name__=='__main__':main()
