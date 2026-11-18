"""Install the verified arm resume script and retain the predecessor for recovery."""

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from build import (BASE_SHA, CHANGED, GAME, ROOT, SAVES, compiler_sources, plain,
                   read, row, safe, sha, verified_baseline, verify_rows, write)


CANDIDATE = ROOT / "candidate_01"
PACKAGE = CANDIDATE / "package"
PLAN = ROOT / "install_plan.json"
RECOVERY = ROOT / "file_recovery"
PROOFS = {"core": CANDIDATE / "core_manifest.json", "compile": CANDIDATE / "compile_01/assessment.json",
          "verification": CANDIDATE / "verification.json", "fixtures": ROOT / "deployment_fixtures.json"}


def closed() -> None:
    cmd = ["powershell.exe", "-NoProfile", "-Command",
           "@(Get-Process -Name Cyberpunk2077,REDlauncher,REDprelauncher "
           "-ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName) -join ','"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if result.returncode or result.stdout.strip() or result.stderr.strip():
        raise RuntimeError(f"Game and launcher must be closed: {result.stdout} {result.stderr}")


def snapshot(saves: Path) -> list[dict]:
    plain(saves)
    result = []
    for folder, dirs, files in os.walk(saves, followlinks=False):
        for name in dirs + files:
            plain(Path(folder) / name)
        result.extend(row(saves, (Path(folder) / name).relative_to(saves).as_posix()) for name in files)
    return sorted(result, key=lambda r: r["path"])


def compare_sources(proof: dict, expected: str) -> None:
    inputs = compiler_sources()
    if proof[expected].keys() != inputs.keys() or any(sha(p) != proof[expected][name] for name, p in inputs.items()):
        raise RuntimeError("Live compiler source inventory or bytes changed")
    if expected == "source_before" and any(sha(Path(p)) != digest for p, digest in proof["auxiliary_inputs"].items()):
        raise RuntimeError("Base cache, registry, or compiler drift")


def prepare() -> None:
    closed()
    base = verified_baseline()
    candidate, proof, verification, fixtures = (read(PROOFS[k]) for k in ("core", "compile", "verification", "fixtures"))
    old = {r["path"]: r for r in base["core_files"]}
    new = {r["path"]: r for r in candidate["core_files"]}
    if (candidate["status"] != "STAGED_OFFLINE" or candidate["baseline_sha256"] != BASE_SHA or
        proof["status"] != "PASS" or verification["status"] != "PASS" or fixtures["status"] != "PASS" or
        candidate["compile_assessment_sha256"] != sha(PROOFS["compile"]) or
        verification["candidate_sha256"] != sha(PROOFS["core"]) or
        old.keys() != new.keys() or {p for p in old if old[p] != new[p]} != set(CHANGED)):
        raise RuntimeError("Unqualified candidate or changed path inventory")
    verify_rows(PACKAGE, candidate["core_files"])
    compare_sources(proof, "source_before")
    preferences = [row(GAME, r["path"]) for r in base["preferences_at_install"]]
    write(PLAN, {"schema": "PTFR_ARM_REFRESH_REPLACEMENT_V1", "baseline_sha256": BASE_SHA,
                 "game_root": str(GAME), "save_root": str(SAVES), "package_root": str(PACKAGE),
                 "paths": list(CHANGED), "proofs": {k: sha(p) for k, p in PROOFS.items()},
                 "before": base["core_files"], "after": candidate["core_files"],
                 "required_files": base["required_files"], "ifp_files": base["ifp_files"],
                 "preferences": preferences, "saved_files": snapshot(SAVES)})
    print(json.dumps({"status": "READY", "plan_sha256": sha(PLAN)}))


def verify_protected(plan: dict, game: Path, saves: Path) -> None:
    verify_rows(game, plan["required_files"] + plan["ifp_files"] + plan["preferences"])
    if snapshot(saves) != plan["saved_files"]:
        raise RuntimeError("Save inventory or bytes changed")


def replace(source: Path, target: Path, before: dict, after: dict, guard) -> None:
    plain(source)
    plain(target)
    with tempfile.NamedTemporaryFile(prefix=".ptfr_photo_", dir=target.parent, delete=False) as f:
        temp = Path(f.name)
    try:
        shutil.copyfile(source, temp)
        if temp.stat().st_size != after["bytes"] or sha(temp) != after["sha256"]:
            raise RuntimeError("Replacement staging drift")
        guard()
        plain(target)
        if sha(target) != before["sha256"]:
            raise RuntimeError(f"Target drift: {target}")
        os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)


