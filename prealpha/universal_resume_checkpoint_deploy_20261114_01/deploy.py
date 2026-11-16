"""Prepare, test and record a guarded deployment of checkpoint candidate 02."""

import argparse
from copy import deepcopy
from hashlib import file_digest, sha256
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
RD10 = HERE.parent / "resume_dispatcher_rd10_kirk_20261113_01"
CHECKPOINT = HERE.parent / "universal_resume_checkpoint_20261114_01"
BASELINE = RD10 / "deployment_01/installed_manifest_01.json"
BASELINE_SHA = "AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8"
GUARD = RD10 / "deploy_core.ps1"
GUARD_SHA = "09A3BBFF589DEAA81C2B4BC09367A8B087AE96C50663659EB93F10F3FE174214"
RD10_TRANSACTION_SHA = "55B78AA7FEF57BE7628B8D3AFD5C4058EC9016D269638ACCD9E2E0F9B362C0B9"
CANDIDATE = CHECKPOINT / "candidate_02/receipt.json"
CANDIDATE_SHA = "3D908EA14BB18926418F07BF64780C7533C0ED91080AD1AEE7411B8804BA0EE6"
EXE = "bin/x64/Cyberpunk2077.exe"
EXE_SHA = "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4"
BEFORE = "RD10_MEET_KIRK_CONTENT_LOCK"
EPOCH = "RD10_EXECUTION_CHECKPOINT"
SCHEMA = "PTFR_RD10_EXECUTION_CHECKPOINT_CORE_V1"
REDS = "r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds"
LUA = "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua"
DLL = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
CHANGES = {REDS, LUA, DLL}
MANIFEST = HERE / "core_manifest_01.json"
INSTALLER = HERE / "deploy_core.ps1"
DEPLOYMENT = HERE / "deployment_01"
RECOVERY = HERE / "recovery/resume_checkpoint_01"


