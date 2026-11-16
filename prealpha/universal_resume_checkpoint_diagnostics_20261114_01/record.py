"""Independently record the guarded v0.1.3 install after readback."""

from hashlib import file_digest, sha256
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEPLOY = HERE / "deployment_01"
PREVIOUS = HERE.parent / "universal_resume_checkpoint_runtime_deploy_20261114_01/deployment_01/installed_manifest_01.json"
MANIFEST = HERE / "core_manifest_01.json"
CANDIDATE = HERE / "candidate_01/receipt.json"
AUTHORIZATION = DEPLOY / "authorization_01.json"
RECOVERY = HERE / "recovery/resume_checkpoint_diagnostics_01"
DLL = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest().upper()


def read(path: Path):
    return json.loads(path.read_bytes())


def record() -> None:
    target = DEPLOY / "installed_manifest_01.json"
    assert not target.exists(), "installed record already exists"
    old = read(PREVIOUS)
    manifest = read(MANIFEST)
    candidate = read(CANDIDATE)
    authorization = read(AUTHORIZATION)
    preflight = read(DEPLOY / "preflight_02.json")
    install = read(DEPLOY / "install.json")
    verify = read(DEPLOY / "verify.json")
    rollback = read(DEPLOY / "rollback_readiness.json")
    assert old["core_epoch"] == manifest["predecessor_epoch"] == "RD10_EXECUTION_CHECKPOINT_RUNTIME"
    assert manifest["source_epoch"] == "RD10_EXECUTION_CHECKPOINT_DIAGNOSTICS"
    assert manifest["changing_paths"] == [DLL]
    assert authorization["user_reply"] == "yes" and authorization["manifest_sha256"] == sha(MANIFEST)
    assert authorization["candidate_sha256"] == sha(CANDIDATE)
    assert preflight["status"] == "PREFLIGHT_READY"
    assert install["status"] == "INSTALLED_VERIFIED"
    assert verify["status"] == "VERIFIED_AFTER"
    assert rollback["status"] == "ROLLBACK_READY"
    envelope = read(RECOVERY / "journal.json")
    payload = envelope["payload_json"]
    assert sha256(payload.encode()).hexdigest().upper() == envelope["payload_sha256"]
    journal = json.loads(payload)
    assert journal["state"] == "INSTALLED_VERIFIED" and journal["manifest_sha256"] == sha(MANIFEST)
    assert journal["completed_paths"] == [DLL]
    assert journal["save_writes"] == journal["game_launches"] == 0
    before = journal["protection_before"]
    after = journal["protection_after"]
    assert before["saves"]["tree_sha256"] == after["saves"]["tree_sha256"]
    assert before["saves"]["tree_sha256"] == preflight["protection"]["saves"]["tree_sha256"]
    assert before["unmanaged"]["tree_sha256"] == after["unmanaged"]["tree_sha256"]
    assert before["dependencies"] == after["dependencies"]
    save_count = sum(row["kind"] == "file" for row in after["saves"]["files"])
    assert save_count == 388

    game = Path(manifest["game_root"])
    current = []
    for row in manifest["files"]:
        item = game / row["path"]
        assert item.stat().st_size == row["after_bytes"] and sha(item) == row["after"]
        current.append({"path": row["path"], "bytes": row["after_bytes"], "sha256": row["after"]})
    assert len(current) == 52
    for row in manifest["required_files"]:
        item = game / row["path"]
        assert item.stat().st_size == row["bytes"] and sha(item) == row["sha256"]
    changed = next(row for row in manifest["files"] if row["path"] == DLL)
    assert sha(RECOVERY / "old" / DLL) == changed["before"]
    assert sha(RECOVERY / "new" / DLL) == changed["after"] == candidate["after_sha256"]

    result = {
        "schema": "PTFR_INSTALLED_EXECUTION_CHECKPOINT_DIAGNOSTICS_V1",
        "core_epoch": manifest["source_epoch"],
        "predecessor_epoch": old["core_epoch"],
        "recorded_utc": journal["updated_utc"],
        "recorded_timezone": "America/Toronto",
        "authorization_record": str(AUTHORIZATION),
        "authorization_record_sha256": sha(AUTHORIZATION),
        "game_root": str(game),
        "save_root": manifest["save_root"],
        "archive_source": old["archive_source"],
        "archive_payloads": old["archive_payloads"],
        "archive_sha256": old["archive_sha256"],
        "core_files": [row for row in current if row["path"] != DLL],
        "companion_files": [row for row in current if row["path"] == DLL],
        "required_files": manifest["required_files"],
        "changed_paths": [DLL],
        "source_candidate": str(CANDIDATE),
        "source_candidate_sha256": sha(CANDIDATE),
        "predecessor_manifest": str(PREVIOUS),
        "predecessor_manifest_sha256": sha(PREVIOUS),
        "core_transaction": str(MANIFEST),
        "core_transaction_sha256": sha(MANIFEST),
        "installed_receipt": str(RECOVERY / "journal.json"),
        "installed_receipt_sha256": sha(RECOVERY / "journal.json"),
        "post_install_verification": str(DEPLOY / "verify.json"),
        "rollback_readiness": str(DEPLOY / "rollback_readiness.json"),
        "save_files_preserved": save_count,
        "save_tree_sha256": after["saves"]["tree_sha256"],
        "unmanaged_tree_sha256": after["unmanaged"]["tree_sha256"],
        "gameplay": "PENDING_REED_CUTOFF_DIAGNOSTIC",
    }
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(f"Recorded {len(result['core_files'])} Core paths, one DLL, 26 dependencies and {save_count} preserved save files.")


if __name__ == "__main__":
    record()
