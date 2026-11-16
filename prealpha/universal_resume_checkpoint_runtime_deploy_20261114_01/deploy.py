"""Prepare the authorized v0.1.2 install using the verified RD10 rollback."""

import argparse
from hashlib import file_digest, sha256
import importlib.util
import json
from pathlib import Path
import shutil


HERE = Path(__file__).resolve().parent
REPAIR = HERE.parent / "universal_resume_checkpoint_runtime_20261114_01"
PREVIOUS = HERE.parent / "universal_resume_checkpoint_rtti_deploy_20261114_01"
ORIGINAL = HERE.parent / "universal_resume_checkpoint_deploy_20261114_01"
BASELINE = HERE.parent / "resume_dispatcher_rd10_kirk_20261113_01/deployment_01/installed_manifest_01.json"
BASELINE_SHA = "AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8"
PREVIOUS_MANIFEST_SHA = "CF255967641ECA9B80B2267F4A34116FCEAE18A1C1237F2CAF817AE8188E1B98"
GUARD_SHA = "DC8E0B862EAF3CB1E4998E123248B5ED2363684F6DDC0D5E724856587599F9B4"
DRIVER_SHA = "42824D3BDCA9E391AA18EDE416E14CDC430396D00E204071A2E0AA9532734613"
RED4EXT_SHA = "58DDFE43766AA91249D11671B55A8323D5EC017F816D847AFFE4B6201DCD0709"
CANDIDATE = REPAIR / "candidate_05/receipt.json"
CANDIDATE_SHA = "95EB12D92A7400D378855B3F749BD79505E76B1B3B622F0A292F6B7AC0042091"
MANIFEST = HERE / "core_manifest_01.json"
INSTALLER = HERE / "deploy_core.ps1"
DEPLOYMENT = HERE / "deployment_01"
RECOVERY = HERE / "recovery/resume_checkpoint_runtime_01"
EPOCH = "RD10_EXECUTION_CHECKPOINT_RUNTIME"
SCHEMA = "PTFR_RD10_EXECUTION_CHECKPOINT_RUNTIME_CORE_V1"
DLL = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
REDS = "r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds"
LUA = "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua"
CHANGES = {DLL, REDS, LUA}


