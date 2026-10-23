"""Independent R6 scope, guarded lifecycle and vanilla service checks.

No game execution. Exact payload comparisons catch accidental additions to the
street, root/scene activation, broad crowd disabling and story-state writes.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from audit_world_interactions import walk
from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_optin import evaluate
from test_misty_viktor_street_r3 import quest_normalized, world_normalized

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/misty_viktor_world"
R5 = ROOT / "build/MistyViktorVariantsR5/source"
R6 = ROOT / "build/MistyViktorRepairR6/source"
PREFIX = "towercontinued\\misty_viktor_world\\"
PHASE = PREFIX + "shell_optin.questphase"
ADDITIONS = {PREFIX + "crowd_alley_r6.streamingsector", PREFIX + "crowd_alley_r6.streamingblock"}
PRIVATE_CROWD_REF = "$/03_night_city/#PTFRMV_TowerStreetCrowdBlocker"
TERMINAL_OWNER = "$/03_night_city/c_watson/little_china/#little_china_data_terminals"
TERMINAL_VARIANT = "q307_fast_travel_terminal_cutscene_hide"
POLICE_OWNER = "$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_gameplay"
LIGHTING_OWNER = "$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/#loc_mystic_mistys_ripperdoc_lightning"
PRIVATE_FACTS = {
    "PTFRMV_Registered", "PTFRMV_Revision", "PTFRMV_Applied",
    "PTFRMV_Acquires", "PTFRMV_Releases", "PTFRMV_AccessRequests",
    "PTFRMV_RestoreRequests", "PTFRMV_CrowdRequests",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def root(name):
    return read(BASE / name)["Data"]["RootChunk"]


def normalized(value, table):
    return quest_normalized(canonical(value, table))


def evaluate_loading(condition, facts, resident):
    if condition["$type"] == "questNodeLoadingCondition":
        assert condition["objectRef"]["$value"] == PRIVATE_CROWD_REF
        return not resident if condition["inverted"] else resident
    if condition["$type"] == "questLogicalCondition":
        values = [evaluate_loading(child, facts, resident) for child in condition["conditions"]]
        return all(values) if condition["operation"] == "AND" else any(values)
    return evaluate(condition, facts)


def test_phase(manifest):
    old, new = root("variants_r5_phase.json"), root("repair_r6_phase.json")
    oh, nh = handles(old), handles(new)
    on, nn = nodes(old), nodes(new)
    assert set(on) == set(range(22)) and set(nn) == set(range(30))
    assert old["phasePrefabs"] == new["phasePrefabs"] == []
    for item in walk(new):
        if "HandleRefId" in item:
            assert str(item["HandleRefId"]) in nh, "Unresolved native handle"
    # Compare the entire payload of every pre-existing node, ignoring sockets
    # only because edges are checked independently below.
    for index in range(22):
        before, after = normalized(on[index], oh), normalized(nn[index], nh)
        if index == 18:
            assert before["type"]["factName"] == after["type"]["factName"] == "PTFRMV_Revision"
            assert before["type"]["value"] == 5 and after["type"]["value"] == 6
            before["type"]["value"] = 6
        if index in (16, 21):
            assert len(before["type"]["params"]) == 1 and len(after["type"]["params"]) == 3
            show = 1 if index == 16 else 0
            lighting = after["type"]["params"].pop()
            assert lighting == {
                "$type": "questTogglePrefabVariant_NodeTypeParams",
                "prefabNodeRef": {"$type": "NodeRef", "$storage": "string", "$value": LIGHTING_OWNER},
                "variantStates": [
                    {"$type": "questVariantState", "name": {"$type": "CName", "$storage": "string", "$value": "Q307_VV"}, "show": 1-show},
                    {"$type": "questVariantState", "name": {"$type": "CName", "$storage": "string", "$value": "V_Default"}, "show": show},
                ],
            }, (index, lighting)
            additional = after["type"]["params"].pop()
            assert additional == {
                "$type": "questTogglePrefabVariant_NodeTypeParams",
                "prefabNodeRef": {"$type": "NodeRef", "$storage": "string", "$value": POLICE_OWNER},
                "variantStates": [{"$type": "questVariantState", "name": {
                    "$type": "CName", "$storage": "string", "$value": "q001_holo_scene",
                }, "show": show}],
            }, (index, additional)
        assert before == after, ("Unexpected existing-node mutation", index)
    old_edges, new_edges = quest_edges(old)[0], quest_edges(new)[0]
    removed = {(19, "Out", 11, "In"), (5, "Out", 20, "In")}
    added = {
        (19, "Out", 22, "In"),
        (22, "Out", 11, "In"), (5, "Out", 24, "In"),
        (24, "Out", 20, "In"),
        (19, "Out", 25, "In"), (25, "Out", 26, "In"),
        (26, "True", 23, "In"), (23, "Out", 29, "In"),
        (29, "Out", 27, "In"), (27, "Out", 28, "In"),
        (28, "True", 25, "In"),
    }
    assert removed <= old_edges
    assert new_edges == (old_edges - removed) | added, (old_edges - new_edges, new_edges - old_edges)
    if "edges" in manifest:
        assert new_edges == {(a, socket, b, "In") for a, socket, b in manifest["edges"]}

    # Vanilla cleanup contains both OFF and later ON for the old crime scene.
    # R6 hides it during the overlay and restores the ON state on the guarded
    # release path only. Do not mistake the earlier OFF for its final baseline.
    cleanup = read(ROOT / "research/q307_extracted/json/ep1/quest/main_quests/q307/phases/q307_cleanup.questphase.json")["Data"]["RootChunk"]
    cleanup_action = canonical(nodes(cleanup)[22]["type"], handles(cleanup))
    original_police = [param for param in cleanup_action["params"] if param["prefabNodeRef"]["$value"] == "#loc_mystic_mistys_ripperdoc_gameplay"]
    shows = [state["show"] for param in original_police for state in param["variantStates"] if state["name"]["$value"] == "q001_holo_scene"]
    assert shows == [0, 1], shows
    original_lighting = [param for param in cleanup_action["params"] if param["prefabNodeRef"]["$value"] == "#loc_mystic_mistys_ripperdoc_lightning"]
    assert len(original_lighting) == 1
    assert [(state["name"]["$value"], state["show"]) for state in original_lighting[0]["variantStates"]] == [("Q307_VV", 0), ("V_Default", 1)]
    scope = read(BASE / "r6_variant_audit_scopes.json")
    expected_scopes = {
        "q001_holo_scene": (2, 19, {"worldEntityNode": 5, "worldStaticMeshNode": 13, "worldCollisionNode": 1}, POLICE_OWNER),
        "V_Default": (13, 267, {"worldEntityNode": 1, "worldDecorationMeshNode": 1, "worldStaticLightNode": 196, "worldInstancedDestructibleMeshNode": 12, "worldStaticMeshNode": 54, "worldCollisionNode": 3}, LIGHTING_OWNER),
        "Q307_VV": (13, 270, {"worldEntityNode": 1, "worldStaticLightNode": 203, "worldReflectionProbeNode": 1, "worldStaticMeshNode": 62, "worldCollisionNode": 3}, LIGHTING_OWNER),
    }
    for name, (range_count, count, types, owner) in expected_scopes.items():
        ranges = [row for row in scope["ranges"] if row["variant"]["name"]["$value"] == name]
        members = [member for row in ranges for member in row["members"]]
        assert len(ranges) == range_count and len(members) == count, name
        assert Counter(member["type"] for member in members) == types, name
        assert all(row["variant"]["nodeRef"]["$value"] == owner for row in ranges), name
        template = ("base\\quest\\main_quests\\prologue\\q001\\entities\\q001_police_holotape.ent" if name == "q001_holo_scene" else "base\\gameplay\\devices\\lights\\indestructible\\spotlight_b_wall.ent")
        assert all(member["full_node"]["entityTemplate"]["DepotPath"]["$value"] == template for member in members if member["type"] == "worldEntityNode"), name

    terminal = normalized(nn[22]["type"], nh)
    expected_param = read(BASE / "bradbury_toggle_params.json")
    assert nn[22]["$type"] == "questWorldDataManagerNodeDefinition"
    assert terminal == {"$type": "questTogglePrefabVariant_NodeType", "params": [expected_param]}
    assert expected_param["prefabNodeRef"]["$value"] == TERMINAL_OWNER
    assert expected_param["variantStates"] == [{
        "$type": "questVariantState",
        "name": {"$type": "CName", "$storage": "string", "$value": TERMINAL_VARIANT},
        "show": 1,
    }]
    source = read(BASE / "bradbury_terminal_audit.json")
    assert source["display_name"]["femaleVariant"] == "Bradbury & Buran"
    assert len(source["ranges"]) == 2 and all(row["count"] == 1 for row in source["ranges"])
    assert [row["members"][0]["type"] for row in source["ranges"]] == ["worldEntityNode", "worldEntityProxyMeshNode"]
    assert [(row["descriptor"], row["variant"]["rangeIndex"]) for row in source["ranges"]] == [(4836, 8), (11031, 21)]
    for row in source["ranges"]:
        assert sha(ROOT / row["source_json"]) == row["source_sha256"]

    crowd_refs = []
    for index, enable in ((23, 1), (24, 0)):
        action = normalized(nn[index]["type"], nh)
        assert nn[index]["$type"] == "questCrowdManagerNodeDefinition"
        assert set(action) == {"$type", "areaReference", "enable"}
        assert action["$type"] == "questCrowdManagerNodeType_EnableNullArea"
        assert action["enable"] == enable
        ref = action["areaReference"]["$value"]
        assert ref == PRIVATE_CROWD_REF
        crowd_refs.append(ref)
    assert crowd_refs[0] == crowd_refs[1]
    assert sum(o.get("$type") == "questCrowdManagerNodeType_EnableNullArea" for o in walk(new)) == 2
    assert not any(o.get("$type") in (
        "questCrowdManagerNodeType_ControlCrowd", "questSceneNodeDefinition",
        "questSpawnManagerNodeDefinition", "questPhaseNodeDefinition",
    ) for o in walk(new))
    assert {o["factName"] for o in walk(new) if o.get("$type") == "questSetVar_NodeType"} == PRIVATE_FACTS

    facts = manifest["guards"]
    entry, stop, restore = (canonical(nn[i]["condition"], nh) for i in (2, 5, 13))
    loading = {"$type": "questNodeLoadingCondition", "inverted": 0,
               "objectRef": {"$type": "NodeRef", "$storage": "string", "$value": PRIVATE_CROWD_REF}}
    unloaded = loading | {"inverted": 1}
    def logic(operation, *conditions):
        return {"$type": "questLogicalCondition", "operation": operation, "conditions": list(conditions)}
    ready = logic("AND", loading, entry)
    wait_ready, check_ready, wait_unload, check_rearm = (canonical(nn[i]["condition"], nh) for i in (25, 26, 27, 28))
    assert wait_ready == logic("OR", ready, stop)
    assert check_ready == ready and wait_unload == logic("OR", unloaded, stop)
    assert check_rearm == entry
    assert nn[25]["$type"] == nn[27]["$type"] == "questPauseConditionNodeDefinition"
    assert nn[26]["$type"] == nn[28]["$type"] == "questConditionNodeDefinition"
    counter = normalized(nn[29]["type"], nh)
    assert counter == {"$type": "questSetVar_NodeType", "factName": "PTFRMV_CrowdRequests", "setExactValue": 0, "value": 1}
    loading_cases = 0
    for resident in (False, True):
        assert evaluate_loading(wait_ready, facts, resident) == resident
        assert evaluate_loading(check_ready, facts, resident) == resident
        assert evaluate_loading(wait_unload, facts, resident) != resident
        assert evaluate_loading(check_rearm, facts, resident)
        loading_cases += 1
    assert evaluate(entry, facts) and not evaluate(stop, facts)
    assert evaluate(restore, facts | {"PTFRMV_Enabled": 0})
    negatives = 0
    for fact, wanted in facts.items():
        for bad in (-1, 0, 1, 2):
            if bad == wanted:
                continue
            candidate = facts | {fact: bad}
            assert not evaluate(entry, candidate) and evaluate(stop, candidate), (fact, bad)
            if fact != "PTFRMV_Enabled":
                assert not evaluate(restore, candidate), (fact, bad, "vanilla release guard")
            for resident in (False, True):
                assert evaluate_loading(wait_ready, candidate, resident)
                assert evaluate_loading(wait_unload, candidate, resident)
                assert not evaluate_loading(check_ready, candidate, resident)
                assert not evaluate_loading(check_rearm, candidate, resident)
                loading_cases += 1
            negatives += 1
    assert negatives == 45
    assert loading_cases == 92
    return crowd_refs[0], negatives, loading_cases


def test_crowd(full_ref):
    assert read(BASE / "repair_r6_crowd.json")["Data"]["EmbeddedFiles"] == []
    sector, block = root("repair_r6_crowd.json"), root("repair_r6_crowd_block.json")
    manifest = read(BASE / "r6_wall_nav_crowd_manifest.json")
    assert manifest["private_ref"] == full_ref == PRIVATE_CROWD_REF
    original_path = ROOT / manifest["source"]
    assert sha(original_path) == manifest["source_sha256"]
    original_json = Path(str(original_path).replace("\\raw\\", "\\json\\") + ".json")
    original = read(original_json)["Data"]["RootChunk"]
    original_node, original_placement = original["nodes"][62]["Data"], original["nodeData"]["Data"][62]
    assert len(sector["nodes"]) == len(sector["nodeData"]["Data"]) == 1
    placement = sector["nodeData"]["Data"][0]
    node = sector["nodes"][placement["NodeIndex"]]["Data"]
    assert node["$type"] == "worldCrowdNullAreaNode"
    omitted = {"debugName", "sourcePrefabHash"}
    assert world_normalized({k: v for k, v in node.items() if k not in omitted}) == world_normalized({k: v for k, v in original_node.items() if k not in omitted})
    assert node["debugName"]["$value"] == "PTFRMV_TowerStreetCrowdBlocker" and str(node["sourcePrefabHash"]) == "0"
    omitted = {"Id", "NodeIndex", "QuestPrefabRefHash", "UkHash1"}
    assert world_normalized({k: v for k, v in placement.items() if k not in omitted}) == world_normalized({k: v for k, v in original_placement.items() if k not in omitted})
    assert placement["Id"] == "730000000006062" and placement["NodeIndex"] == 0
    assert placement["QuestPrefabRefHash"]["$value"] == PRIVATE_CROWD_REF
    assert placement["UkHash1"]["$value"] in ("", "0")
    assert sector["nodeRefs"] == [placement["QuestPrefabRefHash"]]
    assert not sector["localInplaceResource"] and not sector["persistentNodes"]
    # Stream with the opt-in street variant. The source disabled flag is
    # preserved above; native ON/OFF still controls the volume's activity.
    assert sector["variantIndices"] == [0, 0]
    assert len(block["descriptors"]) == 1
    descriptor = block["descriptors"][0]
    assert descriptor["data"]["DepotPath"]["$value"] == PREFIX + "crowd_alley_r6.streamingsector"
    prior_descriptor = root("variants_r5_street.json")["descriptors"][0]
    assert descriptor["numNodeRanges"] == 2 and len(descriptor["variants"]) == 1
    assert world_normalized({k: v for k, v in descriptor.items() if k != "data"}) == world_normalized({k: v for k, v in prior_descriptor.items() if k != "data"})
    audited_shape = read(BASE / "r6_wall_nav_audit.json")["native_crowd_area"]
    for i, axis in enumerate(("X", "Y", "Z")):
        assert descriptor["streamingBox"]["Min"][axis] <= audited_shape["world_aabb"]["min"][i]
        assert descriptor["streamingBox"]["Max"][axis] >= audited_shape["world_aabb"]["max"][i]
    assert audited_shape["point_checks"]["npc_crossing"]["inside_xy"]
    assert audited_shape["point_checks"]["npc_crossing"]["inside_z"]
    # The isolated source build must be copied byte-for-byte into the main R6.
    crowd_source = ROOT / "build/MistyViktorCrowdR6/source"
    for depot in ADDITIONS:
        assert (R6 / depot).read_bytes() == (crowd_source / depot).read_bytes(), depot
    assert sha(crowd_source / (PREFIX + "crowd_alley_r6.streamingsector")) == manifest["sha256"]
    assert sha(crowd_source / (PREFIX + "crowd_alley_r6.streamingblock")) == manifest["block_sha256"]
    return node, placement, full_ref


def test_probe(facts):
    sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
    from lupa.lua51 import LuaRuntime
    probe = (ROOT / "diagnostics/PTFR_MistyViktor_World/init.lua").read_text()
    assert probe.count('SetFactStr("PTFRMV_Enabled",') == 2
    assert not any(token in probe for token in ("NewObject", "Teleport(", "ExecuteQuest", "TogglePrefab"))
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={};writes={};f={};pos={x=-1658.9,y=997.4,z=23.7}
    function IsDefined(x)return x~=nil end
    function registerForEvent(n,cb)events[n]=cb end
    function print(...)end
    json={encode=function()return 'row' end}
    io={open=function(n,m)if m=='r' then return nil end;return {write=function(self)return self end,flush=function()return true end,close=function()return true end}end}
    local q={GetFactStr=function(self,k)return f[k] or 0 end,SetFactStr=function(self,k,v)f[k]=v;writes[#writes+1]={k,v}end}
    Game={GetQuestsSystem=function()return q end,GetPlayer=function()return {GetWorldPosition=function()return pos end}end}''')
    mod = lua.execute(probe)
    lf = lua.globals().f
    for key, value in facts.items():
        lf[key] = value
    lf.PTFRMV_Registered, lf.PTFRMV_Enabled = 1, 0
    for stale in (0, 4, 5):
        lf.PTFRMV_Revision = stale
        mod.Start()
        assert len(lua.globals().writes) == 0, stale
    lf.PTFRMV_Revision = 6
    mod.Start()
    mod.Start()
    assert len(lua.globals().writes) == 1
    lua.execute('pos={x=-1542,y=1210,z=16}')
    mod.Stop()
    assert lf.PTFRMV_Enabled == 1
    lua.execute('pos={x=-1658.9,y=997.4,z=23.7}')
    mod.Stop()
    assert lf.PTFRMV_Enabled == 0
    mod.Finish()
    lf.q307_active = 1
    mod.Start()
    assert len(lua.globals().writes) == 2
    return sha(ROOT / "diagnostics/PTFR_MistyViktor_World/init.lua")


def main():
    from audit_bradbury_crowd_readiness import main as verify_vanilla_readiness
    verify_vanilla_readiness()
    manifest, prior = read(BASE / "repair_r6_manifest.json"), read(BASE / "variants_r5_manifest.json")
    assert manifest["guards"] == prior["guards"]
    assert len(prior["resources"]) == 17
    assert len(manifest["resources"]) == len(set(manifest["resources"])) == 19
    assert set(manifest["resources"]) == set(prior["resources"]) | ADDITIONS
    changed = {depot for depot in prior["resources"] if (R5 / depot).read_bytes() != (R6 / depot).read_bytes()}
    assert changed == {PHASE}, changed
    for depot in manifest["resources"]:
        assert depot.startswith(PREFIX) and ".." not in depot
    assert sha(Path(manifest["archive"])) == manifest["sha256"]
    assert sha(Path(manifest["archive"] + ".xl")) == manifest["xl_sha256"]
    before = Path(prior["archive"] + ".xl").read_text(encoding="utf-8-sig")
    after = Path(manifest["archive"] + ".xl").read_text(encoding="utf-8-sig")
    newlines = [line for line in after.splitlines() if "crowd_alley_r6.streamingblock" in line]
    assert len(newlines) == 1 and newlines[0].strip() == "- " + PREFIX + "crowd_alley_r6.streamingblock"
    assert [line for line in after.splitlines() if line not in newlines] == before.splitlines()
    full_ref, negatives, loading_cases = test_phase(manifest)
    test_crowd(full_ref)
    probe_hash = test_probe(manifest["guards"])
    report = {
        "status": "PASS_R6_OFFLINE_NOT_LIVE", "archive_sha256": manifest["sha256"],
        "xl_sha256": manifest["xl_sha256"], "probe_sha256": probe_hash,
        "unchanged_prior_resources": 16, "changed_prior_resources": sorted(changed),
        "new_resources": sorted(ADDITIONS), "native_nodes": 30,
        "loading_guard_cases": loading_cases,
        "same_type_vanilla_readiness_precedent": "default_dialogs/7/33/3:pause33->EnableNullArea32",
        "negative_guards": negatives, "terminal_ranges": 2, "terminal_entities_added": 0,
        "crime_scene_off_on_optin": True, "crime_scene_on_guarded_release": True,
        "original_lighting_switch": {"V_Default_members": 267, "Q307_VV_members": 270, "ranges_each": 13},
        "crowd_private_ref": full_ref, "global_crowd_actions": 0,
        "story_writes": 0, "scene_starts": 0, "live_tested": False,
    }
    (BASE / "repair_r6_tests.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
