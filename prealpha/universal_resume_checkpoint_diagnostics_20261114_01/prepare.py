"""Stage a DLL-only diagnostic successor over the exact installed v0.1.2 build.

Writes only candidate_01 and core_manifest_01.json in this fresh workspace.
"""

from copy import deepcopy
from hashlib import file_digest
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "universal_resume_checkpoint_runtime_deploy_20261114_01"
INSTALLED = PREVIOUS / "deployment_01/installed_manifest_01.json"
INSTALLED_SHA = "96C3D0F463FECD7953B2924927E36D358C3219042B8840657E4D8AC9071260E2"
PREVIOUS_CORE = PREVIOUS / "core_manifest_01.json"
DLL = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
REDS = "r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds"
LUA = "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua"
SOURCE = HERE / "source_01/receipt.json"
BUILD = HERE / "build_02/build.json"
CHECKS = HERE / "checks_01/results.json"
BUILT_DLL = HERE / "build_02/PTFR_ExecutionCheckpoint.dll"
CANDIDATE = HERE / "candidate_01"
MANIFEST = HERE / "core_manifest_01.json"
SCHEMA = "PTFR_RD10_EXECUTION_CHECKPOINT_DIAGNOSTICS_CORE_V1"
EPOCH = "RD10_EXECUTION_CHECKPOINT_DIAGNOSTICS"
SCOPE = "Replace only the checkpoint DLL with v0.1.3 diagnostics for the Reed cutoff capture failure."


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest().upper()


def read(path: Path):
    return json.loads(path.read_bytes())


def write(path: Path, value) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def pinned(path: Path, digest: str) -> Path:
    assert sha(path) == digest, path
    return path


def prepare() -> None:
    assert not CANDIDATE.exists() and not MANIFEST.exists(), "fresh candidate required"
    installed = read(pinned(INSTALLED, INSTALLED_SHA))
    previous = read(PREVIOUS_CORE)
    source = read(SOURCE)
    build = read(BUILD)
    checks = read(CHECKS)
    assert installed["core_epoch"] == previous["source_epoch"] == "RD10_EXECUTION_CHECKPOINT_RUNTIME"
    assert len(installed["core_files"]) == 51 and len(installed["companion_files"]) == 1
    assert len(installed["required_files"]) == 26 and installed["companion_files"][0]["path"] == DLL
    assert checks["checkpoint_exit"] == checks["registration_exit"] == 0
    assert checks["checkpoint_pass_count"] == 46 and checks["registration_pass_count"] == 15
    assert checks["checkpoint_failure_count"] == checks["registration_failure_count"] == 0
    assert checks["dll_sha256"] == sha(BUILT_DLL)
    for name, digest in source["sources"].items():
        location = HERE / ("source_01" if name in
                           ("NativeCheckpoint.cpp", "Checkpoint.hpp", "CheckpointChecks.cpp",
                            "PTFR_HistorySnapshotHS1.reds") else "") / name
        pinned(location, digest)
    build_files = {row["name"]: row["sha256"] for row in build}
    assert build_files["NativeCheckpoint.cpp"] == source["sources"]["NativeCheckpoint.cpp"]
    assert build_files["PTFR_ExecutionCheckpoint.dll"] == checks["dll_sha256"]

    game = Path(installed["game_root"])
    managed = {row["path"]: row for row in installed["core_files"] + installed["companion_files"]}
    assert len(managed) == 52 and managed[DLL]["sha256"] != checks["dll_sha256"]
    for row in managed.values():
        target = pinned(game / row["path"], row["sha256"])
        assert target.stat().st_size == row["bytes"]
    for row in installed["required_files"]:
        target = pinned(game / row["path"], row["sha256"])
        assert target.stat().st_size == row["bytes"]
    assert managed[REDS]["sha256"] == source["sources"]["PTFR_HistorySnapshotHS1.reds"]
    assert managed[LUA]["sha256"] == previous["files"][next(i for i, row in
           enumerate(previous["files"]) if row["path"] == LUA)]["after"]

    compile_inputs = {}
    for path in previous["compile_inputs"]:
        current = Path(path)
        assert current.is_file(), current
        compile_inputs[path] = sha(current)
    old_reds = {path for path in previous["compile_inputs"] if path.lower().endswith(".reds")}
    live_reds = {str(path) for branch in ("r6/scripts", "red4ext/plugins")
                 for path in (game / branch).rglob("*.reds")}
    assert len(old_reds) == 148 and {p.lower() for p in old_reds} == {p.lower() for p in live_reds}
    assert compile_inputs[str(game / REDS)] == managed[REDS]["sha256"]

    package = CANDIDATE / "files" / DLL
    package.parent.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(BUILT_DLL, package)
    assert sha(package) == checks["dll_sha256"]
    receipt = {
        "status": "DIAGNOSTIC_CANDIDATE_NOT_INSTALLED",
        "predecessor_installed_manifest": str(INSTALLED),
        "predecessor_installed_manifest_sha256": INSTALLED_SHA,
        "changed_paths": [DLL],
        "before_sha256": managed[DLL]["sha256"],
        "after_sha256": sha(package),
        "after_bytes": package.stat().st_size,
        "unchanged_history_sha256": managed[REDS]["sha256"],
        "unchanged_lua_sha256": managed[LUA]["sha256"],
        "source_receipt_sha256": sha(SOURCE),
        "build_receipt_sha256": sha(BUILD),
        "checks_sha256": sha(CHECKS),
        "live_capture_verified": False,
    }
    write(CANDIDATE / "receipt.json", receipt)

    manifest = deepcopy(previous)
    manifest.update(schema=SCHEMA, source_epoch=EPOCH,
                    predecessor_epoch="RD10_EXECUTION_CHECKPOINT_RUNTIME", scope=SCOPE,
                    package_root=str(CANDIDATE / "files"), changing_paths=[DLL],
                    zip="", zip_sha256="", compile_inputs=compile_inputs)
    for row in manifest["files"]:
        exact = managed[row["path"]]
        row.update(before=exact["sha256"], before_bytes=exact["bytes"],
                   after=exact["sha256"], after_bytes=exact["bytes"])
        if row["path"] == DLL:
            row.update(after=receipt["after_sha256"], after_bytes=receipt["after_bytes"])
    assert len(manifest["files"]) == 52
    assert [row["path"] for row in manifest["files"] if row["before"] != row["after"]] == [DLL]
    assert manifest["required_files"] == previous["required_files"]
    manifest["proofs"] = [{"path": str(path), "sha256": sha(path)} for path in
                          (INSTALLED, SOURCE, BUILD, CHECKS, CANDIDATE / "receipt.json")]
    write(MANIFEST, manifest)
    print("Staged one-file diagnostic candidate against all 52 installed paths and 26 dependencies.")


if __name__ == "__main__":
    prepare()