def sha(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest().upper()


def read(path):
    return json.loads(path.read_bytes())


def write(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(data, indent=2) + "\n")


def pinned(path, expected):
    assert sha(path) == expected, path
    return path


def build_guard():
    base = pinned(GUARD, GUARD_SHA).read_text(encoding="utf-8-sig")
    old_scope = """$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive')
if($manifest.files.Count -ne 51 -or $changes.Count -ne 1 -or @($manifest.files|Where-Object {$null -eq $_.before}).Count -or (@($changes.path|Sort-Object)-join ',') -cne (@($wanted|Sort-Object)-join ',')){throw 'Core51/archive-only Meet Kirk scope drift'}"""
    new_scope = (
        f"$wanted=@('{LUA}','{REDS}','{DLL}')\n"
        "$additions=@($manifest.files|Where-Object {$null -eq $_.before})\n"
        "if($manifest.files.Count -ne 52 -or $manifest.required_files.Count -ne 26 -or $changes.Count -ne 3 "
        f"-or $additions.Count -ne 1 -or $additions[0].path -cne '{DLL}' "
        "-or (@($changes.path|Sort-Object)-join ',') -cne (@($wanted|Sort-Object)-join ','))"
        "{throw 'Execution checkpoint deployment scope drift'}"
    )
    edits = [
        ("# Replace the qualified Meet Kirk archive after installation authorization.",
         "# Install checkpoint candidate 02 with the authorized two replacements and private plugin."),
        (RD10_TRANSACTION_SHA, sha(MANIFEST)),
        ("PTFR_RD10_MEET_KIRK_CONTENT_LOCK_CORE_V1", SCHEMA),
        ("$manifest.source_epoch -cne 'RD10_MEET_KIRK_CONTENT_LOCK'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'RD9_MEET_KIRK_DISTANCE'", f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ("core_resume_rd10_kirk_01", "resume_checkpoint_01"),
        ("foreach($row in $manifest.files){CheckFile (Safe $manifest.package_root $row.path) $row.after $row.after_bytes}",
         "foreach($row in $changes){CheckFile (Safe $manifest.package_root $row.path) $row.after $row.after_bytes}"),
        ("(@($manifest.files.path|Sort-Object)-join ',')){throw 'Exact source package inventory drift'}",
         "(@($changes.path|Sort-Object)-join ',')){throw 'Exact source package inventory drift'}"),
        (old_scope, new_scope),
    ]
    for old, new in edits:
        assert base.count(old) == 1, old
        base = base.replace(old, new, 1)
    with INSTALLER.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(base)


def prepare():
    previous = read(pinned(BASELINE, BASELINE_SHA))
    predecessor = pinned(RD10 / "core_manifest_01.json", RD10_TRANSACTION_SHA)
    processes = read(predecessor)["process_names"]
    game = Path(previous["game_root"])
    candidate = read(pinned(CANDIDATE, CANDIDATE_SHA))
    assert set(candidate["files"]) == CHANGES
    assert candidate["archive_sha256"] == previous["archive_sha256"]
    evidence = read(CHECKPOINT / "checkpoint.json")
    assert evidence["candidate_sha256"] == CANDIDATE_SHA
    checks = pinned(CHECKPOINT / evidence["checks"], candidate["check_receipt_sha256"])
    assert len(read(checks)["native_checks"]) == 41 and len(read(checks)["lua_checks"]) == 12
    build = pinned(CHECKPOINT / evidence["native_build"], candidate["build_receipt_sha256"])
    compiled = pinned(CHECKPOINT / candidate["compile_receipt"], candidate["compile_receipt_sha256"])
    compile_receipt = read(compiled)
    assert compile_receipt["source_count"] == 148
    assert compile_receipt["staged_redscript"] == {REDS: candidate["files"][REDS]}
    assert compile_receipt["staged_lua"] == {LUA: candidate["files"][LUA]}
    assert next(row["sha256"] for row in read(build) if row["name"] == Path(DLL).name) == candidate["files"][DLL]
    pins = compile_receipt["compiler_inputs"]
    assert sum(path.endswith(".reds") for path in pins) == 148
    inputs = {str(pinned(game / rel, value)): value for rel, value in pins.items()}
    inputs[str(pinned(game / EXE, EXE_SHA))] = EXE_SHA
    package = CANDIDATE.parent / "files"
    assert {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()} == CHANGES
    after = {rel: pinned(package / rel, candidate["files"][rel]) for rel in CHANGES}
    files = []
    for row in previous["core_files"]:
        rel = row["path"]
        source = pinned(game / rel, row["sha256"])
        assert source.stat().st_size == row["bytes"]
        new = after.get(rel, source)
        files.append({"path": rel, "before": row["sha256"], "before_bytes": row["bytes"],
                      "after": candidate["files"].get(rel, row["sha256"]), "after_bytes": new.stat().st_size})
    assert len(files) == 51 and not (game / DLL).exists()
    files.append({"path": DLL, "before": None, "before_bytes": None, "after": candidate["files"][DLL],
                  "after_bytes": after[DLL].stat().st_size})
    assert {row["path"] for row in files if row["before"] != row["after"]} == CHANGES
    inherited = previous["required_files"]
    assert len(inherited) == 26
    for row in inherited:
        assert pinned(game / row["path"], row["sha256"]).stat().st_size == row["bytes"]
    DEPLOYMENT.mkdir(exist_ok=False)
    proofs = [BASELINE, predecessor, CANDIDATE, checks, build, compiled]
    write(MANIFEST, {
        "schema": SCHEMA, "component": "Core", "source_epoch": EPOCH, "predecessor_epoch": BEFORE,
        "scope": "Install execution checkpoint candidate 02 for a genuine Tower capture and save-reload test.",
        "game_root": str(game), "save_root": previous["save_root"], "package_root": str(package),
        "process_names": processes, "files": files, "changing_paths": sorted(CHANGES), "required_files": inherited,
        "protected_saves": [], "working_save_files": [], "zip": "", "zip_sha256": None,
        "proofs": [{"path": str(path), "sha256": sha(path)} for path in proofs], "compile_inputs": inputs,
    })
    build_guard()
    print("Prepared the three confirmed candidate files and the full installed-state inventory.")


def fixtures(powershell):
    manifest = read(MANIFEST)
    cases = {
        "rollback": [("Install", "INSTALLED_VERIFIED"), ("Verify", "VERIFIED_AFTER"),
                     ("ValidateRollback", "ROLLBACK_READY"), ("Rollback", "ROLLED_BACK_VERIFIED"),
                     ("Verify", "VERIFIED_BEFORE", "-ExpectedState", "Before")],
        "crash_stage": [("Install", 72, "-FailurePoint", "CrashAfterStage"),
                        ("Recover", "RECOVERED_BEFORE"), ("Verify", "VERIFIED_BEFORE", "-ExpectedState", "Before")],
        "crash_second": [("Install", 72, "-FailurePoint", "CrashAfterSecondReplace"),
                         ("Recover", "RECOVERED_BEFORE"), ("Verify", "VERIFIED_BEFORE", "-ExpectedState", "Before")],
        "crash_with_plugin": [("Install", 72, "-FailurePoint", "CrashBeforeReceipt"),
                              ("Recover", "RECOVERED_BEFORE"), ("Verify", "VERIFIED_BEFORE", "-ExpectedState", "Before")],
        "game_running": [("Install", 1, "-FixtureProcesses", "Cyberpunk2077")],
        "plugin_occupied": [("Install", 1)],
    }
    root = HERE / "fixtures/deployment_01"
    root.mkdir(parents=True, exist_ok=False)
    results = []
    for case, steps in cases.items():
        folder = root / case
        game, saves, package = (folder / rel for rel in ("game", "saves", "package"))
        current = deepcopy(manifest)
        current.update(game_root=str(game), save_root=str(saves), package_root=str(package), proofs=[], compile_inputs={})
        for row in current["files"]:
            rel = row["path"]
            source, payload = game / rel, package / rel
            if row["before"] is not None:
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_bytes(("fixture before " + rel).encode())
                row.update(before=sha(source), before_bytes=source.stat().st_size)
            if rel in CHANGES:
                payload.parent.mkdir(parents=True, exist_ok=True)
                payload.write_bytes(("fixture after " + rel).encode())
                row.update(after=sha(payload), after_bytes=payload.stat().st_size)
            else:
                row.update(after=row["before"], after_bytes=row["before_bytes"])
        for row in current["required_files"]:
            item = game / row["path"]
            item.parent.mkdir(parents=True, exist_ok=True)
            item.write_bytes(row["path"].encode())
            row.update(sha256=sha(item), bytes=item.stat().st_size)
        save = saves / "FixtureSave/sav.dat"
        save.parent.mkdir(parents=True)
        save.write_bytes(b"original save bytes")
        external = game / "external/keep.dat"
        external.parent.mkdir()
        external.write_bytes(b"original unrelated mod bytes")
        addon = game / DLL
        if case == "plugin_occupied":
            addon.parent.mkdir()
            addon.write_bytes(b"unrecognized plugin bytes")
        fixture = folder / "manifest.json"
        write(fixture, current)
        for action, expected, *flags in steps:
            result = subprocess.run([powershell, "-NoProfile", "-File", str(INSTALLER), "-Action", action,
                                     "-FixtureRoot", str(folder), "-FixtureManifest", str(fixture),
                                     "-FixtureManifestSHA", sha(fixture), *flags], capture_output=True,
                                    encoding="utf-8", errors="replace", timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
            if isinstance(expected, int):
                assert result.returncode == expected, (case, action, result.stdout, result.stderr)
                status = None
                if case == "plugin_occupied":
                    assert "Expected absent path is occupied" in result.stderr
                if case == "crash_with_plugin":
                    assert sha(addon) == next(row["after"] for row in current["files"] if row["path"] == DLL)
            else:
                assert result.returncode == 0, (case, action, result.stdout, result.stderr)
                status = json.loads(result.stdout)["status"]
                assert status == expected, (case, action, status)
            results.append({"fixture": case, "action": action, "status": status, "returncode": result.returncode})
        for row in current["files"]:
            path = game / row["path"]
            if row["before"] is not None:
                pinned(path, row["before"])
            elif case == "plugin_occupied":
                assert path.read_bytes() == b"unrecognized plugin bytes"
            else:
                assert not path.exists()
        for row in current["required_files"]:
            pinned(game / row["path"], row["sha256"])
        assert save.read_bytes() == b"original save bytes"
        assert external.read_bytes() == b"original unrelated mod bytes"
        if case in ("game_running", "plugin_occupied"):
            assert not (folder / "recovery").exists()
    results_path = HERE / "fixture_results.json"
    scope = HERE / "scope_review.json"
    write(results_path, {"status": "PASS", "actions": results})
    write(scope, {"scope": manifest["scope"], "changed_paths": sorted(CHANGES),
                  "candidate_sha256": CANDIDATE_SHA, "before_sha256": BASELINE_SHA,
                  "installed_archive_sha256": read(BASELINE)["archive_sha256"], "gameplay": "PENDING_USER_PLAYTEST"})
    write(HERE / "readiness.json", {"status": "READY_NOT_INSTALLED", "manifest_sha256": sha(MANIFEST),
                                    "installer_sha256": sha(INSTALLER), "fixture_result": results_path.name,
                                    "fixture_result_sha256": sha(results_path), "scope_review": scope.name,
                                    "scope_review_sha256": sha(scope)})
    print(f"Passed {len(results)} installation and recovery fixture actions.")


def record():
    previous = read(pinned(BASELINE, BASELINE_SHA))
    manifest = read(MANIFEST)
    receipt = RECOVERY / "journal.json"
    envelope = read(receipt)
    payload = envelope["payload_json"]
    assert sha256(payload.encode()).hexdigest().upper() == envelope["payload_sha256"]
    journal = json.loads(payload)
    assert journal["manifest_sha256"] == sha(MANIFEST) and journal["state"] == "INSTALLED_VERIFIED"
    assert set(journal["completed_paths"]) == CHANGES and journal["save_writes"] == journal["game_launches"] == 0
    assert read(DEPLOYMENT / "verify.json")["status"] == "VERIFIED_AFTER"
    assert read(DEPLOYMENT / "rollback_readiness.json")["status"] == "ROLLBACK_READY"
    before, after = journal["protection_before"], journal["protection_after"]
    for name in ("saves", "unmanaged"):
        assert before[name]["tree_sha256"] == after[name]["tree_sha256"]
    assert before["dependencies"] == after["dependencies"]
    game = Path(manifest["game_root"])
    observed = [{"path": row["path"], "bytes": row["after_bytes"], "sha256": row["after"]}
                for row in manifest["files"]]
    for row in observed + manifest["required_files"]:
        assert pinned(game / row["path"], row["sha256"]).stat().st_size == row["bytes"]
    saves = sum(row["kind"] == "file" for row in after["saves"]["files"])
    authorization = DEPLOYMENT / "authorization_01.json"
    write(authorization, {"scope": manifest["scope"], "candidate_sha256": CANDIDATE_SHA,
                          "authorization": "User requested installation and test instructions."})
    write(DEPLOYMENT / "installed_manifest_01.json", {
        "schema": "PTFR_INSTALLED_EXECUTION_CHECKPOINT_V1", "core_epoch": EPOCH,
        "predecessor_epoch": BEFORE, "recorded_utc": journal["updated_utc"], "recorded_timezone": "America/Toronto",
        "authorization": manifest["scope"], "authorization_record": str(authorization),
        "authorization_record_sha256": sha(authorization), "game_root": manifest["game_root"],
        "save_root": manifest["save_root"], "archive_source": previous["archive_source"],
        "archive_payloads": previous["archive_payloads"], "archive_sha256": previous["archive_sha256"],
        "core_files": [row for row in observed if row["path"] != DLL],
        "companion_files": [row for row in observed if row["path"] == DLL],
        "required_files": manifest["required_files"], "changed_paths": sorted(CHANGES),
        "source_candidate": str(CANDIDATE), "source_candidate_sha256": CANDIDATE_SHA,
        "predecessor_manifest": str(BASELINE), "predecessor_manifest_sha256": BASELINE_SHA,
        "core_transaction": str(MANIFEST), "core_transaction_sha256": sha(MANIFEST),
        "installed_receipt": str(receipt), "installed_receipt_sha256": sha(receipt),
        "post_install_verification": str(DEPLOYMENT / "verify.json"),
        "rollback_readiness": str(DEPLOYMENT / "rollback_readiness.json"),
        "save_files_preserved": saves, "save_tree_sha256": after["saves"]["tree_sha256"],
        "unmanaged_tree_sha256": after["unmanaged"]["tree_sha256"], "gameplay": "PENDING_USER_PLAYTEST",
    })
    print(f"Verified 51 Core paths, the checkpoint DLL, 26 dependencies and {saves} preserved save files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "fixtures", "record"))
    parser.add_argument("--powershell", default=str(shutil.which("pwsh") or "pwsh"))
    options = parser.parse_args()
    if options.action == "prepare":
        prepare()
    elif options.action == "fixtures":
        fixtures(options.powershell)
    else:
        record()
