"""Stage and test archival of the pinned exact-resume development files."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import subprocess

from prepare import CURRENT, CURRENT_SHA, DONOR, DONOR_SHA, STAGE, PREALPHA
from prepare import CACHE, CORE_REPLACEMENTS, DLL, HISTORY, digest, load, payload_path, pin, require, write_json

PRIOR = "RD10_EXECUTION_CHECKPOINT_TRAVEL_FOUNDATION"
EPOCH = "RD10_EXACT_RESUME_ARCHIVED"
WORKER = PREALPHA / "quest_resume_travel_20261115_01/staged_01/deploy_core.ps1"
WORKER_SHA = "1B45F4EDE6363DBA45F20EB863C5E0DEBE634E9EB4C57200CB5BA59F0F309702"
DETACHED = {
    HISTORY + "/checkpoint_execution_2185a8b5a6758511822fdab7bf4f517e.json":
        "15B5BFAE5F435AE4471490B867D156A9EC8D845EFDD40B8C549534B94B4A0295",
    HISTORY + "/checkpoint_execution_26659fa28c9e8dda762e583248abed74.json":
        "54E06927145DA7ECDD6C292A0B7A0492E6BA955943295A29A7208B73064B5844",
    HISTORY + "/checkpoint_execution_27f5fb2228de1ee652b9aeabde09705f.json":
        "41B2D601602926C8128A480BFDAE63DBBD90C579B5CC1779947FB042104A53E9",
    HISTORY + "/checkpoint_execution_feff5775c34c732362f886201f4b2fb7.json":
        "D519744FC3D88E28F60B0BF3E98673D2BC21283EA3A59CB72A24679036822C0D",
    CACHE: "706144B0FE325395681073AB291425F3B25A13C40B6D1B479FCAA5D727F28431",
    "red4ext/logs/ptfr_executioncheckpoint-2026-11-15-18-10-27.log":
        "CA3120534D0C1BC610BFD422D7C24555CE3D6861FB867DDA2167DDE24F553399",
}
REMOVALS = [DLL, *DETACHED]
CHANGES = [DLL, *CORE_REPLACEMENTS, *DETACHED]
RECOVERY = "recovery/exact_resume_archive_01"


def manifest_files(baseline, preparation):
    game = Path(baseline["game_root"])
    indexed = {row["path"]: row for row in baseline["core_files"] + baseline["companion_files"]}
    require(len(indexed) == 52 and set(indexed).isdisjoint(DETACHED), "Baseline inventory drift")
    for path, sha in DETACHED.items():
        before = pin(payload_path(game, path), sha)
        indexed[path] = dict(path=path, sha256=sha, bytes=before.stat().st_size)
    for folder, pattern, expected in (
        (Path(DLL).parent.as_posix(), "*", [DLL]),
        (HISTORY, "checkpoint_execution_*", [key for key in DETACHED if key.startswith(HISTORY)]),
        ("red4ext/logs", "ptfr_executioncheckpoint*.log", [key for key in DETACHED if key.startswith("red4ext/logs")]),
    ):
        actual = {path.relative_to(game).as_posix() for path in payload_path(game, folder).glob(pattern)}
        require(actual == set(expected), f"Review unrecognized checkpoint artifacts in {folder}")
    paths = [path for path in indexed if path not in CHANGES] + CHANGES
    result = []
    for path in paths:
        before = indexed[path]
        after = None if path in REMOVALS else preparation["replacements"].get(path, before)
        result.append(dict(path=path, before=before["sha256"], before_bytes=before["bytes"],
                           after=after["sha256"] if after else None, after_bytes=after["bytes"] if after else None))
    return result


def quote_paths(paths):
    return "@(" + ",".join(f"'{path}'" for path in paths) + ")"


def prepare_worker(path, manifest_sha, managed_count):
    text = pin(WORKER, WORKER_SHA).read_text(encoding="utf-8")
    before_guard = "if($null -eq $wanted -or $null -eq $other){throw 'Only existing manifest files may be replaced'}"
    after_guard = (
        "if($null -eq $wanted){"
        "CheckFile (Payload 'old' $row) $row.before $row.before_bytes -Fresh;"
        "Closed;$target=Safe $game $row.path;CheckFile $target $other -Fresh;"
        "[IO.File]::Delete($target);CheckFile $target $null;return}"
    )
    backup = "$new=Payload 'new' $row;EnsureDir ([IO.Path]::GetDirectoryName($new));[IO.File]::Copy((Safe $manifest.package_root $row.path),$new,$false);CheckFile $new $row.after $row.after_bytes"
    edits = [
        ("# Guard the single v0.1.13 checkpoint DLL replacement.", "# Archive the exact-resume experiment."),
        ("05322D7F8D2278B9D3E6107E58CE07B15BF1B46BDEE38F1C8ACA135469D98479", manifest_sha),
        (f"PTFR_{PRIOR}_CORE_V1", f"PTFR_{EPOCH}_CORE_V1"),
        (f"source_epoch -cne '{PRIOR}'", f"source_epoch -cne '{EPOCH}'"),
        ("predecessor_epoch -cne 'RD10_EXECUTION_CHECKPOINT_CASSIUS_HANDOFF'", f"predecessor_epoch -cne '{PRIOR}'"),
        ("recovery/travel_foundation_01", RECOVERY),
        ("Missing native compile inputs", "Missing REDscript compile inputs"),
        ("(@($changes.path|Sort-Object)-join ',')", "(@($changes|Where-Object {$null -ne $_.after}|ForEach-Object {$_.path}|Sort-Object)-join ',')"),
        (before_guard, after_guard),
        ("[IO.File]::Replace($stage,$target,[NullString]::Value)",
         "if($null -eq $other){[IO.File]::Move($stage,$target,$false)}else{[IO.File]::Replace($stage,$target,[NullString]::Value)}"),
        (backup, "if($null -ne $row.after){" + backup + "}"),
        ("if($row.after -notmatch '^[A-F0-9]{64}$' -or",
         "if(($null -ne $row.after -and $row.after -notmatch '^[A-F0-9]{64}$') -or"),
        (f"$wanted=@('{DLL}')", "$wanted=" + quote_paths(CHANGES) + "\n$wantedRemoved=" + quote_paths(REMOVALS)),
        ("$additions=@($manifest.files|Where-Object {$null -eq $_.before})",
         "$additions=@($manifest.files|Where-Object {$null -eq $_.before})\n"
         "$removed=@($changes|Where-Object {$null -eq $_.after})"),
        ("$manifest.files.Count -ne 52", f"$manifest.files.Count -ne {managed_count}"),
        ("$changes.Count -ne 1 -or", f"$changes.Count -ne {len(CHANGES)} -or "
         "($removed.path -join ',') -cne ($wantedRemoved -join ',') -or"),
    ]
    for before, after in edits:
        require(text.count(before) == 1, f"Installer adaptation source drift: {before}")
        text = text.replace(before, after, 1)
    with path.open("x", encoding="utf-8", newline="\r\n") as stream:
        stream.write(text)


CASES = {
    "archive_and_undo": [
        ("Install", "INSTALLED_VERIFIED", []), ("Verify", "VERIFIED_AFTER", []),
        ("ValidateRollback", "ROLLBACK_READY", []), ("Rollback", "ROLLED_BACK_VERIFIED", []),
        ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"]),
    ],
    "interrupted_after_detach": [
        ("Install", 72, ["-FailurePoint", "CrashAfterFirstReplace"]),
        ("Recover", "RECOVERED_BEFORE", []), ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"]),
    ],
    "exception_after_replacement": [
        ("Install", 1, ["-FailurePoint", "AfterSecondReplace"]),
        ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"]),
    ],
    "busy_launcher": [("Install", 1, ["-FixtureProcesses", "REDlauncher"])],
    "modified_export": [("Install", 1, [])],
}


def mock_file(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(value)
    return digest(path), len(value)


def exercise(case, manifest):
    folder = STAGE / "fixtures" / case
    game, saves, package = (folder / part for part in ("game", "saves", "package"))
    fixture = deepcopy(manifest)
    fixture.update(game_root=str(game), save_root=str(saves), package_root=str(package), compile_inputs={}, proofs=[])
    preserve = {}
    for row in fixture["files"]:
        target = payload_path(game, row["path"])
        before = mock_file(target, f"before {row['path']}".encode())
        preserve[target] = before
        if row["path"] in REMOVALS:
            after = None, None
        elif row["path"] in CORE_REPLACEMENTS:
            after = mock_file(payload_path(package, row["path"]), f"after {row['path']}".encode())
        else:
            after = before
        row.update(before=before[0], before_bytes=before[1], after=after[0], after_bytes=after[1])
    for row in fixture["required_files"]:
        target = payload_path(game, row["path"])
        preserve[target] = mock_file(target, row["path"].encode())
        row["sha256"], row["bytes"] = preserve[target]
    for path in (saves / "ManualSave-31/sav.dat", game / "external/keep.dat"):
        preserve[path] = mock_file(path, b"existing user data")
    if case == "modified_export":
        check = payload_path(game, next(iter(DETACHED)))
        check.write_bytes(b"changed since preflight")
        preserve[check] = digest(check), check.stat().st_size
    file = folder / "manifest.json"
    write_json(file, fixture)
    manifest_sha = digest(file)
    recovery = folder / "recovery/core"
    actions = []
    for index, (action, expected, parameters) in enumerate(CASES[case], 1):
        result = subprocess.run(["pwsh", "-NoProfile", "-File", str(STAGE / "deploy_core.ps1"),
                                 "-Action", action, "-FixtureRoot", str(folder), "-FixtureManifest", str(file),
                                 "-FixtureManifestSHA", manifest_sha, *parameters], capture_output=True,
                                encoding="utf-8", timeout=70, creationflags=subprocess.CREATE_NO_WINDOW)
        (folder / f"{index:02}_{action}.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
        if isinstance(expected, int):
            require(result.returncode == expected, f"{case}: {result.stdout} {result.stderr}")
            if case == "interrupted_after_detach":
                require(not (game / DLL).exists(), "Crash fixture did not detach the DLL")
                pin(recovery / "old" / DLL, *preserve[game / DLL])
            elif case == "busy_launcher":
                require("must be closed naturally" in result.stderr, "Wrong process refusal")
            elif case == "modified_export":
                require("Hash drift:" in result.stderr, "Wrong drift refusal")
            else:
                require("AfterSecondReplace" in result.stderr, "Wrong injected exception")
            status = "INTERRUPTED" if expected == 72 else "REFUSED"
        else:
            require(result.returncode == 0, f"{case} {action}: {result.stderr}")
            status = json.loads(result.stdout)["status"]
            require(status == expected, f"Wrong transaction state in {case}: {status}")
            if action == "Install":
                for removed in REMOVALS:
                    require(not (game / removed).exists(), f"Removal failed: {removed}")
                    pin(recovery / "old" / removed, *preserve[game / removed])
        actions.append(dict(case=case, action=action, result=status))
    for path, identity in preserve.items():
        pin(path, *identity)
    require(not any(path.is_file() for path in (recovery / "stage").rglob("*")), "Staging leftovers")
    if case in ("busy_launcher", "modified_export"):
        require(not recovery.exists(), "Refused transaction created a recovery tree")
    return actions


def main():
    baseline = load(CURRENT, CURRENT_SHA)
    require(baseline["core_epoch"] == PRIOR, "Wrong installed predecessor")
    prepared = STAGE / "preparation.json"
    compile_report = STAGE / "compile/assessment.json"
    preparation = load(prepared, digest(prepared))
    compiled = load(compile_report, preparation["compile_report_sha256"])
    require(preparation["status"] == compiled["status"] == "PASS" and compiled["sources"] == 148,
            "Workspace compile unavailable")
    require(len(preparation["preserved_saved_fields"]) == 8 and
            set(preparation["replacements"]) == set(CORE_REPLACEMENTS), "Prepared write scope drift")
    rows = manifest_files(baseline, preparation)
    scope = "Archive exact mid-journey resume files and install save-compatible RD10 scripts."
    manifest = dict(schema=f"PTFR_{EPOCH}_CORE_V1", component="Core", source_epoch=EPOCH, predecessor_epoch=PRIOR,
                    scope=scope, game_root=baseline["game_root"], save_root=baseline["save_root"],
                    package_root=str(STAGE / "files"), process_names=["Cyberpunk2077", "REDlauncher", "REDprelauncher"],
                    files=rows, changing_paths=CHANGES, removed_paths=REMOVALS, required_files=baseline["required_files"],
                    protected_saves=[], working_save_files=[], zip=None, zip_sha256=None, compile_inputs=compiled["input_pins"],
                    proofs=[dict(path=str(path), sha256=sha) for path, sha in
                            ((CURRENT, CURRENT_SHA), (DONOR, DONOR_SHA), (prepared, digest(prepared)),
                             (compile_report, preparation["compile_report_sha256"]))]
                    )
    file = STAGE / "core_manifest_01.json"
    write_json(file, manifest)
    manifest_sha = digest(file)
    worker = STAGE / "deploy_core.ps1"
    prepare_worker(worker, manifest_sha, len(rows))
    scope_file = STAGE / "scope_review.json"
    write_json(scope_file, dict(scope=scope, changed_paths=CHANGES, removed_paths=REMOVALS,
                               preserved_saved_fields=preparation["preserved_saved_fields"]))
    results = STAGE / "fixture_results.json"
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(exercise, case, manifest) for case in CASES]
        actions = [action for job in jobs for action in job.result()]
    write_json(results, dict(status="PASS", cases=len(CASES), actions=actions))
    write_json(STAGE / "readiness.json", dict(status="READY_NOT_INSTALLED", manifest_sha256=manifest_sha,
               installer_sha256=digest(worker), fixture_result=results.name, fixture_result_sha256=digest(results),
               scope_review=scope_file.name, scope_review_sha256=digest(scope_file)))
    write_json(STAGE / "authorization_01.json", dict(authorized_action=scope, changed_paths=CHANGES,
               manifest_sha256=manifest_sha, recorded_utc=datetime.now(timezone.utc).isoformat()))
    print(f"Passed {len(actions)} archive fixture actions for {len(CASES)} isolated trees.")


if __name__ == "__main__":
    main()
