"""Verify the committed QR18 install and record the current composite."""
import json
import hashlib
from pathlib import Path

from prepare_deployment import ALLOWED, ARCHIVE, HERE, RECOVERY, TRANSACTION, checked, read, sha, write


def main():
    out = HERE / "deployment_01"
    manifest = HERE / TRANSACTION
    m = read(manifest)
    game = Path(m["game_root"])
    saves = Path(m["save_root"])
    recovery = HERE / RECOVERY
    readiness = read(HERE / "readiness.json")
    checked(manifest, readiness["manifest_sha256"])
    checked(HERE / "deploy_core.ps1", readiness["installer_sha256"])
    receipts = {}
    for name, state in (("preflight", "PREFLIGHT_READY"), ("install", "INSTALLED_VERIFIED"),
                        ("verify", "VERIFIED_AFTER"), ("rollback_ready", "ROLLBACK_READY")):
        p = out / (name + ".json")
        data = read(p)
        assert data["status"] == state, (name, data["status"])
        receipts[name] = {"path": str(p), "sha256": sha(p)}
    envelope = read(recovery / "journal.json")
    assert envelope["schema"] == "PTFR_QR18_JOURNAL_V1"
    assert hashlib.sha256(envelope["payload_json"].encode()).hexdigest().upper() == envelope["payload_sha256"]
    journal = json.loads(envelope["payload_json"])
    assert journal["operation"] == "Install" and journal["state"] == "INSTALLED_VERIFIED"
    assert journal["manifest_sha256"] == sha(manifest) and journal["completed_paths"] == ALLOWED
    assert journal["save_writes"] == journal["game_launches"] == 0
    before, after = journal["protection_before"], journal["protection_after"]
    for key in ("saves", "unmanaged"):
        assert before[key]["tree_sha256"] == after[key]["tree_sha256"]
    assert before["dependencies"] == after["dependencies"]
    assert read(out / "preflight.json")["protection"]["saves"]["tree_sha256"] == before["saves"]["tree_sha256"]
    save_rows = {r["path"]: r for r in before["saves"]["files"] if r["kind"] == "file"}
    assert set(save_rows) == {p.relative_to(saves).as_posix() for p in saves.rglob("*") if p.is_file()}
    for name, row in save_rows.items():
        checked(saves / name, row["sha256"])

    payloads = []
    core = {}
    for row in m["files"]:
        rel = row["path"]
        p = checked(game / rel, row["after"])
        assert p.stat().st_size == row["after_bytes"]
        core[rel] = {"path": rel, "sha256": row["after"], "bytes": row["after_bytes"]}
        checked(Path(m["package_root"]) / rel, row["after"])
        if rel in ALLOWED:
            for side, expected in (("old", "before"), ("new", "after")):
                p = checked(recovery / side / rel, row[expected])
                payloads.append({"path": str(p), "sha256": row[expected], "bytes": p.stat().st_size})
    for row in m["required_files"]:
        checked(game / row["path"], row["sha256"])
    for path, digest in m["compile_inputs"].items():
        rel = Path(path).relative_to(game).as_posix()
        checked(path, core[rel]["sha256"] if rel in core else digest)
    for proof in m["proofs"]:
        checked(proof["path"], proof["sha256"])
    checked(m["zip"], m["zip_sha256"])
    verification_path = out / "verification.json"
    write(verification_path, {
        "status": "PASS_QR18_INSTALLED_AND_PRESERVED", "core_epoch": "QR18", "core_files": len(core),
        "required_files": len(m["required_files"]), "save_files": len(save_rows), "changed_paths": ALLOWED,
        "old_and_new_recovery_payloads": payloads, "unmanaged_metadata_unchanged": True,
        "all_save_names_and_hashes_unchanged": True, "save_or_fact_writes": 0, "game_launches": 0,
        "rollback_ready": True, "gameplay_qualification": "UNTESTED",
    })
    package_manifest = HERE / "candidate_01/package_manifest.json"
    write(out / "installed_manifest_01.json", {
        "schema": "PTFR_QR18_CURRENT_INSTALLED_V1", "core_epoch": "QR18", "predecessor_epoch": "QR13:02",
        "installed_utc": journal["updated_utc"], "authorization": "User explicitly requested install.",
        "game_root": str(game), "save_root": str(saves),
        "core_source_epoch": str(package_manifest), "core_source_epoch_sha256": sha(package_manifest),
        "transaction_manifest": str(manifest), "transaction_manifest_sha256": sha(manifest),
        "core_files": list(core.values()), "required_files": m["required_files"],
        "diagnostic_code_profile": "QR10D01 candidate02 / D00E config",
        "archive_payloads": len(read(package_manifest)["source_resources"]),
        "archive_sha256": core[ARCHIVE]["sha256"], "recovery_root": str(recovery),
        "verification": str(verification_path), "verification_sha256": sha(verification_path),
        "receipt_files": receipts, "gameplay_qualification": "Installation verified. No eligible local fixture proven.",
    })
    report = f"""# QR18 installed

The user's explicit install request authorized replacement of the consolidated archive and S23 script. The closed-game preflight, transaction, readback and rollback-readiness checks passed. The original QR13:02 files are backed up under `../{RECOVERY}/old/`.

All {len(core)} Core files and {len(m['required_files'])} dependency and diagnostic files match their expected bytes. All {len(save_rows)} save files match the fresh preflight and install snapshots. The unmanaged game metadata and all other managed paths match across the install. The installed compiler cache and validated diagnostics were preserved.

The new Core includes both portable Brendan fallbacks. This is installation evidence. No game was launched and the new quest routes remain untested in gameplay.

[Current installed manifest](installed_manifest_01.json) and [preservation checks](verification.json)
"""
    with (out / "REPORT.md").open("x", encoding="utf-8", newline="\n") as f:
        f.write(report)
    print(f"Verified QR18. {len(core)} Core files, {len(m['required_files'])} dependencies, {len(save_rows)} save files.")


if __name__ == "__main__":
    main()
