"""Check the compiled rooftop request against the native pickup and the restored-save path."""

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ALIGN = ROOT.parent / "misty_rooftop_alignment_20261118_01"
PREVIOUS = ROOT.parent / "misty_roof_light_retest_20261118_01"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def driver(bundle):
    code = bundle.read_text(encoding="utf-8-sig")
    marker = "class PTFR.MistyViktorAuto.MistyViktorAuto extends ScriptableSystem {"
    assert code.count(marker) == 1
    return code.split(marker, 1)[1].split("\n}", 1)[0]


def methods(code):
    return dict(re.findall(r"\bfunc (\w+)(\([^\n]*\)\s*[^{}]*\{.*?\n  })", code, re.S))


def check(game, compiled_dir):
    traces = {}
    for name, expected in (
        ("saved_lighting_trace.json", "CB6475AAED8715A958BB1170CA4F86501C13AA5F9EEDF2835CB90A0B5096880A"),
        ("saved_ending_trace.json", "EB99FD16F9536F8DC5F11515345DCC5D79DEF6C33931327351197700B9991C62"),
    ):
        path = ALIGN / name
        assert digest(path) == expected
        trace = json.loads(path.read_bytes())
        assert trace["defaults"]["Q307_AV"] == 0 and trace["pickup_writes"] == [[2022, "Q307_AV", 1], [3050, "Q307_AV", 1]]
        assert trace["q307_cleanup_explicit_roof_variant_writes"] == []
        traces.update({s["slot"]: s["saved_roof_states"]["Q307_AV"] for s in trace["samples"]})
    assert traces["AutoSave-10"] == traces["ManualSave-32"] == traces["EndGameSave-124"] == 1
    assert traces["ManualSave-26"] is None
    owner = trace["owner"]
    api = (game / "red4ext/plugins/Codeware/Scripts/Codeware.Global.reds").read_text(encoding="utf-8-sig")
    assert "public native func ToggleVariant(ref: NodeRef, name: CName, state: Bool)" in api

    image = compiled_dir / "compiled.script"
    driver_now = driver(image)
    old = methods(driver(PREVIOUS / "compile_01/compiled.script"))
    new = methods(driver_now)
    assert new.keys() == old.keys() and {"Completed", "SafeStreet", "Poll", "RefreshRooftopSeat"} <= new.keys()
    assert {n for n in old if old[n] != new[n]} == {"ReleaseRooftopExposure", "OnAttach", "OnRestored"}
    for hook in ("OnAttach", "OnRestored"):
        assert "this.rooftopPickupReleaseRequested = false;" in new[hook]
    release = new["ReleaseRooftopExposure"]
    guards = ("this.rooftopPickupReleaseRequested", "!IsDefined(p)", "> 6400.0", "!this.Completed(q)",
              "GameplayReleased(game)", "!this.SafeStreet(p)", "p.IsDead()", "GetLocalPlayerControlledGameObject() != p", ".IsReady()")
    call = release.index(".ToggleVariant(")
    assert all(release.index(g) < call for g in guards)
    assert release.count(owner) == 1 and release.index(owner) < call
    assert re.search(r'\.ToggleVariant\(roof\$local\$\d+, n"Q307_AV", false\);', release)
    assert release.index("this.rooftopPickupReleaseRequested = true;") > call
    assert driver_now.count(".ToggleVariant(") == 1 and new["Poll"].count(".ReleaseRooftopExposure(") == 1
    assert ".ToggleNode(" not in release and "SetFact" not in release

    records = json.loads((ALIGN / "work/pickup_ranges_01/providers.json").read_bytes())["providers"]
    types = Counter()
    roof = (-1541.07, 1201.90, 57.0)
    distances = {}
    for record in records:
        path = Path(record["json"])
        assert digest(path) == record["json_sha256"] and digest(Path(record["raw"])) == record["sha256"]
        for member in json.loads(path.read_bytes()):
            kind = member["type"]
            types[kind] += 1
            if kind in {"worldCookedStaticMeshNode", "worldCookedCollisionNode"}:
                sector = json.loads((PREVIOUS / "work/sector_details" / path.name).read_bytes())["Data"]["RootChunk"]
                setup, = [s for s in sector["variantNodes"][member["range"] - 1] if int(s["nodeIdx"]) == member["node"]]
                position = setup["transform"]["position"]
                distances[kind] = round(math.dist(roof, tuple(position[k] for k in "XYZ")), 2)
    assert len(records) == 7 and sum(types.values()) == 13 and min(distances.values()) > 630
    positions = json.loads((PREVIOUS / "verification.json").read_bytes())["points"]
    assert all(math.dist(roof, p) < 80 for p in positions.values())
    return {"owner": owner, "variant": "Q307_AV", "requested_state": False, "approach_radius_m": 80,
            "saved_states": traces, "pickup_members_by_type": dict(types), "geometry_pivot_distances_m": distances,
            "readback_sha256": digest(image), "user_CET_result": "Building detail returned",
            "automated_gameplay": "PENDING"}
