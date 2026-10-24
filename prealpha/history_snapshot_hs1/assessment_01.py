"""Read-only final installed HS1 audit; write a new local evidence receipt."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parent.parent
C = HERE / "candidate_01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main():
    mpath = C / "install_manifest_01.json"
    m = read(mpath)
    assert sha(mpath) == (C / "install_manifest_01.json.sha256").read_text().strip()
    game, backup = Path(m["game_root"]), Path(m["backup_root"])
    receipt_path = backup / "receipt.json"
    receipt = read(receipt_path)
    assert receipt["status"] == "HS1_INSTALLED_LIVE_PENDING"
    assert receipt["manifest_sha256"] == sha(mpath)
    installed = []
    for f in m["files"]:
        assert sha(game / f["target"]) == f["after"], f["target"]
        assert sha(C / "package" / f["target"]) == f["after"]
        if f["before"] is not None:
            assert sha(backup / f["target"]) == f["before"]
        installed.append(dict(f))
    for p in m["protected"] + m["proofs"]:
        assert sha(p["path"]) == p["sha256"], p["path"]
    reports = {
        "compile_04/result.json": "PASS_FULL_SCC_NOT_LIVE",
        "tests_02.json": "PASS_OFFLINE_NOT_LIVE",
        "readback_01.json": "PASS_COMPILED_READBACK_NOT_LIVE",
        "native_check_01.json": "PASS_CURRENT_NATIVE_TIMEOUT_BRANCH",
        "deployment_tests_01.json": "PASS_REAL_INSTALLER_FIXTURES",
    }
    for name, status in reports.items():
        assert read(C / name)["status"] == status
    assert read(C / "deployment_tests_01.json")["manifest_sha256"] == sha(mpath)
    catalogue = read(C / "catalogue.json")
    assert len(catalogue["rows"]) == 158
    pins = [mpath, receipt_path, C / "catalogue.json"] + [C / n for n in reports]
    pins += sorted(p for p in HERE.iterdir() if p.is_file())
    report = {
        "schema": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "HS1_INSTALLED_VERIFIED_LIVE_PENDING",
        "authorization": "User 2026-10-24 accepts a labelled current post-ending snapshot when no pre-ending snapshot exists.",
        "installed": installed,
        "protected_unchanged": len(m["protected"]),
        "save_files_unchanged": sum("Saved Games" in p["path"] for p in m["protected"]),
        "catalogue_fingerprint": catalogue["fingerprint"],
        "selected_roots": 158,
        "detailed_catalogue_entries": 140,
        "root_only_entries": 18,
        "new_quest_restoration_coverage": 0,
        "compile": {"sources": 85, "full_scc_equipmentex": True, "compiled_sha256": read(C / "compile_04/result.json")["compiled_sha256"]},
        "offline_exporter_source_checks": read(C / "tests_02.json")["count"],
        "installer_fixture_actions": read(C / "deployment_tests_01.json")["count"],
        "deployment_actions": ["Validate PASS", "Install PASS", "Verify PASS", "ValidateRollback PASS"],
        "rollback": "prealpha/history_snapshot_hs1/deploy_01.ps1 -Action ValidateRollback then -Action Rollback; only this package, file undo is not save undo",
        "backup": str(backup),
        "game_launched_by_assistant": False,
        "save_file_edits": 0,
        "manual_runtime_fact_writes": 0,
        "runtime_recovery_scope": ["PTFRPA2_Fault=0 only for the exact receipt-bound preparation timeout", "PTFRPA2_Finished=1 only after existing profile/housing/world/arrival acknowledgements"],
        "native_story_fact_setters_added": 0,
        "preserved": ["Existing persistent field identities and method signatures", "Completed/failed baseline entries, earned rewards, supported unfinished progress, existing owners", "Core/cosmetic stack and current 2.5 Tower archives"],
        "limitations": ["Native capture, serialization, CET game integration and reload await live verification", "Current post-ending fallback is not proof of pre-ending history", "Failed entries in the accepted baseline remain failed; this does not infer whether the ending caused failure", "Unsupported unfinished stages defer; 18 root-only entries gain no restoration implementation", "No non-pausing loading cover, refund cadence change or measured deployment speedup", "No arbitrary external JSON import or global latest-snapshot lookup", "Public release package has not been changed"],
        "next": "Cold-load retained post-ending AutoSave 8 or 9 without overwriting the original; verify snapshot file, setup, new manual save and reload. Test a genuine pre-cutoff branch separately.",
        "pins": {str(p.relative_to(WS)): sha(p) for p in pins},
    }
    out = C / "assessment_01.json"
    with out.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(json.dumps({"status": report["status"], "files": len(installed), "protected": report["protected_unchanged"], "saves": report["save_files_unchanged"], "assessment_sha256": sha(out)}))


if __name__ == "__main__":
    main()
