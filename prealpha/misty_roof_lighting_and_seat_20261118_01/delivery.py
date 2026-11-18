"""Qualify and install the two-file Misty rooftop update against its exact predecessor."""

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALIGN = ROOT.parent / "misty_rooftop_alignment_20261118_01"
SEAT = ROOT.parent / "misty_rooftop_seat_20261117_01"
sys.path[:0] = [str(ALIGN), str(SEAT)]
import lighting
import placement
import deploy as tx
from build import ARCHIVE, EXE, EXE_SHA, GAME, REDS, read, row, safe, sha, verify_rows, write

BASE = placement.BASE
CHAIR = ALIGN / "candidate_01/core_manifest.json"
CHAIR_SHA = "12DB5E188CA1A4A6F7BE403A9580A910432F04E3CA906C781032394776EDAB10"
PACKAGE = ROOT / "candidate_01/package"
CORE = PACKAGE.parent / "core_manifest.json"
COMPILE = ROOT / "compile_02/assessment.json"
ASSETS = ALIGN / "work/pack_01/readback.json"
CHECK = ROOT / "verification.json"
FIXTURES = ROOT / "fixture_results.json"
PLAN = ROOT / "install_plan.json"
RECOVERY = ROOT / "recovery"
MANIFEST = ROOT / "installed_manifest.json"
CHANGED = (ARCHIVE, REDS)
# The reused install/recover routines consume this allowlist and explicit root arguments.
tx.CHANGED = CHANGED


def predecessor():
    assert sha(BASE) == placement.BASE_HASH and sha(CHAIR) == CHAIR_SHA
    base = read(BASE)
    assert len(base["core_files"]) == 51 and base["game_root"] == str(GAME) and base["save_root"] == str(tx.SAVES)
    assert sha(safe(GAME, EXE)) == EXE_SHA
    previous_plan = Path(base["installation_plan"])
    assert sha(previous_plan) == base["installation_plan_sha256"]
    assert tx.archive_environment(GAME) == read(previous_plan)["archive_environment"]
    return base