def recover(plan: dict, game: Path, saves: Path, recovery: Path, guard) -> None:
    before = {r["path"]: r for r in plan["before"]}
    after = {r["path"]: r for r in plan["after"]}
    guard()
    verify_rows(recovery / "old", [before[p] for p in CHANGED])
    current = {p: row(game, p) for p in CHANGED}
    # Detect unrelated drift before doing any restoration.
    for p in CHANGED:
        if current[p] not in (before[p], after[p]):
            raise RuntimeError(f"Unknown target drift, recovery refused: {p}")
    verify_rows(game, [r for r in plan["before"] if r["path"] not in CHANGED])
    for p in reversed(CHANGED):
        if current[p] == after[p]:
            replace(safe(recovery / "old", p), safe(game, p), after[p], before[p], guard)
    verify_rows(game, plan["before"])
    verify_protected(plan, game, saves)


def install(plan: dict, game: Path, saves: Path, package: Path, recovery: Path, guard, *, fail_first=False) -> None:
    guard()
    verify_rows(game, plan["before"])
    verify_rows(package, plan["after"])
    verify_protected(plan, game, saves)
    before = {r["path"]: r for r in plan["before"]}
    after = {r["path"]: r for r in plan["after"]}
    plain(recovery)
    recovery.mkdir(exist_ok=False)
    for p in CHANGED:
        old = safe(recovery / "old", p)
        old.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe(game, p), old)
    verify_rows(recovery / "old", [before[p] for p in CHANGED])
    write(recovery / "prepared.json", {"paths": list(CHANGED), "before": [before[p] for p in CHANGED],
                                      "after": [after[p] for p in CHANGED]})
    try:
        for p in CHANGED:
            replace(safe(package, p), safe(game, p), before[p], after[p], guard)
            if fail_first:
                raise RuntimeError("Fixture interruption after first replacement")
        guard()
        verify_rows(game, plan["after"])
        verify_protected(plan, game, saves)
        write(recovery / "installed.json", {"status": "INSTALLED_VERIFIED",
              "core_files": len(plan["after"]), "changed_paths": list(CHANGED),
              "protected_files": len(plan["required_files"]) + len(plan["ifp_files"]) + len(plan["preferences"]),
              "save_files_preserved": len(plan["saved_files"]), "game_launches": 0, "save_writes": 0})
    except Exception:
        recover(plan, game, saves, recovery, guard)
        write(recovery / "recovered.json", {"status": "RESTORED_PREDECESSOR_VERIFIED"})
        raise


def load_plan(expected: str) -> dict:
    if len(expected) != 64 or sha(PLAN) != expected:
        raise RuntimeError("Install plan hash mismatch")
    plan = read(PLAN)
    if (plan["schema"] != "PTFR_ARM_REFRESH_REPLACEMENT_V1" or plan["baseline_sha256"] != BASE_SHA or
        plan["paths"] != list(CHANGED) or plan["game_root"] != str(GAME) or plan["save_root"] != str(SAVES) or
        plan["package_root"] != str(PACKAGE) or plan["proofs"] != {k: sha(p) for k, p in PROOFS.items()}):
        raise RuntimeError("Wrong plan or altered proof")
    return plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "install", "verify", "recover"))
    parser.add_argument("--plan-sha", default="")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
        return
    closed()
    plan = load_plan(args.plan_sha)
    proof = read(PROOFS["compile"])
    if args.action == "install":
        verified_baseline()
        compare_sources(proof, "source_before")
        install(plan, GAME, SAVES, PACKAGE, RECOVERY, closed)
    if args.action == "recover":
        journal = read(RECOVERY / "prepared.json")
        if journal["paths"] != list(CHANGED) or (RECOVERY / "recovered.json").exists():
            raise RuntimeError("No matching deployment to recover")
        # Take the current save and preference snapshot for file-only recovery.
        plan["saved_files"] = snapshot(SAVES)
        plan["preferences"] = [row(GAME, r["path"]) for r in plan["preferences"]]
        recover(plan, GAME, SAVES, RECOVERY, closed)
        write(RECOVERY / "recovered.json", {"status": "RESTORED_PREDECESSOR_VERIFIED"})
        print("Predecessor scripts verified.")
        return
    verify_rows(GAME, plan["after"])
    verify_protected(plan, GAME, SAVES)
    compare_sources(proof, "source_after")
    verify_rows(RECOVERY / "old", [r for r in plan["before"] if r["path"] in CHANGED])
    print("Installed 51 Core paths verified. The predecessor script is available for rollback.")


if __name__ == "__main__":
    main()
