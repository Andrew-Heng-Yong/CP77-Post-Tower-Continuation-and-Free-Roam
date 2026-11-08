"""Select existing community schedule workspots from the two native donors."""

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "phone_support_ph1"))
from model import read, sha

NATIVE = HERE / "native_01"
OWNER = r"towercontinued\heavy_hearts_hh1\support.questphase"
BLOCK = r"towercontinued\heavy_hearts_hh1\workspots.streamingblock"
COMMUNITIES = {
    "street": ("6618713760615573885", "15570256530843676615", "11225996957150521658"),
    "guard": ("4800043633707195335",),
}
WITNESSES = {
    "street": (
        ("6618713760615573885", "waitress_fluff", "Character.sts_ep1_06_waitress_fluff",
         71, "#sts_ep1_06_waitress_fluff_night_006", (-1601.3795166016, -2328.6069335938, 43.053596496582)),
        ("6618713760615573885", "chat_kurtz_001a", "Character.sts_ep1_06_nightlife_ma_savable",
         30, "#sts_ep1_06_ws_chat_kurtz_001a", (-1610.9465332031, -2330.8776855469, 43.054420471191)),
    ),
    "guard": (
        ("4800043633707195335", "enemy_019", "Character.sts_ep1_06_enemy_rifle_suit_ma_outside_sts",
         42, "#sts_ep1_06_enemy_019_night", (-1612.4591064453, -2353.6320800781, 44.049995422363)),
    ),
}
COMMON = {
    "PostTowerFreeRoamActive": 1, "PTFRP0_DR13": 1, "q307_active": 0, "q307_done": 1,
    "q307_finished": 1, "q307_2079": 1, "q307_main_game_killed": 1, "q307_ep1_killed": 1,
    "q115_point_of_no_return": 0, "q305_johnny_scene_active": 0, "PTFRBASE_Suspended": 0,
    "PTFRPA2_Finished": 1, "PTFRPA3_CoverReleased": 1, "ep1_side_content": 1,
    "sts_ep1_06_close_club": 0, "sts_ep1_06_despawn_npcs_on_combat": 0,
    "sts_ep1_06_ground_floor_combat": 0, "sts_ep1_06_upper_floor_combat": 0,
}


def write(path, data):
    with path.open("x", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")


def plan_sector(name, native, communities, capture):
    assert native["persistent_nodes"] == 0 and not any(native["variant_nodes"])
    base_limit = native["variants"][1] if len(native["variants"]) > 1 else len(native["nodes"])
    nodes = {row["index"]: row["payload"] for row in native["nodes"]}
    by_ref = defaultdict(set)
    for p in native["placements"]:
        if nodes[p["node"]]["$type"] == "worldAISpotNode":
            by_ref[p["ref"]].add(p["node"])
            for alias in p["ref"].split(";"):
                by_ref[alias.rsplit("/", 1)[-1]].add(p["node"])

    bindings = []
    unmapped = set()
    for cid in COMMUNITIES[name]:
        for row in communities[cid]["registry"]["template"]["Data"]["entries"]:
            entry = row["Data"]
            refs = {r["$value"] for phase in entry["phases"] for period in phase["Data"]["timePeriods"]
                    for r in period["spotNodeRefs"]}
            for ref in sorted(refs):
                hits = by_ref.get(ref) or by_ref.get(ref.removeprefix("~/../"))
                if not hits:
                    unmapped.add(ref)
                    continue
                assert len(hits) == 1, (name, ref, hits)
                bindings.append({"community": cid, "entry": entry["entryName"]["$value"],
                                 "record": entry["characterRecordId"]["$value"], "ref": ref, "node": next(iter(hits))})
    selected = {row["node"] for row in bindings}
    masters = {}
    held = {}
    pending = sorted(selected)
    for i in pending:
        node = nodes[i]
        spot = (node.get("spot") or {}).get("Data")
        if not spot or node["lookAtTarget"]["$value"] != "0":
            held[i] = "Missing standalone action spot or external look-at dependency"
            continue
        ref = spot["masterNodeRef"]["$value"]
        if ref == "0":
            continue
        hits = by_ref.get(ref.removeprefix("~/../"), set())
        assert len(hits) == 1, (name, i, ref, hits)
        master = next(iter(hits))
        masters[i] = master
        if master not in selected:
            selected.add(master)
            pending.append(master)
    assert not set(masters.values()).intersection(held)
    keep = sorted(selected - held.keys())
    assert keep and max(keep) < base_limit, "A selected spot belongs to a conditional prefab variant"
    workspots = set()
    for i in keep:
        node = nodes[i]
        spot = node["spot"]["Data"]
        assert spot["$type"] == "AIActionSpot"
        assert node["lookAtTarget"]["$value"] == "0"
        workspots.add(spot["resource"]["DepotPath"]["$value"])

    observed = []
    for cid, entry, record, node, ref, position in WITNESSES[name]:
        assert {"community": cid, "entry": entry, "record": record, "ref": ref, "node": node} in bindings
        match = [p for p in native["placements"] if p["node"] == node and p["ref"].endswith("/" + ref)]
        assert len(match) == 1
        distance = math.dist(position, match[0]["xyz"])
        assert distance < 0.001
        observed.append({"entry": entry, "record": record, "node": node, "distance_m": distance})

    donor = next(row for row in capture["providers"] if row["name"] == name)
    return {
        "name": name, "donor": donor["depot"], "sha256": capture["pins"][name],
        "private_ref": "$/03_night_city/towercontinued/heavy_hearts_hh1/" + name,
        "keep": keep, "bindings": bindings, "unmapped_refs": sorted(unmapped), "held": held, "masters": masters,
        "communities": [communities[cid]["ref"] for cid in COMMUNITIES[name]],
        "workspots": sorted(workspots), "observed": observed, "source_nodes": len(nodes),
    }


if __name__ == "__main__":
    assert __debug__
    capture = read(NATIVE / "capture.json")
    communities = {row["hash"]: row for row in capture["communities"]}
    assert len(communities) == len(capture["communities"])
    rows = [plan_sector(name, read(NATIVE / (name + ".json")), communities, capture) for name in COMMUNITIES]
    write(HERE / "plan.json", {
        "capture_sha256": sha(NATIVE / "capture.json"), "sectors": rows, "guard": COMMON,
        "owner": OWNER, "block": BLOCK,
    })
    print("Selected native workspots:", {r["name"]: len(r["keep"]) for r in rows})
