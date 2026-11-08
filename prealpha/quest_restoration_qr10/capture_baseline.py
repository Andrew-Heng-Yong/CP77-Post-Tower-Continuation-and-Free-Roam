"""One-shot QR10 read-only baseline; output only this new task directory."""
from pathlib import Path
import concurrent.futures
import datetime
import hashlib
import json
import os
import stat
import subprocess

H = Path(__file__).resolve().parent
W = H.parents[1]
Q9 = W / "prealpha/quest_restoration_qr9"


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def sha(p):
    with Path(p).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest().upper()


def meta(root):
    rows = {}
    for folder, dirs, files in os.walk(root, followlinks=False):
        for name in list(dirs):
            p = Path(folder) / name
            s = p.lstat()
            if stat.S_ISLNK(s.st_mode) or getattr(s, "st_file_attributes", 0) & 0x400:
                rows[p.relative_to(root).as_posix()] = {"kind": "REPARSE_NOT_FOLLOWED"}
                dirs.remove(name)
        for name in files:
            p = Path(folder) / name
            s = p.lstat()
            rows[p.relative_to(root).as_posix()] = {"bytes": s.st_size, "mtime_ns": s.st_mtime_ns,
                "kind": "REPARSE_NOT_FOLLOWED" if stat.S_ISLNK(s.st_mode) or getattr(s, "st_file_attributes", 0) & 0x400 else "file"}
    return rows


def main():
    target = H / "baseline.json"
    assert not target.exists(), "Fresh baseline only"
    baseline = read(Q9 / "baseline.json")
    game, save = Path(baseline["game_root"]), Path(baseline["save_root"])
    stage = Q9 / "stage_report_01/completion.json"
    assert sha(stage) == "5907E72B91190E7168B8988A3B40490E15678C13F1208D71EEC7B1735C952E38"
    protected = {}
    for row in read(stage)["artifacts"]:
        p = Path(row["path"])
        assert sha(p) == row["sha256"], p
        protected[str(p)] = row["sha256"]
    for row in baseline["core_files"]:
        p = game / row["path"]
        assert sha(p) == row["after"]
        protected[str(p)] = row["after"]
    dep = []
    for row in baseline["external_dependencies"]:
        p = game / row["path"]
        assert sha(p) == row["sha256"], p
        protected[str(p)] = row["sha256"]
        dep.append(row)
    addon = read(Q9 / "worker_b/addon_manifest_04.json")
    for row in addon["files"]:
        p = game / row["path"]
        assert sha(p) == row["sha256"]
        protected[str(p)] = row["sha256"]
    for p in [Q9 / "report.md", Q9 / "worker_b/test_offline.py", Q9 / "worker_a/deploy_qr9_guarded.ps1",
              Q9 / "worker_b/addon_manifest_04.json", W / "prealpha/quest_restoration_qr8/source_epoch_02.json"]:
        protected[str(p)] = sha(p)
    master = read(Q9 / "selected_master.json")
    for name, row in master["files"].items():
        for root in (Path(master["path"]), Q9 / "worker_a/recovery/core_qr8_02_01/master_before/ManualSave-23"):
            p = root / name
            assert sha(p) == row["sha256"]
            protected[str(p)] = row["sha256"]
    save_meta = meta(save)
    save_files = [save / p for p, row in save_meta.items() if row["kind"] == "file"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        save_hashes = dict(zip((str(p) for p in save_files), pool.map(sha, save_files)))
    git = ["git", "-c", "safe.directory=" + str(W).replace("\\", "/")]
    result = {"status": "PASS_QR8_CORE_QR9B04_AND_MASTER_BASELINE", "captured_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "workspace": str(W), "game_root": str(game), "save_root": str(save), "protected_sha256": protected,
        "core_files": baseline["core_files"], "external_dependencies": dep, "diagnostics": addon,
        "save_sha256": save_hashes, "save_metadata": save_meta, "game_metadata": meta(game), "QR9_metadata": meta(Q9),
        "branch": subprocess.check_output(git + ["branch", "--show-current"], cwd=W, text=True).strip(),
        "HEAD": subprocess.check_output(git + ["rev-parse", "HEAD"], cwd=W, text=True).strip(),
        "git_status_before": subprocess.check_output(git + ["status", "--short"], cwd=W, text=True),
        "scope": "QR10 offline diagnostic investigation/implementation/preparation only. No real install, game/API launch, CUA, save/fact writes, core build or prior observation edits."}
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    checkpoint = {"state": "QR10_INVESTIGATING_CALLBACK_CONTRACT", "baseline": str(target), "baseline_sha256": sha(target),
        "next": "Pin CET NativeProxy and actual installed callback/dispatcher contract; implement smallest confirmed correction plus independent bounded getter-difference fallback. No installation.",
        "reviewer": "Not spawned; wait for concrete change/disputed finding.", "runtime_installed_changes": 0,
        "game_launches": 0, "save_or_fact_writes": 0, "CUA_calls": 0, "goal_status": "none"}
    (H / "checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
    print({"status": result["status"], "protected_hashes": len(protected), "save_files_hashed": len(save_files), "QR9_metadata_files": len(result["QR9_metadata"])})


if __name__ == "__main__":
    main()
