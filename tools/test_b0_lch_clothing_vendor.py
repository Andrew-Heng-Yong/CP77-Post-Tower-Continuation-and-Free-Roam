"""Static isolation checks for the one-shop Little China clothing owner."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime  # noqa: E402
from audit_wilson_vendor_owner import graph_edges, walk  # noqa: E402
from report_scene_route import scalars  # noqa: E402
from test_b0_h10_mirror_prompt import read  # noqa: E402

VAL = ROOT / "research/b0_lch_clothing_vendor/validation"
PREFIX = "PTFRB0LCHV_"


def nodes(graph: dict) -> dict[int, dict]:
    return {item["Data"]["id"]: item["Data"] for item in graph["nodes"]}


def main() -> None:
    manifest = read(VAL / "build_manifest.json")
    assert manifest["status"] == "STATIC_EXPERIMENTAL_NOT_INSTALLED"
    assert manifest["vanilla_replacements"] == []
    assert manifest["resources"] == [
        "towercontinued\\b0_lch_clothing_vendor\\vendor_owner.questphase"
    ]
    archive = ROOT / "build/B0_LCH_Clothing_Vendor" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    xl = (ROOT / "archive/b0_lch_clothing_vendor/TowerContinued_B0_LCH_Clothing_Vendor.archive.xl").read_text(encoding="utf-8")
    assert xl.count("- path:") == 1
    assert manifest["resources"][0] in xl
    assert "parent: ep1\\quest\\ep1.quest" in xl
    graph = nodes(read(VAL / "vendor_owner.questphase.json")["Data"]["RootChunk"]["graph"]["Data"])
    assert set(graph) == set(range(9)), set(graph)
    assert [n["type"]["Data"]["factName"] for n in graph.values()
            if n["$type"] == "questFactsDBManagerNodeDefinition"] == [
                PREFIX + "Ready", PREFIX + "Near", PREFIX + "Departed", PREFIX + "Near"
            ]
    guard = graph[2]
    assert guard["$type"] == "questPauseConditionNodeDefinition"
    assert set(str(v) for v in scalars(guard["condition"], "factName")) == set(manifest["guard_facts"])
    assert set(manifest["guard_facts"]) >= {
        "q307_done", "q307_2079", "q307_main_game_killed",
        "wat_lch_clothingshop_01_default_on", PREFIX + "Enabled",
    }
    near = graph[3]["condition"]["Data"]["type"]["Data"]
    assert near["comparisonType"] == "Less"
    assert near["distanceDefinition2"]["Data"]["distanceValue"] == 50
    assert "#wat_lch_clothingstore_01_mp" in set(str(v) for v in scalars(near, "$value"))
    inner = nodes(graph[5]["phaseGraph"]["Data"])
    assert set(inner) == {0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11}, set(inner)
    handles = {str(v["HandleId"]): v["Data"] for v in walk(read(VAL / "vendor_owner.questphase.json")["Data"]["RootChunk"])
               if "HandleId" in v and "Data" in v}
    outer_edges = {(e["source_node_id"], e["source_socket"], e["destination_node_id"], e["destination_socket"])
                   for e in graph_edges(read(VAL / "vendor_owner.questphase.json")["Data"]["RootChunk"]["graph"]["Data"],
                                        "clothing-outer", handles)}
    assert outer_edges == {
        (0, "Out", 1, "In"), (1, "Out", 2, "In"), (2, "Out", 3, "In"),
        (3, "Out", 4, "In"), (4, "Out", 5, "In1"), (5, "Out1", 6, "In"),
        (6, "Out", 7, "In"), (7, "Out", 8, "In"), (8, "Out", 3, "In"),
    }, outer_edges
    inner_edges = {(e["source_node_id"], e["source_socket"], e["destination_node_id"], e["destination_socket"])
                   for e in graph_edges(graph[5]["phaseGraph"]["Data"], "clothing-inner", handles)}
    assert inner_edges == {
        (0, "Out", 5, "In"), (0, "Out", 10, "In"), (10, "Out", 7, "In"),
        (5, "Out", 8, "In"), (8, "Out", 4, "In"),
        (4, "Out", 9, "In"), (9, "Out", 2, "wat_lch_clothingshop_01_start"),
        (7, "Out", 6, "In"), (6, "Out", 11, "In"), (11, "Out", 1, "In"),
    }, inner_edges
    assert inner[8]["type"]["Data"]["factName"] == PREFIX + "SpawnActionOut"
    assert inner[9]["type"]["Data"]["factName"] == PREFIX + "ActorDistanceGate"
    assert inner[10]["type"]["Data"]["factName"] == PREFIX + "ExitWatchArmed"
    assert inner[11]["type"]["Data"]["factName"] == PREFIX + "DespawnActionOut"
    actors = []
    for node_id, action in ((5, "Activate"), (6, "Deactivate")):
        node = inner[node_id]
        assert node["$type"] == "questSpawnManagerNodeDefinition"
        assert len(node["actions"]) == 1
        spawn = node["actions"][0]["type"]["Data"]
        assert spawn["$type"] == "questSpawnSet_NodeType"
        assert spawn["action"] == action
        assert spawn["entryName"]["$value"] == "wat_lch_clothingshop_01"
        assert spawn["phaseName"]["$value"] == "default"
        actors.append(spawn["reference"]["$value"])
    assert actors == ["#wat_lch_clothingshop_01"] * 2
    scene = inner[2]
    assert scene["$type"] == "questSceneNodeDefinition"
    assert scene["sceneFile"]["DepotPath"]["$value"] == (
        "base\\open_world\\vendors\\watson\\little_china\\"
        "wat_lch_clothingshop_01\\wat_lch_clothingshop_01.scene"
    )
    assert scene["sceneLocation"]["nodeRef"]["$value"] == "#wat_sm_lch_clothingshop_01"
    close = inner[4]["condition"]["Data"]["type"]["Data"]
    far = inner[7]["condition"]["Data"]["type"]["Data"]
    assert close["comparisonType"] == "Less" and close["distanceDefinition2"]["Data"]["distanceValue"] == 12
    assert far["factName"] == PREFIX + "Far" and far["value"] == 1
    rearm = graph[8]["condition"]["Data"]["type"]["Data"]
    assert rearm["factName"] == PREFIX + "Far" and rearm["value"] == 0
    assert {node["type"]["Data"]["factName"] for node in inner.values()
            if node["$type"] == "questFactsDBManagerNodeDefinition"} == {
        PREFIX + "SpawnActionOut", PREFIX + "ActorDistanceGate",
        PREFIX + "ExitWatchArmed", PREFIX + "DespawnActionOut"
    }
    assert all(node["$type"] != "questJournalNodeDefinition" for node in graph.values())
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("registerForEvent = function() end")
    addon = (ROOT / "diagnostics/PTFR_B0_LCH_Clothing_Vendor/init.lua").read_text(encoding="utf-8")
    module = lua.execute(addon)
    assert all(module[key] is not None for key in ("Inspect", "Enable", "Observe", "Stop"))
    print("Little China clothing: one spawn-set entry, vanilla trade scene, 50m/12m lifecycle")
    print("Static checks PASS. V2 menu worked but departure failed; V3 live result is pending.")


if __name__ == "__main__":
    main()
