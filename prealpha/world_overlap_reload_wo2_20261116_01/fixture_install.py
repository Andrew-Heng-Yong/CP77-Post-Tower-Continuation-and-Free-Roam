"""Exercise one-file install, crash recovery, drift refusal and rollback in workspace."""

from pathlib import Path
import json
import shutil

import installer

HERE = Path(__file__).resolve().parent
ROOT = HERE / "fixtures_01"
RESULT = HERE / "fixture_results_01.json"


def row(root: Path, relative: str) -> dict:
    path = root / relative
    return {"path": relative, "bytes": path.stat().st_size, "sha256": installer.sha(path)}


def fixture(name: str):
    root = ROOT / name
    root.mkdir(parents=True, exist_ok=False)
    game, saves, package = (root / label for label in ("game", "saves", "package"))
    changed = installer.SCRIPT
    old = game / changed
    new = package / changed
    old.parent.mkdir(parents=True)
    new.parent.mkdir(parents=True)
    shutil.copyfile(installer.GAME / changed, old)
    shutil.copyfile(installer.OUT / "package" / changed, new)
    external = game / "ExternalMod/keep.dat"
    external.parent.mkdir()
    external.write_bytes(b"external preserved")
    saved = saves / "FixtureSave/sav.dat"
    saved.parent.mkdir(parents=True)
    saved.write_bytes(b"fixture save preserved")
    before, after = row(game, changed), row(package, changed)
    plan = {"changed_path": changed, "before": before, "after": after,
            "core_before": [before], "core_after": [after],
            "required": [row(game, "ExternalMod/keep.dat")], "ifp": [], "preferences": [],
            "saved_files": [row(saves, "FixtureSave/sav.dat")]}
    return plan, game, saves, package, root / "recovery", root / "installed.json"


def main() -> None:
    if ROOT.exists() or RESULT.exists():
        raise RuntimeError("Fresh fixture output required")
    cases = []
    args = fixture("clean_rollback")
    plan, game, saves, package, recovery, receipt = args
    installer.install_files(*args, guard_process=False)
    installer.verify_rows(game, plan["core_after"])
    installer.verify_protected(plan, game, saves)
    installer.rollback_files(plan, game, saves, recovery, receipt, guard_process=False)
    installer.verify_rows(game, plan["core_before"])
    cases.append("exact install and rollback preserve external file and save")

    args = fixture("crash_recover")
    plan, game, saves, package, recovery, receipt = args
    try:
        installer.install_files(*args, guard_process=False, failure_point="crash_after_replace")
    except SystemExit as error:
        assert error.code == 72
    else:
        raise AssertionError("Crash fixture did not stop")
    installer.verify_rows(game, plan["core_after"])
    installer.recover_files(plan, game, saves, recovery, guard_process=False)
    installer.verify_rows(game, plan["core_before"])
    installer.verify_protected(plan, game, saves)
    cases.append("interrupted replacement restores exact old bytes")

    args = fixture("unknown_drift")
    plan, game, saves, package, recovery, receipt = args
    try:
        installer.install_files(*args, guard_process=False, failure_point="crash_after_replace")
    except SystemExit as error:
        assert error.code == 72
    else:
        raise AssertionError("Drift fixture did not stop")
    target = game / plan["changed_path"]
    target.write_bytes(b"independent unknown change")
    try:
        installer.recover_files(plan, game, saves, recovery, guard_process=False)
    except RuntimeError as error:
        assert "Unknown target drift" in str(error)
    else:
        raise AssertionError("Unknown drift was not refused")
    assert target.read_bytes() == b"independent unknown change"
    installer.verify_protected(plan, game, saves)
    cases.append("unknown changed file preserved for review")

    with RESULT.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump({"status": "PASS", "cases": cases, "game_writes": 0, "save_writes": 0}, stream, indent=2)
        stream.write("\n")
    print(f"PASS: {len(cases)} isolated install/recovery fixtures")


if __name__ == "__main__":
    main()
