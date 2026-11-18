"""Use the two actual archives in isolated copies of the installation target."""

import shutil

from install_repair import (ARCHIVE, DEPLOY, FIXTURES, GAME, PACKAGE, ROOT, archive_environment,
                            install_archive, recover_archive, row, safe, snapshot, validate_package,
                            verify_protected, verify_rows, write)


def fixture_guard():
    pass


def interrupt():
    raise RuntimeError("Fixture interruption")


def main():
    base, core, _ = validate_package()
    fixture_root = ROOT / "deployment_fixtures"
    fixture_root.mkdir(exist_ok=False)
    DEPLOY.mkdir(exist_ok=False)
    cases = ["clean rollback", "interrupted install", "unknown archive drift"]
    for name in cases:
        root = fixture_root / name
        game, saves, recovery = root / "game", root / "saves", root / "recovery"
        target = safe(game, ARCHIVE)
        target.parent.mkdir(parents=True)
        shutil.copyfile(safe(GAME, ARCHIVE), target)
        protected_path = "archive/pc/mod/external.archive.xl"
        safe(game, protected_path).write_bytes(b"fixture registration")
        (target.parent / "external.archive").write_bytes(b"fixture data")
        saves.mkdir()
        (saves / "sav.dat").write_bytes(b"fixture save")
        plan = {"before": [r for r in base["core_files"] if r["path"] == ARCHIVE],
                "after": [r for r in core["core_files"] if r["path"] == ARCHIVE],
                "required_files": [row(game, protected_path)], "archivexl_files": [],
                "ifp_files": [], "preferences": [], "archive_environment": archive_environment(game),
                "saved_files": snapshot(saves)}
        if name == "interrupted install":
            try:
                install_archive(plan, game, saves, PACKAGE, recovery, fixture_guard, interrupt)
            except RuntimeError as error:
                assert str(error) == "Fixture interruption"
            else:
                raise AssertionError("Interruption missing")
            assert (recovery / "recovered.json").is_file()
            verify_rows(game, plan["before"])
        else:
            install_archive(plan, game, saves, PACKAGE, recovery, fixture_guard)
            verify_rows(game, plan["after"])
            if name == "unknown archive drift":
                target.write_bytes(b"unexpected archive")
                try:
                    recover_archive(plan, game, recovery / "old", fixture_guard)
                except RuntimeError as error:
                    assert "Unknown archive drift" in str(error)
                else:
                    raise AssertionError("Unknown archive was overwritten")
                assert target.read_bytes() == b"unexpected archive"
            else:
                recover_archive(plan, game, recovery / "old", fixture_guard)
                verify_rows(game, plan["before"])
        verify_protected(plan, game, saves)
        assert not list(game.rglob(".ptfr_seat_*"))
    write(FIXTURES, {"status": "PASS", "cases": cases, "game_writes": 0, "save_writes": 0})
    print("Three single-archive deployment and recovery fixtures passed.")


if __name__ == "__main__":
    main()
