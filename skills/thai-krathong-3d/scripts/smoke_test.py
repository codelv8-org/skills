#!/usr/bin/env python3
"""Basic release tests of all bundled presets and generation stages; no Blender required."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "scripts" / "generate_krathong.py"
QA = ROOT / "scripts" / "qa_model.py"


def call(*args):
    p = subprocess.run([sys.executable, *map(str,args)],capture_output=True,text=True)
    if p.returncode:
        raise AssertionError(f"Command failed: {args}\nSTDOUT: {p.stdout}\nSTDERR: {p.stderr}")
    return p.stdout


def run():
    total = 0
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)
        for preset, quality in [("traditional","medium"),("lotus","medium"),("stylized","low")]:
            glb = dest / f"{preset}.glb"
            call(GEN,"--preset",ROOT/"assets"/f"{preset}.json","--out",glb)
            report = json.loads(call(QA,glb,"--quality",quality))
            assert report["valid"] and report["triangles"]>1000
            total += 1
        for stage in ["base","leaves","flowers","ceremonial"]:
            glb = dest / f"stage-{stage}.glb"
            call(GEN,"--preset",ROOT/"assets"/"traditional.json","--stage",stage,"--out",glb)
            report = json.loads(call(QA,glb,"--stage",stage))
            assert report["valid"]
            total += 1
        # Verify configuration override path and no-decorations still yield valid GLB.
        config = dest/"override.json"
        config.write_text(json.dumps({"flower_style":"none","candle":False,"incense_count":0,
                                     "amaranth_count":0,"quality":"low"}))
        glb = dest/"bare.glb"
        call(GEN,"--preset",ROOT/"assets"/"traditional.json","--config",config,"--out",glb)
        report=json.loads(call(QA,glb,"--quality","low"))
        assert report["valid"] and report["counts"].get("candles",0)==0
        total += 1
    print(f"PASS: {total} generation + geometry QA cases")


if __name__ == '__main__':
    run()
