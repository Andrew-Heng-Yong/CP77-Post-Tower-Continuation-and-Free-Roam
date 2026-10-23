"""Exact resource scope and automatic native-controller simulation for R8."""
import copy
import json
from pathlib import Path

from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "research/misty_viktor_world"
world = json.loads((AUDIT / "lighting_r8_world_manifest.json").read_text())
phases = json.loads((AUDIT / "lighting_r8_phase_manifest.json").read_text())
package = json.loads((AUDIT / "lighting_r8_package_manifest.json").read_text())
assert (world["status"], phases["status"], package["status"]) == (
    "BUILT_R8_WORLD_SOURCE_NOT_INSTALLED",
    "BUILT_R8_AUTOMATIC_NATIVE_PHASES_NOT_INSTALLED",
    "BUILT_R8_AUTOMATIC_PACKAGE_NOT_INSTALLED",
)
assert (len(world["original_targets"]), len(world["cold_targets"])) == (12, 5)
assert len({x["alias"] for x in world["original_targets"] + world["cold_targets"]}) == 17
assert {x["datum"] for x in world["original_targets"] if x["group"] == "police"} == set(range(3901, 3908))
assert {x["datum"] for x in world["original_targets"] if x["group"] == "pink"} == {3921, 3923, 3943, 3945, 3946}
assert {x["datum"] for x in world["cold_targets"]} == {3542, 3543, 3544, 3547, 3548}

source_path = AUDIT / "r7_lighting_sources/base/worlds/03_night_city/_compiled/default/exterior_-25_18_0_0.streamingsector.json"
original = json.loads(source_path.read_text())
patched = json.loads((AUDIT / "lighting_r8_original_sector.json").read_text())
before, after = original["Data"]["RootChunk"], patched["Data"]["RootChunk"]
assert len(after["nodes"]) == len(before["nodes"]) == 3941
assert len(after["nodeData"]["Data"]) == len(before["nodeData"]["Data"]) == 4534
assert len(after["nodeRefs"]) == len(before["nodeRefs"]) + 12
for i, target in enumerate(world["original_targets"]):
    datum = target["datum"]
    assert after["nodeRefs"][len(before["nodeRefs"]) + i]["$value"] == target["alias"]
    assert after["nodeData"]["Data"][datum]["QuestPrefabRefHash"]["$value"] == target["alias"]
    after["nodeData"]["Data"][datum]["QuestPrefabRefHash"] = copy.deepcopy(
        before["nodeData"]["Data"][datum]["QuestPrefabRefHash"]
    )
del after["nodeRefs"][len(before["nodeRefs"]):]
patched["Header"]["ExportedDateTime"] = original["Header"]["ExportedDateTime"]
assert patched == original, "Official-sector decoded delta exceeds 12 aliases + 12 nodeRefs"

private = json.loads((AUDIT / "lighting_r8_cold_sector.json").read_text())["Data"]["RootChunk"]
assert len(private["nodes"]) == len(private["nodeData"]["Data"]) == len(private["nodeRefs"]) == 5
assert private["variantIndices"] == [0, 0]
for i, target in enumerate(world["cold_targets"]):
    source_node = copy.deepcopy(before["nodes"][target["node"]]["Data"])
    clone_node = copy.deepcopy(private["nodes"][i]["Data"])
    clone_node["debugName"] = source_node["debugName"]
    clone_node["sourcePrefabHash"] = source_node["sourcePrefabHash"]
    assert clone_node == source_node, f"Cold node properties changed: {target['datum']}"
    source_data = copy.deepcopy(before["nodeData"]["Data"][target["datum"]])
    clone_data = copy.deepcopy(private["nodeData"]["Data"][i])
    for key in ("Id", "NodeIndex", "QuestPrefabRefHash", "UkHash1"):
        clone_data[key] = source_data[key]
    assert clone_data == source_data, f"Cold placement transform changed: {target['datum']}"
    assert private["nodeRefs"][i]["$value"] == target["alias"]
block = json.loads((AUDIT / "lighting_r8_cold_block.json").read_text())["Data"]["RootChunk"]
variant = block["descriptors"][0]["variants"][0]
assert len(block["descriptors"]) == 1
assert variant["enabledByDefault"] == 0
assert variant["name"]["$value"] == world["private_variant"]


def evaluate(cond, facts, loaded):
    kind = cond["$type"]
    if kind == "questNodeLoadingCondition":
        present = cond["objectRef"]["$value"] in loaded
        return present != bool(cond["inverted"])
    if kind == "questLogicalCondition":
        values = [evaluate(c, facts, loaded) for c in cond["conditions"]]
        return all(values) if cond["operation"] == "AND" else any(values)
    assert kind == "questFactsDBCondition", kind
    term = cond["type"]
    equal = facts.get(term["factName"], 0) == term["value"]
    return equal if term["comparisonType"] == "Equal" else not equal


