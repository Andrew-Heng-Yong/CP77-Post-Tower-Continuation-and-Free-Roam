"""Bounded semantic readback tests for the six staged native resources."""
import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
O = Path(__file__).resolve().parent
C = O / "candidate_02"
sys.path.insert(0, str(W / "tools"))
sys.path.insert(0, str(W / "diagnostics/restored_audit_20261025_03/dialogue"))
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
from helpers_01 import parse, canonical

inventory = json.loads((W / "diagnostics/restored_audit_20261025_01/installed_01/inventory.json").read_text(encoding="utf-8"))
refs = {r["depot"]: r for r in inventory["resources"]}
plan = json.loads((O / "plan_01.json").read_text(encoding="utf-8"))
build = json.loads((C / "build_native_02.json").read_text(encoding="utf-8"))
assert len(build["resources"]) == 6


def g(path, graph="root"):
    obj = json.loads(path.read_text(encoding="utf-8"))
    return next(x for x in flatten(SafeResource(obj), obj["Data"]["RootChunk"]) if x["path"] == graph)


def pair(depot, label):
    return g(W / refs[depot]["json"]), g(C / "readback" / (label + ".json"))


def nodes(graph):
    return {n["id"]: n for n in graph["nodes"]}


def unchanged_nodes(a, b, excluded):
    na, nb = nodes(a), nodes(b)
    assert set(na) - excluded == set(nb) - excluded
    assert all(na[i] == nb[i] for i in set(na) - excluded)


def edge_delta(a, b, removed, added):
    ea = {tuple(x) for x in a["edges"]}
    eb = {tuple(x) for x in b["edges"]}
    assert ea - eb == {tuple(x) for x in removed}, (ea - eb)
    assert eb - ea == {tuple(x) for x in added}, (eb - ea)


dep = r"towercontinued\sidejobs_s23\base_b\mq030.questphase"
a, b = pair(dep, "bullets_owner")
unchanged_nodes(a, b, {1021})
assert 1021 not in nodes(a) and nodes(b)[1021]["$type"] == "questPauseConditionNodeDefinition"
edge_delta(a, b, [], [[1020, "Out1", 1021, "In"], [1021, "Out", 1020, "In1"]])

dep = r"towercontinued\sidejobs_s29\entries\mq058_semimaru_crystalcoat.questphase"
a, b = pair(dep, "mq058_receipt")
unchanged_nodes(a, b, {64000})
edge_delta(a, b, [[64000, "Out1", 65007, "In"]], [[64000, "End Quest", 65007, "In"]])

dep = r"towercontinued\sidejobs_s25\families\sq025_fresh.questphase"
a, b = pair(dep, "s25_delamain_phone")
unchanged_nodes(a, b, {65020})
assert 65020 not in nodes(a) and nodes(b)[65020]["type"]["factName"] == "PTFRS22_SQ025_SupportIssued"
edge_delta(a, b, [[92, "Out", 94, "In1"]], [[92, "Out", 65020, "In"], [65020, "Out", 94, "In1"]])

dep = r"towercontinued\sidejobs_s29\entries\sq025b_delamain_insurgence.questphase"
a, b = pair(dep, "delamain_sequel_guard")
unchanged_nodes(a, b, {65003, 65004})
edge_delta(a, b, [], [])
predecessor = set(next(e for e in build["edits"] if e["kind"] == "sequel_not_predecessor_message_freshness")["removed_paths"])
for i in (65003, 65004):
    old = nodes(a)[i]["condition"]["conditions"]
    new = nodes(b)[i]["condition"]["conditions"]
    kept = [x for x in old if x.get("type", {}).get("path", {}).get("realPath") not in predecessor]
    assert kept == new
    assert len(old) - len(new) == 7

dep = r"towercontinued\sidejobs_s29\phone\delamain.questphase"
a, b = pair(dep, "delamain_phone_guard")
unchanged_nodes(a, b, {1002, 1003})
edge_delta(a, b, [], [])
for i in (1002, 1003):
    old = nodes(a)[i]["condition"]["conditions"]
    new = nodes(b)[i]["condition"]["conditions"]
    assert old == new[:-1]
    assert new[-1]["type"]["factName"] == "PTFRS25_SQ025_FRESH_Issued"
    assert new[-1]["type"]["value"] == 0

dep = r"towercontinued\b0_story_eight\yoko.scene"
installed = parse(str((C / "baseline_yoko.json").relative_to(W)))
patched = parse(str((C / "readback/yoko_scene.json").relative_to(W)))
assert set(installed["nodes"]) == set(patched["nodes"])
for ident in installed["nodes"]:
    if ident == 779:
        continue
    assert canonical(installed["nodes"][ident], installed["handles"]) == canonical(patched["nodes"][ident], patched["handles"]), ident
old = canonical(installed["nodes"][779], installed["handles"])
new = canonical(patched["nodes"][779], patched["handles"])
for i in range(len(old["options"])):
    if i not in (4, 5, 6, 7):
        assert old["options"][i] == new["options"][i]
        assert old["outputSockets"][i] == new["outputSockets"][i]
    else:
        assert not old["outputSockets"][i]["destinations"]
        assert new["outputSockets"][i]["destinations"]
        assert "PTFRS29_q305_postcontent_Issued" in json.dumps(new["options"][i]["questCondition"])
assert old["outputSockets"][2] == new["outputSockets"][2]

proof = {"status": "PASS_SIX_RESOURCE_SCOPED_SEMANTIC_READBACK_NOT_LIVE", "resources": 6, "checks": ["Yoko four quest options only", "Bullets native rearm loop", "MQ058 End Quest receipt", "S25 phone receipt", "S29 predecessor path removal", "S29 phone duplicate guard"], "game_writes": 0, "save_writes": 0}
p = C / "test_native_01.json"
assert not p.exists()
p.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
print(json.dumps(proof))
