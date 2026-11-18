"""Verify the cooked pickup volumes against the camera position in the failed run."""

import base64
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "misty_rooftop_alignment_20261118_01"))
from placement import express_in, pose, read, root, sha

DETAIL = ROOT / "work/sector_details"
SOURCE = ROOT.parent / "misty_rooftop_alignment_20261118_01/work/pickup_ranges_01/providers.json"
DEPOTS = ("exterior_-7_4_0_2.streamingsector","exterior_-1_0_0_6.streamingsector")


def covers(setup, outline, point):
    # The cooked outline buffer can describe a different polygon than the editor defaults.
    data = base64.b64decode(outline["buffer"], validate=True)
    count, = struct.unpack_from("<I",data)
    assert count >= 3 and len(data) == 8 + 16*count
    corners = list(struct.iter_unpack("<4f", data[4:-4]))
    height, = struct.unpack_from("<f",data,len(data)-4)
    assert height > 0 and all(v[2:] == corners[0][2:] for v in corners)
    xy,z,_ = express_in(pose(setup["transform"]), (complex(*point[:2]),point[2],1))
    scale = setup["scale"]
    x,y,z = xy.real/scale["X"],xy.imag/scale["Y"],z/scale["Z"]
    inside = False
    for a,b in zip(corners,corners[1:]+corners[:1],strict=True):
        if (a[1]>y) != (b[1]>y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return inside and corners[0][2] <= z <= corners[0][2]+height


def check(game, compiled_dir):
    log = (game / "bin/x64/plugins/cyber_engine_tweaks/gamelog.log").read_text(encoding="utf-8",errors="replace")
    time = "[2026-11-18 12:49:20 "
    samples = [s for s in log.splitlines() if s.startswith(time)]
    assert any("[PTFR_MistyRoof] Requested removal" in s for s in samples)
    camera, = [s for s in samples if "[PTFR_LoadingLC3] Control diagnostic" in s]
    xyz = [float(i) for i in re.search(r"activeXYZ=([-\d.,]+)",camera)[1].split(",")]
    assert len(xyz) == 3 and "fault=0" in camera and "noMovement=false" in camera
    sector_inputs = read(ROOT / "work/inputs/providers.json")
    original = read(SOURCE)["providers"]
    seat = read(ROOT.parent / "misty_rooftop_seat_20261117_01/work/scene_01/manifest.json")
    points = {"recorded_camera":xyz, "chair":[seat["seat"]["position"][k] for k in "XYZ"],
              "landing_eye":[seat["anchor"]["position"][k] for k in "XYZ"]}
    # The panel pivot is at 54.42 m. Check the landing at the observed free-roam camera height.
    points["landing_eye"][2] = xyz[2]
    details = []
    for index,name in enumerate(DEPOTS):
        current = [r for r in sector_inputs["hits"] if r["depot"].endswith("\\"+name)]
        assert len(current) == 2 and {r["archive"] for r in current} == {"basegame_3_nightcity.archive","ep1_1_nightcity.archive"}
        official, = [r for r in current if r["archive"].startswith("ep1_")]
        old, = [r for r in original if r["depot"] == official["depot"]]
        assert old["sha256"] == official["sha256"] == sha(Path(official["raw"])) == sha(Path(old["raw"]))
        world = root(DETAIL / (name+".json"))
        instances = world["nodeData"]["Data"]
        assert (len(instances),len(world["nodes"])) == [(2992,214),(427,204)][index]
        members = world["variantNodes"][0 if index==0 else 2]
        expected = [(2940,207,"{T_Rooftop}",6,5,True)] if index==0 else [
            (412,189,"{T_Flight_Part_}2",6,10,False), (413,190,"{T_Trailer}",6,3,True),
            (414,191,"{T_Flight_Part_}1",5,3,True)]
        assert len(expected) == len(members)
        for s,(i,definition,label,priority,blend,inside) in zip(members,expected,strict=True):
            n = world["nodes"][definition]["Data"]
            assert s == instances[i] and s["globalNodeId"]["hash"] == "0" and int(s["nodeIdx"]) == definition
            assert n["debugName"]["$value"] == label and n["$type"] == "worldTriggerAreaNode"
            env, = (h["Data"] for h in n["notifiers"])
            assert env["$type"] == "worldEnvAreaNotifier" and env["priority"] == priority and env["blendTimeIn"] == blend
            if inside:
                assert env["blendTimeOut"] == blend
            hits = {k:covers(s,n["outline"]["Data"],point) for k,point in points.items()}
            assert all(v == inside for v in hits.values()), (label,hits)
            details.append({"area":label,"setup":i,"definition":definition,"contains":hits,
                            "active_settings":[h["Data"]["$type"] for h in env["params"]["areaParameters"] if h["Data"]["enable"]]})
        for alias in ("ptfr_misty_q307_trailer_environment","ptfr_misty_q307_flight_environment"):
            assert not any(alias in str(r).lower() for r in world["nodeRefs"])
    code = (compiled_dir / "compiled.script").read_text(encoding="utf-8-sig")
    def method(name):
        return code.split("func "+name+"(",1)[1].split("\n  }",1)[0]
    flight = method("BindFlight")
    assert "413, 190, 6, 3.0" in flight and "414, 191, 5, 3.0" in flight and "412," not in flight
    release = method("ReleaseRooftopExposure")
    for token in ("this.Completed(q)","GameplayReleased(game)","this.SafeStreet(p)","GetLocalPlayerControlledGameObject()",
                  ".IsReady()"):
        assert token in release, token
    assert re.findall(r"\.ToggleNode\(PTFR\.MistyViktorAuto\.MistyRoofExposure\.(\w+)\(\), false\)",release) == [
        "Address","TrailerAddress","FlightAddress"]
    assert "ToggleVariant" not in release and "SetFact" not in release
    assert "SetGlobalNodeID(" in method("BindAddress") and "ResolveNodeRef(" in method("BindAddress")
    assert code.count("this.ReleaseRooftopExposure(") == 1
    return {"game_log_time":time[1:].strip(), "points":points, "areas":details,
            "private_requests":3, "compiled_readback_sha256":sha(compiled_dir/"compiled.script")}
