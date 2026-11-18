"""Exercise BV1 atomic replacement and exact rollback on workspace copies."""

from copy import deepcopy
import json
from pathlib import Path
import shutil

import deploy

WORK = Path(__file__).resolve().parent / "work"


def fixture(name: str) -> tuple[Path, dict]:
    root = WORK / name
    root.mkdir(exist_ok=False)
    (root / "saves").mkdir()
    plan = deepcopy(deploy.read_plan())
    plan["before"] = [row for row in plan["before"] if row["path"] in deploy.CHANGED]
    plan["after"] = [row for row in plan["after"] if row["path"] in deploy.CHANGED]
    plan["dependencies"] = []
    plan["ifp"] = []
    plan["preferences"] = []
    plan["saves"] = []
    deploy.GAME = root / "game"
    deploy.SAVES = root / "saves"
    deploy.RECOVERY = root / "recovery"
    deploy.RECOVERY.mkdir()
    for row in plan["before"]:
        relative = row["path"]
        source = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077") / relative
        target = deploy.safe(deploy.GAME, relative)
        backup = deploy.safe(deploy.RECOVERY / "old", relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        shutil.copyfile(source, backup)
    (deploy.RECOVERY / "journal.json").write_text(json.dumps({"state": "PREPARED",
        "changed_paths": list(deploy.CHANGED), "applied": []}) + "\n", encoding="utf-8")
    return root, plan


def main() -> None:
    deploy.closed()
    root, plan = fixture("fixture_restore_01")
    before = {row["path"]: row for row in plan["before"]}
    after = {row["path"]: row for row in plan["after"]}
    for relative in deploy.CHANGED:
        deploy.replace_from(deploy.safe(deploy.PACKAGE, relative),
                            deploy.safe(deploy.GAME, relative), after[relative])
    deploy.rows_check(deploy.GAME, plan["after"])
    deploy.restore(plan, {"state": "PREPARED", "changed_paths": list(deploy.CHANGED), "applied": list(deploy.CHANGED)})
    deploy.rows_check(deploy.GAME, plan["before"])
    assert json.loads((root / "recovery/journal.json").read_text())["state"] == "RESTORED_BEFORE_VERIFIED"

    root, plan = fixture("fixture_unknown_drift_01")
    relative = deploy.CHANGED[-1]
    target = deploy.safe(deploy.GAME, relative)
    target.write_bytes(b"unknown-external-change")
    try:
        deploy.restore(plan, {"state": "PREPARED", "changed_paths": list(deploy.CHANGED), "applied": []})
    except RuntimeError as error:
        assert "Unknown target drift" in str(error)
    else:
        raise AssertionError("Unknown drift was not refused")
    assert target.read_bytes() == b"unknown-external-change"
    assert json.loads((root / "recovery/journal.json").read_text())["state"] == "UNKNOWN_DRIFT_REVIEW_REQUIRED"

    result = {"status": "PASS", "cases": ["two_file_exact_replace_and_rollback",
             "unknown_drift_refused_and_preserved"], "game_writes": 0, "save_writes": 0}
    deploy.write_new(WORK / "fixture_results.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
