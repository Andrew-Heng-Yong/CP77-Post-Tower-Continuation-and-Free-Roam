"""Deploy the verified NCART and Welcome to Paradise successor with file recovery."""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECTS = ROOT.parent
sys.path.insert(0, str(PROJECTS / "misty_rooftop_seat_20261117_01"))
import deploy as tx
import fixtures
import build
from build import ARCHIVE, XL, EXE, EXE_SHA, GAME, read, row, safe, sha, verify_rows, write

STAGE = PROJECTS / "ncart_post_tower_20261118_01"
CANDIDATE = STAGE / "candidate_01"
PACKAGE = CANDIDATE / "package"
BASE = PROJECTS / "misty_roof_pickup_release_20261118_01/installed_manifest.json"
CORE = CANDIDATE / "core_manifest.json"
PROOF = CANDIDATE / "verification.json"
ASSETS = STAGE / "work/pack_01/readback.json"
PROVIDERS = STAGE / "work/sources_01/providers.json"
COMPILE = PROJECTS / "welcome_to_paradise_20261118_01/work/compile_01/assessment.json"
CURRENT_COMPILE = ROOT / "compile_01/assessment.json"
TOUR = PROJECTS / "welcome_to_paradise_cut_20261118_01/candidate_01"
PLAN = ROOT / "install_plan.json"
RECOVERY = ROOT / "recovery"
MANIFEST = ROOT / "installed_manifest.json"
FIXTURES = ROOT / "fixture_results.json"
CHANGED = (ARCHIVE, XL, "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds")
tx.CHANGED = CHANGED


def inputs():
    assert sha(BASE) == "CED6C03DE5B242E5B3F934BCE79160FE60DEDBACADF673951F4258D2A113B404"
    assert sha(CORE) == "92D48E395C3877787CB1A057395CFA4F83BF3C6A20B18E8768159A70CF6F319B"
    assert sha(PROOF) == "E9A28E30BB31E8284FCA289BEF9A7F638DD1888B04227C58F7A8924DA6D8A258"
    base, core, proof, compiler = read(BASE), read(CORE), read(PROOF), read(COMPILE)
    assert (base["game_root"], base["save_root"]) == (str(GAME), str(tx.SAVES))
    assert sha(safe(GAME, EXE)) == EXE_SHA
    assert core["baseline_sha256"] == sha(BASE) and proof["core_sha256"] == sha(CORE)
    assert core["predecessor_candidate_sha256"] == sha(TOUR/"core_manifest.json") == read(TOUR/"verification.json")["candidate_sha256"]
    assert core["asset_assessment_sha256"] == sha(ASSETS)
    assert core["compile_assessment_sha256"] == sha(COMPILE)
    assert compiler["status"] == "PASS" and compiler["changed_sources"] == [CHANGED[2]]
    assert sha(COMPILE.parent/"cache/compiled.redscripts") == compiler["compiled_sha256"]
    before, after = base["core_files"], core["core_files"]
    assert len(before) == len(after) == 51 and [x["path"] for x in before] == [x["path"] for x in after]
    assert list(CHANGED) == core["changed_paths"] == [a["path"] for a,b in zip(after,before) if a!=b]
    assert read(ASSETS)["archive_sha256"] == next(f["sha256"] for f in after if f["path"] == ARCHIVE)
    verify_rows(PACKAGE, after)
    return base, core


def prepare():
    tx.closed()
    base, core = inputs()
    verify_rows(GAME, base["core_files"])
    previous = Path(base["installation_plan"])
    assert sha(previous) == base["installation_plan_sha256"]
    env = tx.archive_environment(GAME)
    assert env == read(previous)["archive_environment"]
    tx.verify_providers(read(PROVIDERS), env, row(GAME, ARCHIVE))
    build.REDS = CHANGED[2]
    current = build.compile_overlay(safe(PACKAGE, CHANGED[2]), CURRENT_COMPILE.parent)
    assert all(current[k] == read(COMPILE)[k] for k in ("source_after", "source_before", "registered_sources"))
    fixtures.ROOT, fixtures.DEPLOYMENT, fixtures.CHANGED, fixtures.PACKAGE = ROOT, ROOT, CHANGED, PACKAGE
    fixtures.main()
    plan = dict(paths=list(CHANGED), before=base["core_files"], after=core["core_files"],
                baseline_sha256=sha(BASE), candidate_sha256=sha(CORE), fixture_sha256=sha(FIXTURES), compile_sha256=sha(CURRENT_COMPILE),
                game_root=str(GAME), save_root=str(tx.SAVES), package_root=str(PACKAGE),
                required_files=base["required_files"], archivexl_files=base["archivexl_files"],
                ifp_files=base["ifp_files"], preferences=[row(GAME,r["path"]) for r in base["preferences_at_install"]],
                saved_files=tx.snapshot(tx.SAVES), archive_environment=env)
    tx.verify_protected(plan, GAME, tx.SAVES)
    write(PLAN, plan)
    print("Plan", sha(PLAN), "save files", len(plan["saved_files"]))


