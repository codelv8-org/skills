#!/usr/bin/env python3
"""Execute only reviewed bundled synthetic tests; no Agent, user input, or API key."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SUITES={
    "webapp-quotation-builder": ["scripts/test_pricing.py"],
    "privacy-first-database-documentation-builder": ["scripts/test_dictionary.py"],
    "photoreal-head-web": ["tests/test_anatomy_tools.py","tests/test_surface_tools.py","tests/test_projection_tools.py","tests/test_robust_blend.py"],
    "lowpoly-character-web": ["tests/test_reference_and_budget.py","tests/test_skill_tools.py"],
    "thai-krathong-3d": ["scripts/smoke_test.py"],
}
def main():
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    result={}
    for skill,files in SUITES.items():
        records=[]
        with tempfile.TemporaryDirectory(prefix="skill-benchmark-") as t:
            tmp=Path(t); home=tmp/"home"; home.mkdir()
            src=ROOT/"skills"/skill; work=tmp/"skill"
            shutil.copytree(src,work,ignore=shutil.ignore_patterns("__pycache__",".git","node_modules"),symlinks=True)
            env={"PATH":os.environ.get("PATH",""),"HOME":str(home),"TMPDIR":str(tmp),"LANG":"C.UTF-8","PYTHONUTF8":"1","PYTHONDONTWRITEBYTECODE":"1"}
            for file in files:
                script=work/file; started=time.monotonic()
                if not script.is_file() or not script.resolve().is_relative_to(work.resolve()):
                    records.append({"suite":file,"status":"not_run","tests":None,"durationMs":0});continue
                try:
                    proc=subprocess.run([sys.executable,str(script)],cwd=work,env=env,capture_output=True,text=True,errors="replace",timeout=120)
                    found=re.search(r"Ran (\d+) tests? in",proc.stdout+"\n"+proc.stderr)
                    status="pass" if proc.returncode==0 else "fail"
                    tests=int(found.group(1)) if found else None
                except subprocess.TimeoutExpired:
                    status="timeout";tests=None
                records.append({"suite":file,"status":status,"tests":tests,"durationMs":round((time.monotonic()-started)*1000)})
        result[skill]={"status":"pass" if all(r["status"]=="pass" for r in records) else "incomplete" if any(r["status"]=="not_run" for r in records) else "fail","suites":records}
        print(skill+": "+result[skill]["status"]+" ("+str(sum(r["status"]=="pass" for r in records))+"/"+str(len(records))+" suites)")
    payload={"schemaVersion":1,"sourceCommit":commit,"skills":result,"method":"allowlisted-synthetic-tool-tests-v1"}
    (ROOT/"data"/"skill-tool-benchmarks.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
