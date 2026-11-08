"""Read-only verification of the authorized QR9 deployment and unchanged saves."""
from pathlib import Path
import concurrent.futures
import datetime
import hashlib
import json
import sys

H = Path(__file__).resolve().parent
Q = H.parent
W = Q.parents[1]
sys.path.insert(0, str(W / "tools/parity_audit"))
from common import tree_metadata


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def sha(p):
    with Path(p).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest().upper()


def write(p, data):
    assert not p.exists(), "Fresh result required"
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    baseline = read(Q / "baseline.json")
    game = Path(baseline["game_root"])
    save = Path(baseline["save_root"])
    cm = read(Q / "worker_a/core_manifest_02.json")
    dm = read(Q / "worker_a/diagnostics_manifest_01.json")
    changes = {r["path"]: r for m in (cm, dm) for r in m["files"] if r["before"] != r["after"]}
    rows = []
    for component, manifest in (("Core", cm), ("Diagnostics", dm)):
        for r in manifest["files"]:
            p = game / r["path"]
            actual = sha(p)
            assert actual == r["after"] and p.stat().st_size == r["after_bytes"], p
            rows.append({"component": component, "path": r["path"], "sha256": actual,
                         "bytes": p.stat().st_size, "before": r["before"], "changed": r["before"] != r["after"]})
        for r in manifest["required_files"]:
            assert sha(game / r["path"]) == r["sha256"], r["path"]
    preflight = read(Q / "worker_a/deployment_01/core_preflight.json")
    save_before = {r["path"]: r["sha256"] for r in preflight["protection"]["saves"]["files"] if r["kind"] == "file"}
    save_after = {p.relative_to(save).as_posix(): sha(p) for p in save.rglob("*") if p.is_file()}
    assert save_after == save_before, "Save names/bytes changed"
    master = read(Q / "selected_master.json")
    backup = Q / "worker_a/recovery/core_qr8_02_01/master_before/ManualSave-23"
    master_rows = []
    for name, r in master["files"].items():
        source, target = Path(master["path"]) / name, backup / name
        assert sha(source) == sha(target) == r["sha256"], name
        master_rows.append({"name": name, "source": str(source), "backup": str(target), "sha256": r["sha256"]})
    old = read(Q / "protection_before.json")
    metadata = tree_metadata(game)
    delta = [p for p in set(metadata) | set(old["game_metadata"]) if metadata.get(p) != old["game_metadata"].get(p)]
    assert {p.replace("\\", "/") for p in delta} == set(changes), delta
    assert tree_metadata(save) == old["save_metadata"], "Save metadata changed since preparation"

    def protected(item):
        name, row = item
        p = Path(name)
        relative = p.relative_to(game).as_posix() if p.is_relative_to(game) else None
        expected = changes[relative]["after"] if relative in changes else row["sha256"]
        actual = sha(p) if p.is_file() else None
        return None if actual == expected else {"path": name, "expected": expected, "actual": actual}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        discrepancies = [r for r in pool.map(protected, old["files"].items()) if r]
    assert not discrepancies, discrepancies
    expected_states = {"core_preflight": "PREFLIGHT_READY", "diagnostics_preflight": "PREFLIGHT_READY",
                       "core_install": "INSTALLED_VERIFIED", "diagnostics_install": "INSTALLED_VERIFIED",
                       "core_verify": "VERIFIED_AFTER", "diagnostics_verify": "VERIFIED_AFTER",
                       "core_rollback_ready": "ROLLBACK_READY", "diagnostics_rollback_ready": "ROLLBACK_READY"}
    for name, expected in expected_states.items():
        assert read(Q / "worker_a/deployment_01" / (name + ".json"))["status"] == expected
    result = {"status": "PASS_INSTALLED_QR8_CORE_AND_QR9B04_DIAGNOSTICS",
        "verified_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_epoch": "QR8:02", "core_paths_verified": len(cm["files"]), "diagnostic_paths_verified": len(dm["files"]),
        "changed_game_paths": sorted(changes), "game_metadata_files": len(metadata),
        "unexpected_game_metadata_changes": 0, "save_files_sha256_verified": len(save_after),
        "save_metadata_changes": 0, "saved_game_writes": 0,
        "protected_sha_files": len(old["files"]), "expected_protected_replacements": 2, "unexpected_protected_changes": 0,
        "master_and_backup_files": master_rows, "installed_files": rows,
        "core_recovery": str(Q / "worker_a/recovery/core_qr8_02_01"),
        "diagnostics_recovery": str(Q / "worker_a/recovery/diagnostics_qr8_02_01"),
        "rollback_readiness": "PASS_BOTH_COMPONENTS_NO_ROLLBACK_EXECUTED",
        "game_launches": 0, "CUA_calls": 0, "gameplay_result": "NOT_TESTED",
        "scope": "All 53 installed payload hashes, required dependencies, master/backup, complete save SHA and game metadata, and named predecessor protected SHA pins checked. Expected archive/XL replacements allowed. No SHA of every unlisted multi-GB game asset. Documentation pointers update after this check."}
    write(H / "verification.json", result)
    print(json.dumps({k: result[k] for k in ["status", "core_paths_verified", "diagnostic_paths_verified", "save_files_sha256_verified", "unexpected_protected_changes", "rollback_readiness"]}))


if __name__ == "__main__":
    main()
