"""Stage, verify and deploy the single rooftop prompt archive."""

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import prompt

ROOT, BASE, ASSETS = prompt.ROOT, prompt.BASE, prompt.PACK / "readback.json"
sys.path.insert(0, str(ROOT.parent / "misty_rooftop_seat_repair_20261118_01"))
from install_repair import archive_row, install_archive, recover_archive
from build import ARCHIVE, EXE, EXE_SHA, GAME, read, row, safe, sha, verify_rows, write
from deploy import SAVES, archive_environment, closed, snapshot, verify_protected

PACKAGE = ROOT / "candidate_01/package"
CORE = PACKAGE.parent / "core_manifest.json"
FIXTURES, PLAN = ROOT / "fixture_results.json", ROOT / "install_plan.json"
RECOVERY = ROOT / "recovery"


def check_base():
    assert sha(BASE) == prompt.BASE_SHA and sha(safe(GAME, EXE)) == EXE_SHA
    base = read(BASE)
    assert len(base["core_files"]) == 51 and (base["game_root"],base["save_root"]) == (str(GAME),str(SAVES))
    previous = Path(base["installation_plan"])
    assert sha(previous) == base["installation_plan_sha256"]
    assert archive_environment(GAME) == read(previous)["archive_environment"]
    verify_rows(GAME, base["required_files"] + base["archivexl_files"] + base["ifp_files"])
    return base


def stage():
    base, assets = check_base(), read(ASSETS)
    verify_rows(GAME, base["core_files"])
    assert assets["status"] == "MEMBERS_VERIFIED" and assets["baseline_sha256"] == sha(BASE)
    assert (assets["checked_members"], assets["preserved_members"]) == (1751,1750)
    assert assets["packed_json_sha256"] == sha(prompt.PACK / "packed.scene.json")
    assert assets["changed_member"]["after"] == sha(prompt.PACK / "packed.scene")
    assert assets["package_file"] == row(prompt.PACK / "package",ARCHIVE)
    prompt.verify()
    PACKAGE.mkdir(parents=True,exist_ok=False)
    for old in base["core_files"]:
        rel = old["path"]
        dest = safe(PACKAGE,rel)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(safe(prompt.PACK / "package" if rel == ARCHIVE else GAME,rel),dest)
    after = [row(PACKAGE, r["path"]) for r in base["core_files"]]
    assert [r["path"] for r,o in zip(after,base["core_files"],strict=True) if r != o] == [ARCHIVE]
    assert archive_row(after) == assets["package_file"]
    write(CORE, {"status":"STAGED_OFFLINE","baseline_sha256":sha(BASE),"core_files":after,
                 "changed_paths":[ARCHIVE],"asset_assessment_sha256":sha(ASSETS),"prompt":prompt.target()})


def exercise():
    for case in ("round_trip","interrupted","unknown_drift"):
        root = ROOT / "deployment_fixtures" / case
        game, saves, recovery = (root / part for part in ("game","saves","recovery"))
        saves.mkdir(parents=True, exist_ok=False)
        (saves / "fixture.sav").write_bytes(b"protected save")
        dest = safe(game,ARCHIVE)
        dest.parent.mkdir(parents=True)
        shutil.copyfile(safe(GAME,ARCHIVE),dest)
        (dest.parent / "other.archive.xl").write_bytes(b"protected XL")
        plan = dict(before=[row(game,ARCHIVE)],after=[row(PACKAGE,ARCHIVE)],required_files=[],
                    archivexl_files=[],ifp_files=[],preferences=[],saved_files=snapshot(saves),
                    archive_environment=archive_environment(game))
        def interrupt():
            raise RuntimeError("fixture interrupt")
        try:
            install_archive(plan,game,saves,PACKAGE,recovery,lambda: None,interrupt if case == "interrupted" else None)
        except RuntimeError as error:
            if case != "interrupted" or str(error) != "fixture interrupt":
                raise
        else:
            assert case != "interrupted"
            if case == "unknown_drift":
                dest.write_bytes(b"independent edit")
                try:
                    recover_archive(plan,game,recovery / "old",lambda: None)
                except RuntimeError as error:
                    assert "Unknown archive drift" in str(error)
                else:
                    raise AssertionError("Unknown edit overwritten")
                assert dest.read_bytes() == b"independent edit"
            else:
                recover_archive(plan,game,recovery / "old",lambda: None)
        if case != "unknown_drift":
            verify_rows(game,plan["before"])
        verify_protected(plan,game,saves)
    write(FIXTURES, {"status":"PASS","cases":["install and rollback","interrupted installation","unknown archive drift"]})


