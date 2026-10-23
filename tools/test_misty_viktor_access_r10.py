"""R10 exact streamed-door and storefront guard checks; no game writes."""
import hashlib
import json
from pathlib import Path

from audit_world_interactions import walk
from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_optin import evaluate

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/misty_viktor_world"
OLD = ROOT / "build/MistyViktorDetailsR7/source"
NEW = ROOT / "build/MistyViktorAccessR10/source"
PHASE = r"towercontinued\misty_viktor_world\shell_optin.questphase"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def eval_stream(condition, facts, loaded):
    if condition["$type"] == "questNodeLoadingCondition":
        value = loaded[condition["objectRef"]["$value"]]
        return not value if condition["inverted"] else value
    if condition["$type"] == "questLogicalCondition":
        values = [eval_stream(c, facts, loaded) for c in condition["conditions"]]
        return all(values) if condition["operation"] == "AND" else any(values)
    return evaluate(condition, facts)


def main():
    m = read(BASE / "access_r10_manifest.json")
    oldm = read(BASE / "details_r7_manifest.json")
    oldtests = read(BASE / "details_r7_tests.json")
    assert m["status"] == "BUILT_R10_STREAMED_DOORS_STREET_NPC_NOT_INSTALLED_OR_LIVE"
    assert oldtests["status"] == "PASS_R7_OFFLINE_NOT_LIVE"
    assert oldtests["archive_sha256"] == oldm["sha256"] and oldtests["xl_sha256"] == oldm["xl_sha256"]
    assert m["resources"] == oldm["resources"] and m["guards"] == oldm["guards"]
    assert m["compatibility_revision"] == 7 and m["access_revision"] == 10
    assert m["removed_r9_clerk"] and m["obsolete_door_actions_bypassed"] == [11, 14, 15]
    assert m["original_world_resource_overrides"] == m["native_scene_starts"] == m["story_fact_writes"] == 0
    assert sha(Path(m["archive"])) == m["sha256"] and sha(Path(m["archive"] + ".xl")) == m["xl_sha256"]
    assert Path(m["archive"] + ".xl").read_bytes() == Path(oldm["archive"] + ".xl").read_bytes()
    changed = {d for d in m["resources"] if (OLD / d).read_bytes() != (NEW / d).read_bytes()}
    assert changed == {PHASE}

    old = read(BASE / "details_r7_phase.json")["Data"]["RootChunk"]
    new = read(BASE / "access_r10_phase.json")["Data"]["RootChunk"]
    oh, nh = handles(old), handles(new)
    on, nn = nodes(old), nodes(new)
    assert set(on) == set(range(30)) and set(nn) == set(range(50))
    assert old["phasePrefabs"] == new["phasePrefabs"] == []
    for obj in walk(new):
        if "HandleRefId" in obj:
            assert str(obj["HandleRefId"]) in nh
    for index in range(30):
        for key in ("type", "condition"):
            if key in on[index] and not (index == 5 and key == "condition"):
                assert canonical(nn[index][key], nh) == canonical(on[index][key], oh), ("R7 payload changed", index, key)

    edges = quest_edges(new)[0]
    assert edges == {(a, s, b, "In") for a, s, b in m["edges"]}
    reachable, frontier = set(), [0]
    adjacency = {}
    for a, _, b, _ in edges:
        adjacency.setdefault(a, set()).add(b)
    while frontier:
        node = frontier.pop()
        if node in reachable:
            continue
        reachable.add(node); frontier.extend(adjacency.get(node, ()))
    assert not ({11, 14, 15} & reachable)
    assert set(range(50)) - {11, 14, 15} <= reachable

    door_specs = {
        34: (m["front_door"]["ref"], "ForceCloseImmediate"),
        35: (m["front_door"]["ref"], "ForceUnlock"),
        36: (m["inner_door"]["ref"], "ForceCloseImmediate"),
        37: (m["inner_door"]["ref"], "ForceUnlock"),
    }
    for index, expected in door_specs.items():
        params = canonical(nn[index]["type"], nh)["params"]
        assert len(params) == 1 and params[0]["deviceControllerClass"]["$value"] == "DoorControllerPS"
        assert params[0]["actionProperties"] == []
        assert (params[0]["objectRef"]["$value"], params[0]["deviceAction"]["$value"]) == expected

    refs = [m["front_door"]["ref"], m["inner_door"]["ref"]]
    valid = m["guards"] | {"PTFRMV_AccessRevision": 10}
    loaded_wait, loaded_check, invalid_wait, guard_wait = (canonical(nn[i]["condition"], nh) for i in (31, 33, 40, 43))
    for front in (False, True):
        for inner in (False, True):
            state = {refs[0]: front, refs[1]: inner}
            both = front and inner
            assert eval_stream(loaded_wait, valid, state) == both
            assert eval_stream(loaded_check, valid, state) == both
            assert eval_stream(invalid_wait, valid, state) == (not both)
            assert eval_stream(guard_wait, valid, state)

    for index, action in ((44, "Reactivate"), (46, "Deactivate")):
        node = canonical(nn[index], nh)
        assert node["$type"] == "questSpawnManagerNodeDefinition" and len(node["actions"]) == 1
        p = node["actions"][0]["type"]
        assert (p["action"], p["communityEntryName"]["$value"], p["communityEntryPhaseName"]["$value"], p["spawnerReference"]["$value"]) == (
            action, m["street_npc"]["entry"], m["street_npc"]["phase"], m["street_npc"]["spawner"])
    clerk = canonical(nn[48], nh)
    assert clerk["$type"] == "questSpawnManagerNodeDefinition" and len(clerk["actions"]) == 1
    cp = clerk["actions"][0]["type"]
    assert (cp["action"], cp["communityEntryName"]["$value"], cp["communityEntryPhaseName"]["$value"], cp["spawnerReference"]["$value"]) == (
        m["clerk_cleanup"]["action"], m["clerk_cleanup"]["entry"], m["clerk_cleanup"]["phase"], m["clerk_cleanup"]["spawner"])
    clerk_actions = [o for o in walk(new) if o.get("communityEntryName", {}).get("$value") == m["clerk_cleanup"]["entry"]]
    assert len(clerk_actions) == 1 and clerk_actions[0]["action"] == "Deactivate"

    facts = {o["factName"]: (o["value"], o["setExactValue"]) for o in walk(new) if o.get("$type") == "questSetVar_NodeType"}
    assert facts["PTFRMV_Revision"] == (7, True) and facts["PTFRMV_AccessRevision"] == (10, True)
    assert facts["PTFRMV_DoorRequests"] == facts["PTFRMV_StreetNPCRequests"] == facts["PTFRMV_StreetNPCReleaseRequests"] == facts["PTFRMV_ClerkRemovalRequests"] == (1, False)
    assert facts["PTFRMV_DoorReady"] in ((1, True), (0, True))
    assert all(name.startswith("PTFRMV_") for name in facts)
    assert not any(o.get("$type") in ("questSceneNodeDefinition", "questPhaseNodeDefinition") for o in walk(new))

    community = read(BASE / "street_npc_sources/json/ep1/quest/main_quests/q307/communities/q307_com_alley.community.json")
    entries = [o for o in walk(community) if o.get("$type") == "communitySpawnEntry"]
    target = [o for o in entries if o["entryName"]["$value"] == m["street_npc"]["entry"]]
    assert len(target) == 1 and target[0]["characterRecordId"]["$value"] == m["street_npc"]["record"]
    phases = {p["Data"]["phaseName"]["$value"]: p["Data"] for p in target[0]["phases"]}
    assert phases[m["street_npc"]["phase"]]["timePeriods"][0]["spotNodeRefs"][0]["$value"] == m["street_npc"]["workspot"]
    sector = read(BASE / "r6_wall_nav_sources/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/ep1/quest_bb3937b6e34a251c.streamingsector.json")["Data"]["RootChunk"]
    spots = [d for d in sector["nodeData"]["Data"] if d["QuestPrefabRefHash"].get("$value", "").endswith(m["street_npc"]["workspot"])]
    assert len(spots) == 1
    pos = spots[0]["Position"]
    assert all(abs(pos[k] - m["street_npc"]["position"][i]) < 0.001 for i, k in enumerate(("X", "Y", "Z")))

    entry, stop, restore = (canonical(nn[i]["condition"], nh) for i in (2, 5, 13))
    oldstop = canonical(on[5]["condition"], oh)
    assert stop["conditions"][:-1] == oldstop["conditions"]
    migration = stop["conditions"][-1]["type"]
    assert (migration["factName"], migration["comparisonType"], migration["value"]) == ("PTFRMV_AccessRevision", "NotEqual", 10)
    assert evaluate(entry, valid) and not evaluate(stop, valid) and evaluate(stop, m["guards"] | {"PTFRMV_AccessRevision": 9})
    assert evaluate(restore, valid | {"PTFRMV_Enabled": 0})
    negatives = 0
    for fact, value in m["guards"].items():
        for bad in (-1, 0, 1, 2):
            if bad == value:
                continue
            state = valid | {fact: bad}
            assert not evaluate(entry, state) and evaluate(stop, state)
            assert eval_stream(loaded_wait, state, {refs[0]: True, refs[1]: True})
            assert not eval_stream(guard_wait, state, {refs[0]: True, refs[1]: True})
            if fact != "PTFRMV_Enabled":
                assert not evaluate(restore, state)
            negatives += 1
    assert negatives == 45

    result = {
        "status": "PASS_R10_OFFLINE_NOT_LIVE", "archive_sha256": m["sha256"], "xl_sha256": m["xl_sha256"],
        "unchanged_prior_resources": 22, "changed_prior_resources": [PHASE], "native_nodes": len(nn),
        "negative_guards": negatives, "door_stream_cases": 4, "exact_door_actions": 4,
        "obsolete_door_nodes_unreachable": [11, 14, 15], "street_npc_entries_targeted": 1,
        "clerk_entries_targeted": 1, "clerk_action": "Deactivate", "original_world_resources_changed": 0, "story_writes": 0, "scene_starts": 0,
        "live_tested": False,
    }
    (BASE / "access_r10_tests.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