def stage():
    base, staged, compiled = predecessor(), read(CHAIR), read(COMPILE)
    verify_rows(GAME, base["core_files"] + base["required_files"] + base["ifp_files"] + base["archivexl_files"])
    assert staged["baseline_sha256"] == placement.BASE_HASH and staged["changed_paths"] == [ARCHIVE]
    assert staged["asset_assessment_sha256"] == sha(ASSETS)
    assert sha(placement.ASSETS / "packed.scene.json") == read(ASSETS)["packed_json_sha256"]
    verify_rows(CHAIR.parent / "package", staged["core_files"])
    placement.verify_packed()
    lighting.main()
    sector = ALIGN / "work/lighting_01/ep1_1_nightcity.archive/exterior_-7_4_0_2.streamingsector"
    assert sha(sector) == "8C0A865367AB4D13672F94A07195B617C766EB68AEA116A48DF1993CACD238B8"
    data = placement.root(Path(str(sector) + ".json"))
    instances = data["nodeData"]["Data"]
    assert len(instances) == 2992 and len(data["nodes"]) == 214
    matches = [i for i, s in enumerate(instances) if int(s["nodeIdx"]) == 207]
    assert matches == [2940] and instances[2940]["globalNodeId"]["hash"] == "0"
    assert data["nodes"][135]["Data"]["debugName"]["$value"] == "{T_Portal}"
    assert int(instances[887]["nodeIdx"]) == 135
    assert not any("ptfr_misty_q307_rooftop_exposure" in str(r).lower() for r in data["nodeRefs"])
    proof_code = COMPILE.parent / "compiled.script"
    assert compiled["status"] == "PASS" and compiled["changed_sources"] == [REDS]
    assert compiled["compiled_sha256"] == sha(COMPILE.parent / "cache/compiled.redscripts")
    tx.compare_sources(compiled, "source_before")
    code = proof_code.read_text(encoding="utf-8-sig")
    service = code.split("class PTFR.MistyViktorAuto.MistyRoofExposure extends", 1)[1].split("\n}", 1)[0]
    for token in ('n"Resource/PostLoad"', "exterior_-7_4_0_2.streamingsector", "GetNodeSetup(2940)",
                  "GetNode(207)", "worldEnvAreaNotifier", "IsNodeRefDefined(", ".SetNodeRef("):
        assert token in service, token
    assert "ToggleNode(" not in service and "ToggleVariant(" not in service
    release = code.split("func ReleaseRooftopExposure(", 1)[1].split("\n  }", 1)[0]
    for token in ("this.Completed(q)", "GameplayReleased(game)", "this.SafeStreet(p)", ".IsReady()",
                  "GetLocalPlayerControlledGameObject()", "ToggleNode(PTFR.MistyViktorAuto.MistyRoofExposure.Address(), false)"):
        assert token in release, token
    assert "SetFact(" not in release and "ToggleVariant(" not in release
    assert code.count("this.ReleaseRooftopExposure(") == 1
    verify_rows(ROOT / "source", [{"path": "PTFR_MistyViktorAuto.reds",
        "bytes": (ROOT / "source/PTFR_MistyViktorAuto.reds").stat().st_size, "sha256": compiled["source_after"][REDS]}])
    assert not any("ptfr_misty_q307_rooftop_exposure" in path.read_text(encoding="utf-8-sig", errors="replace").lower()
                   for path in tx.compiler_sources().values())
    PACKAGE.mkdir(parents=True, exist_ok=False)
    for item in staged["core_files"]:
        rel = item["path"]
        dest = safe(PACKAGE, rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        donor = ROOT / "source/PTFR_MistyViktorAuto.reds" if rel == REDS else safe(CHAIR.parent / "package", rel)
        shutil.copyfile(donor, dest)
    rows = [row(PACKAGE, r["path"]) for r in base["core_files"]]
    assert {r["path"] for old, r in zip(base["core_files"], rows, strict=True) if r != old} == set(CHANGED)
    assert next(r for r in rows if r["path"] == ARCHIVE) == read(ASSETS)["package_file"]
    assert next(r["sha256"] for r in rows if r["path"] == REDS) == compiled["source_after"][REDS]
    write(CHECK, {"status": "PASS", "compiled_readback_sha256": sha(proof_code),
          "native_sector_sha256": sha(sector), "volume": [2940,207], "ordinary_portal": [887,135],
          "seat_readback_sha256": sha(ASSETS), "archive_members": 1751, "unchanged_archive_members": 1750,
          "registered_sources": compiled["registered_sources"], "gameplay": "PENDING"})
    write(CORE, {"status": "STAGED_OFFLINE", "core_files": rows, "changed_paths": list(CHANGED),
          "baseline_sha256": sha(BASE), "compile_assessment_sha256": sha(COMPILE), "verification_sha256": sha(CHECK)})


def fixtures():
    results = []
    for label, stop in (("install and rollback", None), ("interrupt after archive", 1),
                        ("interrupt after script", 2), ("refuse unknown drift", None)):
        root = ROOT / "deployment_fixtures" / label
        game, saves, recovery = (root / p for p in ("game", "saves", "recovery"))
        saves.mkdir(parents=True, exist_ok=False)
        (saves / "fixture.sav").write_bytes(b"protected save")
        for rel in CHANGED:
            dest = safe(game, rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(safe(GAME, rel), dest)
        (game / "archive/pc/mod/other.xl").write_bytes(b"protected configuration")
        plan = {"before": [row(game,p) for p in CHANGED], "after": [row(PACKAGE,p) for p in CHANGED],
                "saved_files": tx.snapshot(saves), "required_files": [], "ifp_files": [], "archivexl_files": [],
                "preferences": [], "archive_environment": tx.archive_environment(game)}
        try:
            tx.install(plan, game, saves, PACKAGE, recovery, lambda: None, fail_after=stop)
        except RuntimeError as err:
            if not stop or str(err) != f"Fixture interruption after replacement {stop}":
                raise
        else:
            assert stop is None
            if label == "refuse unknown drift":
                safe(game, REDS).write_bytes(b"unknown")
                try:
                    tx.recover(plan, game, saves, recovery, lambda: None)
                except RuntimeError as err:
                    assert "Unknown target drift" in str(err)
                else:
                    raise AssertionError("Rollback overwrote unknown drift")
                assert safe(game, REDS).read_bytes() == b"unknown"
                verify_rows(game, [plan["after"][0]])
            else:
                tx.recover(plan, game, saves, recovery, lambda: None)
        if label != "refuse unknown drift":
            verify_rows(game, plan["before"])
        tx.verify_protected(plan, game, saves)
        results.append(label)
    write(FIXTURES, {"status":"PASS", "cases":results})


def prepare():
    tx.closed()
    base, core = predecessor(), read(CORE)
    assert read(FIXTURES)["status"] == "PASS" and core["verification_sha256"] == sha(CHECK)
    assert core["baseline_sha256"] == sha(BASE) and core["compile_assessment_sha256"] == sha(COMPILE)
    verify_rows(GAME, base["core_files"])
    verify_rows(PACKAGE, core["core_files"])
    tx.compare_sources(read(COMPILE), "source_before")
    plan = {"paths": list(CHANGED), "game_root": str(GAME), "save_root": str(tx.SAVES), "package_root": str(PACKAGE),
            "baseline_sha256": sha(BASE), "candidate_sha256": sha(CORE), "fixture_sha256": sha(FIXTURES),
            "before": base["core_files"], "after": core["core_files"], "required_files": base["required_files"],
            "archivexl_files": base["archivexl_files"], "ifp_files": base["ifp_files"],
            "preferences": [row(GAME,r["path"]) for r in base["preferences_at_install"]],
            "saved_files": tx.snapshot(tx.SAVES), "archive_environment": tx.archive_environment(GAME)}
    tx.verify_protected(plan, GAME, tx.SAVES)
    write(PLAN, plan)
    print("Prepared verified plan", sha(PLAN))


def live(action, digest):
    tx.closed()
    assert sha(PLAN) == digest
    plan, base, core = read(PLAN), predecessor(), read(CORE)
    assert plan["candidate_sha256"] == sha(CORE) and plan["before"] == base["core_files"] and plan["after"] == core["core_files"]
    assert plan["paths"] == list(CHANGED) and plan["fixture_sha256"] == sha(FIXTURES)
    assert plan["baseline_sha256"] == sha(BASE) and core["verification_sha256"] == sha(CHECK)
    assert core["compile_assessment_sha256"] == sha(COMPILE)
    prove_scripts = lambda: tx.compare_sources(read(COMPILE), "source_after")
    if action == "recover":
        assert read(RECOVERY / "prepared.json")["paths"] == list(CHANGED)
        plan["saved_files"] = tx.snapshot(tx.SAVES)
        plan["preferences"] = [row(GAME,r["path"]) for r in plan["preferences"]]
        tx.verify_protected(plan, GAME, tx.SAVES)
        tx.recover(plan, GAME, tx.SAVES, RECOVERY, tx.closed)
        return
    if action == "install":
        tx.compare_sources(read(COMPILE), "source_before")
        tx.install(plan, GAME, tx.SAVES, PACKAGE, RECOVERY, tx.closed, verify_after=prove_scripts)
    receipt = RECOVERY / "installed.json"
    assert read(receipt)["status"] == "INSTALLED_VERIFIED" and read(receipt)["changed_paths"] == list(CHANGED)
    verify_rows(GAME, plan["after"])
    verify_rows(RECOVERY / "old", [r for r in plan["before"] if r["path"] in CHANGED])
    tx.verify_protected(plan, GAME, tx.SAVES)
    prove_scripts()
    if action == "install":
        write(MANIFEST, {**base, "schema":"PTFR_INSTALLED_MISTY_ROOF_LIGHTING_AND_SEAT_V1",
              "core_epoch":"MISTY_ROOF_LIGHTING_AND_SEAT", "recorded_utc":datetime.now(timezone.utc).isoformat(),
              "predecessor_manifest":str(BASE), "predecessor_manifest_sha256":sha(BASE),
              "core_manifest":str(CORE), "core_manifest_sha256":sha(CORE), "core_files":plan["after"],
              "archive_sha256":row(GAME, ARCHIVE)["sha256"], "changed_paths":list(CHANGED),
              "compile_assessment":str(COMPILE), "compile_assessment_sha256":sha(COMPILE),
              "asset_assessment":str(ASSETS), "asset_assessment_sha256":sha(ASSETS),
              "verification":str(CHECK), "verification_sha256":sha(CHECK),
              "preferences_at_install":plan["preferences"], "installation_plan":str(PLAN),
              "installation_plan_sha256":digest, "installation_receipt":str(receipt),
              "installation_receipt_sha256":sha(receipt), "rollback_backup":str(RECOVERY / "old"),
              "rollback_verified":True, "save_files_preserved":len(plan["saved_files"]),
              "autosave_16_sha256":next((r["sha256"] for r in plan["saved_files"] if r["path"]=="AutoSave-16/sav.dat"),None),
              "gameplay":"PENDING_USER_RETEST"})
    print(read(receipt))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["stage","fixtures","prepare","install","verify","recover"])
    parser.add_argument("--plan-sha")
    args = parser.parse_args()
    if args.action in ("stage","fixtures","prepare"):
        {"stage":stage, "fixtures":fixtures, "prepare":prepare}[args.action]()
    else:
        live(args.action, args.plan_sha)
