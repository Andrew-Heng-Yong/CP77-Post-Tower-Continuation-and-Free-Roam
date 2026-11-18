"""Exercise the exact script replacement in isolated workspace directories."""

import shutil

from build import CHANGED, GAME, ROOT, row, verify_rows, write
from deploy import PACKAGE, install, recover, snapshot


def make_fixture(name):
    root = ROOT / "deployment_fixtures" / name
    root.mkdir(parents=True, exist_ok=False)
    game, saves, recovery = (root / part for part in ("game", "saves", "recovery"))
    before = []
    for relative in CHANGED:
        target = game / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(GAME / relative, target)
        before.append(row(game, relative))
    (game / "external.mod").write_bytes(b"external")
    saves.mkdir()
    (saves / "test.sav").write_bytes(b"protected fixture save")
    plan = {"before": before, "after": [row(PACKAGE, relative) for relative in CHANGED],
            "required_files": [row(game, "external.mod")], "ifp_files": [], "preferences": [],
            "saved_files": snapshot(saves)}
    return plan, game, saves, recovery


def allow_fixture():
    pass


def main():
    plan, game, saves, recovery = make_fixture("complete")
    install(plan, game, saves, PACKAGE, recovery, allow_fixture)
    verify_rows(game, plan["after"])
    recover(plan, game, saves, recovery, allow_fixture)
    verify_rows(game, plan["before"])

    plan, game, saves, recovery = make_fixture("interruption")
    try:
        install(plan, game, saves, PACKAGE, recovery, allow_fixture, fail_first=True)
    except RuntimeError as error:
        assert "Fixture interruption" in str(error)
    else:
        raise AssertionError("Interruption fixture did not run")
    assert (recovery / "recovered.json").is_file()
    verify_rows(game, plan["before"])

    plan, game, saves, recovery = make_fixture("drift")
    install(plan, game, saves, PACKAGE, recovery, allow_fixture)
    changed = game / CHANGED[0]
    changed.write_bytes(b"external change")
    try:
        recover(plan, game, saves, recovery, allow_fixture)
    except RuntimeError as error:
        assert "Unknown target drift" in str(error)
    else:
        raise AssertionError("Recovery did not refuse unrelated drift")
    assert changed.read_bytes() == b"external change"
    verify_rows(game, plan["required_files"])
    assert snapshot(saves) == plan["saved_files"]

    write(ROOT / "deployment_fixtures.json", {"status": "PASS",
          "cases": ["script install and exact rollback", "interrupted replacement recovery",
                    "unknown target drift refused before any restore"],
          "game_writes": 0, "save_writes": 0})
    print("Three isolated deployment and recovery fixtures passed.")


if __name__ == "__main__":
    main()
