"""Verify the completed Cassius installation and record the new baseline."""

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json

from build import INSTALL, INSTALL_SHA, digest, load, payload_path, pin, require, write_json
from prepare_install import BUILD, BUILD_SHA, DLL_SHA, EPOCH, PATHS, PRIOR, STAGE, VERSION


def read(path):
    return load(path, digest(path))


def record():
    readiness = read(STAGE / "readiness.json")
    transaction = STAGE / "core_manifest_01.json"
    manifest_sha = readiness["manifest_sha256"]
    staged = load(transaction, manifest_sha)
    pin(STAGE / "deploy_core.ps1", readiness["installer_sha256"])
    baseline = load(INSTALL, INSTALL_SHA)
    require(baseline["core_epoch"] == staged["predecessor_epoch"] == PRIOR
            and staged["source_epoch"] == EPOCH and staged["changing_paths"] == PATHS,
            "Installed predecessor or staged scope drift")
    authorization_path = STAGE / "authorization_01.json"
    auth = read(authorization_path)
    require(auth["user_reply"] == "install" and auth["paths"] == PATHS
            and auth["manifest_sha256"] == manifest_sha and auth["candidate_sha256"] == DLL_SHA,
            "Authorization does not cover the staged files")
    receipt = STAGE / "recovery/cassius_handoff_01/journal.json"
    envelope = read(receipt)
    payload = envelope["payload_json"]
    require(envelope["schema"] == "PTFR_SNAPSHOT_CUTOFF_JOURNAL_V1"
            and sha256(payload.encode("utf-8")).hexdigest().upper() == envelope["payload_sha256"],
            "Transaction journal hash drift")
    journal = json.loads(payload)
    reports = [
        ("installation_report", STAGE / "install_01.json", "INSTALLED_VERIFIED"),
        ("post_install_verification", STAGE / "verify_01.json", "VERIFIED_AFTER"),
        ("rollback_readiness", STAGE / "rollback_readiness_01.json", "ROLLBACK_READY"),
    ]
    for label, path, status in reports:
        data = read(path)
        require(data["status"] == status and Path(data["receipt"]) == receipt, f"Missing {status}")
        if label == "installation_report":
            require(data["journal"] == journal, "Installation report and committed journal disagree")
    require(journal["manifest_sha256"] == manifest_sha and journal["operation"] == "Install"
            and journal["state"] == "INSTALLED_VERIFIED" and journal["completed_paths"] == PATHS
            and journal["game_root"] == staged["game_root"] and journal["save_root"] == staged["save_root"]
            and journal["save_writes"] == journal["game_launches"] == 0, "Committed install scope drift")
    before, after = journal["protection_before"], journal["protection_after"]
    require(before == after and after["saves"]["mode"] == "EXACT_NAMES_BYTES_SHA",
            "Protection snapshots differ")

    game = Path(staged["game_root"])
    reports.extend([("installed_receipt", receipt, None), ("authorization_record", authorization_path, None)])
    summary = {field: baseline[field] for field in ("schema", "game_root", "save_root",
               "archive_source", "archive_payloads", "archive_sha256", "required_files")}
    new_rows = {}
    for row in staged["files"]:
        path, expected, length = row["path"], row["after"], row["after_bytes"]
        pin(payload_path(game, path), expected, length)
        new_rows[path] = dict(path=path, sha256=expected, bytes=length)
        if path in PATHS:
            pin(payload_path(receipt.parent / "old", path), row["before"], row["before_bytes"])
            pin(payload_path(receipt.parent / "new", path), expected, length)
    for row in staged["required_files"]:
        pin(payload_path(game, row["path"]), row["sha256"], row["bytes"])
    for group in ("core_files", "companion_files"):
        summary[group] = [baseline_row | new_rows[baseline_row["path"]] for baseline_row in baseline[group]]
    save_count = sum(row["kind"] == "file" for row in after["saves"]["files"])
    summary.update(
        core_epoch=EPOCH, predecessor_epoch=PRIOR, checkpoint_version=VERSION,
        recorded_utc=datetime.now(timezone.utc).isoformat(), recorded_timezone="America/Toronto",
        changed_paths=PATHS, source_candidate=str(BUILD), source_candidate_sha256=BUILD_SHA,
        predecessor_manifest=str(INSTALL), predecessor_manifest_sha256=INSTALL_SHA,
        core_transaction=str(transaction), core_transaction_sha256=manifest_sha,
        save_files_preserved=True, save_file_count=save_count, save_tree_sha256=after["saves"]["tree_sha256"],
        unmanaged_tree_sha256=after["unmanaged"]["tree_sha256"], live_restore_enabled=True,
        gameplay="DEFERRED_TO_END_OF_STEP_5",
    )
    for label, path, _ in reports:
        summary[label] = str(path)
        summary[label + "_sha256"] = digest(path)
    output = STAGE / "deployment_01/installed_manifest_01.json"
    output.parent.mkdir()
    write_json(output, summary)
    print(f"Installed v{VERSION}, {save_count} save files preserved. Manifest SHA-256 {digest(output)}")


if __name__ == "__main__":
    record()
