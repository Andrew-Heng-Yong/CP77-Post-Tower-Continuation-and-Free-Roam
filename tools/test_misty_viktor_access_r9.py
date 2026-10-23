"""R9 door-state and single-clerk restoration checks; no game writes."""
import hashlib
import json
from pathlib import Path

from audit_world_interactions import walk
from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_optin import evaluate
from test_misty_viktor_repair_r6 import evaluate_loading

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/misty_viktor_world"
OLD = ROOT / "build/MistyViktorDetailsR7/source"
NEW = ROOT / "build/MistyViktorAccessR9/source"
PHASE = r"towercontinued\misty_viktor_world\shell_optin.questphase"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def payload(node, table, key):
    return canonical(node[key], table)


def main():
    m = read(BASE / "access_r9_manifest.json")
    oldm = read(BASE / "details_r7_manifest.json")
    oldtests = read(BASE / "details_r7_tests.json")
    assert oldtests["status"] == "PASS_R7_OFFLINE_NOT_LIVE"
    assert oldtests["archive_sha256"] == oldm["sha256"] and oldtests["xl_sha256"] == oldm["xl_sha256"]
    assert m["status"] == "BUILT_R9_ACCESS_CLERK_NOT_INSTALLED_OR_LIVE"
    assert m["resources"] == oldm["resources"] and m["guards"] == oldm["guards"]
    assert m["compatibility_revision"] == 7 and m["access_revision"] == 9
    assert m["original_world_resource_overrides"] == m["native_scene_starts"] == m["story_fact_writes"] == 0
    assert sha(Path(m["archive"])) == m["sha256"]
    assert sha(Path(m["archive"] + ".xl")) == m["xl_sha256"]
    assert (Path(m["archive"] + ".xl")).read_bytes() == (Path(oldm["archive"] + ".xl")).read_bytes()
    changed = {d for d in m["resources"] if (OLD / d).read_bytes() != (NEW / d).read_bytes()}
    assert changed == {PHASE}

    old = read(BASE / "details_r7_phase.json")["Data"]["RootChunk"]
    new = read(BASE / "access_r9_phase.json")["Data"]["RootChunk"]
    oh, nh = handles(old), handles(new)
    on, nn = nodes(old), nodes(new)
    assert set(on) == set(range(30)) and set(nn) == set(range(39))
    assert old["phasePrefabs"] == new["phasePrefabs"] == []
    for obj in walk(new):
        if "HandleRefId" in obj:
            assert str(obj["HandleRefId"]) in nh
    for index in range(30):
        for key in ("type", "condition"):
            if key in on[index]:
                if index == 5 and key == "condition":
                    continue
                assert payload(nn[index], nh, key) == payload(on[index], oh, key), ("R7 payload changed", index, key)
    assert quest_edges(new)[0] == {(a, s, b, "In") for a, s, b in m["edges"]}

    doors = {}
    for index in (11, 30, 31, 32):
        p = payload(nn[index], nh, "type")["params"]
        assert len(p) == 1 and p[0]["deviceControllerClass"]["$value"] == "DoorControllerPS"
        assert p[0]["actionProperties"] == []
        doors[index] = (p[0]["objectRef"]["$value"], p[0]["deviceAction"]["$value"])
    assert doors == {
        11: (m["rear_door"], "ForceUnlock"),
        30: (m["front_door"], "ForceCloseImmediate"),
        31: (m["front_door"], "ForceUnlock"),
        32: (m["rear_door"], "ForceCloseImmediate"),
    }

    for index, action in ((33, "Reactivate"), (34, "Deactivate")):
        node = canonical(nn[index], nh)
        assert node["$type"] == "questSpawnManagerNodeDefinition" and len(node["actions"]) == 1
        p = node["actions"][0]["type"]
        assert (p["action"], p["communityEntryName"]["$value"],
                p["communityEntryPhaseName"]["$value"], p["spawnerReference"]["$value"]) == (
                    action, m["clerk"]["entry"], m["clerk"]["phase"], m["clerk"]["spawner"])

    facts = {o["factName"]: (o["value"], o["setExactValue"]) for o in walk(new)
             if o.get("$type") == "questSetVar_NodeType"}
    assert facts["PTFRMV_Revision"] == (7, True)
    assert facts["PTFRMV_AccessRevision"] == (9, True)
    assert facts["PTFRMV_DoorRequests"] == facts["PTFRMV_ClerkRequests"] == facts["PTFRMV_ClerkReleaseRequests"] == (1, False)
    assert all(name.startswith("PTFRMV_") for name in facts)
    assert not any(o.get("$type") in ("questSceneNodeDefinition", "questPhaseNodeDefinition") for o in walk(new))

    community = read(BASE / "street_npc_sources/json/ep1/quest/main_quests/q307/communities/q307_com_main.community.json")
    entries = [o for o in walk(community) if o.get("$type") == "communitySpawnEntry"]
    clerk = [o for o in entries if o["entryName"]["$value"] == m["clerk"]["entry"]]
    assert len(clerk) == 1 and clerk[0]["characterRecordId"]["$value"] == "Character.q307_zetatech_clerk"
    phases = {p["Data"]["phaseName"]["$value"]: p["Data"] for p in clerk[0]["phases"]}
    assert m["clerk"]["phase"] in phases
    assert phases[m["clerk"]["phase"]]["timePeriods"][0]["spotNodeRefs"] == [
        {"$type": "NodeRef", "$storage": "string", "$value": "#q307_ws_zetatech_clerk_return"}
    ]

    entry, stop, restore = (canonical(nn[i]["condition"], nh) for i in (2, 5, 13))
    guards = m["guards"]
    oldstop = canonical(on[5]["condition"], oh)
    assert stop["operation"] == oldstop["operation"] == "OR"
    assert stop["conditions"][:-1] == oldstop["conditions"]
    migration = stop["conditions"][-1]["type"]
    assert (migration["factName"], migration["comparisonType"], migration["value"]) == ("PTFRMV_AccessRevision", "NotEqual", 9)
    current = guards | {"PTFRMV_AccessRevision": 9}
    assert evaluate(entry, current) and not evaluate(stop, current)
    assert evaluate(stop, guards | {"PTFRMV_AccessRevision": 0})
    assert evaluate(restore, guards | {"PTFRMV_Enabled": 0})
    negatives = 0
    wait, ready, unload, rearm = (canonical(nn[i]["condition"], nh) for i in (25, 26, 27, 28))
    for fact, value in guards.items():
        for bad in (-1, 0, 1, 2):
            if bad == value:
                continue
            state = current | {fact: bad}
            assert not evaluate(entry, state) and evaluate(stop, state)
            if fact != "PTFRMV_Enabled":
                assert not evaluate(restore, state)
            for resident in (False, True):
                assert evaluate_loading(wait, state, resident) and evaluate_loading(unload, state, resident)
                assert not evaluate_loading(ready, state, resident) and not evaluate_loading(rearm, state, resident)
            negatives += 1
    assert negatives == 45

    result = {
        "status": "PASS_R9_OFFLINE_NOT_LIVE",
        "archive_sha256": m["sha256"], "xl_sha256": m["xl_sha256"],
        "unchanged_prior_resources": 22, "changed_prior_resources": [PHASE],
        "native_nodes": len(nn), "negative_guards": negatives, "loading_guard_cases": 92,
        "door_actions": 4, "clerk_actions": 2, "clerk_entries_targeted": 1,
        "original_world_resources_changed": 0, "story_writes": 0, "scene_starts": 0,
        "live_tested": False,
    }
    (BASE / "access_r9_tests.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
