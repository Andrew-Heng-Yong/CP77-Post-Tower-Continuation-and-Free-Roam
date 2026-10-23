"""Build or read-only check the guarded Misty/Zetatech shop exit probe."""
import argparse
import json
import time
import zipfile
from pathlib import Path

from package_phase2b_p2 import ROOT, GAME, MODS, ARCHIVE, ARCHIVE_SHA, sha, require_hash, check_baseline

MODULE = "PTFR_Phase2B_P3_ShopExitProbe"
SOURCE = ROOT / "diagnostics" / MODULE / "init.lua"
OUTPUT = ROOT / "build/Phase2B_P3_ShopExit"
PACKAGE = OUTPUT / (MODULE + ".zip")
MANIFEST = OUTPUT / "manifest.json"
INSTALLED = MODS / MODULE / "init.lua"
LOG = MODS / MODULE / "ptfr_p3_shop_exit.jsonl"


def build():
    baseline = check_baseline()
    require_hash(GAME / "archive/pc/mod" / ARCHIVE, ARCHIVE_SHA)
    payload = SOURCE.read_bytes()
    member = MODULE + "/init.lua"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(PACKAGE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        info = zipfile.ZipInfo(member, date_time=(2026, 9, 22, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, payload)
    with zipfile.ZipFile(PACKAGE) as archive:
        assert archive.namelist() == [member]
        assert archive.testzip() is None
        assert archive.read(member) == payload
    manifest = {
        "phase": "2B-P3 manual shop exit probe",
        "package": str(PACKAGE), "package_sha256": sha(PACKAGE),
        "entries": [{"path": member, "bytes": len(payload), "sha256": sha(SOURCE)}],
        "extract_destination": str(MODS),
        "required_existing_archive": {"path": str(GAME / "archive/pc/mod" / ARCHIVE), "sha256": ARCHIVE_SHA},
        "baseline_save_read_only": baseline,
        "static_targets": ["#q115_dvc_ripperdoc_room_door", "#q115_misty_door_back", "#q307_zetatech_door / legacy #q115_misty_door"],
        "install_note": "Move older P2 CET probe outside mods after preserving its trace; keep P0 archive.",
        "validation_scope": "Single-member ZIP; offline LuaJIT mocks. No game-side installation or runtime test by build.",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


def installed():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require_hash(INSTALLED, manifest["entries"][0]["sha256"])
    require_hash(GAME / "archive/pc/mod" / ARCHIVE, ARCHIVE_SHA)
    check_baseline()
    print("INSTALL CHECK PASS: P3 probe/P0 archive match and original ManualSave-11 hashes unchanged.")
    if (MODS / "PTFR_Phase2B_P2_RepairProbe").exists():
        print("NOTE: older P2 probe remains in CET mods. Preserve its trace and move it outside mods for an isolated P3 run.")


def trace_rows():
    rows=[]
    for number,line in enumerate(LOG.read_text(encoding="utf-8-sig").splitlines(),1):
        if not line.strip():
            continue
        row=json.loads(line)
        if row.get("probe")!="Phase2B-P3-shop-exit" or row.get("schema")!=1:
            raise ValueError(f"Unexpected probe/schema at trace line {number}")
        rows.append(row)
    return rows


def ready():
    installed()
    rows=trace_rows()
    if not rows:
        raise ValueError("No live P3 trace; start game and load the disposable save")
    if time.time()-LOG.stat().st_mtime>30:
        raise ValueError("P3 trace is stale; game is not actively logging")
    latest=rows[-1]
    run=latest.get("run_id")
    session=latest.get("session_id")
    current=[row for row in rows if row.get("run_id")==run and row.get("session_id")==session]
    run_rows=[row for row in rows if row.get("run_id")==run]
    if not any(row.get("event")=="INIT" and row.get("detail",{}).get("manual_only") is True
               and row.get("detail",{}).get("hooks_registered") is True for row in run_rows):
        raise ValueError("Latest run has no verified manual-only INIT/load hooks")
    if any(row.get("event")=="SHUTDOWN" for row in run_rows):
        raise ValueError("Latest run has shut down")
    life=[row.get("event") for row in current if row.get("event") in ("SESSION_ATTACHED","SESSION_DETACHED")]
    if not life or life[-1]!="SESSION_ATTACHED":
        raise ValueError("Latest load session is not attached")
    baselines=[row for row in current if row.get("event")=="EXIT_BASELINE"]
    if not baselines:
        raise ValueError("Aim at a shop exit and run InspectDoor() first")
    baseline=baselines[-1]
    state=baseline.get("state",{})
    target=state.get("exit_target",{})
    if state.get("guard",{}).get("passed") is not True:
        raise ValueError("Post-Tower guard failed in latest InspectDoor")
    if target.get("position_match_verified") is not True or target.get("slot") not in ("ROOM","BACK","FRONT"):
        raise ValueError("Looked-at object did not match a verified room/back/front shop exit")
    if baseline.get("read_errors"):
        raise ValueError("InspectDoor recorded unavailable API reads: " + ", ".join(baseline["read_errors"]))
    print(f"READY: looked-at {target['slot']} exit, entity {target['id']}; OpenDoor() may be requested once.")


def summarize():
    rows=trace_rows()
    if not rows:
        raise ValueError("No trace rows")
    selected=(rows[-1].get("run_id"),rows[-1].get("session_id"))
    current=[r for r in rows if (r.get("run_id"),r.get("session_id"))==selected]
    output={"run_id":selected[0],"session_id":selected[1],"doors":{},"errors":[]}
    for row in current:
        event=row.get("event")
        if event=="ERROR": output["errors"].append(row.get("detail"))
        if row.get("stage") not in ("ROOM","BACK","FRONT"):
            continue
        tag=row["stage"]
        door=output["doors"].setdefault(tag,{"requests":0,"readbacks":[]})
        if event=="EXIT_REQUESTED": door["requests"]+=1
        if event in ("EXIT_BASELINE","EXIT_BEFORE","EXIT_RETURNED","EXIT_STABILITY","EXIT_ALREADY_OPEN","EXIT_REJECTED"):
            target=row.get("state",{}).get("exit_target",{})
            door["readbacks"].append({"event":event,"seq":row.get("seq"),"delay_s":row.get("detail",{}).get("delay_s"),
                                      "id":target.get("id"),"open":target.get("device",{}).get("IsOpen"),
                                      "locked":target.get("device",{}).get("IsLocked"),
                                      "sealed":target.get("device",{}).get("IsSealed"),
                                      "guard":row.get("state",{}).get("guard",{}).get("passed"),
                                      "reason":row.get("detail",{}).get("reason")})
    print(json.dumps(output,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument("--check-installed",action="store_true")
    group.add_argument("--check-ready",action="store_true")
    group.add_argument("--analyze",action="store_true")
    args=parser.parse_args()
    try:
        if args.check_installed: installed()
        elif args.check_ready: ready()
        elif args.analyze: summarize()
        else: build()
        return 0
    except (OSError,ValueError,AssertionError,json.JSONDecodeError,zipfile.BadZipFile) as error:
        print("NOT READY: " + str(error))
        return 1


if __name__=="__main__":
    raise SystemExit(main())
