"""Verify and install the single archive that repairs Misty's rooftop seat."""

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

import stage
from build import EXE, EXE_SHA, plain, read, row, safe, sha, verify_rows, write
from deploy import SAVES, archive_environment, closed, replace, snapshot, verify_protected, verify_providers


ROOT, GAME, ARCHIVE = stage.ROOT, stage.GAME, stage.ARCHIVE
PACKAGE = stage.CANDIDATE / "package"
CORE = stage.CANDIDATE / "core_manifest.json"
CORE_SHA = "A49330B7B99C6A41A7B941868C52FCC5F900E2E41A71039714451AC7748EBC8C"
ASSETS = stage.ASSETS / "readback.json"
DEPLOY = ROOT / "deployment_01"
PLAN = DEPLOY / "install_plan.json"
FIXTURES = DEPLOY / "fixture_results.json"
RECOVERY = DEPLOY / "recovery"
RECEIPT = RECOVERY / "installed.json"
MANIFEST = ROOT / "installed_manifest.json"


def archive_row(rows):
    selected = [item for item in rows if item["path"] == ARCHIVE]
    if len(selected) != 1:
        raise RuntimeError("Expected one managed chair archive")
    return selected[0]


def validate_package():
    if sha(CORE) != CORE_SHA or sha(stage.BASELINE) != stage.BASELINE_SHA:
        raise RuntimeError("Pinned manifest changed")
    core, base, assets = read(CORE), read(stage.BASELINE), read(ASSETS)
    if (core["baseline_sha256"] != stage.BASELINE_SHA or core["asset_assessment_sha256"] != sha(ASSETS)
            or core["status"] != "STAGED_OFFLINE" or core["changed_paths"] != [ARCHIVE]
            or assets["status"] != "MEMBERS_VERIFIED" or assets["scene_depot"] != stage.SEAT_DEPOT
            or assets["package_file"] != archive_row(core["core_files"])
            or (assets["checked_members"], assets["preserved_members"]) != (1751, 1750)):
        raise RuntimeError("Unqualified archive repair")
    before, after = base["core_files"], core["core_files"]
    if (len(after) != 51 or [r["path"] for r in before] != [r["path"] for r in after]
            or [r["path"] for r, old in zip(after, before, strict=True) if r != old] != [ARCHIVE]):
        raise RuntimeError("Unexpected package changes")
    verify_rows(PACKAGE, after)
    stage.verify_scene(assets)
    return base, core, assets


def prepare():
    closed()
    base, core, assets = validate_package()
    stage.verified_baseline()
    if base["game_root"] != str(GAME) or base["save_root"] != str(SAVES):
        raise RuntimeError("Installation root changed")
    if read(FIXTURES)["status"] != "PASS":
        raise RuntimeError("Deployment fixtures missing")
    environment = archive_environment(GAME)
    verify_providers({"archives": assets["archive_provider_scan"]}, environment, archive_row(base["core_files"]))
    previous_plan = Path(base["installation_plan"])
    if (sha(previous_plan) != base["installation_plan_sha256"]
            or read(previous_plan)["archive_environment"]["xl"] != environment["xl"]):
        raise RuntimeError("ArchiveXL environment changed since the chair phase was verified")
    preferences = [row(GAME, r["path"]) for r in base["preferences_at_install"]]
    write(PLAN, {"baseline_sha256": stage.BASELINE_SHA, "candidate_sha256": CORE_SHA,
                 "fixture_sha256": sha(FIXTURES), "paths": [ARCHIVE], "game_root": str(GAME),
                 "save_root": str(SAVES), "package_root": str(PACKAGE),
                 "before": base["core_files"], "after": core["core_files"],
                 "required_files": base["required_files"], "archivexl_files": base["archivexl_files"],
                 "ifp_files": base["ifp_files"], "preferences": preferences,
                 "archive_environment": environment, "saved_files": snapshot(SAVES)})
    print("Prepared plan", sha(PLAN))


def recover_archive(plan, game, backup, guard):
    old, new = archive_row(plan["before"]), archive_row(plan["after"])
    verify_rows(backup, [old])
    current = row(game, ARCHIVE)
    if current == new:
        replace(safe(backup, ARCHIVE), safe(game, ARCHIVE), new, old, guard)
    elif current != old:
        raise RuntimeError("Unknown archive drift, recovery refused")
    verify_rows(game, plan["before"])


