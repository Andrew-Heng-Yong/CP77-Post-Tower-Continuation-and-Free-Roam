"""Freeze a one-file guarded WO2 deployment plan without game writes."""

from pathlib import Path
import json
import os
import stat
import subprocess

from prepare_candidate import BASE, BASE_SHA, GAME, HERE, OUT, SCRIPT, check_rows, plain, sha

SAVES = Path(r"C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077")
PLAN = HERE / "install_plan_01.json"
PREFERENCES = (
    "bin/x64/plugins/cyber_engine_tweaks/mods/ImmersiveFirstPerson/config.json",
    "bin/x64/plugins/cyber_engine_tweaks/mods/ImmersiveFirstPerson/db.sqlite3",
    "bin/x64/plugins/cyber_engine_tweaks/mods/ImmersiveFirstPerson/ImmersiveFirstPerson.log",
    "bin/x64/plugins/cyber_engine_tweaks/bindings.json",
)


def closed() -> None:
    cmd = ["powershell.exe", "-NoProfile", "-Command",
           "@(Get-Process -Name Cyberpunk2077,REDlauncher,REDprelauncher "
           "-ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName) -join ','"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if result.returncode or result.stdout.strip():
        raise RuntimeError(f"Game or launcher open, or process check failed: {result.stdout} {result.stderr}")


def snapshot(root: Path) -> list[dict]:
    plain(root)
    rows = []
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            plain(Path(parent) / name)
        for name in files:
            path = Path(parent) / name
            rows.append({"path": path.relative_to(root).as_posix(),
                         "bytes": path.stat().st_size, "sha256": sha(path)})
    return sorted(rows, key=lambda row: row["path"])


def main() -> None:
    closed()
    if PLAN.exists():
        raise RuntimeError("Fresh deployment plan required")
    baseline = json.loads(BASE.read_text(encoding="utf-8-sig"))
    candidate_path = OUT / "core_manifest_01.json"
    compile_path = OUT / "compile_01/assessment.json"
    assessment_path = OUT / "assessment.json"
    candidate = json.loads(candidate_path.read_text(encoding="utf-8-sig"))
    compiled = json.loads(compile_path.read_text(encoding="utf-8-sig"))
    assessed = json.loads(assessment_path.read_text(encoding="utf-8-sig"))
    assert sha(BASE) == BASE_SHA and compiled["status"] == "PASS" and assessed["status"] == "PASS_OFFLINE_CANDIDATE"
    assert candidate["changed_paths"] == compiled["changed_sources"] == [SCRIPT]
    check_rows(baseline["core_files"] + baseline["required_files"])
    for row in candidate["core_files"]:
        source = OUT / "package" / row["path"]
        plain(source)
        assert source.stat().st_size == row["bytes"] and sha(source) == row["sha256"]
    ifp = json.loads((HERE.parent / "ifp_update_20261116_01/work/plan_01.json").read_text(encoding="utf-8-sig"))
    ifp_rows = [{"path": row["path"], **row["after"]} for row in ifp["managed"]]
    for row in ifp_rows:
        path = GAME / row["path"]
        plain(path)
        if path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise RuntimeError(f"IFP drift: {row['path']}")
    preferences = []
    for relative in PREFERENCES:
        path = GAME / relative
        plain(path)
        if path.exists():
            preferences.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha(path)})
    saved = snapshot(SAVES)
    before = next(row for row in baseline["core_files"] if row["path"] == SCRIPT)
    after = next(row for row in candidate["core_files"] if row["path"] == SCRIPT)
    plan = {
        "schema": "WO2_ONE_SCRIPT_INSTALL_V1", "scope": "User-requested fresh-load street cleanup for AutoSave-16",
        "game_root": str(GAME), "save_root": str(SAVES), "package_root": str(OUT / "package"),
        "changed_path": SCRIPT, "before": before, "after": after,
        "baseline_sha256": BASE_SHA, "candidate_sha256": sha(candidate_path),
        "compile_sha256": sha(compile_path), "assessment_sha256": sha(assessment_path),
        "core_before": baseline["core_files"], "core_after": candidate["core_files"],
        "required": baseline["required_files"], "ifp": ifp_rows, "preferences": preferences,
        "saved_files": saved, "game_writes": 0, "save_writes": 0,
    }
    with PLAN.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(plan, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "PREPARED", "changed": 1, "core": len(plan["core_before"]),
                      "required": len(plan["required"]), "ifp": len(plan["ifp"]),
                      "preferences": len(plan["preferences"]), "saved_files": len(saved),
                      "plan_sha256": sha(PLAN)}))


if __name__ == "__main__":
    main()
