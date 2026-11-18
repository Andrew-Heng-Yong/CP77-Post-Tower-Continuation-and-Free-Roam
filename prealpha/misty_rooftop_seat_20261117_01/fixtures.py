"""Exercise the three-file replacement in isolated workspace directories."""

import shutil

from build import CHANGED, GAME, ROOT, row, verify_rows, write
from deploy import DEPLOYMENT, PACKAGE, archive_environment, install, recover, snapshot, verify_protected


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
    for extension in ("archive", "archive.xl"):
        (game / "archive/pc/mod" / f"external.{extension}").write_bytes(b"external archive fixture")
    saves.mkdir()
    (saves / "test.sav").write_bytes(b"protected fixture save")
    plan = {"before": before, "after": [row(PACKAGE, relative) for relative in CHANGED],
            "required_files": [row(game, "external.mod")], "archivexl_files": [], "ifp_files": [], "preferences": [],
            "archive_environment": archive_environment(game), "saved_files": snapshot(saves)}
    return plan, game, saves, recovery


def allow_fixture():
    pass


def main():
    plan, game, saves, recovery = make_fixture("complete")
    install(plan, game, saves, PACKAGE, recovery, allow_fixture)
    verify_rows(game, plan["after"])
    recover(plan, game, saves, recovery, allow_fixture)
    verify_rows(game, plan["before"])
    verify_protected(plan, game, saves)
    assert not list(game.rglob(".ptfr_seat_*"))

    for step in range(1, len(CHANGED) + 1):
        plan, game, saves, recovery = make_fixture(f"interruption_{step}")
        try:
            install(plan, game, saves, PACKAGE, recovery, allow_fixture, fail_after=step)
        except RuntimeError as error:
            assert str(error) == f"Fixture interruption after replacement {step}"
        else:
            raise AssertionError("Interruption fixture did not run")
        assert (recovery / "recovered.json").is_file()
        verify_rows(game, plan["before"])
        verify_protected(plan, game, saves)
        assert not list(game.rglob(".ptfr_seat_*"))

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
    verify_rows(game, plan["after"][1:])
    verify_protected(plan, game, saves)
    assert not list(game.rglob(".ptfr_seat_*"))

    write(DEPLOYMENT / "fixture_results.json", {"status": "PASS",
          "cases": ["install and exact rollback", "recovery after archive replacement",
                    "recovery after ArchiveXL replacement", "recovery after REDscript replacement",
                    "unknown target drift refused before any restore"],
          "game_writes": 0, "save_writes": 0})
    print("Five isolated deployment and recovery fixtures passed.")


if __name__ == "__main__":
    main()
