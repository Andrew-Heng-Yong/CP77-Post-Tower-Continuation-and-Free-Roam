"""Record the verified Core installation and the off-game archive."""

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json

from stage_transaction import CURRENT, CURRENT_SHA, DONOR, DONOR_SHA, CHANGES, REMOVALS, RECOVERY
from stage_transaction import STAGE, EPOCH, PRIOR, CORE_REPLACEMENTS, digest, load, payload_path, pin, require, write_json


def read(path):
    return load(path, digest(path))


def main():
    baseline = load(CURRENT, CURRENT_SHA)
    ready = read(STAGE / "readiness.json")
    transaction = STAGE / "core_manifest_01.json"
    manifest = load(transaction, ready["manifest_sha256"])
    pin(STAGE / "deploy_core.ps1", ready["installer_sha256"])
    authorization = STAGE / "authorization_01.json"
    auth = read(authorization)
    require(auth["changed_paths"] == CHANGES and auth["manifest_sha256"] == ready["manifest_sha256"],
            "Archive authorization differs from transaction scope")
    require(manifest["source_epoch"] == EPOCH and manifest["predecessor_epoch"] == PRIOR and
            manifest["changing_paths"] == CHANGES and manifest["removed_paths"] == REMOVALS, "Wrong archive manifest")
    receipt = STAGE / RECOVERY / "journal.json"
    envelope = read(receipt)
    payload = envelope["payload_json"]
    require(envelope["schema"] == "PTFR_SNAPSHOT_CUTOFF_JOURNAL_V1" and
            sha256(payload.encode()).hexdigest().upper() == envelope["payload_sha256"], "Journal hash drift")
    journal = json.loads(payload)
    require(journal["state"] == "INSTALLED_VERIFIED" and journal["operation"] == "Install" and
            journal["manifest_sha256"] == ready["manifest_sha256"] and journal["completed_paths"] == CHANGES and
            journal["save_writes"] == journal["game_launches"] == 0, "Archive transaction did not commit")
    reports = [
        ("installation_report", STAGE / "install_01.json", "INSTALLED_VERIFIED"),
        ("post_install_verification", STAGE / "verify_01.json", "VERIFIED_AFTER"),
        ("rollback_readiness", STAGE / "rollback_readiness_01.json", "ROLLBACK_READY"),
    ]
    for label, path, status in reports:
        result = read(path)
        require(result["status"] == status and Path(result["receipt"]) == receipt, f"Missing {status}")
        if label == "installation_report":
            require(result["journal"] == journal, "Install result differs from committed journal")
    protection = journal["protection_after"]
    require(protection == journal["protection_before"] and protection["saves"]["mode"] == "EXACT_NAMES_BYTES_SHA",
            "Preservation snapshots differ")
    game = Path(manifest["game_root"])
    installed, archived = {}, []
    for row in manifest["files"]:
        path = row["path"]
        current = payload_path(game, path)
        if path in CHANGES:
            old = pin(payload_path(receipt.parent / "old", path), row["before"], row["before_bytes"])
            archived.append(dict(game_path=path, archive_path=str(old), sha256=row["before"], bytes=row["before_bytes"]))
        if path in REMOVALS:
            require(not current.exists() and not current.is_symlink(), f"Archived path still present: {current}")
        else:
            pin(current, row["after"], row["after_bytes"])
            installed[path] = dict(path=path, sha256=row["after"], bytes=row["after_bytes"])
            if path in CORE_REPLACEMENTS:
                pin(payload_path(receipt.parent / "new", path), row["after"], row["after_bytes"])
    for row in manifest["required_files"]:
        pin(payload_path(game, row["path"]), row["sha256"], row["bytes"])
    require(len(installed) == 51 and len(archived) == len(CHANGES), "Installed or archived inventory drift")
    save_count = sum(row["kind"] == "file" for row in protection["saves"]["files"])
    successor = {key: baseline[key] for key in ("schema", "game_root", "save_root", "archive_source",
                 "archive_payloads", "archive_sha256", "required_files")}
    successor.update(core_epoch=EPOCH, predecessor_epoch=PRIOR, checkpoint_version=None,
                     recorded_utc=datetime.now(timezone.utc).isoformat(), recorded_timezone="America/Toronto",
                     core_files=[row | installed[row["path"]] for row in baseline["core_files"]], companion_files=[],
                     changed_paths=CHANGES, archived_files=archived, archive_root=str(receipt.parent / "old"),
                     removed_paths=REMOVALS, live_restore_enabled=False, exact_resume_status="ARCHIVED",
                     predecessor_manifest=str(CURRENT), predecessor_manifest_sha256=CURRENT_SHA,
                     source_donor=str(DONOR), source_donor_sha256=DONOR_SHA,
                     core_transaction=str(transaction), core_transaction_sha256=ready["manifest_sha256"],
                     save_files_preserved=True, save_file_count=save_count,
                     save_tree_sha256=protection["saves"]["tree_sha256"],
                     unmanaged_tree_sha256=protection["unmanaged"]["tree_sha256"],
                     gameplay="STARTUP_AND_SAVE_LOAD_PENDING")
    reports.extend([("installed_receipt", receipt, None), ("authorization_record", authorization, None)])
    for label, path, _ in reports:
        successor[label] = str(path)
        successor[label + "_sha256"] = digest(path)
    output = STAGE / "deployment_01/installed_manifest_01.json"
    output.parent.mkdir()
    write_json(output, successor)
    print(f"Archived {len(archived)} original files, verified 51 Core files and preserved {save_count} saves.")
    print(f"Installed manifest SHA-256 {digest(output)}")


if __name__ == "__main__":
    main()
