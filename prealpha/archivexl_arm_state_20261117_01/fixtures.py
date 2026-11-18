"""Verify the scoped ArchiveXL transaction with copies in isolated directories."""

import copy
import json
import shutil
import subprocess
import sys

from prepare import GAME, WORK, read, safe, sha, write


INSTALLER = WORK / "install.ps1"
MANIFEST = WORK / "tool_manifest_01.json"
RESULTS = []


def fixture(name, manifest):
    root = WORK / "fixtures" / name
    root.mkdir(parents=True, exist_ok=False)
    game = root / "game"
    saves = root / "saves"
    save = saves / "ManualSave-1/sav.dat"
    save.parent.mkdir(parents=True)
    save.write_bytes(b"saved before ArchiveXL update")
    for item in manifest["files"]:
        target = safe(game, item["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe(GAME, item["path"]), target)
        if sha(target) != item["before"]:
            raise RuntimeError(f"Fixture input changed: {item['path']}")
    external = game / "external.mod"
    external.write_bytes(b"external mod fixture")
    scoped = copy.deepcopy(manifest)
    scoped.update(game_root=str(game), save_root=str(saves), compile_inputs={}, proofs=[], zip=None,
                  required_files=[{"path": "external.mod", "bytes": external.stat().st_size,
                                   "sha256": sha(external), "active_only": False}])
    write(root / "manifest.json", scoped)
    return root


def run(powershell, root, action, *options, exit_code=0, status):
    manifest = root / "manifest.json"
    command = [powershell, "-NoProfile", "-File", str(INSTALLER), "-Action", action,
               "-FixtureRoot", str(root), "-FixtureManifest", str(manifest),
               "-FixtureManifestSHA", sha(manifest), *options]
    result = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace",
                            timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
    record = {"fixture": root.name, "action": action, "options": options, "exit_code": result.returncode,
              "stdout": result.stdout, "stderr": result.stderr}
    RESULTS.append(record)
    if result.returncode != exit_code or status not in result.stdout + result.stderr:
        raise RuntimeError(json.dumps(record))


def verify_fixture(root, rows, side):
    game = root / "game"
    for item in rows:
        if sha(safe(game, item["path"])) != item[side]:
            raise RuntimeError(f"Fixture file readback failed: {item['path']}")
    if (game / "external.mod").read_bytes() != b"external mod fixture":
        raise RuntimeError("Fixture external mod changed")
    if (root / "saves/ManualSave-1/sav.dat").read_bytes() != b"saved before ArchiveXL update":
        raise RuntimeError("Fixture save changed")


def main(powershell):
    manifest = read(MANIFEST)
    clean = fixture("round_trip", manifest)
    run(powershell, clean, "Install", status="INSTALLED_VERIFIED")
    verify_fixture(clean, manifest["files"], "after")
    run(powershell, clean, "ValidateRollback", status="ROLLBACK_READY")
    run(powershell, clean, "Rollback", status="ROLLED_BACK_VERIFIED")
    verify_fixture(clean, manifest["files"], "before")

    interrupted = fixture("interrupted_after_second_file", manifest)
    run(powershell, interrupted, "Install", "-FailurePoint", "CrashAfterSecondReplace",
        exit_code=72, status="")
    replaced = [item["path"] for item in manifest["files"] if item["before"] != item["after"]][:2]
    for item in manifest["files"]:
        expected = item["after"] if item["path"] in replaced else item["before"]
        if sha(safe(interrupted / "game", item["path"])) != expected:
            raise RuntimeError(f"Expected a partial replacement: {item['path']}")
    run(powershell, interrupted, "Recover", status="RECOVERED_BEFORE")
    verify_fixture(interrupted, manifest["files"], "before")

    running = fixture("game_running", manifest)
    run(powershell, running, "Install", "-FixtureProcesses", "Cyberpunk2077",
        exit_code=1, status="must be closed naturally")
    verify_fixture(running, manifest["files"], "before")

    result = WORK / "fixture_results.json"
    scope = WORK / "scope_review.json"
    write(result, {"status": "PASS", "cases": 3, "results": RESULTS, "game_writes": 0})
    write(WORK / "readiness.json", {"status": "READY_NOT_INSTALLED", "manifest_sha256": sha(MANIFEST),
          "installer_sha256": sha(INSTALLER), "fixture_result": result.name,
          "fixture_result_sha256": sha(result), "scope_review": scope.name, "scope_review_sha256": sha(scope)})
    print("ArchiveXL install, rollback, interruption recovery, and running-game guard passed.")


if __name__ == "__main__":
    main(sys.argv[1])
