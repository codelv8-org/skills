import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def main():
    root = Path(__file__).resolve().parents[1]
    catalog = json.loads((root / "data/skills.json").read_text(encoding="utf-8"))
    downloads = root / "downloads"
    downloads.mkdir(exist_ok=True)

    seen = set()
    for skill in catalog["skills"]:
        skill_id = skill["id"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_id) or skill_id in seen:
            raise ValueError(f"Invalid or duplicate skill ID: {skill_id}")
        seen.add(skill_id)

        source = root / "skills" / skill_id
        if skill["path"] != f"skills/{skill_id}" or not (source / "SKILL.md").is_file():
            raise ValueError(f"Missing or invalid skill directory: {source}")

        files = sorted(path for path in source.rglob("*") if path.is_file())
        if any(not path.resolve().is_relative_to(source) for path in files):
            raise ValueError(f"Skill file points outside its directory: {source}")

        archive_path = downloads / f"{skill_id}.zip"
        with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, path.relative_to(source.parent).as_posix())
        print(f"{archive_path.relative_to(root).as_posix()} ({len(files)} files)")


if __name__ == "__main__":
    main()
