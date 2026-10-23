"""Static scope and wiring checks for the opt-in rearming H10 owner."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime  # noqa: E402

from report_scene_route import scalars, unwrap
from audit_h10_mirror_entry_paths import path as executable_path
from test_b0_h10_mirror_prompt import nodes, read, reachable, targets


VAL = ROOT / "research/b0_h10_persistent/validation"
PREFIX = "PTFRB0H10P_"


def check_scene() -> None:
    scene = read(VAL / "h10_interactions.scene.json")
    root = scene["Data"]["RootChunk"]
    graph = nodes(scene)
    entries = {unwrap(item["name"]): item["nodeId"]["id"] for item in root["entryPoints"]}
    assert entries["in"] == 1
    assert targets(graph[1]) == [215, 1112]
    outside_edge = next(
        edge for edge in graph[1]["outputSockets"][0]["destinations"]
        if edge["nodeId"]["id"] == 1112
    )
    assert outside_edge["isockStamp"]["ordinal"] == 1
    assert targets(graph[1112]) == [2]
    assert graph[1112]["outputSockets"][0]["destinations"][0]["isockStamp"]["ordinal"] == 0
    assert targets(graph[215]) == [6, 47, 220, 1339, 1371]
    assert targets(graph[242]) == [2], "Mirror Leave must restart the native owner"
    assert graph[242]["outputSockets"][0]["destinations"][0]["isockStamp"]["ordinal"] == 0

    visited = reachable(graph, entries["in"])
    required = {2, 6, 10, 47, 193, 220, 226, 242, 328, 658, 1339,
                36, 55, 51, 202, 22, 1341, 1345, 1347,
                1125, 1246, 1250, 1266, 1329, 1204, 1206, 1208,
                1210, 1212, 1333, 1335, 1337}
    assert required <= visited, required - visited
    forbidden = {1084, 1325, 1428, 1591, 1163, 1165, 1167, 1173,
                 1404, 1407, 172, 183, 175, 1469, 1480, 1628, 1114, 1602}
    assert not forbidden & visited, forbidden & visited
    choices = {node_id for node_id in visited if graph[node_id]["$type"] == "scnChoiceNode"}
    assert choices == {6, 10, 47, 193, 220, 226, 328, 658, 1125, 1246, 1339}, choices
    assert targets(graph[226]) == [228, 397, 1125, 1246]
    assert targets(graph[222])[:2] == [1246, 1270]
    assert executable_path(graph, 220, 1246, attachments=False) == [220, 222, 1246]
    assert executable_path(graph, 220, 1125, attachments=False) == [220, 222, 1246, 1125]
    assert executable_path(graph, 220, 226, attachments=False) == [220, 222, 1270, 226]
    assert all(edge["isockStamp"]["name"] == 0 and edge["isockStamp"]["ordinal"] == 0
               for edge in graph[222]["outputSockets"][0]["destinations"])
    assert targets(graph[1246]) == [1250, 1125]
    assert targets(graph[1250]) == [1329], "Hairdresser must bypass old mq000 history"
    assert targets(graph[1329]) == [1266]
    assert all(option["questCondition"] is None for option in graph[1125]["options"][:5])
    assert len(graph[1125]["options"]) == 6
    menu = graph[1266]["questNode"]["Data"]
    assert menu["$type"] == "questUIManagerNodeDefinition"
    scenario = menu["type"]["Data"]
    assert scenario["startScenarioName"]["$value"] == "MenuScenario_CharacterCustomizationMirror"
    assert scenario["userData"]["Data"]["editMode"] == "HairDresser"
    facts = {str(value) for node_id in visited for value in scalars(graph[node_id], "factName")}
    assert facts == {"mq000_mirror_blinders_closed", "tv_apartment", "tv_on",
                     "v_using_apartment_bed", "v_using_apartment_shower"}, facts
    writers = {
        graph[node_id]["questNode"]["Data"]["type"]["Data"]["factName"]
        for node_id in visited
        if graph[node_id].get("questNode", {}).get("Data", {}).get("$type")
        == "questFactsDBManagerNodeDefinition"
    }
    assert writers == {"mq000_mirror_blinders_closed", "tv_apartment",
                       "v_using_apartment_bed", "v_using_apartment_shower"}, writers
    for before, after in [(224, 497), (609, 614), (476, 484), (1077, 1080),
                          (1064, 1067), (1234, 1236), (170, 207),
                          (1071, 1074), (1239, 1241), (36, 55),
                          (1059, 1061), (1228, 1230), (917, 943),
                          (1339, 1341), (1345, 1347)]:
        assert {before, after} <= visited, (before, after)
    assert graph[6]["options"][0]["questCondition"] is None
    assert graph[328]["options"][0]["questCondition"] is None
    assert next(edge for edge in graph[51]["outputSockets"][0]["destinations"]
                if edge["nodeId"]["id"] == 193)["isockStamp"]["ordinal"] == 0
    assert next(edge for edge in graph[1353]["outputSockets"][0]["destinations"]
                if edge["nodeId"]["id"] == 22)["isockStamp"]["ordinal"] == 0
    props = {item["propName"]: item["spawnDespawnParams"]["spawnOnStart"]
             for item in root["props"]}
    assert props == {"shower": True, "tv_lookat": True}, props
    assert all(not actor["spawnDespawnParams"]["spawnOnStart"] for actor in root["actors"])
    print(f"H10 scene: {len(visited)} reachable nodes; five choice families including full mirror options; no reachable story facts")


def check_gate(expected_guard: dict) -> None:
    doc = read(VAL / "h10_owner.questphase.json")
    handles: dict[str, dict] = {}

    def collect(value: object) -> None:
        if isinstance(value, dict):
            if "HandleId" in value and "Data" in value:
                handles[str(value["HandleId"])] = value["Data"]
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(doc)
    graph = {node["Data"]["id"]: node["Data"]
             for node in doc["Data"]["RootChunk"]["graph"]["Data"]["nodes"]}
    assert set(graph) == set(range(10)), set(graph)
    writers = [node["type"]["Data"]["factName"] for node in graph.values()
               if node["$type"] == "questFactsDBManagerNodeDefinition"]
    assert writers and all(name.startswith(PREFIX) for name in writers), writers
    assert graph[2]["$type"] == "questPauseConditionNodeDefinition"
    guard_facts = set(str(value) for value in scalars(graph[2]["condition"], "factName"))
    assert guard_facts == set(expected_guard), guard_facts ^ set(expected_guard)
    condition_types = set(str(value) for value in scalars(graph[2]["condition"], "$type"))
    assert {"questTriggerCondition", "questUICondition"} <= condition_types
    assert graph[4]["sceneFile"]["DepotPath"]["$value"] == (
        "towercontinued\\b0_h10_persistent\\h10_interactions.scene")
    sockets = {
        unwrap((socket.get("Data") or handles[str(socket["HandleRefId"])])["name"]):
            (socket.get("Data") or handles[str(socket["HandleRefId"])]).get("connections", [])
        for socket in graph[4]["sockets"]
    }
    assert sockets["in"] and sockets["out"] and sockets["Default INT"]
    assert graph[7]["condition"]["Data"]["$type"] == "questTimeCondition"
    delay = graph[7]["condition"]["Data"]["type"]["Data"]
    assert delay["$type"] == "questRealtimeDelay_ConditionType" and delay["seconds"] == 1
    print("Native owner: opt-in Tower/H10 guard, one scene, one-second rearm, interruption stop")


def main() -> None:
    manifest = read(VAL / "build_manifest.json")
    assert manifest["status"] == "EXPERIMENTAL_OPT_IN_REARM_DISPOSABLE_ONLY"
    assert manifest["vanilla_replacements"] == []
    archive = ROOT / "build/B0_H10_Persistent" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    assert len(manifest["resources"]) == 2
    xl = (ROOT / "archive/b0_h10_persistent/TowerContinued_B0_H10_Persistent.archive.xl").read_text(encoding="utf-8")
    assert xl.count("- path:") == 1
    assert "towercontinued\\b0_h10_persistent\\h10_owner.questphase" in xl
    check_scene()
    check_gate(manifest["guard_facts"])
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("registerForEvent = function() end")
    addon = (ROOT / "diagnostics/PTFR_B0_H10_Persistent/init.lua").read_text(encoding="utf-8")
    module = lua.execute(addon)
    assert module["Inspect"] is not None and module["Enable"] is not None and module["Observe"] is not None
    print("Static checks PASS. Expanded mirror actions and forced-action cleanup remain live-unproven.")


if __name__ == "__main__":
    main()
