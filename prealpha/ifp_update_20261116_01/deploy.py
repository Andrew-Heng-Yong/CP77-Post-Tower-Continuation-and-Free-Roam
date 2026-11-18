"""Guarded, exact-file IFP v2.2.0 update. Writes only with install action."""

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORK = HERE / "work"
GAME = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
SAVES = Path(r"C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077")
STAGED = WORK / "staged_01"
PLAN = WORK / "plan_01.json"
RECOVERY = WORK / "recovery_01"
ZIP = WORK / "Immersive.First.Person.zip"
ZIP_SHA = "F576D7FA67818F87E231F8AFC4C1840D0AFC82C0C1BE26C74646EFD478C15809"
CORE = ROOT / "prealpha/credits_cover_lc5_20261116_01/work/deployment_01/installed_manifest_01.json"
COMPILE = ROOT / "prealpha/credits_cover_lc5_20261116_01/candidate_01/compile_01/assessment.json"
MANAGED_PREFIXES = (
    "archive/pc/mod/ImmersiveFirstPersonHeight.archive",
    "bin/x64/plugins/cyber_engine_tweaks/mods/ImmersiveFirstPerson/",
    "r6/scripts/ImmersiveFirstPerson/",
    "red4ext/plugins/ImmersiveFirstPerson/",
)
PROCESS_NAMES = {"cyberpunk2077", "redlauncher", "redprelauncher"}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def plain(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.exists() and part.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise RuntimeError(f"Reparse path refused: {part}")


def safe(base, relative):
    parts = relative.split("/")
    if (not parts or any(not part or part in (".", "..") or part.endswith(".")
                         or part.endswith(" ") or ":" in part or "\\" in part for part in parts)):
        raise RuntimeError(f"Unsafe relative path: {relative}")
    result = base.joinpath(*parts)
    if not result.absolute().is_relative_to(base.absolute()):
        raise RuntimeError(f"Path escaped target: {relative}")
    plain(result)
    return result


def closed():
    command = ["powershell.exe", "-NoProfile", "-Command",
               "@(Get-Process -Name Cyberpunk2077,REDlauncher,REDprelauncher "
               "-ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName) "
               "-join ','"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=12)
    if result.returncode or result.stdout.strip():
        raise RuntimeError(f"Game or launcher is running, or process check failed: {result.stdout} {result.stderr}")


def snapshot(root):
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


def check_rows(base, rows):
    for row in rows:
        path = safe(base, row["path"])
        if not path.is_file() or path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise RuntimeError(f"Protected file changed: {path}")


def check_sources():
    assessment = json.loads(COMPILE.read_text(encoding="utf-8-sig"))
    expected = assessment["staged_sources"]
    actual = {path.relative_to(GAME).as_posix() for base in (GAME / "r6/scripts", GAME / "red4ext/plugins")
              for path in base.rglob("*.reds")}
    if actual != set(expected):
        raise RuntimeError("REDscript inventory changed since the 149-source compile")
    for relative, digest in expected.items():
        if sha(safe(GAME, relative)) != digest:
            raise RuntimeError(f"REDscript changed since compile: {relative}")
    return len(expected)


def write_new(path, obj):
    plain(path)
    if path.exists():
        raise RuntimeError(f"Evidence path already occupied: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(obj, stream, indent=2)
        stream.write("\n")


def read_plan():
    if sha(ZIP) != ZIP_SHA:
        raise RuntimeError("Official ZIP checksum changed")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if plan["schema"] != "IFP_2_2_0_EXACT_UPDATE_V1" or plan["zip_sha256"] != ZIP_SHA:
        raise RuntimeError("Wrong plan or source ZIP")
    if sha(CORE) != plan["core_manifest_sha256"] or sha(COMPILE) != plan["compile_assessment_sha256"]:
        raise RuntimeError("Pinned Core/compile evidence changed")
    return plan


def prepare():
    closed()
    if PLAN.exists() or RECOVERY.exists():
        raise RuntimeError("Fresh preparation required; preserve the existing plan/recovery")
    if sha(ZIP) != ZIP_SHA:
        raise RuntimeError("Official release checksum mismatch")
    core = json.loads(CORE.read_text(encoding="utf-8-sig"))
    if core["core_epoch"] != "LC5_CREDITS_COVER" or len(core["core_files"]) != 51:
        raise RuntimeError("Unexpected Tower baseline")
    check_rows(GAME, core["core_files"] + core["required_files"])
    source_count = check_sources()
    staged = snapshot(STAGED)
    if len(staged) != 14 or any(not any(row["path"].startswith(p) for p in MANAGED_PREFIXES)
                                for row in staged):
        raise RuntimeError("Unexpected official payload paths")
    if any(row["path"] in {r["path"] for r in core["core_files"] + core["required_files"]}
           for row in staged):
        raise RuntimeError("IFP payload collides with Tower/protected dependency")
    managed = []
    for row in staged:
        live = safe(GAME, row["path"])
        managed.append({"path": row["path"], "before":
                        {"bytes": live.stat().st_size, "sha256": sha(live)} if live.exists() else None,
                        "after": {"bytes": row["bytes"], "sha256": row["sha256"]}})
    prefs = ["bin/x64/plugins/cyber_engine_tweaks/mods/ImmersiveFirstPerson/config.json",
             "bin/x64/plugins/cyber_engine_tweaks/mods/ImmersiveFirstPerson/db.sqlite3",
             "bin/x64/plugins/cyber_engine_tweaks/mods/ImmersiveFirstPerson/ImmersiveFirstPerson.log",
             "bin/x64/plugins/cyber_engine_tweaks/bindings.json"]
    protected = []
    for rel in prefs:
        path = safe(GAME, rel)
        if path.exists():
            protected.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha(path)})
    plan = {"schema": "IFP_2_2_0_EXACT_UPDATE_V1", "source_url":
            "https://github.com/cp2077/ImmersiveFirstPerson/releases/download/v2.2.0/Immersive.First.Person.zip",
            "zip_sha256": ZIP_SHA, "core_manifest_sha256": sha(CORE),
            "compile_assessment_sha256": sha(COMPILE), "compiled_sources_verified": source_count,
            "managed": managed, "core": core["core_files"], "dependencies": core["required_files"],
            "preferences": protected, "saves": snapshot(SAVES),
            "game_writes": 0, "save_writes": 0}
    write_new(PLAN, plan)
    print(json.dumps({"status": "PREPARED", "files": len(managed),
                      "changed": sum(x["before"] is None or x["before"]["sha256"] != x["after"]["sha256"]
                                     for x in managed), "saves": len(plan["saves"]),
                      "source_count": source_count, "plan_sha256": sha(PLAN)}))


