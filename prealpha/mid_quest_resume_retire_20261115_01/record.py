"""Record the verified restoration build and its archived predecessor files."""

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json

from stage_install import DEPLOY, EPOCH, PRIOR, RECOVERY, ARCHIVE, STAGE, BEFORE, BEFORE_SHA
from stage_install import digest, load, payload_path, pin, require, write_json


def read(path):
    return load(path, digest(path))


def main():
    baseline = load(BEFORE, BEFORE_SHA)
    ready = read(DEPLOY / "readiness.json")
    transaction = DEPLOY / "core_manifest_01.json"
    manifest = load(transaction, ready["manifest_sha256"])
    paths = manifest["changing_paths"]
    auth = DEPLOY / "authorization_01.json"
    authorization = read(auth)
    require(authorization["changed_paths"] == paths and authorization["manifest_sha256"] == ready["manifest_sha256"],
            "Transaction scope differs from authorization")
    receipt = DEPLOY / RECOVERY / "journal.json"
    envelope = read(receipt)
    payload = envelope["payload_json"]
    require(envelope["schema"] == "PTFR_SNAPSHOT_CUTOFF_JOURNAL_V1" and
            sha256(payload.encode()).hexdigest().upper() == envelope["payload_sha256"], "Invalid journal")
    journal = json.loads(payload)
    require(journal["manifest_sha256"] == ready["manifest_sha256"] and journal["operation"] == "Install"
            and journal["state"] == "INSTALLED_VERIFIED" and set(journal["completed_paths"]) == set(paths)
            and journal["save_writes"] == journal["game_launches"] == 0, "Archive transaction did not commit")
    reports = [
        ("installation_report", DEPLOY / "install_01.json", "INSTALLED_VERIFIED"),
        ("post_install_verification", DEPLOY / "verify_01.json", "VERIFIED_AFTER"),
        ("rollback_readiness", DEPLOY / "rollback_readiness_01.json", "ROLLBACK_READY"),
    ]
    for label, path, status in reports:
        report = read(path)
        require(report["status"] == status and Path(report["receipt"]) == receipt, f"Missing {status}")
        if label == "installation_report":
            require(report["journal"] == journal, "Install report differs from committed journal")
    protected = journal["protection_after"]
    require(protected == journal["protection_before"] and protected["saves"]["mode"] == "EXACT_NAMES_BYTES_SHA",
            "Save or external preservation differs")
    game = Path(baseline["game_root"])
    archive_dir = receipt.parent / "old"
    installed, archived = {}, []
    for row in manifest["files"]:
        path = row["path"]
        pin(payload_path(game, path), row["after"], row["after_bytes"])
        installed[path] = dict(sha256=row["after"], bytes=row["after_bytes"])
        if path in paths:
            saved = pin(payload_path(archive_dir, path), row["before"], row["before_bytes"])
            pin(payload_path(receipt.parent / "new", path), row["after"], row["after_bytes"])
            archived.append(dict(game_path=path, path=str(saved), sha256=row["before"], bytes=row["before_bytes"]))
    for row in manifest["required_files"]:
        pin(payload_path(game, row["path"]), row["sha256"], row["bytes"])
    require(set(paths) == {row["game_path"] for row in archived} and len(installed) == 51, "Readback coverage drift")
    saves = sum(row["kind"] == "file" for row in protected["saves"]["files"])
    successor = {key: baseline[key] for key in ("schema", "game_root", "save_root", "archive_payloads", "required_files")}
    successor.update(core_epoch=EPOCH, predecessor_epoch=PRIOR, checkpoint_version=None,
                     recorded_utc=datetime.now(timezone.utc).isoformat(), recorded_timezone="America/Toronto",
                     archive_source=str(STAGE / "pack/source"), archive_sha256=installed[ARCHIVE]["sha256"],
                     core_files=[row | installed[row["path"]] for row in baseline["core_files"]], companion_files=[],
                     changed_paths=paths, archived_files=archived, archive_root=str(archive_dir),
                     predecessor_manifest=str(BEFORE), predecessor_manifest_sha256=BEFORE_SHA,
                     core_transaction=str(transaction), core_transaction_sha256=ready["manifest_sha256"],
                     save_files_preserved=True, save_file_count=saves, save_tree_sha256=protected["saves"]["tree_sha256"],
                     unmanaged_tree_sha256=protected["unmanaged"]["tree_sha256"], live_restore_enabled=False,
                     exact_resume_status="ARCHIVED", legacy_resume_admission="RETIRED",
                     gameplay="STARTUP_AND_SAVE_LOAD_PENDING")
    reports.extend([("installed_receipt", receipt, None), ("authorization_record", auth, None)])
    for label, path, _ in reports:
        successor[label] = str(path)
        successor[label + "_sha256"] = digest(path)
    output = DEPLOY / "deployment_01/installed_manifest_01.json"
    output.parent.mkdir()
    write_json(output, successor)
    print(f"Archived the six predecessor files and verified {saves} unchanged save files.")
    print(f"Installed manifest SHA-256 {digest(output)}")


if __name__ == "__main__":
    main()