def install_archive(plan, game, saves, package, recovery, guard, check_after=None):
    guard()
    verify_rows(game, plan["before"])
    verify_rows(package, plan["after"])
    verify_protected(plan, game, saves)
    old, new = archive_row(plan["before"]), archive_row(plan["after"])
    plain(recovery)
    recovery.mkdir(exist_ok=False)
    backup = recovery / "old"
    destination = safe(backup, ARCHIVE)
    destination.parent.mkdir(parents=True)
    shutil.copyfile(safe(game, ARCHIVE), destination)
    verify_rows(backup, [old])
    write(recovery / "prepared.json", {"paths": [ARCHIVE], "before": old, "after": new})
    try:
        replace(safe(package, ARCHIVE), safe(game, ARCHIVE), old, new, guard)
        guard()
        verify_rows(game, plan["after"])
        verify_protected(plan, game, saves)
        if check_after:
            check_after()
        protected = plan["required_files"] + plan["archivexl_files"] + plan["ifp_files"] + plan["preferences"]
        write(recovery / "installed.json", {
            "status": "INSTALLED_VERIFIED", "changed_paths": [ARCHIVE], "core_files": len(plan["after"]),
            "protected_files": len({r["path"] for r in protected}),
            "save_files_preserved": len(plan["saved_files"]),
            "protected_archive_providers": len(plan["archive_environment"]["archives"]),
            "protected_xl_files": len(plan["archive_environment"]["xl"]), "game_launches": 0, "save_writes": 0})
    except Exception:
        guard()
        recover_archive(plan, game, backup, guard)
        verify_protected(plan, game, saves)
        write(recovery / "recovered.json", {"status": "RESTORED_PREDECESSOR_VERIFIED"})
        raise


def verified_plan(digest):
    if sha(PLAN) != digest or sha(safe(GAME, EXE)) != EXE_SHA:
        raise RuntimeError("Install plan or game executable changed")
    plan = read(PLAN)
    base, core, _ = validate_package()
    if (plan["candidate_sha256"] != CORE_SHA or plan["fixture_sha256"] != sha(FIXTURES)
            or plan["baseline_sha256"] != stage.BASELINE_SHA or plan["paths"] != [ARCHIVE]
            or (plan["game_root"], plan["save_root"], plan["package_root"]) != (str(GAME), str(SAVES), str(PACKAGE))
            or plan["before"] != base["core_files"] or plan["after"] != core["core_files"]):
        raise RuntimeError("Plan does not match verified inputs")
    return plan


def record(plan):
    receipt = read(RECEIPT)
    if receipt["status"] != "INSTALLED_VERIFIED" or receipt["changed_paths"] != [ARCHIVE]:
        raise RuntimeError("Missing verified archive installation")
    base = read(stage.BASELINE)
    write(MANIFEST, {
        **base, "schema": "PTFR_INSTALLED_MISTY_ROOFTOP_SEAT_ANIMATION_REPAIR_V1",
        "recorded_utc": datetime.now(timezone.utc).isoformat(), "core_epoch": "MISTY_ROOFTOP_SEAT_ANIMATION_REPAIR",
        "predecessor_manifest": str(stage.BASELINE), "predecessor_manifest_sha256": stage.BASELINE_SHA,
        "core_manifest": str(CORE), "core_manifest_sha256": CORE_SHA, "core_files": plan["after"],
        "archive_sha256": archive_row(plan["after"])["sha256"], "changed_paths": [ARCHIVE],
        "asset_assessment": str(ASSETS), "asset_assessment_sha256": sha(ASSETS),
        "preferences_at_install": plan["preferences"], "installation_plan": str(PLAN),
        "installation_plan_sha256": sha(PLAN), "installation_receipt": str(RECEIPT),
        "installation_receipt_sha256": sha(RECEIPT), "rollback_backup": str(RECOVERY / "old"),
        "rollback_verified": True, "save_files_preserved": receipt["save_files_preserved"],
        "autosave_16_sha256": next((r["sha256"] for r in plan["saved_files"] if r["path"] == "AutoSave-16/sav.dat"), None),
        "gameplay": "PENDING_USER_RETEST"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "install", "record", "recover"))
    parser.add_argument("--plan-sha")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
        return
    closed()
    plan = verified_plan(args.plan_sha)
    if args.action == "install":
        stage.verified_baseline()
        install_archive(plan, GAME, SAVES, PACKAGE, RECOVERY, closed)
        print("Installed and verified rooftop seat animation archive.")
    elif args.action == "recover":
        if read(RECOVERY / "prepared.json")["before"] != archive_row(plan["before"]):
            raise RuntimeError("Recovery record mismatch")
        plan["saved_files"] = snapshot(SAVES)
        plan["preferences"] = [row(GAME, r["path"]) for r in plan["preferences"]]
        verify_protected(plan, GAME, SAVES)
        verify_rows(GAME, [r for r in plan["before"] if r["path"] != ARCHIVE])
        recover_archive(plan, GAME, RECOVERY / "old", closed)
        verify_protected(plan, GAME, SAVES)
        write(RECOVERY / "recovered.json", {"status": "RESTORED_PREDECESSOR_VERIFIED"})
    else:
        verify_rows(GAME, plan["after"])
        verify_rows(RECOVERY / "old", [archive_row(plan["before"])])
        verify_protected(plan, GAME, SAVES)
        record(plan)
        print("Recorded installed manifest", sha(MANIFEST))


if __name__ == "__main__":
    main()