def check_protected(plan):
    check_rows(GAME, plan["core"] + plan["dependencies"] + plan["preferences"])
    check_rows(SAVES, plan["saves"])
    if snapshot(SAVES) != plan["saves"]:
        raise RuntimeError("Save tree changed")


def check_managed(plan, side):
    for row in plan["managed"]:
        path = safe(GAME, row["path"])
        expected = row[side]
        if expected is None:
            if path.exists():
                raise RuntimeError(f"New target path occupied: {path}")
        elif not path.is_file() or path.stat().st_size != expected["bytes"] or sha(path) != expected["sha256"]:
            raise RuntimeError(f"Managed file drift: {path}")


def replace_from(source, target, expected):
    plain(source)
    plain(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".ifp22_", dir=target.parent)
    os.close(fd)
    try:
        shutil.copyfile(source, temporary)
        if sha(temporary) != expected["sha256"]:
            raise RuntimeError("Staged replacement checksum mismatch")
        closed()
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install():
    closed()
    plan = read_plan()
    if RECOVERY.exists():
        raise RuntimeError("Recovery already occupied; do not rerun installation")
    check_protected(plan)
    check_managed(plan, "before")
    check_sources()
    check_rows(STAGED, [{"path": r["path"], **r["after"]} for r in plan["managed"]])
    changes = [r for r in plan["managed"] if r["before"] is None or
               r["before"]["sha256"] != r["after"]["sha256"]]
    RECOVERY.mkdir()
    for row in changes:
        source = safe(GAME, row["path"])
        if row["before"] is not None:
            backup = safe(RECOVERY / "old", row["path"])
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, backup)
            if sha(backup) != row["before"]["sha256"]:
                raise RuntimeError("Backup checksum mismatch")
    journal = {"state": "PREPARED", "plan_sha256": sha(PLAN), "changed": [r["path"] for r in changes],
               "applied": []}
    write_new(RECOVERY / "journal.json", journal)
    try:
        for row in changes:
            closed()
            target = safe(GAME, row["path"])
            expected = row["before"]
            if expected is None:
                if target.exists():
                    raise RuntimeError("New target unexpectedly occupied")
            elif sha(target) != expected["sha256"]:
                raise RuntimeError("Target changed during installation")
            replace_from(safe(STAGED, row["path"]), target, row["after"])
            journal["applied"].append(row["path"])
            (RECOVERY / "journal.json").write_text(json.dumps(journal, indent=2) + "\n", encoding="utf-8")
        check_managed(plan, "after")
        check_protected(plan)
        journal["state"] = "INSTALLED_VERIFIED"
        (RECOVERY / "journal.json").write_text(json.dumps(journal, indent=2) + "\n", encoding="utf-8")
        write_new(WORK / "installed_01.json", {"status": "INSTALLED_VERIFIED", "plan_sha256": sha(PLAN),
                    "release_zip_sha256": ZIP_SHA, "files": len(plan["managed"]), "changed": len(changes),
                    "save_files_preserved": len(plan["saves"]), "core_files_preserved": len(plan["core"]),
                    "protected_dependencies_preserved": len(plan["dependencies"]),
                    "preferences_preserved": len(plan["preferences"]), "game_launches": 0,
                    "save_writes": 0})
        print(json.dumps({"status": "INSTALLED_VERIFIED", "changed": len(changes),
                          "saves": len(plan["saves"])}))
    except Exception:
        # Restore only the exact installed bytes. Preserve an unknown drift for review.
        for row in reversed(changes):
            target = safe(GAME, row["path"])
            current = sha(target) if target.is_file() else None
            if current == row["after"]["sha256"]:
                if row["before"] is None:
                    closed()
                    target.unlink()
                else:
                    replace_from(safe(RECOVERY / "old", row["path"]), target, row["before"])
            elif row["before"] is None and current is None:
                continue
            elif row["before"] is not None and current == row["before"]["sha256"]:
                continue
            else:
                journal["state"] = "UNKNOWN_DRIFT_REVIEW_REQUIRED"
                (RECOVERY / "journal.json").write_text(json.dumps(journal, indent=2) + "\n", encoding="utf-8")
                raise RuntimeError(f"Unknown target drift during recovery: {target}")
        check_managed(plan, "before")
        journal["state"] = "RESTORED_BEFORE_VERIFIED"
        (RECOVERY / "journal.json").write_text(json.dumps(journal, indent=2) + "\n", encoding="utf-8")
        raise


def verify():
    plan = read_plan()
    check_managed(plan, "after")
    check_protected(plan)
    journal = json.loads((RECOVERY / "journal.json").read_text())
    if journal["state"] != "INSTALLED_VERIFIED" or journal["plan_sha256"] != sha(PLAN):
        raise RuntimeError("Installation receipt mismatch")
    for row in plan["managed"]:
        if row["before"] is not None and row["before"]["sha256"] != row["after"]["sha256"]:
            backup = safe(RECOVERY / "old", row["path"])
            if sha(backup) != row["before"]["sha256"]:
                raise RuntimeError("Rollback backup changed")
    print(json.dumps({"status": "INSTALLED_VERIFIED_ROLLBACK_READY", "files": len(plan["managed"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "install", "verify"))
    action = parser.parse_args().action
    {"prepare": prepare, "install": install, "verify": verify}[action]()
