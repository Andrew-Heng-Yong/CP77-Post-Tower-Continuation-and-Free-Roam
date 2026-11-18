"""Guarded BV1 two-script installation. No game writes unless 'install' is run."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORK = HERE / "work"
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
SAVES = Path(r"C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077")
BASELINE = ROOT / "prealpha/credits_cover_lc5_20261116_01/work/deployment_01/installed_manifest_01.json"
BASELINE_SHA = "02E089A382D01A0542BA804CAA6B2892D2A411B8C25F755A8C503C1483D703DF"
CANDIDATE = HERE / "candidate_01/core_manifest_01.json"
CANDIDATE_SHA = "8A6182A3B104AC3DE6D835EF2351D04EF019EA0544A652F8ED546F06FB11003C"
COMPILE = HERE / "candidate_01/compile_01/assessment.json"
COMPILE_SHA = "1E49989FFEA3448B19AABBA82C910E33B48F5CC06C4949969705DFA5F1688235"
IFP_PLAN = ROOT / "prealpha/ifp_update_20261116_01/work/plan_01.json"
IFP_RECEIPT = ROOT / "prealpha/ifp_update_20261116_01/work/installed_01.json"
IFP_RECEIPT_SHA = "D1A52987D8E7EA24FA6F1AACCC015FE3310DFB0B414BD361D956F6741FB7F11E"
PACKAGE = HERE / "candidate_01/package"
PLAN = WORK / "plan_01.json"
RECOVERY = WORK / "recovery_01"
RECEIPT = WORK / "installed_01.json"
CHANGED = (
    "r6/scripts/PTFR_Consolidated/PTFR_LoadingCoverLC1.reds",
    "r6/scripts/PTFR_Consolidated/PTFR_RestrictionsR1.reds",
)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def plain(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink() or (part.exists() and part.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise RuntimeError(f"Linked path refused: {part}")


def safe(root: Path, relative: str) -> Path:
    parts = relative.split("/")
    if not parts or any(not p or p in (".", "..") or p.endswith(".") or p.endswith(" ") or
                        ":" in p or "\\" in p for p in parts):
        raise RuntimeError(f"Unsafe relative path: {relative}")
    path = root.joinpath(*parts)
    if not path.absolute().is_relative_to(root.absolute()):
        raise RuntimeError(f"Escaped root: {relative}")
    plain(path)
    return path


def closed() -> None:
    command = ["powershell.exe", "-NoProfile", "-Command",
               "@(Get-Process -Name Cyberpunk2077,REDlauncher,REDprelauncher "
               "-ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName) -join ','"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=12)
    if result.returncode or result.stdout.strip():
        raise RuntimeError(f"Game/launcher open or process check failed: {result.stdout} {result.stderr}")


def rows_check(root: Path, rows: list[dict]) -> None:
    for row in rows:
        path = safe(root, row["path"])
        if not path.is_file() or path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise RuntimeError(f"Protected file changed: {path}")


def snapshot(root: Path) -> list[dict]:
    plain(root)
    rows = []
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            plain(Path(parent) / name)
        for name in files:
            path = Path(parent) / name
            rows.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
                         "sha256": sha(path)})
    return sorted(rows, key=lambda row: row["path"])


def write_new(path: Path, obj: dict) -> None:
    plain(path)
    if path.exists():
        raise RuntimeError(f"Evidence already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(obj, stream, indent=2)
        stream.write("\n")


def evidence() -> tuple[dict, dict, dict, dict]:
    for path, expected in ((BASELINE, BASELINE_SHA), (CANDIDATE, CANDIDATE_SHA),
                           (COMPILE, COMPILE_SHA), (IFP_RECEIPT, IFP_RECEIPT_SHA)):
        plain(path)
        if sha(path) != expected:
            raise RuntimeError(f"Pinned evidence drift: {path}")
    baseline = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
    candidate = json.loads(CANDIDATE.read_text(encoding="utf-8-sig"))
    compile_result = json.loads(COMPILE.read_text(encoding="utf-8-sig"))
    ifp = json.loads(IFP_PLAN.read_text(encoding="utf-8-sig"))
    ifp_receipt = json.loads(IFP_RECEIPT.read_text(encoding="utf-8-sig"))
    if ifp_receipt["status"] != "INSTALLED_VERIFIED" or ifp_receipt["plan_sha256"] != sha(IFP_PLAN):
        raise RuntimeError("IFP evidence mismatch")
    if baseline["core_epoch"] != "LC5_CREDITS_COVER" or candidate["status"] != "STAGED_OFFLINE" or \
       compile_result["status"] != "PASS" or candidate["changed_paths"] != list(CHANGED) or \
       compile_result["changed_sources"] != list(CHANGED) or len(baseline["core_files"]) != 51 or \
       len(candidate["core_files"]) != 51 or len(baseline["required_files"]) != 47 or \
       len(compile_result["staged_sources"]) != 149 or \
       candidate["compile_assessment_sha256"] != COMPILE_SHA:
        raise RuntimeError("Unexpected candidate or baseline")
    return baseline, candidate, compile_result, ifp


def sources_check(expected: dict[str, str]) -> None:
    actual = {p.relative_to(GAME).as_posix()
              for base in (GAME / "r6/scripts", GAME / "red4ext/plugins")
              for p in base.rglob("*.reds")}
    if actual != set(expected):
        raise RuntimeError("Registered source inventory changed")
    for relative, digest in expected.items():
        if sha(safe(GAME, relative)) != digest:
            raise RuntimeError(f"Source drift: {relative}")


def read_plan() -> dict:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if plan["schema"] != "BV1_EXACT_TWO_SCRIPT_UPDATE_V1" or \
       plan["baseline_sha256"] != BASELINE_SHA or plan["candidate_sha256"] != CANDIDATE_SHA or \
       plan["compile_sha256"] != COMPILE_SHA:
        raise RuntimeError("Wrong or stale deployment plan")
    baseline, candidate, _, ifp = evidence()
    if plan["before"] != baseline["core_files"] or plan["after"] != candidate["core_files"] or \
       plan["dependencies"] != baseline["required_files"] or \
       plan["ifp"] != [{"path": row["path"], **row["after"]} for row in ifp["managed"]] or \
       plan["changed_paths"] != list(CHANGED):
        raise RuntimeError("Plan differs from pinned candidate or protected installation")
    return plan


def compiler_inputs_check(compiled: dict) -> None:
    for path, expected in compiled["installed_inputs"].items():
        live = Path(path)
        plain(live)
        if not live.is_file() or sha(live) != expected:
            raise RuntimeError(f"Compiler input changed: {path}")


def prepare() -> None:
    closed()
    if WORK.exists():
        raise RuntimeError("Fresh work directory required; retain existing evidence")
    before, after, compiled, ifp = evidence()
    rows_check(GAME, before["core_files"] + before["required_files"])
    rows_check(PACKAGE, after["core_files"])
    prior = json.loads((ROOT / "prealpha/credits_cover_lc5_20261116_01/candidate_01/compile_01/assessment.json").read_text())
    sources_check(prior["staged_sources"])
    compiler_inputs_check(compiled)
    for row in before["core_files"]:
        successor = next(r for r in after["core_files"] if r["path"] == row["path"])
        if row["path"] not in CHANGED and row != successor:
            raise RuntimeError(f"Unreviewed Core change: {row['path']}")
    ifp_rows = [{"path": row["path"], **row["after"]} for row in ifp["managed"]]
    rows_check(GAME, ifp_rows)
    preferences = []
    for relative in ("bin/x64/plugins/cyber_engine_tweaks/mods/ImmersiveFirstPerson/config.json",
                     "bin/x64/plugins/cyber_engine_tweaks/mods/ImmersiveFirstPerson/db.sqlite3",
                     "bin/x64/plugins/cyber_engine_tweaks/mods/ImmersiveFirstPerson/ImmersiveFirstPerson.log",
                     "bin/x64/plugins/cyber_engine_tweaks/bindings.json"):
        path = safe(GAME, relative)
        if path.exists():
            preferences.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha(path)})
    plan = {"schema": "BV1_EXACT_TWO_SCRIPT_UPDATE_V1", "baseline_sha256": BASELINE_SHA,
            "candidate_sha256": CANDIDATE_SHA, "compile_sha256": COMPILE_SHA,
            "before": before["core_files"], "after": after["core_files"],
            "dependencies": before["required_files"], "ifp": ifp_rows,
            "preferences": preferences, "saves": snapshot(SAVES),
            "changed_paths": list(CHANGED), "game_writes": 0, "save_writes": 0}
    WORK.mkdir(exist_ok=False)
    write_new(PLAN, plan)
    print(json.dumps({"status": "PREPARED", "core": len(plan["before"]),
                      "dependencies": len(plan["dependencies"]), "ifp": len(ifp_rows),
                      "saves": len(plan["saves"]), "plan_sha256": sha(PLAN)}))


def protected(plan: dict) -> None:
    rows_check(GAME, plan["dependencies"] + plan["ifp"] + plan["preferences"])
    rows_check(SAVES, plan["saves"])
    if snapshot(SAVES) != plan["saves"]:
        raise RuntimeError("Save inventory changed")


def replace_from(source: Path, target: Path, expected: dict) -> None:
    plain(source)
    plain(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".bv1_", dir=target.parent)
    os.close(fd)
    try:
        shutil.copyfile(source, temporary)
        if sha(Path(temporary)) != expected["sha256"]:
            raise RuntimeError("Staged replacement changed")
        closed()
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def restore(plan: dict, journal: dict) -> None:
    before = {r["path"]: r for r in plan["before"]}
    after = {r["path"]: r for r in plan["after"]}
    for relative in reversed(CHANGED):
        target = safe(GAME, relative)
        old, new = before[relative], after[relative]
        current = sha(target) if target.is_file() else None
        if current == old["sha256"]:
            continue
        if current != new["sha256"]:
            journal["state"] = "UNKNOWN_DRIFT_REVIEW_REQUIRED"
            (RECOVERY / "journal.json").write_text(json.dumps(journal, indent=2) + "\n")
            raise RuntimeError(f"Unknown target drift: {target}")
        replace_from(safe(RECOVERY / "old", relative), target, old)
    rows_check(GAME, plan["before"])
    protected(plan)
    journal["state"] = "RESTORED_BEFORE_VERIFIED"
    (RECOVERY / "journal.json").write_text(json.dumps(journal, indent=2) + "\n")


def install() -> None:
    closed()
    plan = read_plan()
    if RECOVERY.exists() or RECEIPT.exists():
        raise RuntimeError("Deployment already attempted; do not reuse evidence")
    rows_check(GAME, plan["before"])
    rows_check(PACKAGE, plan["after"])
    protected(plan)
    compiler_inputs_check(json.loads(COMPILE.read_text(encoding="utf-8-sig")))
    prior = json.loads((ROOT / "prealpha/credits_cover_lc5_20261116_01/candidate_01/compile_01/assessment.json").read_text())
    sources_check(prior["staged_sources"])
    RECOVERY.mkdir()
    for relative in CHANGED:
        backup = safe(RECOVERY / "old", relative)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe(GAME, relative), backup)
        expected = next(r for r in plan["before"] if r["path"] == relative)
        rows_check(RECOVERY / "old", [expected])
    journal = {"state": "PREPARED", "plan_sha256": sha(PLAN),
               "changed_paths": list(CHANGED), "applied": []}
    write_new(RECOVERY / "journal.json", journal)
    try:
        for relative in CHANGED:
            closed()
            old = next(r for r in plan["before"] if r["path"] == relative)
            new = next(r for r in plan["after"] if r["path"] == relative)
            rows_check(GAME, [old])
            replace_from(safe(PACKAGE, relative), safe(GAME, relative), new)
            journal["applied"].append(relative)
            (RECOVERY / "journal.json").write_text(json.dumps(journal, indent=2) + "\n")
        rows_check(GAME, plan["after"])
        protected(plan)
        sources_check(json.loads(COMPILE.read_text())["staged_sources"])
        journal["state"] = "INSTALLED_VERIFIED"
        (RECOVERY / "journal.json").write_text(json.dumps(journal, indent=2) + "\n")
        write_new(RECEIPT, {"status": "INSTALLED_VERIFIED", "plan_sha256": sha(PLAN),
                            "core_files": 51, "changed_files": 2, "dependencies": 47,
                            "ifp_files": len(plan["ifp"]), "preferences": len(plan["preferences"]),
                            "save_files": len(plan["saves"]), "game_launches": 0, "save_writes": 0})
        print(json.dumps({"status": "INSTALLED_VERIFIED", "changed": 2,
                          "saves": len(plan["saves"])}))
    except Exception:
        restore(plan, journal)
        raise


def verify() -> None:
    plan = read_plan()
    rows_check(GAME, plan["after"])
    protected(plan)
    sources_check(json.loads(COMPILE.read_text())["staged_sources"])
    journal = json.loads((RECOVERY / "journal.json").read_text())
    receipt = json.loads(RECEIPT.read_text())
    if journal["state"] != "INSTALLED_VERIFIED" or receipt["status"] != "INSTALLED_VERIFIED" or \
       journal["plan_sha256"] != sha(PLAN) or receipt["plan_sha256"] != sha(PLAN):
        raise RuntimeError("Installation receipt mismatch")
    before = {r["path"]: r for r in plan["before"]}
    rows_check(RECOVERY / "old", [before[p] for p in CHANGED])
    print(json.dumps({"status": "INSTALLED_VERIFIED_ROLLBACK_READY", "files": 51,
                      "saves": len(plan["saves"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "install", "verify"))
    {"prepare": prepare, "install": install, "verify": verify}[parser.parse_args().action]()
