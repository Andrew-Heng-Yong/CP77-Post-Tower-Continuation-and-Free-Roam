"""Record the verified stage 01 installation from the transaction reports."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import stat

from candidate_common import (EPOCH, HERE, INSTALLED, INSTALLED_SHA, OLD_DLL_SHA, PRIOR_EPOCH, SAVE_FIXTURE,
                              SCHEMA, TARGET, VERSION, digest, load, payload_path, pin, require,
                              workspace_file, write_json)


STAGE = HERE / "staged_01"
MANIFEST = STAGE / "core_manifest_01.json"
MANIFEST_SHA = "30A84D9C9EE2D3602C11D07D55A0A4142F713A0525670E05F4E813EA8F99324B"
INSTALLER_SHA = "AC3C04060C3502EA646E3E72905F6A20DBA6FC84C0194AED075664D15CBACEDC"
CANDIDATE_SHA = "98840F6F4AC2BAE2FC9A8020D66F6D7DD70EB93FB49AB2BA562AFA50CFFC3AB9"
BUILD = HERE / "run_06/assessment.json"
BUILD_SHA = "D11C0EC16DD3704CE0042C2109826AD1BB6105E193D487051BDA4DC655376669"
RECOVERY = STAGE / "recovery/ms31_live_handoff_01"
DEFAULT_OUTPUT = STAGE / "deployment_01/installed_manifest_01.json"
UNIX_EPOCH_TICKS = 621355968000000000


def report(path):
    path = workspace_file(path)
    require(path.is_relative_to(STAGE), f"Report belongs outside stage 01: {path}")
    value = digest(path)
    return path, value, load(path, value)


def timestamp(recorded):
    value = datetime.fromisoformat(recorded)
    require(value.utcoffset() is not None, "Expected a timezone-qualified transaction date")
    return value


def validate_authorization(data, journal):
    require(isinstance(data["user_reply"], str) and data["user_reply"].strip()
            and VERSION in data["authorized_action"] and "install" in data["authorized_action"].lower()
            and data["paths"] == [TARGET] and data["manifest_sha256"] == MANIFEST_SHA
            and data["candidate_sha256"] == CANDIDATE_SHA, "Authorization scope differs from the staged DLL")
    require(timestamp(data["recorded_utc"]) <= timestamp(journal["created_utc"])
            <= timestamp(journal["updated_utc"]), "Authorization or journal timestamps are out of order")


def journal_payload(record):
    payload = record["payload_json"]
    require(record["schema"] == "PTFR_SNAPSHOT_CUTOFF_JOURNAL_V1"
            and sha256(payload.encode("utf-8")).hexdigest().upper() == record["payload_sha256"],
            "Committed journal envelope hash drift")
    return json.loads(payload)


def require_unlinked(path):
    require(all(not item.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                for item in (path, *path.parents)), f"Reparse path refused: {path}")


def compact_rows(rows):
    # ConvertTo-Json -Compress uses the .NET JSON escaping for these Unicode separators.
    value = rows if len(rows) > 1 else (rows[0] if rows else None)
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return text.translate({0x85: r"\u0085", 0x2028: r"\u2028", 0x2029: r"\u2029"})


def verify_tree(snapshot, root, managed=None):
    require(Path(snapshot["root"]) == root, "Snapshot root differs from staged manifest")
    require_unlinked(root)
    restore_saves = managed is None
    rows = snapshot["files"]
    required_mode = "EXACT_NAMES_BYTES_SHA" if restore_saves else "NAMES_BYTES_MTIME_REPARSE_METADATA"
    require(snapshot["mode"] == required_mode and rows, "Install omitted the required protection snapshot")
    require(sha256(compact_rows(rows).encode("utf-8")).hexdigest().upper() == snapshot["tree_sha256"],
            f"Recorded tree digest drift: {root}")
    expected = {row["path"]: row for row in rows}
    require(len(rows) == len(expected), "Duplicated report paths")
    managed = set() if managed is None else {value.casefold() for value in managed}
    ancestors = {parent.as_posix() for value in managed for parent in Path(value).parents}
    stack = [root]
    while stack:
        for entry in stack.pop().iterdir():
            relative = entry.relative_to(root).as_posix()
            if relative.casefold() in managed:
                continue
            info = entry.lstat()
            actual = {"path": relative}
            if info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                require(not restore_saves, f"Linked save entry refused: {entry}")
                actual.update(kind="REPARSE_NOT_FOLLOWED", attributes=info.st_file_attributes)
            elif stat.S_ISDIR(info.st_mode):
                stack.append(entry)
                if relative.casefold() in ancestors:
                    continue
                actual.update(kind="directory")
            else:
                require(stat.S_ISREG(info.st_mode), f"Unexpected tree entry type: {entry}")
                actual.update(kind="file", bytes=info.st_size)
                if restore_saves:
                    actual.update(sha256=digest(entry))
                else:
                    actual.update(mtime_utc_ticks=UNIX_EPOCH_TICKS + info.st_mtime_ns // 100)
            require(expected.pop(relative, None) == actual, f"Protection snapshot changed: {entry}")
    require(not expected, f"Protection snapshot contains missing entries: {root}")
    return sum(row["kind"] == "file" for row in rows)


def output_path(path):
    path = Path(path).absolute()
    require(path.is_relative_to(STAGE) and ".." not in path.parts and path.name == DEFAULT_OUTPUT.name,
            "Installed manifest requires a fresh workspace output in stage 01")
    parent = path.parent
    require_unlinked(parent if parent.exists() else parent.parent)
    parent.mkdir(exist_ok=True)
    require_unlinked(parent)
    return path


def record(args):
    staged = load(MANIFEST, MANIFEST_SHA)
    baseline = load(INSTALLED, INSTALLED_SHA)
    build = load(BUILD, BUILD_SHA)
    pin(STAGE / "deploy_core.ps1", INSTALLER_SHA)
    require(staged["schema"] == SCHEMA and staged["source_epoch"] == EPOCH
            and staged["predecessor_epoch"] == PRIOR_EPOCH and staged["changing_paths"] == [TARGET]
            and build["target"]["candidate_sha256"] == CANDIDATE_SHA, "Staged scope drift")
    install_path, install_sha, installation = report(args.install)
    verify_path, verify_sha, verification = report(args.verify)
    rollback_path, rollback_sha, rollback = report(args.rollback_ready)
    auth_path, auth_sha, authorization = report(args.authorization)
    receipt_path, receipt_sha, envelope = report(RECOVERY / "journal.json")
    journal = journal_payload(envelope)
    for actual, status in ((installation, "INSTALLED_VERIFIED"), (verification, "VERIFIED_AFTER"),
                           (rollback, "ROLLBACK_READY")):
        require(actual["status"] == status and Path(actual["receipt"]) == receipt_path
                and actual["file_rollback_is_not_save_rollback"] is True, f"Wrong transaction report {status}")
    require(journal == installation["journal"] and journal["schema"] == 1 and journal["component"] == "Core"
            and journal["manifest_sha256"] == MANIFEST_SHA and journal["operation"] == "Install"
            and journal["state"] == "INSTALLED_VERIFIED" and journal["completed_paths"] == [TARGET]
            and journal["game_root"] == staged["game_root"] and journal["save_root"] == staged["save_root"]
            and journal["save_writes"] == journal["game_launches"] == 0, "Transaction journal scope drift")
    validate_authorization(authorization, journal)

    game, saves = (Path(staged[key]) for key in ("game_root", "save_root"))
    managed = {row["path"] for row in staged["files"]}
    require(len(managed) == 52 and len(staged["required_files"]) == 26, "Staged write-set inventory drift")
    target, = [row for row in staged["files"] if row["before"] != row["after"]]
    require(target["path"] == TARGET and target["before"] == OLD_DLL_SHA and target["after"] == CANDIDATE_SHA,
            "Replacement identity drift")
    for row in staged["files"]:
        pin(payload_path(game, row["path"]), row["after"], row["after_bytes"])
    for row in staged["required_files"]:
        pin(payload_path(game, row["path"]), row["sha256"], row["bytes"])
    for row in staged["proofs"]:
        pin(Path(row["path"]), row["sha256"])
    pin(payload_path(Path(staged["package_root"]), TARGET), target["after"], target["after_bytes"])
    for side, field in (("old", "before"), ("new", "after")):
        pin(payload_path(RECOVERY / side, TARGET), target[field], target[f"{field}_bytes"])
    pin(payload_path(saves, SAVE_FIXTURE["path"]), SAVE_FIXTURE["sha256"], SAVE_FIXTURE["bytes"])

    before, after = journal["protection_before"], journal["protection_after"]
    require(before == journal["original_install_protection"] and before == after,
            "Saves or external state changed across the committed transaction")
    required = [{key: row[key] for key in ("path", "sha256", "bytes")} for row in staged["required_files"]]
    require(required == after["dependencies"], "Protection receipt missed an exact external dependency")
    save_files = verify_tree(after["saves"], saves)
    verify_tree(after["unmanaged"], game, managed)

    for path, value in ((install_path, install_sha), (verify_path, verify_sha), (rollback_path, rollback_sha),
                        (auth_path, auth_sha), (receipt_path, receipt_sha)):
        pin(path, value)
    output = output_path(args.output)
    write_json(output, {
        "schema": "PTFR_INSTALLED_EXECUTION_CHECKPOINT_LIVE_HANDOFF_V1", "core_epoch": EPOCH,
        "predecessor_epoch": PRIOR_EPOCH, "checkpoint_version": VERSION,
        "recorded_utc": datetime.now(timezone.utc).isoformat(), "recorded_timezone": "America/Toronto",
        "authorization_record": str(auth_path), "authorization_record_sha256": auth_sha,
        "game_root": str(game), "save_root": str(saves),
        **{key: baseline[key] for key in ("archive_source", "archive_payloads", "archive_sha256", "core_files")},
        "companion_files": [{"path": TARGET, "bytes": target["after_bytes"], "sha256": target["after"]}],
        "required_files": staged["required_files"], "changed_paths": [TARGET],
        "source_candidate": str(BUILD), "source_candidate_sha256": BUILD_SHA,
        "predecessor_manifest": str(INSTALLED), "predecessor_manifest_sha256": INSTALLED_SHA,
        "core_transaction": str(MANIFEST), "core_transaction_sha256": MANIFEST_SHA,
        "installation_report": str(install_path), "installation_report_sha256": install_sha,
        "installed_receipt": str(receipt_path), "installed_receipt_sha256": receipt_sha,
        "post_install_verification": str(verify_path), "post_install_verification_sha256": verify_sha,
        "rollback_readiness": str(rollback_path), "rollback_readiness_sha256": rollback_sha,
        "save_files_preserved": True, "save_file_count": save_files,
        "save_tree_sha256": after["saves"]["tree_sha256"],
        "unmanaged_tree_sha256": after["unmanaged"]["tree_sha256"],
        "gameplay": "PENDING_GENUINE_MS31_TOWER_HANDOFF_AND_SAVE_RELOAD",
    })
    print(f"{output} {digest(output)} ({save_files} save files)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for label in ("authorization", "install", "verify", "rollback-ready"):
        parser.add_argument(f"--{label}", required=True, type=Path)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path)
    record(parser.parse_args())


if __name__ == "__main__":
    main()
