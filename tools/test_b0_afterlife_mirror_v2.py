"""Static scope checks for the Afterlife mirror plane-distance v2 experiment."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from report_scene_route import scalars  # noqa: E402
from test_b0_h10_mirror_prompt import read  # noqa: E402

VAL = ROOT / "research/b0_afterlife_mirror/validation_v2"
PREFIX = "PTFRB0ALM_"


def graph_nodes(doc: dict) -> dict[int, dict]:
    return {item["Data"]["id"]: item["Data"]
            for item in doc["Data"]["RootChunk"]["graph"]["Data"]["nodes"]}


def scene_nodes(doc: dict) -> dict[int, dict]:
    return {item["Data"]["nodeId"]["id"]: item["Data"]
            for item in doc["Data"]["RootChunk"]["sceneGraph"]["Data"]["graph"]}


def main() -> None:
    manifest = read(VAL / "build_manifest.json")
    assert manifest["status"] == "EXPERIMENTAL_V2_PLANE_DISTANCE_NOT_INSTALLED"
    assert manifest["vanilla_replacements"] == []
    assert manifest["resources"] == [
        "towercontinued\\b0_afterlife_mirror\\afterlife_mirror_owner.questphase",
        "towercontinued\\b0_afterlife_mirror\\afterlife_mirror_scene.scene",
    ]
    archive = ROOT / "build/B0_Afterlife_Mirror_V2" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    graph = graph_nodes(read(VAL / "afterlife_mirror_owner.questphase.json"))
    assert set(graph) == set(range(10))
    assert all(node["type"]["Data"]["factName"].startswith(PREFIX)
               for node in graph.values() if node["$type"] == "questFactsDBManagerNodeDefinition")
    guard = graph[2]["condition"]
    assert set(str(v) for v in scalars(guard, "factName")) == set(manifest["guard_facts"])
    assert "questTriggerCondition" not in set(str(v) for v in scalars(guard, "$type"))
    assert "questDistanceCondition" in set(str(v) for v in scalars(guard, "$type"))
    assert "#mirror_plane_afterlife" in set(str(v) for v in scalars(guard, "$value"))
    assert 4 in list(scalars(guard, "distanceValue"))
    assert graph[4]["sceneFile"]["DepotPath"]["$value"] == manifest["scene"]
    delay = graph[7]["condition"]["Data"]["type"]["Data"]
    assert delay["$type"] == "questRealtimeDelay_ConditionType"
    assert delay["seconds"] == 1

    source = read(ROOT / "research/b0_afterlife_mirror/extracted/json/base/open_world/scenes/mirrors/mirror_scene_afterlife.scene.json")
    modified = read(VAL / "afterlife_mirror_scene.scene.json")
    old_nodes, new_nodes = scene_nodes(source), scene_nodes(modified)
    assert set(old_nodes) == set(new_nodes)
    assert {i: n["$type"] for i, n in old_nodes.items()} == {i: n["$type"] for i, n in new_nodes.items()}
    assert len(source["Data"]["RootChunk"]["actors"]) == len(modified["Data"]["RootChunk"]["actors"]) == 2
    assert source["Data"]["RootChunk"]["props"] == modified["Data"]["RootChunk"]["props"] == []
    old_exit = old_nodes[4398]["questNode"]["Data"]["condition"]["Data"]
    new_exit = new_nodes[4398]["questNode"]["Data"]["condition"]["Data"]
    assert old_exit["$type"] == "questTriggerCondition" and old_exit["type"] == "IsOutside"
    assert new_exit["$type"] == "questDistanceCondition"
    cmp = new_exit["type"]["Data"]
    assert cmp["comparisonType"] == "Greater"
    assert cmp["distanceDefinition2"]["Data"]["distanceValue"] == 4
    assert "#mirror_plane_afterlife" in set(str(v) for v in scalars(cmp, "$value"))
    print("Afterlife v2: one mod-owned scene exit uses the physical mirror plane; native route retained")
    print("Static checks PASS. Live scene entry, prompt, exit and reload remain unproven.")


if __name__ == "__main__":
    main()
