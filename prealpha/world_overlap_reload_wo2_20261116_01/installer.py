"""Guarded one-script WO2 install, verification and exact file rollback."""

from pathlib import Path
import argparse
import json
import os
import shutil
import stat
import tempfile

from prepare_candidate import GAME, HERE, OUT, SCRIPT, plain, sha
from prepare_install import PLAN, SAVES, closed, snapshot

PLAN_SHA = "AED49BDB813E5D3316101A1A9DA79CC24912DAAA085475F7202BBDF0436B1A47"
RECOVERY = HERE / "recovery_01"
RECEIPT = HERE / "installed_01.json"


def safe(root: Path, relative: str) -> Path:
    parts = relative.split("/")
    if not parts or any(not p or p in (".", "..") or p.endswith((".", " ")) or
                        ":" in p or "\\" in p for p in parts):
        raise RuntimeError(f"Unsafe relative path: {relative}")
    path = root.joinpath(*parts)
    if not path.absolute().is_relative_to(root.absolute()):
        raise RuntimeError(f"Path escapes root: {relative}")
    plain(path)
    return path


def verify_rows(root: Path, rows: list[dict]) -> None:
    for row in rows:
        path = safe(root, row["path"])
        if not path.is_file() or path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise RuntimeError(f"Protected file drift: {path}")


def verify_protected(plan: dict, game: Path, saves: Path) -> None:
    verify_rows(game, plan["required"] + plan["ifp"] + plan["preferences"])
    verify_rows(saves, plan["saved_files"])
    if snapshot(saves) != plan["saved_files"]:
        raise RuntimeError("Save inventory changed")


def write_new(path: Path, value: dict) -> None:
    plain(path)
    if path.exists():
        raise RuntimeError(f"Evidence already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def rewrite(path: Path, value: dict) -> None:
    plain(path)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def replace_file(source: Path, target: Path, expected_sha: str, *, guard_process: bool) -> None:
    plain(source)
    plain(target)
    if guard_process:
        closed()
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".wo2_", dir=target.parent)
    os.close(descriptor)
    try:
        shutil.copyfile(source, temporary)
        if sha(Path(temporary)) != expected_sha:
            raise RuntimeError("Temporary replacement drift")
        if guard_process:
            closed()
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_plan() -> dict:
    if sha(PLAN) != PLAN_SHA:
        raise RuntimeError("Deployment plan drift")
    plan = json.loads(PLAN.read_text(encoding="utf-8-sig"))
    if plan["schema"] != "WO2_ONE_SCRIPT_INSTALL_V1" or plan["changed_path"] != SCRIPT or \
       plan["game_root"] != str(GAME) or plan["save_root"] != str(SAVES) or \
       plan["package_root"] != str(OUT / "package") or \
       len(plan["core_before"]) != 51 or len(plan["core_after"]) != 51 or \
       [r["path"] for r in plan["core_before"] if r not in plan["core_after"]] != [SCRIPT]:
        raise RuntimeError("Unexpected deployment plan")
    evidence = {"candidate_sha256": OUT / "core_manifest_01.json",
                "compile_sha256": OUT / "compile_01/assessment.json",
                "assessment_sha256": OUT / "assessment.json"}
    for key, path in evidence.items():
        if sha(path) != plan[key]:
            raise RuntimeError(f"Pinned proof drift: {path}")
    return plan


def verify_compiler_inputs(plan: dict, *, installed: bool) -> None:
    compiled = json.loads((OUT / "compile_01/assessment.json").read_text(encoding="utf-8-sig"))
    expected = compiled["staged_sources"] if installed else {
        Path(path).relative_to(GAME).as_posix(): digest
        for path, digest in compiled["input_hashes"].items() if path.lower().endswith(".reds")}
    actual = {path.relative_to(GAME).as_posix()
              for root in (GAME / "r6/scripts", GAME / "red4ext/plugins")
              for path in root.rglob("*.reds")}
    if set(expected) != actual:
        raise RuntimeError("REDscript source inventory changed")
    for relative, digest in expected.items():
        if sha(safe(GAME, relative)) != digest:
            raise RuntimeError(f"REDscript source drift: {relative}")
    if not installed:
        for path, digest in compiled["input_hashes"].items():
            if not path.lower().endswith(".reds") and sha(Path(path)) != digest:
                raise RuntimeError(f"Compiler input drift: {path}")


def validate() -> dict:
    closed()
    plan = load_plan()
    verify_rows(GAME, plan["core_before"])
    verify_rows(OUT / "package", plan["core_after"])
    verify_protected(plan, GAME, SAVES)
    verify_compiler_inputs(plan, installed=False)
    return plan


