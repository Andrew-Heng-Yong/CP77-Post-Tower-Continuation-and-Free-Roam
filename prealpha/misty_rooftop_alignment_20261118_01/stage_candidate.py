"""Stage the 51-file installation and verify the current external archive environment."""

from pathlib import Path
import shutil
import sys

import placement

sys.path.insert(0, str(placement.SEAT))
from build import EXE, EXE_SHA, GAME, read, row, safe, sha, verify_rows, write
from deploy import archive_environment


def main():
    placement.verify_packed()
    base = read(placement.BASE)
    dependencies = base["required_files"] + base["archivexl_files"] + base["ifp_files"]
    verify_rows(GAME, base["core_files"] + dependencies)
    assert sha(safe(GAME, EXE)) == EXE_SHA
    prior_plan = Path(base["installation_plan"])
    assert sha(prior_plan) == base["installation_plan_sha256"]
    assert archive_environment(GAME) == read(prior_plan)["archive_environment"]
    proof_path = placement.ASSETS / "readback.json"
    proof = read(proof_path)
    assert proof["baseline_sha256"] == placement.BASE_HASH and proof["scene_depot"] == placement.DEPOT
    assert proof["status"] == "MEMBERS_VERIFIED" and (proof["checked_members"], proof["preserved_members"]) == (1751, 1750)
    assert proof["packed_json_sha256"] == sha(placement.ASSETS / "packed.scene.json")
    assert proof["changed_member"]["after"] == sha(placement.ASSETS / "packed.scene")
    archive = placement.ARCHIVE
    assert proof["package_file"] == row(placement.ASSETS / "package", archive)
    candidate = placement.ROOT / "candidate_01"
    package = candidate / "package"
    package.mkdir(parents=True, exist_ok=False)
    for old in base["core_files"]:
        rel = old["path"]
        dest = safe(package, rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe(placement.ASSETS / "package" if rel == archive else GAME, rel), dest)
    rows = [row(package, r["path"]) for r in base["core_files"]]
    expected = [proof["package_file"] if r["path"] == archive else r for r in base["core_files"]]
    assert rows == expected and len(rows) == 51 and rows != base["core_files"]
    verify_rows(GAME, base["core_files"])
    write(candidate / "core_manifest.json", {
        "status": "STAGED_OFFLINE", "baseline_sha256": placement.BASE_HASH,
        "core_files": rows, "changed_paths": [archive], "asset_assessment_sha256": sha(proof_path),
        "changed_scene": placement.DEPOT, "preserved_archive_members": 1750, "gameplay": "PENDING"})
    print("Staged the verified chair placement in the full 51-file payload.")


if __name__ == "__main__":
    main()
