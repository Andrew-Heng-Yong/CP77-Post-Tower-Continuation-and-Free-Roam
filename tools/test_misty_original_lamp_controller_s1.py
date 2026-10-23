"""Offline graph and release validation for the original-lamp singleton."""
import json
from pathlib import Path

from audit_world_interactions import walk
from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "research/misty_viktor_world"
m = json.loads((AUDIT / "original_lamp_s1_controller_manifest.json").read_text())
phase = json.loads((AUDIT / "original_lamp_s1_phase.json").read_text())["Data"]["RootChunk"]
nn = {i: canonical(n, handles(phase)) for i, n in nodes(phase).items()}
assert set(nn) == set(range(33))
expected_edges = {(a, s, b, "In") for a, s, b in m["edges"]}
assert quest_edges(phase)[0] == expected_edges
assert len(expected_edges) == len(m["edges"])
assert phase["phasePrefabs"] == []
for obj in walk(phase):
    if "HandleRefId" in obj:
        assert str(obj["HandleRefId"]) in handles(phase)
    if obj.get("$type") == "questTogglePrefabVariant_NodeType":
        raise AssertionError("Original lamp controller must not toggle variants")
    if obj.get("$type") == "questSetVar_NodeType":
        assert obj["factName"].startswith("PTFRMVOL_")
actions = {i: nn[i]["type"] for i in (14, 19, 27)}
assert [actions[i]["show"] for i in (14, 19, 27)] == [1, 0, 1]
for action in actions.values():
    assert action["$type"] == "questShowWorldNode_NodeType"
    assert action["objectRef"]["$value"] == m["alias"]


def evaluate(cond, facts, resident):
    kind = cond["$type"]
    if kind == "questNodeLoadingCondition":
        assert cond["objectRef"]["$value"] == m["alias"]
        return bool(resident) != bool(cond["inverted"])
    if kind == "questLogicalCondition":
        values = [evaluate(c, facts, resident) for c in cond["conditions"]]
        return all(values) if cond["operation"] == "AND" else any(values)
    assert kind == "questFactsDBCondition"
    term = cond["type"]
    equal = facts.get(term["factName"], 0) == term["value"]
    return equal if term["comparisonType"] == "Equal" else not equal


edges = {(a, s): b for a, s, b in m["edges"]}


class Runner:
    def __init__(self, resident=True):
        self.pc, self.resident = 0, resident
        self.facts = dict(m["guards"])
        self.actions = []
        self.run()
        assert self.pc == 7 and self.facts["PTFRMVOL_Enabled"] == 0

    def run(self):
        for _ in range(100):
            node = nn[self.pc]
            kind = node["$type"]
            sock = "Out"
            if kind in ("questPauseConditionNodeDefinition", "questConditionNodeDefinition"):
                truth = evaluate(node["condition"], self.facts, self.resident)
                if kind == "questPauseConditionNodeDefinition":
                    if not truth:
                        return
                else:
                    sock = "True" if truth else "False"
            elif kind == "questFactsDBManagerNodeDefinition":
                t = node["type"]
                self.facts[t["factName"]] = t["value"] + (0 if t["setExactValue"] else self.facts.get(t["factName"], 0))
            elif kind == "questWorldDataManagerNodeDefinition":
                assert self.pc in actions
                self.actions.append((self.pc, node["type"]["show"]))
            else:
                assert kind == "questInputNodeDefinition"
            self.pc = edges[self.pc, sock]
        raise AssertionError("graph did not settle")


r = Runner()
r.facts["PTFRMVOL_Enabled"] = 1
r.run()
assert r.pc == 18 and r.actions == [(14, 1)]
r.facts["PTFRMVOL_DesiredVisible"] = 0
r.run()
assert r.pc == 23 and r.actions == [(14, 1), (19, 0)]
r.facts["PTFRMVOL_Enabled"] = 0
r.run()
assert r.pc == 7 and r.actions == [(14, 1), (19, 0), (27, 1)]
assert r.facts["PTFRMVOL_Applied"] == r.facts["PTFRMVOL_Ready"] == 0

story = Runner()
story.facts["PTFRMVOL_Enabled"] = 1
story.run()
story.facts["PTFRMVOL_DesiredVisible"] = 0
story.run()
story.facts["q307_active"] = 1
story.run()
assert story.pc == 7 and story.actions == [(14, 1), (19, 0)]

unloaded = Runner(resident=False)
unloaded.facts["PTFRMVOL_Enabled"] = 1
unloaded.run()
assert unloaded.pc == 11 and unloaded.actions == []
unloaded.resident = True
unloaded.run()
assert unloaded.pc == 18 and unloaded.actions == [(14, 1)]
unloaded.resident = False
unloaded.run()
assert unloaded.pc == 11 and unloaded.actions == [(14, 1)]

print("PASS: exact 33-node graph, original alias targets, guarded stop and story handover, stream-out wait")