def install_files(plan: dict, game: Path, saves: Path, package: Path,
                  recovery: Path, receipt: Path, *, guard_process: bool,
                  failure_point: str = "") -> None:
    if guard_process:
        closed()
    if recovery.exists() or receipt.exists():
        raise RuntimeError("Deployment already attempted; preserve recovery evidence")
    verify_rows(game, plan["core_before"])
    verify_rows(package, plan["core_after"])
    verify_protected(plan, game, saves)
    changed = plan["changed_path"]
    target = safe(game, changed)
    backup = safe(recovery / "old", changed)
    backup.parent.mkdir(parents=True)
    recovery.mkdir(exist_ok=True)
    shutil.copyfile(target, backup)
    verify_rows(recovery / "old", [plan["before"]])
    journal = {"state": "PREPARED", "plan_sha256": sha(PLAN) if guard_process else "FIXTURE",
               "changed_path": changed, "before_sha256": plan["before"]["sha256"],
               "after_sha256": plan["after"]["sha256"]}
    write_new(recovery / "journal.json", journal)
    try:
        replace_file(safe(package, changed), target, plan["after"]["sha256"], guard_process=guard_process)
        if failure_point == "crash_after_replace":
            raise SystemExit(72)
        verify_rows(game, plan["core_after"])
        verify_protected(plan, game, saves)
        journal["state"] = "INSTALLED_VERIFIED"
        rewrite(recovery / "journal.json", journal)
        write_new(receipt, {"status": "INSTALLED_VERIFIED", "plan_sha256": journal["plan_sha256"],
                            "changed_paths": [changed], "core_files": len(plan["core_after"]),
                            "saves_preserved": len(plan["saved_files"]), "game_launches": 0, "save_writes": 0})
    except Exception:
        recover_files(plan, game, saves, recovery, guard_process=guard_process)
        raise


def recover_files(plan: dict, game: Path, saves: Path, recovery: Path,
                  *, guard_process: bool) -> None:
    if guard_process:
        closed()
    journal_path = recovery / "journal.json"
    journal = json.loads(journal_path.read_text(encoding="utf-8-sig"))
    if journal["state"] != "PREPARED" or journal["changed_path"] != plan["changed_path"]:
        raise RuntimeError("No interrupted deployment to recover")
    backup = safe(recovery / "old", plan["changed_path"])
    verify_rows(recovery / "old", [plan["before"]])
    target = safe(game, plan["changed_path"])
    current = sha(target)
    if current == plan["after"]["sha256"]:
        replace_file(backup, target, plan["before"]["sha256"], guard_process=guard_process)
    elif current != plan["before"]["sha256"]:
        journal["state"] = "UNKNOWN_DRIFT_REVIEW_REQUIRED"
        rewrite(journal_path, journal)
        raise RuntimeError("Unknown target drift; recovery refused")
    verify_rows(game, plan["core_before"])
    verify_protected(plan, game, saves)
    journal["state"] = "RESTORED_BEFORE_VERIFIED"
    rewrite(journal_path, journal)


def verify_install(plan: dict) -> None:
    closed()
    verify_rows(GAME, plan["core_after"])
    verify_protected(plan, GAME, SAVES)
    verify_compiler_inputs(plan, installed=True)
    verify_rows(RECOVERY / "old", [plan["before"]])
    journal = json.loads((RECOVERY / "journal.json").read_text(encoding="utf-8-sig"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8-sig"))
    if journal["state"] != "INSTALLED_VERIFIED" or receipt["status"] != "INSTALLED_VERIFIED" or \
       journal["plan_sha256"] != PLAN_SHA or receipt["plan_sha256"] != PLAN_SHA:
        raise RuntimeError("Installation receipt mismatch")


def rollback_files(plan: dict, game: Path, saves: Path, recovery: Path,
                   receipt: Path, *, guard_process: bool) -> None:
    if guard_process:
        closed()
    journal_path = recovery / "journal.json"
    journal = json.loads(journal_path.read_text(encoding="utf-8-sig"))
    installed = json.loads(receipt.read_text(encoding="utf-8-sig"))
    if journal["state"] != "INSTALLED_VERIFIED" or installed["status"] != "INSTALLED_VERIFIED":
        raise RuntimeError("Exact installed state required for rollback")
    verify_rows(game, plan["core_after"])
    verify_protected(plan, game, saves)
    verify_rows(recovery / "old", [plan["before"]])
    changed = plan["changed_path"]
    replace_file(safe(recovery / "old", changed), safe(game, changed),
                 plan["before"]["sha256"], guard_process=guard_process)
    verify_rows(game, plan["core_before"])
    verify_protected(plan, game, saves)
    journal["state"] = "ROLLED_BACK_VERIFIED"
    rewrite(journal_path, journal)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("validate", "install", "verify", "recover", "validate_rollback", "rollback"))
    action = parser.parse_args().action
    if action == "validate":
        plan = validate()
        print(json.dumps({"status": "READY_NOT_INSTALLED", "changed": 1,
                          "saved_files": len(plan["saved_files"])}))
    elif action == "install":
        plan = validate()
        fixtures = json.loads((HERE / "fixture_results_01.json").read_text(encoding="utf-8-sig"))
        if fixtures["status"] != "PASS":
            raise RuntimeError("Deployment fixtures missing")
        install_files(plan, GAME, SAVES, OUT / "package", RECOVERY, RECEIPT, guard_process=True)
        verify_install(plan)
        print(json.dumps({"status": "INSTALLED_VERIFIED", "changed": 1,
                          "saved_files": len(plan["saved_files"])}))
    elif action in ("verify", "validate_rollback"):
        plan = load_plan()
        verify_install(plan)
        print(json.dumps({"status": "INSTALLED_VERIFIED_ROLLBACK_READY", "changed": 1,
                          "saved_files": len(plan["saved_files"])}))
    elif action == "recover":
        plan = load_plan()
        recover_files(plan, GAME, SAVES, RECOVERY, guard_process=True)
        print(json.dumps({"status": "RESTORED_BEFORE_VERIFIED"}))
    else:
        plan = load_plan()
        rollback_files(plan, GAME, SAVES, RECOVERY, RECEIPT, guard_process=True)
        print(json.dumps({"status": "ROLLED_BACK_VERIFIED"}))


if __name__ == "__main__":
    main()
