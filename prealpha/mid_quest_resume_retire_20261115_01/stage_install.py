"""Stage the restoration-only build and exercise the guarded deployment."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import subprocess

from prepare_scripts import HERE, PREALPHA, BEFORE, BEFORE_SHA, SCRIPT_STAGE, STAGE, digest, load, pin, require, write_json
from candidate_common import payload_path

DEPLOY = HERE / "stage_08"
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
EPOCH = "RD10_MID_QUEST_RESUME_RETIRED"
PRIOR = "RD10_EXACT_RESUME_ARCHIVED"
RECOVERY = "recovery/mid_quest_resume_01"
TEMPLATE = PREALPHA / "resume_dispatcher_rd10_kirk_20261113_01/deploy_core.ps1"
TEMPLATE_SHA = "09A3BBFF589DEAA81C2B4BC09367A8B087AE96C50663659EB93F10F3FE174214"


def adapt(dest, manifest_sha, paths):
    script = pin(TEMPLATE, TEMPLATE_SHA).read_text(encoding="utf-8")
    names = ",".join(f"'{path}'" for path in paths)
    for old, new in (
        ("55B78AA7FEF57BE7628B8D3AFD5C4058EC9016D269638ACCD9E2E0F9B362C0B9", manifest_sha),
        ("PTFR_RD10_MEET_KIRK_CONTENT_LOCK_CORE_V1", f"PTFR_{EPOCH}_CORE_V1"),
        ("source_epoch -cne 'RD10_MEET_KIRK_CONTENT_LOCK'", f"source_epoch -cne '{EPOCH}'"),
        ("predecessor_epoch -cne 'RD9_MEET_KIRK_DISTANCE'", f"predecessor_epoch -cne '{PRIOR}'"),
        ("recovery/core_resume_rd10_kirk_01", RECOVERY),
        ("Join-Path (Split-Path $worker -Parent) 'quest_restoration_qr9/worker_a'",
         "Join-Path (Split-Path (Split-Path $worker -Parent) -Parent) 'quest_restoration_qr9/worker_a'"),
        (f"$wanted=@('{ARCHIVE}')", f"$wanted=@({names})"),
        ("$changes.Count -ne 1 -or", f"$changes.Count -ne {len(paths)} -or"),
        ("Core51/archive-only Meet Kirk scope drift", "Mid-quest retirement scope drift"),
        ("foreach($row in $manifest.files){CheckFile (Safe $manifest.package_root $row.path)",
         "foreach($row in $changes){CheckFile (Safe $manifest.package_root $row.path)"),
        ("@($manifest.files.path|Sort-Object)", "@($changes.path|Sort-Object)"),
    ):
        require(script.count(old) == 1, f"Installer source changed at {old}")
        script = script.replace(old, new, 1)
    with dest.open("x", encoding="utf-8", newline="\r\n") as stream:
        stream.write(script)


CASES = {
    "clean_archive_and_rollback": [("Install", "INSTALLED_VERIFIED", []), ("Verify", "VERIFIED_AFTER", []),
                                 ("ValidateRollback", "ROLLBACK_READY", []), ("Rollback", "ROLLED_BACK_VERIFIED", []),
                                 ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
    "crash_after_two_replacements": [("Install", 72, ["-FailurePoint", "CrashAfterSecondReplace"]),
                                     ("Recover", "RECOVERED_BEFORE", []),
                                     ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
    "exception_after_two_replacements": [("Install", 1, ["-FailurePoint", "AfterSecondReplace"]),
                                         ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
    "launcher_running": [("Install", 1, ["-FixtureProcesses", "REDlauncher"])],
}


def seed(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    return digest(path), len(data)


def exercise(case, manifest):
    folder = DEPLOY / "fixtures" / case
    game, saves, package = (folder / name for name in ("game", "saves", "package"))
    trial = deepcopy(manifest)
    trial.update(game_root=str(game), save_root=str(saves), package_root=str(package), proofs=[], compile_inputs={})
    keep = {}
    for row in trial["files"]:
        relative = row["path"]
        target = payload_path(game, relative)
        before = seed(target, f"installed {relative}".encode())
        after = (seed(payload_path(package, relative), f"replacement {relative}".encode())
                 if relative in trial["changing_paths"] else before)
        keep[target] = before
        row.update(before=before[0], before_bytes=before[1], after=after[0], after_bytes=after[1])
    for row in trial["required_files"]:
        target = payload_path(game, row["path"])
        keep[target] = seed(target, row["path"].encode())
        row["sha256"], row["bytes"] = keep[target]
    for path in (saves / "ManualSave-31/sav.dat", game / "external/keep.dat"):
        keep[path] = seed(path, b"existing user data")
    proof = folder / "manifest.json"
    write_json(proof, trial)
    recovery = folder / "recovery/core"
    results = []
    for index, (action, expected, flags) in enumerate(CASES[case]):
        process = subprocess.run(["pwsh", "-NoProfile", "-File", str(DEPLOY / "deploy_core.ps1"),
                                  "-FixtureRoot", str(folder), "-FixtureManifest", str(proof),
                                  "-FixtureManifestSHA", digest(proof), "-Action", action, *flags],
                                 capture_output=True, encoding="utf-8", timeout=70,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
        (folder / f"{index}_{action}.txt").write_text(process.stdout + process.stderr, encoding="utf-8")
        if isinstance(expected, int):
            require(process.returncode == expected, f"{case}: {process.stdout} {process.stderr}")
            reason = ("must be closed naturally" if case == "launcher_running" else "AfterSecondReplace")
            require(expected == 72 or reason in process.stderr, f"Wrong refusal reason: {case}")
            status = "INTERRUPTED" if expected == 72 else "REFUSED"
        else:
            require(process.returncode == 0, f"{case}: {process.stderr}")
            status = json.loads(process.stdout)["status"]
            require(status == expected, f"Wrong response for {case}")
        results.append(dict(case=case, action=action, status=status))
    for path, identity in keep.items():
        pin(path, *identity)
    require(not any(path.is_file() for path in (recovery / "stage").rglob("*")), "Staging leftovers")
    require(case != "launcher_running" or not recovery.exists(), "Busy game began a transaction")
    return results


def main():
    baseline = load(BEFORE, BEFORE_SHA)
    require(baseline["core_epoch"] == PRIOR and not baseline["companion_files"], "Wrong predecessor")
    require((PREALPHA / "quest_restoration_qr9/worker_a/installer.lock").stat().st_size == 0,
            "Shared installer lock drift")
    game = Path(baseline["game_root"])
    core = baseline["core_files"]
    require(len(core) == 51 and len(baseline["required_files"]) == 26, "Installed inventory changed")
    for row in core + baseline["required_files"]:
        pin(payload_path(game, row["path"]), row["sha256"], row["bytes"])
    require(not (game / "r6/cache/final.redscripts.modded").exists(), "Game rebuilt its cache; review current outputs")
    compile_proof = SCRIPT_STAGE / "compile/assessment.json"
    compiled = load(compile_proof, digest(compile_proof))
    require(compiled["status"] == "PASS" and compiled["sources"] == 148, "Missing source compilation")
    graph_proof = STAGE / "gate_checks.json"
    graphs = load(graph_proof, digest(graph_proof))
    pack_proof = STAGE / "pack/readback.json"
    archive = load(pack_proof, digest(pack_proof))
    require(graphs["status"] == archive["status"] == "PASS" and len(graphs["gates"]) == 20
            and len(archive["members"]) == 1748 and len(archive["changed_depots"]) == 10, "Missing graph/archive proof")
    script_proof = SCRIPT_STAGE / "script_changes.json"
    scripts = load(script_proof, digest(script_proof))
    paths = [ARCHIVE, *scripts]
    require(len(paths) == 6, "Unexpected write scope")
    staged = {path: pin(SCRIPT_STAGE / "package" / path, row["after"], row["bytes"])
              for path, row in scripts.items()}
    staged[ARCHIVE] = pin(STAGE / "pack" / Path(ARCHIVE).name, archive["archive_sha256"])
    DEPLOY.mkdir()
    package = DEPLOY / "files"
    for path, source in staged.items():
        target = payload_path(package, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        pin(target, digest(source), source.stat().st_size)
    rows = []
    for old in core:
        path = old["path"]
        source = staged.get(path)
        rows.append(dict(path=path, before=old["sha256"], before_bytes=old["bytes"],
                         after=digest(source) if source else old["sha256"],
                         after_bytes=source.stat().st_size if source else old["bytes"]))
    require({row["path"] for row in rows if row["before"] != row["after"]} == set(paths), "Actual delta differs")
    manifest = dict(schema=f"PTFR_{EPOCH}_CORE_V1", component="Core", source_epoch=EPOCH, predecessor_epoch=PRIOR,
                    game_root=baseline["game_root"], save_root=baseline["save_root"], package_root=str(package),
                    process_names=["Cyberpunk2077", "REDlauncher", "REDprelauncher"],
                    files=rows, changing_paths=paths, required_files=baseline["required_files"], protected_saves=[],
                    working_save_files=[], zip=None, zip_sha256=None, compile_inputs=compiled["input_pins"],
                    proofs=[dict(path=str(path), sha256=digest(path)) for path in
                            (BEFORE, compile_proof, graph_proof, pack_proof, script_proof)])
    manifest_path = DEPLOY / "core_manifest_01.json"
    write_json(manifest_path, manifest)
    manifest_sha = digest(manifest_path)
    installer = DEPLOY / "deploy_core.ps1"
    adapt(installer, manifest_sha, paths)
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = [pool.submit(exercise, case, manifest) for case in CASES]
        actions = [action for task in tasks for action in task.result()]
    fixture = DEPLOY / "fixture_results.json"
    write_json(fixture, dict(status="PASS", actions=actions))
    scope = DEPLOY / "scope_review.json"
    write_json(scope, dict(changed_paths=paths, archived_scope="Exact and legacy mid-journey admission",
                          existing_owners="Preserve", history="Shared restoration dependency retained"))
    write_json(DEPLOY / "readiness.json", dict(status="READY_NOT_INSTALLED", manifest_sha256=manifest_sha,
               installer_sha256=digest(installer), fixture_result=fixture.name, fixture_result_sha256=digest(fixture),
               scope_review=scope.name, scope_review_sha256=digest(scope)))
    write_json(DEPLOY / "authorization_01.json", dict(user_request="revert and archive everything about mid journey resume",
               changed_paths=paths, manifest_sha256=manifest_sha, recorded_utc=datetime.now(timezone.utc).isoformat()))
    print(f"Prepared six replacements and passed {len(actions)} deployment fixture actions.")


if __name__ == "__main__":
    main()