def live(action, digest):
    tx.closed()
    assert digest == sha(PLAN)
    base, core = inputs()
    plan = read(PLAN)
    assert plan["paths"] == list(CHANGED) and plan["candidate_sha256"] == sha(CORE) and plan["baseline_sha256"] == sha(BASE)
    assert plan["before"] == base["core_files"] and plan["after"] == core["core_files"]
    assert plan["fixture_sha256"] == sha(FIXTURES) and read(FIXTURES)["status"] == "PASS"
    assert plan["compile_sha256"] == sha(CURRENT_COMPILE)
    if action == "recover":
        assert read(RECOVERY/"prepared.json")["paths"] == list(CHANGED)
        plan["saved_files"] = tx.snapshot(tx.SAVES)
        plan["preferences"] = [row(GAME,r["path"]) for r in plan["preferences"]]
        tx.verify_protected(plan,GAME,tx.SAVES)
        tx.recover(plan,GAME,tx.SAVES,RECOVERY,tx.closed)
        return
    def scripts():
        tx.compare_sources(read(CURRENT_COMPILE), "source_after")
    if action == "install":
        assert not MANIFEST.exists()
        tx.compare_sources(read(CURRENT_COMPILE), "source_before")
        tx.install(plan,GAME,tx.SAVES,PACKAGE,RECOVERY,tx.closed,verify_after=scripts)
    receipt_file = RECOVERY/"installed.json"
    receipt = read(receipt_file)
    assert receipt["status"] == "INSTALLED_VERIFIED" and receipt["changed_paths"] == list(CHANGED)
    verify_rows(GAME, plan["after"])
    verify_rows(RECOVERY/"old", [r for r in plan["before"] if r["path"] in CHANGED])
    tx.verify_protected(plan,GAME,tx.SAVES)
    scripts()
    if not MANIFEST.exists():
        write(MANIFEST, dict(base, schema="PTFR_INSTALLED_NCART_PARADISE_V1", core_epoch="NCART_PARADISE",
              recorded_utc=datetime.now(timezone.utc).isoformat(), core_files=plan["after"], changed_paths=list(CHANGED),
              archive_sha256=row(GAME,ARCHIVE)["sha256"], predecessor_manifest=str(BASE),predecessor_manifest_sha256=sha(BASE),
              core_manifest=str(CORE),core_manifest_sha256=sha(CORE),compile_assessment=str(CURRENT_COMPILE),compile_assessment_sha256=sha(CURRENT_COMPILE),
              asset_assessment=str(ASSETS),asset_assessment_sha256=sha(ASSETS),verification=str(PROOF),verification_sha256=sha(PROOF),
              installation_plan=str(PLAN),installation_plan_sha256=digest,installation_receipt=str(receipt_file),
              installation_receipt_sha256=sha(receipt_file),rollback_backup=str(RECOVERY/"old"),rollback_verified=True,
              preferences_at_install=plan["preferences"],save_files_preserved=receipt["save_files_preserved"],
              autosave_16_sha256=next((r["sha256"] for r in plan["saved_files"] if r["path"]=="AutoSave-16/sav.dat"),None),
              gameplay="PENDING_USER_RETEST"))
    assert read(MANIFEST)["installation_receipt_sha256"] == sha(receipt_file)
    print("Verified installation and rollback copies", receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare","install","verify","recover"))
    parser.add_argument("--plan-sha")
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        live(args.action,args.plan_sha)
