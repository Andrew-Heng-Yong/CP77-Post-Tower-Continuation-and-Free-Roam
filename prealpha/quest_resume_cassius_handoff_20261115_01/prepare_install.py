"""Stage and exercise the authorized four-file Cassius development installation."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import subprocess

from build import HERE, INSTALL, INSTALL_SHA, PREVIOUS, digest, load, payload_path, pin, require
from build import verify_baseline, write_json

STAGE = HERE / "staged_01"
DLL = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
SCRIPTS = [
    f"r6/scripts/PTFR_Consolidated/{name}.reds"
    for name in ("PTFR_HistorySnapshotHS1", "PTFR_SideJobsS22", "PTFR_SideJobsS24")
]
PATHS = [*SCRIPTS, DLL]
VERSION = "0.1.12"
EPOCH = "RD10_EXECUTION_CHECKPOINT_CASSIUS_HANDOFF"
PRIOR = "RD10_EXECUTION_CHECKPOINT_CASSIUS_SELECTION"
SCHEMA = f"PTFR_{EPOCH}_CORE_V1"
BUILD = HERE / "run_07/assessment.json"
BUILD_SHA = "05BA3EC0D193FD83A7EF9404DCEDA913CCC6A4C65FF25F8986744A8126165C49"
SCRIPT_SHA = "5E97B4AB6A6CD404DA8451B007B8880BA181C08A36EEE667A88E79CB9D429D7B"
DLL_SHA = "0FBB3A38AFED941CA34F588D1CDE0BFCFFD272F159A27A5FEDC14019042742EB"
SOURCE_INSTALLER_SHA = "831D47B978C44FBC361B3BA27A0A2A463A6CFE11E6714CD32267DDD08B3A6023"


def adapt_installer(path, manifest_sha):
    original = pin(PREVIOUS / "staged_01/deploy_core.ps1", SOURCE_INSTALLER_SHA)
    text = original.read_text(encoding="utf-8")
    replacements = [
        ("# Guard the sole v0.1.11 checkpoint DLL replacement.",
         "# Guard the three Cassius script overlays and the matching v0.1.12 checkpoint DLL."),
        ("FBEC1D3D165A680769D0149BAEB3F1B0EC5E5E2DE965BF47C6A990B294679A0C", manifest_sha),
        (f"PTFR_{PRIOR}_CORE_V1", SCHEMA),
        (f"source_epoch -cne '{PRIOR}'", f"source_epoch -cne '{EPOCH}'"),
        ("predecessor_epoch -cne 'RD10_EXECUTION_CHECKPOINT_NATIVE_REGISTRATION'",
         f"predecessor_epoch -cne '{PRIOR}'"),
        ("recovery/cassius_selection_01", "recovery/cassius_handoff_01"),
        ("Only an existing DLL may be replaced", "Only existing manifest files may be replaced"),
        (f"$wanted=@('{DLL}')", "$wanted=@(" + ",".join(f"'{value}'" for value in PATHS) + ")"),
        ("$changes.Count -ne 1", "$changes.Count -ne 4"),
        ("(@($changes.path|Sort-Object)-join ',') -cne (@($wanted|Sort-Object)-join ',')",
         "($changes.path -join ',') -cne ($wanted -join ',')"),
        ("if($count -eq 1){Fault 'AfterFirstReplace'};}",
         "if($count -eq 1){Fault 'AfterFirstReplace'};if($count -eq 2){Fault 'AfterSecondReplace'};}"),
    ]
    for before, after in replacements:
        require(text.count(before) == 1, f"Installer adaptation input drift: {before}")
        text = text.replace(before, after, 1)
    with path.open("x", encoding="utf-8", newline="\r\n") as stream:
        stream.write(text)


def make_manifest():
    baseline = load(INSTALL, INSTALL_SHA)
    verify_baseline(baseline)
    require(baseline["core_epoch"] == PRIOR, "Wrong installed predecessor")
    build = load(BUILD, BUILD_SHA)
    compile_path = HERE / "compile_02/assessment.json"
    scripts = load(compile_path, SCRIPT_SHA)
    gates = HERE / "run_07/legacy_entry_gates.json"
    pin(gates, "FB6A127B817762F539FDFB072AAFFE217DD2D04535F12CEFC2107CB6AB5DB8C8")
    pin(HERE / "compile_02/cache/compiled.redscripts", scripts["compiled_sha256"])
    require(build["status"] == "OFFLINE_CASSIUS_HANDOFF_BUILD_PASS" and build["version"] == VERSION
            and build["candidate_sha256"] == DLL_SHA and sum(build["checks"].values()) == 130,
            "Wrong native validation")
    require(scripts["status"] == "PASS" and scripts["sources"] == 148
            and set(scripts["overlay"]) == set(SCRIPTS), "Wrong REDscript validation")
    source_inventory = {}
    for group in [*build["compile_inputs"].values(), scripts["input_pins"]]:
        for raw_path, expected in group.items():
            key = str(Path(raw_path)).lower()
            require(source_inventory.setdefault(key, expected) == expected, f"Conflicting input pin: {raw_path}")
    for name, expected in source_inventory.items():
        pin(Path(name), expected)
    replacements = {path: (HERE / "overlay" / path, scripts["overlay"][path]) for path in SCRIPTS}
    replacements[DLL] = (HERE / "run_07/PTFR_ExecutionCheckpoint.dll", DLL_SHA)
    for source, sha in replacements.values():
        pin(source, sha)
    STAGE.mkdir()
    package = STAGE / "files"
    before = {row["path"]: row for row in baseline["core_files"] + baseline["companion_files"]}
    require(len(before) == 52 and set(PATHS) <= set(before), "Managed path drift")
    rows = []
    for path in [*(p for p in before if p not in replacements), *PATHS]:
        old = before[path]
        after_hash, after_size = old["sha256"], old["bytes"]
        if path in replacements:
            source, after_hash = replacements[path]
            target = payload_path(package, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            after_size = pin(target, after_hash).stat().st_size
        rows.append(dict(path=path, before=old["sha256"], before_bytes=old["bytes"],
                         after=after_hash, after_bytes=after_size))

    return dict(schema=SCHEMA, component="Core", source_epoch=EPOCH, predecessor_epoch=PRIOR,
                scope="Install checkpoint v0.1.12 with the three validated Cassius overlays.",
                game_root=baseline["game_root"], save_root=baseline["save_root"], package_root=str(package),
                process_names=["Cyberpunk2077", "REDlauncher", "REDprelauncher"], files=rows,
                changing_paths=PATHS, required_files=baseline["required_files"], protected_saves=[],
                working_save_files=[], zip=None, zip_sha256=None, compile_inputs=source_inventory,
                proofs=[dict(path=str(path), sha256=digest(path)) for path in (INSTALL, BUILD, compile_path, gates)])


CASES = {
    "install_rollback": [("Install", "INSTALLED_VERIFIED", []), ("Verify", "VERIFIED_AFTER", []),
                         ("ValidateRollback", "ROLLBACK_READY", []), ("Rollback", "ROLLED_BACK_VERIFIED", []),
                         ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
    "partial_exception": [("Install", 1, ["-FailurePoint", "AfterSecondReplace"]),
                          ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
    "partial_crash": [("Install", 72, ["-FailurePoint", "CrashAfterSecondReplace"]),
                      ("Recover", "RECOVERED_BEFORE", []),
                      ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
    "running_launcher": [("Install", 1, ["-FixtureProcesses", "REDlauncher"])],
    "staged_drift": [("Install", 1, [])],
}


def seed(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text)
    return dict(sha256=digest(path), bytes=path.stat().st_size)


def exercise(case, manifest, installer):
    folder = STAGE / "fixtures/deployment_01" / case
    game, saves, package = (folder / name for name in ("game", "saves", "package"))
    fixture = deepcopy(manifest)
    fixture.update(game_root=str(game), save_root=str(saves), package_root=str(package),
                   proofs=[], compile_inputs={})
    watched = {}
    for row in fixture["files"]:
        path = payload_path(game, row["path"])
        before = seed(path, f"existing {row['path']}")
        after = (seed(payload_path(package, row["path"]), f"next {row['path']}")
                 if row["path"] in PATHS else before)
        row.update(before=before["sha256"], before_bytes=before["bytes"],
                   after=after["sha256"], after_bytes=after["bytes"])
        watched[path] = before
    for row in fixture["required_files"]:
        path = payload_path(game, row["path"])
        watched[path] = seed(path, row["path"])
        row.update(watched[path])
    for path in (saves / "ManualSave-31/sav.dat", game / "other/keep.dat"):
        watched[path] = seed(path, "user data")
    if case == "staged_drift":
        payload_path(package, SCRIPTS[1]).write_bytes(b"unexpected staged contents")
    input_file = folder / "manifest.json"
    write_json(input_file, fixture)
    fixture_sha = digest(input_file)
    actions = []
    for index, (action, expected, flags) in enumerate(CASES[case], 1):
        result = subprocess.run(["pwsh", "-NoProfile", "-File", str(installer), "-Action", action,
                                 "-FixtureRoot", str(folder), "-FixtureManifest", str(input_file),
                                 "-FixtureManifestSHA", fixture_sha, *flags],
                                capture_output=True, encoding="utf-8", timeout=80,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        (folder / f"{index:02}_{action}.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
        if isinstance(expected, int):
            require(result.returncode == expected, f"{case} {action}: {result.stdout} {result.stderr}")
            reason = {"partial_exception": "AfterSecondReplace", "running_launcher": "must be closed naturally",
                      "staged_drift": "Hash drift:"}.get(case)
            require(reason is None or reason in result.stderr, f"Wrong rejection in {case}: {result.stderr}")
            status = "INTERRUPTED" if expected == 72 else "REFUSED"
            if case == "partial_crash":
                for path in PATHS:
                    row = next(entry for entry in fixture["files"] if entry["path"] == path)
                    pin(payload_path(game, path), row["after"] if path in PATHS[:2] else row["before"])
        else:
            require(result.returncode == 0, f"{case} {action}: {result.stderr}")
            status = json.loads(result.stdout)["status"]
            require(status == expected, f"Wrong state in {case} {action}: {status}")
        actions.append(dict(case=case, action=action, status=status))
    for path, record in watched.items():
        pin(path, record["sha256"], record["bytes"])
    recovery = folder / "recovery/core"
    require(not any(entry.is_file() for entry in (recovery / "stage").rglob("*")), "Left staged replacements")
    require(case not in ("staged_drift", "running_launcher") or not recovery.exists(),
            f"Refused case created a transaction: {case}")
    return actions


def main():
    manifest = make_manifest()
    manifest_path = STAGE / "core_manifest_01.json"
    write_json(manifest_path, manifest)
    manifest_sha = digest(manifest_path)
    installer = STAGE / "deploy_core.ps1"
    adapt_installer(installer, manifest_sha)
    scope = STAGE / "scope_review.json"
    write_json(scope, dict(scope=manifest["scope"], changed_paths=PATHS, candidate_sha256=DLL_SHA,
                           live_restore_enabled=True, gameplay="DEFERRED_TO_END_OF_STEP_5"))
    results = STAGE / "fixture_results.json"
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = [pool.submit(exercise, case, manifest, installer) for case in CASES]
        actions = [action for task in pending for action in task.result()]
    write_json(results, dict(status="PASS", fixture_trees=len(CASES), actions=actions))
    write_json(STAGE / "readiness.json", dict(status="READY_NOT_INSTALLED", manifest_sha256=manifest_sha,
               installer_sha256=digest(installer), fixture_result=results.name, fixture_result_sha256=digest(results),
               scope_review=scope.name, scope_review_sha256=digest(scope)))
    write_json(STAGE / "authorization_01.json", dict(user_reply="install", authorized_action=manifest["scope"],
               paths=PATHS, manifest_sha256=manifest_sha, candidate_sha256=DLL_SHA,
               recorded_utc=datetime.now(timezone.utc).isoformat()))
    print(f"Staged {len(PATHS)} files. Passed {len(actions)} actions across {len(CASES)} deployment fixtures.")


if __name__ == "__main__":
    main()
