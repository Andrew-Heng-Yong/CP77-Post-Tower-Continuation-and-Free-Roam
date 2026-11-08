"""Independent read-only preflight. Does not invoke/import the installer or game."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import datetime
import stat

H = Path(__file__).resolve().parent
MANIFESTS = {"Core": ("core_manifest_02.json", "06CD479C47E32403371E360092648431EAE1BC93DEE3E61BD6822560133CBCF1"),
             "Diagnostics": ("diagnostics_manifest_01.json", "C41A1547DB7B33F0F97B68ADC7509E937A6487B85D95E34F7AAFBF83991C38E1")}


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def safe(p):
    for x in (p, *p.parents):
        if x.exists() or x.is_symlink():
            s = x.lstat()
            assert not stat.S_ISLNK(s.st_mode) and not getattr(s, "st_file_attributes", 0) & 0x400, f"link/reparse refused: {x}"
    return p


def sha(p):
    safe(p)
    before = p.stat()
    with p.open("rb") as f:
        h = hashlib.file_digest(f, "sha256").hexdigest().upper()
    after = p.stat()
    assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), f"file changed while hashing: {p}"
    return h


def child(root, rel):
    assert "\\" not in rel and ":" not in rel and not rel.startswith("/")
    assert all(x not in ("", ".", "..") for x in rel.split("/"))
    p = root / rel
    assert p.is_relative_to(root)
    return safe(p)


def check_file(p, h, size=None):
    safe(p)
    if h is None:
        assert not p.exists(), f"expected absent: {p}"
    else:
        assert p.is_file() and sha(p) == h, f"hash mismatch: {p}"
        assert size is None or p.stat().st_size == size, f"size mismatch: {p}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--installer-sha", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    out = safe(H / a.output)
    assert out.resolve().is_relative_to(H) and not out.exists(), "Fresh QR9 evidence output required"
    b = read(H / "baseline.json")
    worker = H / "worker_a"
    script = worker / "deploy_qr9_guarded.ps1"
    check_file(script, a.installer_sha)
    process_code = "$p=@(Get-Process -ErrorAction SilentlyContinue | Where-Object {$_.ProcessName -in @('Cyberpunk2077','REDprelauncher','REDlauncher')} | Select-Object -ExpandProperty ProcessName); ConvertTo-Json -InputObject $p -Compress"
    result = subprocess.run(["pwsh", "-NoProfile", "-Command", process_code], text=True, capture_output=True, check=True)
    running = json.loads(result.stdout)
    assert not running, f"game/RED launcher running; no automatic process control: {running}"
    components = []
    game, save = Path(b["game_root"]), Path(b["save_root"])
    baseline_rows = {r["path"]: r for r in b["core_files"]}
    for name, (filename, expected) in MANIFESTS.items():
        path = worker / filename
        check_file(path, expected)
        m = read(path)
        assert m["component"] == name and m["source_epoch"] == "QR8:02"
        assert Path(m["game_root"]) == game and Path(m["save_root"]) == save
        assert set(m["process_names"]) == {"Cyberpunk2077", "REDprelauncher", "REDlauncher"}
        package = Path(m["package_root"])
        safe(package)
        for r in m["files"]:
            if name == "Core":
                old = baseline_rows[r["path"]]
                assert r["before"] == old["before"] and r["after"] == old["after"]
            check_file(child(game, r["path"]), r["before"], r["before_bytes"])
            check_file(child(package, r["path"]), r["after"], r["after_bytes"])
        actual = []
        for p in package.rglob("*"):
            safe(p)
            if p.is_file(): actual.append(p.relative_to(package).as_posix())
        assert sorted(actual) == sorted(r["path"] for r in m["files"]), "package inventory differs"
        for p in m["proofs"]: check_file(Path(p["path"]), p["sha256"])
        for r in m["required_files"]: check_file(child(game, r["path"]), r["sha256"], r["bytes"])
        if m.get("zip"): check_file(Path(m["zip"]), m["zip_sha256"])
        recovery = safe(worker / "recovery" / (name.lower() + "_qr8_02_01"))
        assert not recovery.exists(), f"occupied recovery path: {recovery}"
        assert game.drive == recovery.drive, "different replacement/staging volumes"
        components.append({"component": name, "manifest": str(path), "manifest_sha256": expected,
                           "paths_checked": len(m["files"]), "dependencies_checked": len(m["required_files"]),
                           "proofs_checked": len(m["proofs"]), "recovery_fresh": True})
    master = read(H / "selected_master.json")
    mp = Path(master["path"])
    assert sorted(p.name for p in mp.iterdir()) == sorted(master["files"]), "master inventory changed"
    for n, r in master["files"].items(): check_file(child(mp, n), r["sha256"], r["bytes"])
    out.mkdir(parents=True)
    report = {"status": "PASS_INDEPENDENT_READ_ONLY_PREPARATION_CHECK", "captured_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_epoch": "QR8:02", "installed_core": "PH3_UNCHANGED", "components": components,
        "installer": {"path": str(script), "sha256": a.installer_sha, "real_Preflight": "NOT_RUN", "all_invocations_fixture_only": True},
        "processes_running": running, "master_files_checked": len(master["files"]),
        "game_writes": 0, "save_writes": 0, "master_backups_created": 0, "game_API_calls": 0,
        "limits": ["Independent preparation validation, not execution of the installer against the real game.",
                   "Future user installer Preflight/Install rechecks then-current state after authorization.",
                   "No real replacement/write permissions were exercised, and no gameplay/API availability is certified."]}
    (out / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "components": len(components), "master_files": len(master["files"]), "installer_real_Preflight": "NOT_RUN"}))


if __name__ == "__main__": main()
