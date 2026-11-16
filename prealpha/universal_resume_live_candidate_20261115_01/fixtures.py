"""Exercise the successor transaction on fresh, isolated Windows file trees."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess

from candidate_common import TARGET, digest, payload_path, require, write_json


CASES = {
    "rollback": [("Install", "INSTALLED_VERIFIED", []), ("Verify", "VERIFIED_AFTER", []),
                 ("ValidateRollback", "ROLLBACK_READY", []), ("Rollback", "ROLLED_BACK_VERIFIED", []),
                 ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
    "crash_stage": [("Install", 72, ["-FailurePoint", "CrashAfterStage"]), ("Recover", "RECOVERED_BEFORE", []),
                    ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
    "crash_replace": [("Install", 72, ["-FailurePoint", "CrashAfterFirstReplace"]),
                      ("Recover", "RECOVERED_BEFORE", []), ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
    "exception_replace": [("Install", 1, ["-FailurePoint", "AfterFirstReplace"]),
                          ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
    "game_running": [("Install", 1, ["-FixtureProcesses", "Cyberpunk2077"])],
    "target_drift": [("Install", 1, [])],
    "staged_drift": [("Install", 1, [])],
    "working_save_drift": [("Install", 1, [])],
}
REJECTED = {
    "game_running": "must be closed naturally",
    "target_drift": "Hash drift:",
    "staged_drift": "Hash drift:",
    "working_save_drift": "Hash drift:",
}


def fixture_inputs(stage, name, manifest):
    folder = stage / "fixtures/deployment_01" / name
    game, saves, package = (folder / part for part in ("game", "saves", "package"))
    current = deepcopy(manifest)
    current.update(game_root=str(game), save_root=str(saves), package_root=str(package),
                   proofs=[], compile_inputs={}, protected_saves=[], working_save_files=[])
    for row in current["files"]:
        file = payload_path(game, row["path"])
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(f"fixture before {row['path']}".encode())
        row.update(before=digest(file), before_bytes=file.stat().st_size)
        if row["path"] == TARGET:
            staged = payload_path(package, row["path"])
            staged.parent.mkdir(parents=True)
            staged.write_bytes(f"fixture candidate {row['path']}".encode())
            row.update(after=digest(staged), after_bytes=staged.stat().st_size)
        else:
            row.update(after=row["before"], after_bytes=row["before_bytes"])
    for row in current["required_files"]:
        file = payload_path(game, row["path"])
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(row["path"].encode())
        row.update(sha256=digest(file), bytes=file.stat().st_size)
    save = saves / "ManualSave-31/sav.dat"
    save.parent.mkdir(parents=True)
    save.write_bytes(b"original fixture save")
    current["working_save_files"] = [{"path": "ManualSave-31/sav.dat", "bytes": save.stat().st_size,
                                     "sha256": digest(save)}]
    unrelated = game / "external/keep.dat"
    unrelated.parent.mkdir()
    unrelated.write_bytes(b"unrelated mod")
    if name == "target_drift":
        payload_path(game, TARGET).write_bytes(b"unknown DLL from another update")
    if name == "staged_drift":
        payload_path(package, TARGET).write_bytes(b"unknown staged replacement")
    if name == "working_save_drift":
        save.write_bytes(b"newer fixture save")
    fixture = folder / "manifest.json"
    write_json(fixture, current)
    return folder, fixture, current


def assert_preserved(name, folder, current):
    game, saves = (Path(current[key]) for key in ("game_root", "save_root"))
    for row in current["files"]:
        file = payload_path(game, row["path"])
        if name == "target_drift" and row["path"] == TARGET:
            require(file.read_bytes() == b"unknown DLL from another update", "Changed drifted file")
        else:
            require(digest(file) == row["before"], f"Wrong recovered byte state: {file}")
    for row in current["required_files"]:
        require(digest(payload_path(game, row["path"])) == row["sha256"], f"Changed dependency: {row['path']}")
    expected_save = b"newer fixture save" if name == "working_save_drift" else b"original fixture save"
    require((saves / "ManualSave-31/sav.dat").read_bytes() == expected_save, "Changed save fixture")
    require((game / "external/keep.dat").read_bytes() == b"unrelated mod", "Changed unrelated fixture")
    require(not list((folder / "recovery/core/stage").rglob("*.dll")), "Left a staged DLL after recovery")
    if name in REJECTED:
        require(not (folder / "recovery").exists(), "Rejected action wrote a recovery payload")


def exercise(stage, manifest):
    installer = stage / "deploy_core.ps1"
    actions = []
    for name, steps in CASES.items():
        folder, fixture, current = fixture_inputs(stage, name, manifest)
        fixture_sha = digest(fixture)
        for index, (action, expected, flags) in enumerate(steps, 1):
            result = subprocess.run(["pwsh", "-NoProfile", "-File", str(installer), "-Action", action,
                                     "-FixtureRoot", str(folder), "-FixtureManifest", str(fixture),
                                     "-FixtureManifestSHA", fixture_sha, *flags], capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=60,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            (folder / f"{index:02}_{action}.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
            if isinstance(expected, int):
                require(result.returncode == expected, f"Unexpected exit: {name} {action} {result.stderr}")
                if name in REJECTED:
                    require(REJECTED[name] in result.stderr, f"Wrong rejection reason: {name} {result.stderr}")
                status = "INTERRUPTED" if expected == 72 else "REFUSED"
            else:
                require(result.returncode == 0, f"Fixture failed: {name} {action} {result.stderr}")
                status = json.loads(result.stdout)["status"]
                require(status == expected, f"Unexpected fixture status: {name} {action} {status}")
            actions.append({"fixture": name, "action": action, "status": status, "returncode": result.returncode})
        assert_preserved(name, folder, current)
    summary = {"status": "PASS", "fixture_trees": len(CASES), "actions": actions, "game_runtime_exercised": False}
    write_json(stage / "fixture_results.json", summary)
    print(f"Passed {len(actions)} installer actions across {len(CASES)} isolated fixtures.")
    return summary