def prepare():
    closed()
    base, core = check_base(), read(CORE)
    assert core["asset_assessment_sha256"] == sha(ASSETS) and read(FIXTURES)["status"] == "PASS"
    verify_rows(GAME,base["core_files"])
    verify_rows(PACKAGE,core["core_files"])
    plan = {"paths":[ARCHIVE],"game_root":str(GAME),"save_root":str(SAVES),"package_root":str(PACKAGE),
            "baseline_sha256":sha(BASE),"candidate_sha256":sha(CORE),"fixture_sha256":sha(FIXTURES),
            "before":base["core_files"],"after":core["core_files"],"preferences":[row(GAME,r["path"]) for r in base["preferences_at_install"]],
            "saved_files":snapshot(SAVES),"archive_environment":archive_environment(GAME)}
    for key in ("required_files","archivexl_files","ifp_files"):
        plan[key] = base[key]
    verify_protected(plan,GAME,SAVES)
    write(PLAN,plan)
    print("Prepared",sha(PLAN))


def live(action,digest):
    closed()
    assert sha(PLAN) == digest
    base, core, plan = check_base(), read(CORE), read(PLAN)
    assert plan["before"] == base["core_files"] and plan["after"] == core["core_files"]
    assert plan["paths"] == [ARCHIVE] and plan["candidate_sha256"] == sha(CORE)
    assert plan["baseline_sha256"] == sha(BASE) and plan["fixture_sha256"] == sha(FIXTURES)
    assert core["asset_assessment_sha256"] == sha(ASSETS)
    if action == "recover":
        assert read(RECOVERY / "prepared.json")["before"] == archive_row(plan["before"])
        plan["saved_files"] = snapshot(SAVES)
        plan["preferences"] = [row(GAME,r["path"]) for r in plan["preferences"]]
        verify_protected(plan,GAME,SAVES)
        verify_rows(GAME,[r for r in plan["before"] if r["path"] != ARCHIVE])
        recover_archive(plan,GAME,RECOVERY / "old",closed)
        verify_protected(plan,GAME,SAVES)
        return
    if action == "install":
        install_archive(plan,GAME,SAVES,PACKAGE,RECOVERY,closed)
    receipt = RECOVERY / "installed.json"
    assert read(receipt)["status"] == "INSTALLED_VERIFIED" and read(receipt)["changed_paths"] == [ARCHIVE]
    verify_rows(GAME,plan["after"])
    verify_rows(RECOVERY / "old",[archive_row(plan["before"])])
    verify_protected(plan,GAME,SAVES)
    if action == "install":
        write(ROOT / "installed_manifest.json",{**base,"schema":"PTFR_INSTALLED_MISTY_ROOF_CHAIR_PROMPT_V1",
              "recorded_utc":datetime.now(timezone.utc).isoformat(),"core_epoch":"MISTY_ROOF_CHAIR_PROMPT",
              "predecessor_manifest":str(BASE),"predecessor_manifest_sha256":sha(BASE),
              "core_manifest":str(CORE),"core_manifest_sha256":sha(CORE),"core_files":plan["after"],
              "verification":str(CORE),"verification_sha256":sha(CORE),"archive_sha256":archive_row(plan["after"])["sha256"],
              "asset_assessment":str(ASSETS),"asset_assessment_sha256":sha(ASSETS),"changed_paths":[ARCHIVE],
              "preferences_at_install":plan["preferences"],"installation_plan":str(PLAN),"installation_plan_sha256":digest,
              "installation_receipt":str(receipt),"installation_receipt_sha256":sha(receipt),"rollback_backup":str(RECOVERY / "old"),
              "save_files_preserved":len(plan["saved_files"]),"rollback_verified":True,"gameplay":"PENDING_USER_RETEST",
              "autosave_16_sha256":next((r["sha256"] for r in plan["saved_files"] if r["path"]=="AutoSave-16/sav.dat"),None)})
    print(read(receipt))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action",choices=["stage","fixtures","prepare","install","verify","recover"])
    parser.add_argument("--plan-sha")
    args = parser.parse_args()
    if args.action in ("stage","fixtures","prepare"):
        {"stage":stage,"fixtures":exercise,"prepare":prepare}[args.action]()
    else:
        live(args.action,args.plan_sha)
