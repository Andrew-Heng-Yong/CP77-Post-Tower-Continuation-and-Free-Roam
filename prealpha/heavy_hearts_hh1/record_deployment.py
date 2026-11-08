"""Read back the committed HH1 transaction and record its installed baseline."""

import hashlib
import json
from pathlib import Path

from prepare_deployment import ALLOWED, ARCHIVE, CANDIDATE, HERE, RECOVERY, TRANSACTION, checked, read, sha, write


def main():
    out = HERE / "deployment_01"
    transaction_path = HERE / TRANSACTION
    manifest = read(transaction_path)
    game = Path(manifest["game_root"])
    saves = Path(manifest["save_root"])
    recovery = HERE / RECOVERY
    ready = read(HERE / "readiness.json")
    checked(transaction_path, ready["manifest_sha256"])
    checked(HERE / "deploy_core.ps1", ready["installer_sha256"])
    receipts = {}
    for name, state in (("preflight", "PREFLIGHT_READY"), ("install", "INSTALLED_VERIFIED"),
                        ("verify", "VERIFIED_AFTER"), ("rollback_ready", "ROLLBACK_READY")):
        path = out / (name + ".json")
        assert read(path)["status"] == state
        receipts[name] = {"path": str(path), "sha256": sha(path)}
    envelope = read(recovery / "journal.json")
    assert envelope["schema"] == "PTFR_HH1_JOURNAL_V1"
    assert hashlib.sha256(envelope["payload_json"].encode()).hexdigest().upper() == envelope["payload_sha256"]
    journal = json.loads(envelope["payload_json"])
    assert journal["operation"] == "Install" and journal["state"] == "INSTALLED_VERIFIED"
    assert journal["manifest_sha256"] == sha(transaction_path) and journal["completed_paths"] == ALLOWED
    assert journal["save_writes"] == journal["game_launches"] == 0
    before, after = journal["protection_before"], journal["protection_after"]
    assert all(before[k]["tree_sha256"] == after[k]["tree_sha256"] for k in ("saves", "unmanaged"))
    assert before["dependencies"] == after["dependencies"]
    assert read(out / "preflight.json")["protection"]["saves"]["tree_sha256"] == before["saves"]["tree_sha256"]
    save_rows = {r["path"]: r for r in before["saves"]["files"] if r["kind"] == "file"}
    assert set(save_rows) == {p.relative_to(saves).as_posix() for p in saves.rglob("*") if p.is_file()}
    for relative, row in save_rows.items():
        checked(saves / relative, row["sha256"])

    core, payloads = [], []
    for row in manifest["files"]:
        relative = row["path"]
        path = checked(game / relative, row["after"])
        assert path.stat().st_size == row["after_bytes"]
        checked(Path(manifest["package_root"]) / relative, row["after"])
        core.append({"path": relative, "sha256": row["after"], "bytes": row["after_bytes"]})
        if relative in ALLOWED:
            for side, key in (("old", "before"), ("new", "after")):
                path = checked(recovery / side / relative, row[key])
                payloads.append({"path": str(path), "sha256": row[key], "bytes": path.stat().st_size})
    for row in manifest["required_files"]:
        checked(game / row["path"], row["sha256"])
    for path, digest in manifest["compile_inputs"].items():
        checked(path, digest)
    for proof in manifest["proofs"]:
        checked(proof["path"], proof["sha256"])
    checked(manifest["zip"], manifest["zip_sha256"])
    package_manifest = CANDIDATE / "package_manifest.json"
    assert core == read(package_manifest)["files"]
    verification_path = out / "verification.json"
    write(verification_path, {
        "status": "PASS_HH1_INSTALLED_AND_PRESERVED", "core_epoch": "HH1", "core_files": len(core),
        "required_files": len(manifest["required_files"]), "save_files": len(save_rows),
        "changed_paths": ALLOWED, "old_and_new_recovery_payloads": payloads,
        "unmanaged_metadata_unchanged": True, "all_save_names_and_hashes_unchanged": True,
        "save_or_fact_writes": 0, "game_launches": 0, "rollback_ready": True,
        "gameplay_qualification": "UNTESTED",
    })
    core_index = {r["path"]: r for r in core}
    write(out / "installed_manifest_01.json", {
        "schema": "PTFR_HH1_CURRENT_INSTALLED_V1", "core_epoch": "HH1", "predecessor_epoch": "QR19",
        "installed_utc": journal["updated_utc"], "authorization": "User requested 'install pls' for Heavy Hearts HH1.",
        "game_root": str(game), "save_root": str(saves),
        "core_source_epoch": str(package_manifest), "core_source_epoch_sha256": sha(package_manifest),
        "transaction_manifest": str(transaction_path), "transaction_manifest_sha256": sha(transaction_path),
        "core_files": core, "required_files": manifest["required_files"],
        "diagnostic_code_profile": "QR10D01 candidate02 / D00E config",
        "archive_payloads": len(read(package_manifest)["source_resources"]),
        "archive_sha256": core_index[ARCHIVE]["sha256"], "recovery_root": str(recovery),
        "verification": str(verification_path), "verification_sha256": sha(verification_path),
        "receipt_files": receipts, "gameplay_qualification": "Heavy Hearts workspot recovery pending human test.",
    })
    report = f"""# Heavy Hearts HH1 installed

The authorized HH1 transaction replaced the consolidated archive and its XL registration file. Closed-game preflight, installation, verification and rollback-readiness checks passed. The exact QR19 predecessor files are preserved in `../{RECOVERY}/old/`.

All {len(core)} Core paths and {len(manifest['required_files'])} dependency and diagnostic files match. All {len(save_rows)} save files retained their names and bytes across installation. Unmanaged game metadata also matches the transaction baseline.

The installed archive contains 1,581 payloads, including HH1's 101 passive workspots and their guarded owners. Live workspot recovery and save/reload still need qualification. Two guard spots with external look-at dependencies remain outside the candidate.

[Installed manifest](installed_manifest_01.json), [preservation verification](verification.json) and [gameplay test command](../REPORT.md).
"""
    with (out / "REPORT.md").open("x", encoding="utf-8", newline="\n") as file:
        file.write(report)
    print(f"Installed HH1 verified. {len(core)} Core, {len(manifest['required_files'])} dependencies, {len(save_rows)} save files.")


if __name__ == "__main__":
    main()
