"""Static scope checks for the one-shot Afterlife scene-start diagnostic."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from report_scene_route import scalars  # noqa: E402
from test_b0_h10_mirror_prompt import read  # noqa: E402
from test_b0_afterlife_mirror_v2 import graph_nodes, scene_nodes  # noqa: E402

VAL = ROOT / "research/b0_afterlife_mirror/validation_v3"


def main() -> None:
    manifest = read(VAL / "build_manifest.json")
    assert manifest["status"] == "EXPERIMENTAL_V3_FACT_ONLY_ONESHOT_NOT_INSTALLED"
    assert manifest["vanilla_replacements"] == []
    assert manifest["resources"] == [
        "towercontinued\\b0_afterlife_mirror\\afterlife_mirror_owner.questphase",
        "towercontinued\\b0_afterlife_mirror\\afterlife_mirror_scene.scene",
    ]
    archive = ROOT / "build/B0_Afterlife_Mirror_V3" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    graph = graph_nodes(read(VAL / "afterlife_mirror_owner.questphase.json"))
    assert set(graph) == set(range(10))
    writers = [n["type"]["Data"]["factName"] for n in graph.values()
               if n["$type"] == "questFactsDBManagerNodeDefinition"]
    assert writers and all(name.startswith("PTFRB0ALM_") for name in writers)
    guard = graph[2]["condition"]
    assert set(str(v) for v in scalars(guard, "factName")) == set(manifest["guard_facts"])
    types = set(str(v) for v in scalars(guard, "$type"))
    assert "questFactsDBCondition" in types and "questCharacterCondition" in types
    assert "questDistanceCondition" not in types and "questTriggerCondition" not in types
    assert graph[4]["sceneFile"]["DepotPath"]["$value"] == manifest["scene"]
    assert graph[6]["type"]["Data"]["factName"] == "PTFRB0ALM_Completed"
    assert all(not socket["Data"]["connections"] for socket in graph[7]["sockets"])

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
    assert new_exit["$type"] == "questTimeCondition"
    delay = new_exit["type"]["Data"]
    assert delay["$type"] == "questRealtimeDelay_ConditionType"
    assert delay["seconds"] == 30 and delay["miliseconds"] == 0
    print("Afterlife v3: fact-only scene entry, unchanged actors/scene route, 30-second safety exit")
    print("Static checks PASS. This is a single-use diagnostic, not a lasting restoration.")


if __name__ == "__main__":
    main()
