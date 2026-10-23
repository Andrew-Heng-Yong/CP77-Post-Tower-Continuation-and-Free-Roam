"""Offline boundary checks for the manually gated H10 V-only mirror probe."""

import json
import csv
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "research/b0_h10_vonly_mirror/validation"
scene = json.loads((VALIDATION / "h10_v_mirror.scene.json").read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
gate = json.loads((VALIDATION / "manual_gate.questphase.json").read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
nodes = {n["Data"]["nodeId"]["id"]: n["Data"] for n in scene["sceneGraph"]["Data"]["graph"]}
edges = {i: [d["nodeId"]["id"] for s in n.get("outputSockets", []) for d in s.get("destinations", [])] for i, n in nodes.items()}
entry = next(p["nodeId"]["id"] for p in scene["entryPoints"] if p["name"].get("$value") == "in_mirror")
assert entry == 434
seen, queue = set(), deque([entry])
while queue:
    i = queue.popleft()
    if i not in seen:
        seen.add(i)
        queue.extend(edges[i])
assert len(seen) == 46, len(seen)
assert 2 in seen  # Genuine scene End reached after authored exit cleanup.
assert {220, 222, 226, 228, 242, 386}.issubset(seen)
assert {982, 983, 988, 994, 1000, 1003, 1031, 1084, 1325, 1412, 1414, 1418, 1586, 1624}.isdisjoint(seen)
assert edges[220] == [222, 1044, 1077, 386]
assert edges[226] == [228, 397]
assert edges[242] == [2]
assert 509 not in seen  # No return to full apartment hub.

writers = {}
for i in seen:
    quest = nodes[i].get("questNode", {}).get("Data", {})
    action = quest.get("type", {}).get("Data", {})
    assert action.get("subtype", {}).get("Data", {}).get("$type") != "questCharacterManagerParameters_SetStatusEffect", i
    if action.get("$type") == "questSetVar_NodeType":
        writers[i] = (action.get("factName"), action.get("value"))
assert writers == {1047: ("mq000_mirror_blinders_closed", 1), 1051: ("mq000_mirror_blinders_closed", 0)}, writers
# Required native action pairs; these assertions prove graph reachability only.
for pair in [(853, 866), (860, 867), (441, 445), (443, 446), (609, 614), (476, 484), (1077, 1080), (224, 497)]:
    assert set(pair).issubset(seen), pair
assert nodes[220]["options"][0]["caption"]["$value"] == "mirror"
assert nodes[226]["options"][0]["caption"]["$value"] == "leave"
assert sorted(p["propName"] for p in scene["props"]) == ["shower", "tv_lookat"]
assert all(p["spawnDespawnParams"]["spawnOnStart"] == 0 for p in scene["props"])
assert all(a["spawnDespawnParams"]["spawnOnStart"] == 0 for a in scene["actors"])

gnodes = {n["Data"]["id"]: n["Data"] for n in gate["graph"]["Data"]["nodes"]}
assert set(gnodes) == set(range(13))
assert gnodes[7]["$type"] == "questSceneNodeDefinition"
assert gnodes[7]["sceneFile"]["DepotPath"]["$value"] == r"towercontinued\b0_h10_vonly_mirror\h10_v_mirror.scene"
with (ROOT / "research/b0_h10_vonly_mirror/graph/nodes.csv").open(newline="", encoding="utf-8-sig") as stream:
    graph_rows = {int(row["node_id"]): row for row in csv.DictReader(stream)}
assert graph_rows[7]["incoming"] == "6:Out->in_mirror"
assert graph_rows[7]["outgoing"] == "out->8:In|Default INT->12:In"
assert not gate.get("phasePrefabs")
gate_writes = sorted(n["type"]["Data"]["factName"] for n in gnodes.values() if n["$type"] == "questFactsDBManagerNodeDefinition")
assert all(x.startswith("PTFRB0H10M_") for x in gate_writes), gate_writes
assert {"PTFRB0H10M_Request", "PTFRB0H10M_Ready", "PTFRB0H10M_Active", "PTFRB0H10M_Completed", "PTFRB0H10M_Interrupted"}.issubset(gate_writes)
guard_conditions = [x["Data"] for x in gnodes[4]["condition"]["Data"]["conditions"]]
assert sum(x["$type"] == "questTriggerCondition" and x["triggerAreaRef"]["$value"] == "#mq000_tr_vs_apartment" for x in guard_conditions) == 1
assert sum(x["$type"] == "questUICondition" and x["type"]["Data"]["$type"] == "questPhoneCallPhase_ConditionType" for x in guard_conditions) == 1
assert any(x["$type"] == "questFactsDBCondition" and x["type"]["Data"]["factName"] == "q305_johnny_scene_active" and x["type"]["Data"]["value"] == 0 for x in guard_conditions)
print("PASS: V-only normal route ends, no reachable Johnny/status/story writes, mod-owned gate writes only. Default INT cleanup and runtime target resolution are NOT validated.")
