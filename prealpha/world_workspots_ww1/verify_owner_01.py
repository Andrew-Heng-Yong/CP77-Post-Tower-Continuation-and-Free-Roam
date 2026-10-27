"""Verify serialized prefab-only prototype; does not simulate engine ownership."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "candidate_01"
DOC = OUT / "owner_readback_01.json"
PREFAB = "$/03_night_city/c_pacifica/coastview/cvi_ce_prefabMZQN2IY/#ce_pac_cvi_116"
EXPECTED = {
    "PostTowerFreeRoamActive": 1, "PTFRP0_DR13": 1, "q307_active": 0,
    "q307_done": 1, "q307_finished": 1, "q307_2079": 1,
    "q307_main_game_killed": 1, "q307_ep1_killed": 1,
    "PTFRBASE_Suspended": 0, "PTFRWW1_CVI116_Request": 1,
    "PTFRWW1_CVI116_Claimed": 0, "PTFRWW1_CVI116_Entered": 0,
    "PTFRWW1_CVI116_Hold": 0,
}


def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v)


def verify(doc):
    handles = {str(o["HandleId"]): o["Data"] for o in walk(doc)
               if "HandleId" in o and isinstance(o.get("Data"), dict)}

    def deref(o):
        return o.get("Data", handles.get(str(o.get("HandleRefId")), o))

    def nodes(g):
        return {n["id"]: n for n in map(deref, g["nodes"])}

    def edges(g):
        nd = nodes(g)
        sockets = {}
        for nid, n in nd.items():
            for s in n["sockets"]:
                sd = deref(s)
                sockets[id(sd)] = (nid, sd["name"]["$value"])
        found = set()
        for n in nd.values():
            for s in map(deref, n["sockets"]):
                for c in map(deref, s["connections"]):
                    found.add((*sockets[id(deref(c["source"]))],
                               *sockets[id(deref(c["destination"]))]))
        return found

    root = doc["Data"]["RootChunk"]
    assert not root.get("phasePrefabs")
    assert not root.get("inplacePhases")
    assert not doc["Data"].get("EmbeddedFiles")
    outer = deref(root["graph"])
    nd = nodes(outer)
    assert set(nd) == set(range(7))
    assert [nd[i]["$type"] for i in range(7)] == [
        "questInputNodeDefinition", "questFactsDBManagerNodeDefinition",
        "questPauseConditionNodeDefinition", "questFactsDBManagerNodeDefinition",
        "questFactsDBManagerNodeDefinition", "questFactsDBManagerNodeDefinition",
        "questPhaseNodeDefinition"]
    assert edges(outer) == {(0,"Out",1,"In"), (1,"Out",2,"In"),
        (2,"Out",3,"In"), (3,"Out",4,"In"), (4,"Out",5,"In"),
        (5,"Out",6,"In1")}
    cond = deref(nd[2]["condition"])
    assert cond["$type"] == "questLogicalCondition"
    assert cond["operation"] == "AND"
    tests = [o for o in walk(cond) if "comparisonType" in o]
    assert len(tests) == len(EXPECTED)
    assert all(t["comparisonType"] == "Equal" for t in tests)
    assert {t["factName"]: t["value"] for t in tests} == EXPECTED
    assert not any(n.get("phaseInstancePrefabs") for n in list(nd.values())[:-1])
    assert nd[6]["phaseInstancePrefabs"] == [{"$type": "questQuestPrefabEntry",
        "prefabNodeRef": {"$type": "NodeRef", "$storage": "string", "$value": PREFAB}}]
    inner = deref(nd[6]["phaseGraph"])
    inn = nodes(inner)
    assert set(inn) == {0, 1, 2}
    assert [inn[i]["$type"] for i in range(3)] == ["questInputNodeDefinition",
        "questFactsDBManagerNodeDefinition", "questPauseConditionNodeDefinition"]
    assert edges(inner) == {(0,"Out",1,"In"), (1,"Out",2,"In")}
    # Whitelist every reachable writer. Never native facts, kills, or Hold.
    writers = [o for o in walk(doc) if o.get("$type") == "questSetVar_NodeType"]
    assert {(o["factName"], o["value"]) for o in writers} == {
        ("PTFRWW1_CVI116_Ready",1), ("PTFRWW1_CVI116_Ready",0),
        ("PTFRWW1_CVI116_Request",0), ("PTFRWW1_CVI116_Claimed",1),
        ("PTFRWW1_CVI116_Entered",1)}
    forbidden = {"questSpawnManagerNodeDefinition", "questCommunityTemplate_NodeType",
        "questSceneNodeDefinition", "questPuppetAIManagerNodeDefinition",
        "questShowWorldNode_NodeType", "questOutputNodeDefinition"}
    assert not any(o.get("$type") in forbidden for o in walk(doc))
    # Exercise every authored equality with a failed condition, including the
    # already-claimed replay gate; this only proves the encoded predicate.
    allows = lambda state: all(state.get(k,0) == v for k,v in EXPECTED.items())
    assert allows(EXPECTED)
    for k,v in EXPECTED.items():
        changed = dict(EXPECTED); changed[k] = 1-v
        assert not allows(changed), k
    return True


doc = json.loads(DOC.read_text(encoding="utf-8-sig"))
verify(doc)
negative_controls = []
for kind in ("wrong_native_gate", "early_prefab", "native_fact_write"):
    broken = copy.deepcopy(doc)
    if kind == "wrong_native_gate":
        next(o for o in walk(broken) if o.get("factName") == "q307_active")["value"] = 1
    elif kind == "early_prefab":
        broken["Data"]["RootChunk"]["phasePrefabs"] = ["injected"]
    else:
        next(o for o in walk(broken) if o.get("$type") == "questSetVar_NodeType")["factName"] = "q307_done"
    try:
        verify(broken)
    except AssertionError:
        negative_controls.append(kind)
    else:
        raise AssertionError("Negative control accepted: " + kind)

result = {"status": "STATIC_OWNER_PROTOTYPE_PASS_NOT_GAMEPLAY_PROOF",
    "readback_sha256": hashlib.sha256(DOC.read_bytes()).hexdigest().upper(),
    "native_guards": len(EXPECTED), "negative_controls_rejected": negative_controls,
    "scope": "One original prefab; no activation, spawn, reset, or native fact write",
    "runtime_recovery": "UNPROVEN", "installed": False}
(OUT / "owner_validation_01.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
