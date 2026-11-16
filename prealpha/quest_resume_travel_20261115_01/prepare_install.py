"""Stage and exercise a fresh single-DLL v0.1.13 development deployment."""

from datetime import datetime, timezone
from pathlib import Path
import shutil

from build import HERE, INSTALL, INSTALL_SHA, PREVIOUS, digest, load, payload_path, pin, require
from build import verify_baseline, write_json
from candidate_common import TARGET as DLL
from fixtures import exercise

STAGE = HERE / "staged_01"
VERSION = "0.1.13"
PRIOR = "RD10_EXECUTION_CHECKPOINT_CASSIUS_HANDOFF"
EPOCH = "RD10_EXECUTION_CHECKPOINT_TRAVEL_FOUNDATION"
BUILD = HERE / "run_04/assessment.json"
BUILD_SHA = "A7B6C3C7DE56285D0F8BAD5413F8B098E226631AFDDCA5FF83CE60654F6DD7B1"
DLL_SHA = "63FD645D6C970877414912455ABB8B6233E518928B176033CBED93BA772B9A77"
SOURCE_INSTALLER_SHA = "29B3C89EA6E6EBB297D0B86C88B0FEB3BB451F9DB252FC12A923221D42F5FEE1"
PATHS = [DLL]


def installer(path, manifest_sha):
    source = pin(PREVIOUS / "staged_01/deploy_core.ps1", SOURCE_INSTALLER_SHA)
    text = source.read_text(encoding="utf-8")
    start = text.index("$wanted=@(")
    end = text.index("\n", start)
    wanted = text[start:end]
    edits = [
        ("# Guard the three Cassius script overlays and the matching v0.1.12 checkpoint DLL.",
         "# Guard the single v0.1.13 checkpoint DLL replacement."),
        ("FBB51343C22B19B340AE98BD174D2A3E363B276A650B1BD716D68FC4E60AC60B", manifest_sha),
        (f"PTFR_{PRIOR}_CORE_V1", f"PTFR_{EPOCH}_CORE_V1"),
        (f"source_epoch -cne '{PRIOR}'", f"source_epoch -cne '{EPOCH}'"),
        ("predecessor_epoch -cne 'RD10_EXECUTION_CHECKPOINT_CASSIUS_SELECTION'",
         f"predecessor_epoch -cne '{PRIOR}'"),
        ("recovery/cassius_handoff_01", "recovery/travel_foundation_01"),
        (wanted, f"$wanted=@('{DLL}')"),
        ("$changes.Count -ne 4", "$changes.Count -ne 1"),
    ]
    for prior, successor in edits:
        require(text.count(prior) == 1, f"Installer source drift: {prior}")
        text = text.replace(prior, successor, 1)
    with path.open("x", encoding="utf-8", newline="\r\n") as stream:
        stream.write(text)


def main():
    baseline = load(INSTALL, INSTALL_SHA)
    verify_baseline(baseline)
    require(baseline["core_epoch"] == PRIOR, "Wrong installed predecessor")
    build = load(BUILD, BUILD_SHA)
    projection = HERE / "run_04/travel_projection.json"
    review = HERE / "review_01/assessment.json"
    require(build["status"] == "OFFLINE_TRAVEL_FOUNDATION_BUILD_PASS" and build["version"] == VERSION
            and build["candidate_sha256"] == DLL_SHA and build["checks"]["TravelChecks"] == 16
            and sum(build["checks"].values()) == 146 and build["travel_runtime_admission"] == "DEFERRED",
            "Wrong v0.1.13 build assessment")
    pin(projection, build["travel_projection_sha256"])
    review_sha = "C91175C3789E2E432275DA36D28A6E57E3B4E28C591D65164784B584E12B4666"
    require(load(review, review_sha)["status"] == "SOURCE_AND_SAVED_CONTROLS_PASS", "Wrong travel assessment")
    binary = pin(HERE / "run_04/PTFR_ExecutionCheckpoint.dll", DLL_SHA)
    compile_inputs = {}
    for group in build["compile_inputs"].values():
        for name, expected in group.items():
            require(compile_inputs.setdefault(name, expected) == expected, f"Conflicting input pin: {name}")
    for name, expected in compile_inputs.items():
        pin(Path(name), expected)

    STAGE.mkdir()
    package = STAGE / "files"
    payload = payload_path(package, DLL)
    payload.parent.mkdir(parents=True)
    shutil.copyfile(binary, payload)
    pin(payload, DLL_SHA)
    rows = []
    for row in baseline["core_files"] + baseline["companion_files"]:
        path, previous, length = row["path"], row["sha256"], row["bytes"]
        rows.append(dict(path=path, before=previous, before_bytes=length,
                         after=DLL_SHA if path == DLL else previous,
                         after_bytes=payload.stat().st_size if path == DLL else length))
    require(len(rows) == 52 and [row["path"] for row in rows if row["before"] != row["after"]] == PATHS,
            "Managed inventory or replacement scope drift")
    scope = "Install checkpoint v0.1.13 with the shared native travel groundwork."
    manifest = dict(schema=f"PTFR_{EPOCH}_CORE_V1", component="Core", source_epoch=EPOCH, predecessor_epoch=PRIOR,
                    scope=scope, game_root=baseline["game_root"], save_root=baseline["save_root"],
                    package_root=str(package), process_names=["Cyberpunk2077", "REDlauncher", "REDprelauncher"],
                    files=rows, changing_paths=PATHS, required_files=baseline["required_files"], protected_saves=[],
                    working_save_files=[], zip=None, zip_sha256=None, compile_inputs=compile_inputs,
                    proofs=[dict(path=str(path), sha256=sha) for path, sha in
                            ((INSTALL, INSTALL_SHA), (BUILD, BUILD_SHA), (projection, build["travel_projection_sha256"]),
                             (review, review_sha))])
    manifest_path = STAGE / "core_manifest_01.json"
    write_json(manifest_path, manifest)
    manifest_sha = digest(manifest_path)
    worker = STAGE / "deploy_core.ps1"
    installer(worker, manifest_sha)
    scope_file = STAGE / "scope_review.json"
    write_json(scope_file, dict(scope=scope, changed_paths=PATHS, candidate_sha256=DLL_SHA,
                                travel_runtime_admission="DEFERRED", gameplay="DEFERRED_TO_END_OF_STEP_5"))
    results = STAGE / "fixture_results.json"
    require(exercise(STAGE, manifest)["status"] == "PASS", "Installer fixtures did not pass")
    write_json(STAGE / "readiness.json", dict(status="READY_NOT_INSTALLED", manifest_sha256=manifest_sha,
               installer_sha256=digest(worker), fixture_result=results.name, fixture_result_sha256=digest(results),
               scope_review=scope_file.name, scope_review_sha256=digest(scope_file)))
    write_json(STAGE / "authorization_01.json", dict(user_reply="install", authorized_action=scope,
               paths=PATHS, manifest_sha256=manifest_sha, candidate_sha256=DLL_SHA,
               recorded_utc=datetime.now(timezone.utc).isoformat()))
    print(f"Prepared v{VERSION}, native DLL only.")


if __name__ == "__main__":
    main()
