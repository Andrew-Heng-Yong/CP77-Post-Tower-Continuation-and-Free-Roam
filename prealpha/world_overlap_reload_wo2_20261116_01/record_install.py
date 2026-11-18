"""Write the exact installed WO2 pointer from guarded deployment evidence."""

from pathlib import Path
import json

from installer import GAME, HERE, OUT, PLAN, PLAN_SHA, RECEIPT, RECOVERY, SCRIPT, load_plan, sha

OUTPUT = HERE / "installed_manifest_01.json"
WO1 = HERE.parent / "world_overlap_20261116_01/work/deployment_01/installed_manifest_01.json"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    if OUTPUT.exists():
        raise RuntimeError("Preserve existing installed manifest")
    plan = load_plan()
    receipt = read(RECEIPT)
    journal_path = RECOVERY / "journal.json"
    journal = read(journal_path)
    old = read(WO1)
    if not (receipt["status"] == journal["state"] == "INSTALLED_VERIFIED") or \
       not (receipt["plan_sha256"] == journal["plan_sha256"] == PLAN_SHA):
        raise RuntimeError("Incomplete installed evidence")
    target = GAME / SCRIPT
    if sha(target) != plan["after"]["sha256"]:
        raise RuntimeError("Installed script drift")
    if sha(RECOVERY / "old" / SCRIPT) != plan["before"]["sha256"]:
        raise RuntimeError("Rollback backup drift")
    if old["archive_sha256"] != plan["core_after"][0]["sha256"]:
        raise RuntimeError("Archive lineage drift")
    result = {
        "schema": "PTFR_INSTALLED_CONSOLIDATED_WO2_V1",
        "status": "INSTALLED_VERIFIED_LIVE_RETEST_PENDING",
        "core_epoch": "WO2_FRESH_LOAD_STREET_CLEANUP",
        "predecessor_epoch": "BV1_BODY_VIEW_REVERT",
        "authorization": "User asked to fix the same raised street meshes on immediate fresh load of AutoSave-16.",
        "game_root": plan["game_root"], "save_root": plan["save_root"],
        "core_files": plan["core_after"], "required_files": plan["required"],
        "ifp_files": plan["ifp"], "preferences_at_install": plan["preferences"],
        "archive_payloads": old["archive_payloads"], "archive_sha256": old["archive_sha256"],
        "archive_source": old["archive_source"],
        "changed_paths": [SCRIPT], "unchanged_core_paths": 50,
        "save_files_preserved": receipt["saves_preserved"],
        "candidate_manifest": str(OUT / "core_manifest_01.json"),
        "candidate_manifest_sha256": sha(OUT / "core_manifest_01.json"),
        "compile_assessment": str(OUT / "compile_01/assessment.json"),
        "compile_assessment_sha256": sha(OUT / "compile_01/assessment.json"),
        "offline_assessment": str(OUT / "assessment.json"),
        "offline_assessment_sha256": sha(OUT / "assessment.json"),
        "installation_plan": str(PLAN), "installation_plan_sha256": PLAN_SHA,
        "installation_receipt": str(RECEIPT), "installation_receipt_sha256": sha(RECEIPT),
        "recovery_journal": str(journal_path), "recovery_journal_sha256": sha(journal_path),
        "rollback_backup": str(RECOVERY / "old" / SCRIPT),
        "game_launches": 0, "save_writes": 0,
        "gameplay": "PENDING_AUTOSAVE16_IMMEDIATE_LOAD_VISUAL_AND_COLLISION_CHECK",
    }
    with OUTPUT.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print("RECORDED: exact 51-path WO2 installation, one script changed, live test pending")


if __name__ == "__main__":
    main()