def sha(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest().upper()


def pinned(path, expected):
    assert sha(path) == expected, path
    return path


def read(path):
    return json.loads(path.read_bytes())


def write(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(data, indent=2) + "\n")


def prepare():
    baseline = read(pinned(BASELINE, BASELINE_SHA))
    predecessor = pinned(PREVIOUS / "core_manifest_01.json", PREVIOUS_MANIFEST_SHA)
    manifest = read(predecessor)
    rollback_path = PREVIOUS / "recovery/resume_checkpoint_rtti_01/journal.json"
    envelope = read(rollback_path)
    payload = envelope["payload_json"]
    assert sha256(payload.encode()).hexdigest().upper() == envelope["payload_sha256"]
    rollback = json.loads(payload)
    assert rollback["state"] == "ROLLED_BACK_VERIFIED" and rollback["manifest_sha256"] == PREVIOUS_MANIFEST_SHA
    assert rollback["save_writes"] == rollback["game_launches"] == 0
    assert (manifest["game_root"], manifest["save_root"]) == (baseline["game_root"], baseline["save_root"])
    assert manifest["predecessor_epoch"] == baseline["core_epoch"] == "RD10_MEET_KIRK_CONTENT_LOCK"
    assert manifest["required_files"] == baseline["required_files"] and len(manifest["required_files"]) == 26

    selected = read(pinned(CANDIDATE, CANDIDATE_SHA))
    compile_receipt = pinned(REPAIR / "compile_02/receipt.json", selected["compile_receipt_sha256"])
    checks_receipt = pinned(REPAIR / "checks_05/results.json", selected["checks_sha256"])
    build_receipt = pinned(REPAIR / "build_01/build.json", selected["build_receipt_sha256"])
    compiled, checks = read(compile_receipt), read(checks_receipt)
    assert compiled["source_count"] == 148 and compiled["staged_sources"][REDS] == selected["files"][REDS]
    assert [len(checks[name]) for name in ("registration_checks", "checkpoint_checks", "lua_checks")] == [15, 41, 12]
    assert len(checks["script_contract"]["removed_native_declarations"]) == 2
    assert not checks["script_contract"]["new_native_declarations"]
    assert checks["script_contract"]["compiled_commit_precedes_gate_acknowledgement"]
    assert selected["archive_sha256"] == baseline["archive_sha256"] and set(selected["files"]) == CHANGES
    native, = (row["sha256"] for row in read(build_receipt) if row["name"] == Path(DLL).name)
    assert selected["files"][DLL] == native

    package = CANDIDATE.parent / "files"
    assert {item.relative_to(package).as_posix() for item in package.rglob("*") if item.is_file()} == CHANGES
    sources = {rel: pinned(package / rel, digest) for rel, digest in selected["files"].items()}
    game = Path(baseline["game_root"])
    core = {row["path"]: row for row in baseline["core_files"]}
    assert len(core) == 51 and set(manifest["changing_paths"]) == CHANGES
    assert {row["path"] for row in manifest["files"]} == {*core, DLL}
    for row in manifest["files"]:
        path = row["path"]
        if path == DLL:
            assert row["before"] is None and not (game / path).exists() and row["after"] != native
        else:
            assert row["before"] == core[path]["sha256"] and row["before_bytes"] == core[path]["bytes"]
            assert pinned(game / path, row["before"]).stat().st_size == row["before_bytes"]
        if path in CHANGES:
            row.update(after=selected["files"][path], after_bytes=sources[path].stat().st_size)
        else:
            assert row["before"] == row["after"] and row["before_bytes"] == row["after_bytes"]
    for row in manifest["required_files"]:
        assert pinned(game / row["path"], row["sha256"]).stat().st_size == row["bytes"]
    inputs = {**compiled["compiler_inputs"], "bin/x64/Cyberpunk2077.exe": checks["native_resolution"]["exe_sha256"],
              "red4ext/RED4ext.dll": RED4EXT_SHA}
    inputs = {str(pinned(game / path, digest)): digest for path, digest in inputs.items()}

    DEPLOYMENT.mkdir(exist_ok=False)
    authorization = DEPLOYMENT / "user_authorization.json"
    write(authorization, {"request": "ok game closed, install pls", "candidate_sha256": CANDIDATE_SHA,
                          "paths": sorted(CHANGES)})
    proofs = [BASELINE, predecessor, rollback_path, CANDIDATE, compile_receipt, checks_receipt, build_receipt, authorization]
    manifest.update(schema=SCHEMA, source_epoch=EPOCH, package_root=str(package),
                    scope="Install execution checkpoint v0.1.2 for the user's Step 2 startup and Manual Save 26 test.",
                    proofs=[{"path": str(path), "sha256": sha(path)} for path in proofs], compile_inputs=inputs)
    write(MANIFEST, manifest)

    guard = pinned(PREVIOUS / "deploy_core.ps1", GUARD_SHA).read_text(encoding="utf-8-sig")
    for before, after in (
        (PREVIOUS_MANIFEST_SHA, sha(MANIFEST)),
        ("PTFR_RD10_EXECUTION_CHECKPOINT_RTTI_REPAIR_CORE_V1", SCHEMA),
        ("$manifest.source_epoch -cne 'RD10_EXECUTION_CHECKPOINT_RTTI_REPAIR'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("recovery/resume_checkpoint_rtti_01", "recovery/resume_checkpoint_runtime_01"),
        ("# Install the checkpoint registration repair with the authorized two replacements and private plugin.",
         "# Install the authorized v0.1.2 checkpoint with two replacements and one private plugin."),
    ):
        assert guard.count(before) == 1, before
        guard = guard.replace(before, after, 1)
    with INSTALLER.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(guard)
    print("Staged v0.1.2 against the exact RD10 rollback and current REDscript inputs.")


def driver():
    previous = pinned(ORIGINAL / "deploy.py", DRIVER_SHA)
    spec = importlib.util.spec_from_file_location("checkpoint_transaction_checks", previous)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("HERE", "BASELINE", "BASELINE_SHA", "CANDIDATE", "CANDIDATE_SHA", "MANIFEST", "INSTALLER",
                 "DEPLOYMENT", "RECOVERY", "EPOCH"):
        setattr(module, name, globals()[name])
    return module


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "fixtures", "record"))
    parser.add_argument("--powershell", default=shutil.which("pwsh") or "pwsh")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    elif args.action == "fixtures":
        driver().fixtures(args.powershell)
    else:
        driver().record()
