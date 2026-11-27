"""Fail-closed evidence integrity checker, not an artist or identity verifier."""
import argparse
import hashlib
import json
from pathlib import Path

ROLES = {
    "G0": "reference inventory capabilities",
    "G1": "clay anatomy comparison",
    "G2": "garment_clay garment_review bent_pose",
    "G3": "gear_clay inventory_match integration_review",
    "G4": "wireframe uv_checker bake_review",
    "G5": "material_views albedo normal_review lighting_review",
    "G6": "export_review deformation_review runtime_review",
    "G7": "final_views final_comparison release_review",
}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def artifact(root, rel):
    if not isinstance(rel, str) or not rel or Path(rel).is_absolute():
        raise ValueError("expected relative project path")
    p = (root / rel).resolve()
    if not p.is_relative_to(root) or not p.is_file() or p.stat().st_size == 0:
        raise ValueError(f"missing, empty or unsafe artifact: {rel}")
    return p


def record(root, stage):
    return artifact(root, f"evidence/{stage}.json")


def expected(root, stage, data, previous):
    if not isinstance(data, dict) or data.get("stage") != stage or data.get("decision") != "PASS":
        raise ValueError(f"{stage}: missing PASS review")
    for key in ("author", "reviewer", "findings"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"{stage}: missing {key}")
    if data["author"].strip().casefold() == data["reviewer"].strip().casefold():
        raise ValueError(f"{stage}: reviewer must differ from author")
    if data.get("reviewer_type") not in ("HUMAN", "AI"):
        raise ValueError(f"{stage}: reviewer type must be declared")
    files = data.get("evidence")
    if not isinstance(files, dict) or not set(ROLES[stage].split()).issubset(files):
        raise ValueError(f"{stage}: required evidence roles missing")
    paths = [artifact(root, data.get("candidate"))] + [artifact(root, p) for p in files.values()]
    if len(set(paths)) != len(paths) or record(root, stage) in paths:
        raise ValueError(f"{stage}: reuse/self-reference in evidence paths")
    review = json.dumps({k: v for k, v in data.items() if k != "seal"}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {"review_sha256": hashlib.sha256(review.encode("utf-8")).hexdigest(), "candidate_sha256": digest(paths[0]), "evidence_sha256": {k: digest(artifact(root, v)) for k, v in files.items()}, "previous_record_sha256": previous}


def run(root, seal=None):
    root = Path(root).resolve()
    previous = None
    for stage in ROLES:
        p = record(root, stage)
        d = json.loads(p.read_text(encoding="utf-8"))
        want = expected(root, stage, d, previous)
        if stage == seal:
            d["seal"] = want
            tmp = p.with_suffix(".tmp")
            if tmp.exists() or tmp.is_symlink():
                raise ValueError(f"temporary path already exists: {tmp}")
            with tmp.open("x", encoding="utf-8") as f:
                f.write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
            tmp.replace(p)
            return f"{stage} SEALED; independent review still required"
        if d.get("seal") != want:
            raise ValueError(f"{stage}: missing/stale seal")
        previous = digest(p)
    return "PASS_EVIDENCE_INTEGRITY_ONLY"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("seal", "check"))
    parser.add_argument("project", type=Path)
    parser.add_argument("stage", choices=tuple(ROLES), nargs="?")
    a = parser.parse_args()
    if (a.command == "seal") != (a.stage is not None):
        parser.error("seal requires stage; check does not accept stage")
    try:
        print(run(a.project, a.stage))
    except (ValueError, OSError, TypeError, KeyError) as e:
        print(f"BLOCKED: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
