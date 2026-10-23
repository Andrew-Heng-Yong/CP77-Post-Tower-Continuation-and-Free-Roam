"""Static scope/safety checks for five manually gated post-Tower H10 probes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from report_scene_route import scalars, unwrap
from test_b0_h10_mirror_prompt import nodes, reachable, read, targets


ROOT = Path(__file__).resolve().parent.parent
VAL = ROOT / "research/b0_h10_all_interactions/validation"
KINDS = {
    "mirror": {"code": "M", "entry": "in_mirror", "choices": {220, 226}, "facts": {"mq000_mirror_blinders_closed"}, "writers": {"mq000_mirror_blinders_closed"}, "pairs": [(224, 497), (609, 614), (476, 484), (1077, 1080)]},
    "shower": {"code": "H", "entry": "in_shower", "choices": {47, 193}, "facts": {"v_using_apartment_shower"}, "writers": {"v_using_apartment_shower"}, "pairs": [(1064, 1067), (1234, 1236), (170, 207)]},
    "sleep": {"code": "B", "entry": "in_bed", "choices": {6}, "facts": {"v_using_apartment_bed"}, "writers": {"v_using_apartment_bed"}, "pairs": [(1071, 1074), (1239, 1241)]},
    "sofa": {"code": "S", "entry": "in", "choices": {10, 328, 658}, "facts": {"tv_apartment", "tv_on"}, "writers": {"tv_apartment"}, "pairs": [(36, 55), (1059, 1061), (1228, 1230), (917, 943)]},
    "wardrobe": {"code": "W", "entry": "in", "choices": {1339}, "facts": set(), "writers": set(), "pairs": [(1339, 1341), (1345, 1347)]},
}


def check_scene(kind: str, spec: dict) -> None:
    doc = read(VAL / f"{kind}.scene.json")
    root = doc["Data"]["RootChunk"]
    graph = nodes(doc)
    entries = {unwrap(item["name"]): item["nodeId"]["id"] for item in root["entryPoints"]}
    visited = reachable(graph, entries[spec["entry"]])
    assert 2 in visited, f"{kind}: no outside end"
    choices = {node_id for node_id in visited if graph[node_id]["$type"] == "scnChoiceNode"}
    assert choices == spec["choices"], (kind, choices)
    facts = {str(value) for node_id in visited for value in scalars(graph[node_id], "factName")}
    assert facts == spec["facts"], (kind, facts)
    writers = {
        graph[node_id]["questNode"]["Data"]["type"]["Data"]["factName"]
        for node_id in visited
        if graph[node_id].get("questNode", {}).get("Data", {}).get("$type") == "questFactsDBManagerNodeDefinition"
    }
    assert writers == spec["writers"], (kind, writers)
    for before, after in spec["pairs"]:
        assert {before, after}.issubset(visited), (kind, before, after)
    props = {prop["propName"]: bool(prop["spawnDespawnParams"]["spawnOnStart"]) for prop in root["props"]}
    assert props == {"shower": kind == "shower", "tv_lookat": kind == "sofa"}, (kind, props)
    assert all(not actor["spawnDespawnParams"]["spawnOnStart"] for actor in root["actors"])
    assert targets(graph[1112]) == [1104] if kind == "mirror" else targets(graph[1112]) == [2]
    entry_node = graph[entries[spec["entry"]]]
    exit_watch_edges = [
        edge
        for socket in entry_node["outputSockets"]
        for edge in socket["destinations"]
        if edge["nodeId"]["id"] == 1112
    ]
    assert len(exit_watch_edges) == 1 and exit_watch_edges[0]["isockStamp"]["ordinal"] == 1, (kind, "outside monitor must enter quest In socket")
    exit_target = 1104 if kind == "mirror" else 2
    exit_edges = [
        edge
        for socket in graph[1112]["outputSockets"]
        for edge in socket["destinations"]
        if edge["nodeId"]["id"] == exit_target
    ]
    expected_exit_ordinal = 1 if kind == "mirror" else 0
    assert len(exit_edges) == 1 and exit_edges[0]["isockStamp"]["ordinal"] == expected_exit_ordinal, (kind, "outside monitor exit socket")
    if kind in {"sofa", "sleep"}:
        choice = graph[328 if kind == "sofa" else 6]
        assert choice["options"][0]["questCondition"] is None
    if kind == "shower":
        assert not {1163, 1165, 1167, 1173, 1404, 1407, 172, 183, 175}.intersection(visited)
        assert next(edge for edge in graph[51]["outputSockets"][0]["destinations"] if edge["nodeId"]["id"] == 193)["isockStamp"]["ordinal"] == 0
    if kind == "sleep":
        assert not {1591, 1469, 1480, 1628}.intersection(visited)
        assert next(edge for edge in graph[1353]["outputSockets"][0]["destinations"] if edge["nodeId"]["id"] == 22)["isockStamp"]["ordinal"] == 0
    if kind == "wardrobe":
        assert 1428 not in visited
    print(f"{kind}: {len(visited)} reachable nodes; {len(choices)} choices; only allowed facts")


def check_gate(kind: str, spec: dict, expected_guard: dict) -> None:
    doc = read(VAL / f"{kind}_gate.questphase.json")
    handles: dict[str, dict] = {}
    def collect_handles(value: object) -> None:
        if isinstance(value, dict):
            if "HandleId" in value and "Data" in value:
                handles[str(value["HandleId"])] = value["Data"]
            for child in value.values():
                collect_handles(child)
        elif isinstance(value, list):
            for child in value:
                collect_handles(child)
    collect_handles(doc)
    graph = {
        node["Data"]["id"]: node["Data"]
        for node in doc["Data"]["RootChunk"]["graph"]["Data"]["nodes"]
    }
    assert set(graph) == set(range(12)), (kind, set(graph))
    prefix = f"PTFRB0H10I_{spec['code']}_"
    writers = [
        node["type"]["Data"]["factName"]
        for node in graph.values()
        if node["$type"] == "questFactsDBManagerNodeDefinition"
    ]
    assert all(name.startswith(prefix) for name in writers), (kind, writers)
    assert graph[2]["condition"]["Data"]["type"]["Data"]["factName"] == prefix + "Request"
    assert graph[7]["sceneFile"]["DepotPath"]["$value"] == f"towercontinued\\b0_h10_interactions\\{kind}.scene"
    socket_names = {
        unwrap((socket.get("Data") or handles[str(socket["HandleRefId"])])["name"]):
            (socket.get("Data") or handles[str(socket["HandleRefId"])]).get("connections", [])
        for socket in graph[7]["sockets"]
    }
    assert socket_names[spec["entry"]], (kind, "scene entry not connected")
    assert socket_names["out"] and socket_names["Default INT"]
    guard_facts = set(str(value) for value in scalars(graph[4]["condition"], "factName"))
    assert guard_facts == set(expected_guard), (kind, guard_facts ^ set(expected_guard))
    print(f"{kind} gate: manual request, Tower/H10 guard, unique mod-owned writes")


def main() -> None:
    manifest = read(VAL / "build_manifest.json")
    assert manifest["status"] == "EXPERIMENTAL_MANUAL_DISPOSABLE_ONLY"
    assert manifest["vanilla_replacements"] == []
    archive = ROOT / "build/B0_H10_AllInteractions" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    assert len(manifest["resources"]) == 10
    xl = (ROOT / "archive/b0_h10_all_interactions/TowerContinued_B0_H10_Interactions.archive.xl").read_text(encoding="utf-8")
    assert xl.count("- path:") == 5
    for kind, spec in KINDS.items():
        assert f"towercontinued\\b0_h10_interactions\\{kind}_gate.questphase" in xl
        check_scene(kind, spec)
        check_gate(kind, spec, manifest["guard_facts"])
    print("Static checks PASS. Active-action interruption/forced-exit cleanup remains UNPROVEN.")


if __name__ == "__main__":
    main()
