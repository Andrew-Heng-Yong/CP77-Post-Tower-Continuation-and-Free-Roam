"""Static executable-edge audit for eight opt-in regional service owners."""

from __future__ import annotations

import hashlib
from pathlib import Path

from audit_wilson_vendor_owner import graph_edges, walk
from report_scene_route import scalars
from test_b0_h10_mirror_prompt import read

ROOT = Path(__file__).resolve().parent.parent
VAL = ROOT / "research/b0_ripnet_eight/validation"


def nodes(graph: dict) -> dict[int, dict]:
    return {item["Data"]["id"]: item["Data"] for item in graph["nodes"]}


def edges(graph: dict, handles: dict, label: str) -> set[tuple]:
    return {(e["source_node_id"], e["source_socket"], e["destination_node_id"], e["destination_socket"])
            for e in graph_edges(graph, label, handles)}


def main() -> None:
    manifest = read(VAL / "build_manifest.json")
    sites = manifest["sites"]
    assert manifest["status"] == "STATIC_EXPERIMENTAL_NOT_INSTALLED"
    assert len(sites) == 8 and len(manifest["resources"]) == 8
    assert manifest["vanilla_replacements"] == []
    assert set(manifest["enable_facts"]) == {s["prefix"] + "Enabled" for s in sites}
    archive = ROOT / "build/B0_RipNetEight" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    xl = (ROOT / "archive/b0_ripnet_eight/TowerContinued_B0_RipNetEight.archive.xl").read_text()
    assert xl.count("- path:") == 8 and xl.count("parent: ep1\\quest\\ep1.quest") == 8
    assert set(manifest["resources"]) == {
        f"towercontinued\\b0_ripnet_eight\\{s['name']}_owner.questphase" for s in sites}
    assert all(path in xl for path in manifest["resources"])

    for site in sites:
        name, prefix = site["name"], site["prefix"]
        exported = read(VAL / f"{name}_owner.questphase.json")["Data"]["RootChunk"]
        outer = nodes(exported["graph"]["Data"])
        assert set(outer) == set(range(9))
        assert outer[2]["$type"] == "questPauseConditionNodeDefinition"
        assert set(map(str, scalars(outer[2]["condition"], "factName"))) == set(manifest["guard_facts"][name])
        assert set(manifest["guard_facts"][name]) >= {
            "q307_done", "q307_2079", "q307_main_game_killed", "q000_done",
            site["gate"], prefix + "Enabled",
        }
        near = outer[3]["condition"]["Data"]["type"]["Data"]
        assert near["comparisonType"] == "Less"
        assert near["distanceDefinition2"]["Data"]["distanceValue"] == site["outer_radius"]
        inner = nodes(outer[5]["phaseGraph"]["Data"])
        assert len(inner) == 11 and {100, 101, 102, 103} <= set(inner)
        inputs = [node_id for node_id, node in inner.items() if node["$type"] == "questInputNodeDefinition"]
        outputs = [node_id for node_id, node in inner.items() if node["$type"] == "questOutputNodeDefinition"]
        assert len(inputs) == len(outputs) == 1
        scene_id = [node_id for node_id, node in inner.items() if node["$type"] == "questSceneNodeDefinition"]
        assert len(scene_id) == 1
        scene_id = scene_id[0]
        spawn_id, despawn_id = site["spawn"]["node"], site["despawn"]["node"]
        far_id = [node_id for node_id, node in inner.items()
                  if node["$type"] == "questPauseConditionNodeDefinition" and
                  prefix + "Far" in set(map(str, scalars(node, "factName")))]
        assert len(far_id) == 1
        far_id = far_id[0]
        close_id = [node_id for node_id, node in inner.items()
                    if node["$type"] == "questPauseConditionNodeDefinition" and node_id != far_id]
        assert len(close_id) == 1
        close_id = close_id[0]
        close = inner[close_id]["condition"]["Data"]["type"]["Data"]
        assert close["comparisonType"] == "Less"
        assert close["distanceDefinition2"]["Data"]["distanceValue"] == site["close_radius"]
        far = inner[far_id]["condition"]["Data"]["type"]["Data"]
        assert far["factName"] == prefix + "Far" and far["value"] == 1
        rearm = outer[8]["condition"]["Data"]["type"]["Data"]
        assert rearm["factName"] == prefix + "Far" and rearm["value"] == 0
        scene = inner[scene_id]
        assert scene["sceneFile"]["DepotPath"]["$value"] == site["scene"]
        assert scene["sceneLocation"]["nodeRef"]["$value"] == site["marker"]
        for node_id, action, item in ((spawn_id, "Activate", site["spawn"]),
                                      (despawn_id, "Deactivate", site["despawn"])):
            actions = inner[node_id]["actions"]
            assert len(actions) == 1
            owner = actions[0]["type"]["Data"]
            assert owner["$type"] == "questSpawnSet_NodeType"
            assert owner["action"] == action
            assert owner["reference"]["$value"] == item["reference"]
            assert owner["entryName"]["$value"] == item["entry"]
            assert owner["phaseName"]["$value"] == item["phase"]
        handles = {str(v["HandleId"]): v["Data"] for v in walk(exported)
                   if "HandleId" in v and "Data" in v}
        assert edges(exported["graph"]["Data"], handles, name + "-outer") == {
            (0, "Out", 1, "In"), (1, "Out", 2, "In"), (2, "Out", 3, "In"),
            (3, "Out", 4, "In"), (4, "Out", 5, "In1"), (5, "Out1", 6, "In"),
            (6, "Out", 7, "In"), (7, "Out", 8, "In"), (8, "Out", 2, "In"),
        }
        assert edges(outer[5]["phaseGraph"]["Data"], handles, name + "-inner") == {
            (inputs[0], "Out", spawn_id, "In"), (inputs[0], "Out", 102, "In"),
            (102, "Out", far_id, "In"), (spawn_id, "Out", 100, "In"),
            (100, "Out", close_id, "In"), (close_id, "Out", 101, "In"),
            (101, "Out", scene_id, site["scene_socket"]),
            (far_id, "Out", despawn_id, "In"),
            (despawn_id, "Out", 103, "In"), (103, "Out", outputs[0], "In"),
        }
        print(f"{name}: guard, vanilla actor/scene, {site['outer_radius']} m / {site['close_radius']} m, exit/rearm PASS")
    print("Eight-resource archive, registry and executable graph scope PASS; live behavior untested")


if __name__ == "__main__":
    main()