class Runner:
    def __init__(self, group, loaded):
        self.meta = phases[group]
        phase = json.loads((AUDIT / f"lighting_r8_{group}_phase.json").read_text())["Data"]["RootChunk"]
        self.nn = {i: canonical(n, handles(phase)) for i, n in nodes(phase).items()}
        assert set(self.nn) == set(range(self.meta["nodes"]))
        assert quest_edges(phase)[0] == {(a, s, b, "In") for a, s, b in self.meta["edges"]}
        assert phase["phasePrefabs"] == []
        self.edges = {(a, s): b for a, s, b in self.meta["edges"]}
        self.facts = dict(self.meta["guard"])
        self.facts["PostTowerFreeRoamActive"] = 0
        self.loaded = set(loaded)
        self.pc = 0
        self.actions = []
        self.run()
        assert self.actions == [] and self.facts[self.meta["prefix"] + "Applied"] == 0

    def run(self):
        for _ in range(300):
            node = self.nn[self.pc]
            kind, socket = node["$type"], "Out"
            if kind in ("questPauseConditionNodeDefinition", "questConditionNodeDefinition"):
                truth = evaluate(node["condition"], self.facts, self.loaded)
                if kind == "questPauseConditionNodeDefinition":
                    if not truth:
                        return
                else:
                    socket = "True" if truth else "False"
            elif kind == "questFactsDBManagerNodeDefinition":
                value = node["type"]
                self.facts[value["factName"]] = value["value"] + (
                    0 if value["setExactValue"] else self.facts.get(value["factName"], 0)
                )
            elif kind == "questWorldDataManagerNodeDefinition":
                t = node["type"]
                if t["$type"] == "questShowWorldNode_NodeType":
                    self.actions.append((t["objectRef"]["$value"], bool(t["show"])))
                elif t["$type"] == "questTogglePrefabVariant_NodeType":
                    self.actions.append(("PRIVATE_VARIANT", bool(t["params"][0]["variantStates"][0]["show"])))
                else:
                    raise AssertionError(t["$type"])
            else:
                assert kind == "questInputNodeDefinition", kind
            self.pc = self.edges[self.pc, socket]
        raise AssertionError("Controller failed to settle")


neon_refs = {x["alias"] for x in world["original_targets"] if x["group"] == "pink"}
cold_refs = {x["alias"] for x in world["cold_targets"]}
police_refs = {x["alias"] for x in world["original_targets"] if x["group"] == "police"}
neon = Runner("neon", neon_refs | cold_refs)
neon.facts["PostTowerFreeRoamActive"] = 1
neon.run()
assert neon.actions == [("PRIVATE_VARIANT", True)] + [(x["alias"], True) for x in world["cold_targets"]] + [
    (x["alias"], False) for x in world["original_targets"] if x["group"] == "pink"
]
assert neon.facts["PTFRMVN_Applied"] == neon.facts["PTFRMVN_Ready"] == 1
neon.facts["PTFRMVN_Suspended"] = 1
neon.run()
assert neon.actions[-6:] == [("PRIVATE_VARIANT", False)] + [(x["alias"], True) for x in world["original_targets"] if x["group"] == "pink"]
assert neon.facts["PTFRMVN_Applied"] == 0

police = Runner("police", police_refs)
police.facts["PostTowerFreeRoamActive"] = 1
police.facts["PTFRMV_Applied"] = 0
police.run()
assert police.actions == []
police.facts["PTFRMV_Applied"] = 1
police.run()
assert police.actions == [(x["alias"], False) for x in world["original_targets"] if x["group"] == "police"]
police.loaded.clear()
police.run()
assert police.facts["PTFRMVP_Ready"] == 0
police.loaded = set(police_refs)
police.run()
assert police.facts["PTFRMVP_Ready"] == 1
police.facts["PTFRMV_Applied"] = 0
police.loaded.clear()
police.run()
assert police.facts["PTFRMVP_Applied"] == 1  # holds until exact originals return for release
police.loaded = set(police_refs)
police.run()
assert police.actions[-7:] == [(x["alias"], True) for x in world["original_targets"] if x["group"] == "police"]
assert police.facts["PTFRMVP_Applied"] == 0

assert package["no_cet_required"] and package["story_fact_writes"] == 0
print("PASS: exact 12-alias original delta, five authored Cold copies, automatic native neon/police guard/release/stream loops")
