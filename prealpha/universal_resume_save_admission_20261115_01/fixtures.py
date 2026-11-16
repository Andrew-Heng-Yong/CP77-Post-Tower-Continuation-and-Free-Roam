"""Exercise the single-DLL guarded install on isolated synthetic game trees.

Writes only fresh fixtures/, fixture_results.json, scope_review.json and
readiness.json under this successor directory. Never touches the live game.
"""

from copy import deepcopy
from hashlib import file_digest
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "core_manifest_01.json"
INSTALLER = HERE / "deploy_core.ps1"
DLL = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
CHANGES = [DLL]
ROOT = HERE / "fixtures/deployment_01"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest().upper()


def write(path: Path, value) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def run() -> None:
    assert not ROOT.exists(), "fresh fixture root required"
    manifest = json.loads(MANIFEST.read_bytes())
    assert manifest["changing_paths"] == CHANGES
    cases = {
        "rollback": [("Install", "INSTALLED_VERIFIED", []), ("Verify", "VERIFIED_AFTER", []),
                     ("ValidateRollback", "ROLLBACK_READY", []), ("Rollback", "ROLLED_BACK_VERIFIED", []),
                     ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
        "crash_stage": [("Install", 72, ["-FailurePoint", "CrashAfterStage"]),
                        ("Recover", "RECOVERED_BEFORE", []),
                        ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
        "crash_replace": [("Install", 72, ["-FailurePoint", "CrashAfterFirstReplace"]),
                          ("Recover", "RECOVERED_BEFORE", []),
                          ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
        "exception_replace": [("Install", 1, ["-FailurePoint", "AfterFirstReplace"]),
                              ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
        "game_running": [("Install", 1, ["-FixtureProcesses", "Cyberpunk2077"])],
        "target_drift": [("Install", 1, [])],
    }
    ROOT.mkdir(parents=True, exist_ok=False)
    results = []
    for name, steps in cases.items():
        folder = ROOT / name
        game, saves, package = (folder / part for part in ("game", "saves", "package"))
        current = deepcopy(manifest)
        current.update(game_root=str(game), save_root=str(saves), package_root=str(package),
                       proofs=[], compile_inputs={})
        for row in current["files"]:
            target = game / row["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(("fixture before " + row["path"]).encode())
            row.update(before=sha(target), before_bytes=target.stat().st_size)
            if row["path"] in CHANGES:
                staged = package / row["path"]
                staged.parent.mkdir(parents=True, exist_ok=True)
                staged.write_bytes(("fixture native save guard " + row["path"]).encode())
                row.update(after=sha(staged), after_bytes=staged.stat().st_size)
            else:
                row.update(after=row["before"], after_bytes=row["before_bytes"])
        for row in current["required_files"]:
            target = game / row["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(row["path"].encode())
            row.update(sha256=sha(target), bytes=target.stat().st_size)
        save = saves / "FixtureSave/sav.dat"
        save.parent.mkdir(parents=True)
        save.write_bytes(b"original fixture save")
        external = game / "external/keep.dat"
        external.parent.mkdir()
        external.write_bytes(b"unrelated mod")
        if name == "target_drift":
            (game / DLL).write_bytes(b"unknown DLL from another update")
        fixture = folder / "manifest.json"
        write(fixture, current)
        for action, expected, flags in steps:
            command = ["pwsh", "-NoProfile", "-File", str(INSTALLER), "-Action", action,
                       "-FixtureRoot", str(folder), "-FixtureManifest", str(fixture),
                       "-FixtureManifestSHA", sha(fixture), *flags]
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", timeout=90, creationflags=subprocess.CREATE_NO_WINDOW)
            if isinstance(expected, int):
                assert result.returncode == expected, (name, action, result.stdout, result.stderr)
                status = None
            else:
                assert result.returncode == 0, (name, action, result.stdout, result.stderr)
                status = json.loads(result.stdout)["status"]
                assert status == expected, (name, action, status)
            results.append({"fixture": name, "action": action, "status": status,
                            "returncode": result.returncode})
        for row in current["files"]:
            target = game / row["path"]
            expected = b"unknown DLL from another update" if name == "target_drift" and row["path"] == DLL else None
            assert (target.read_bytes() == expected if expected is not None else sha(target) == row["before"])
        for row in current["required_files"]:
            assert sha(game / row["path"]) == row["sha256"]
        assert save.read_bytes() == b"original fixture save"
        assert external.read_bytes() == b"unrelated mod"
        assert not list((folder / "recovery").rglob("*.dll.tmp"))
        assert not list((folder / "recovery/core/stage").rglob("*.dll"))
        if name in ("game_running", "target_drift"):
            assert not (folder / "recovery").exists()
    results_path = HERE / "fixture_results.json"
    scope_path = HERE / "scope_review.json"
    write(results_path, {"status": "PASS", "actions": results})
    write(scope_path, {"scope": manifest["scope"], "changed_paths": CHANGES,
                       "candidate_sha256": sha(HERE / "run_01/PTFR_ExecutionCheckpoint.dll"),
                       "predecessor_installed_manifest_sha256": sha(HERE.parent /
                         "universal_resume_checkpoint_probe_20261114_01/deployment_01/installed_manifest_01.json"),
                       "gameplay": "PENDING_MS26_SAVE_ADMISSION_SMOKE_TEST"})
    write(HERE / "readiness.json", {"status": "READY_NOT_INSTALLED", "manifest_sha256": sha(MANIFEST),
                                    "installer_sha256": sha(INSTALLER),
                                    "fixture_result": results_path.name,
                                    "fixture_result_sha256": sha(results_path),
                                    "scope_review": scope_path.name,
                                    "scope_review_sha256": sha(scope_path)})
    print(f"Passed {len(results)} isolated deployment and recovery actions.")


if __name__ == "__main__":
    run()
