"""Fail-closed evidence integrity checker; not artistic or engine approval."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, BadZipFile

ROLES = {
    "G0": "reference inventory capabilities",
    "G1": "design_brief blockout_views silhouette_review",
    "G2": "clay_views anatomy_review part_comparison",
    "G3": "garment_clay layer_review bent_pose",
    "G4": "hair_review armor_review assembly_views",
    "G5": "wireframe topology_report deformation_trial",
    "G6": "uv_layout uv_checker density_report",
    "G7": "bake_settings map_review seam_review",
    "G8": "material_views albedo lighting_review",
    "G9": "rig_review deformation_review clip_review",
    "G10": "export_review engine_review runtime_report",
    "G11": "final_views final_comparison release_review",
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
    candidate = artifact(root, data.get("candidate"))
    paths = [candidate] + [artifact(root, p) for p in files.values()]
    if len(set(paths)) != len(paths) or any(p.parent == root / "evidence" and p.name in {f"{g}.json" for g in ROLES} for p in paths):
        raise ValueError(f"{stage}: reused path or gate record as artifact")
    if stage == "G11":
        if candidate.suffix.lower() != ".zip":
            raise ValueError("G11: candidate must be exact delivery ZIP")
        with ZipFile(candidate) as archive:
            names = archive.namelist()
            if not names or len(names) != len(set(names)):
                raise ValueError("G11: empty or duplicate ZIP entries")
            if any(n.startswith(('/', '\\')) or '\\' in n or ':' in n or '..' in n.split('/') or n.endswith('evidence/G11.json') for n in names):
                raise ValueError("G11: unsafe or circular ZIP entry")
    review = json.dumps({k: v for k, v in data.items() if k != "seal"}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {"review_sha256": hashlib.sha256(review.encode("utf-8")).hexdigest(), "candidate_sha256": digest(candidate), "evidence_sha256": {k: digest(artifact(root, v)) for k, v in files.items()}, "previous_record_sha256": previous}


def run(root, seal=None):
    root = Path(root).resolve()
    if seal is not None and seal not in ROLES:
        raise ValueError("unknown stage")
    previous = None
    for stage in ROLES:
        p = artifact(root, f"evidence/{stage}.json")
        d = json.loads(p.read_text(encoding="utf-8"))
        want = expected(root, stage, d, previous)
        if stage == seal:
            d["seal"] = want
            tmp = p.with_suffix(".tmp")
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
    except (ValueError, OSError, TypeError, KeyError, BadZipFile) as e:
        print(f"BLOCKED: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
