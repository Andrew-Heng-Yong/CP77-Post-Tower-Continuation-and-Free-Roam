"""Static audit of the opt-in Badlands junk/melee native owner pair."""

from __future__ import annotations

import hashlib
from pathlib import Path

from audit_wilson_vendor_owner import graph_edges, walk
from report_scene_route import scalars
from test_b0_h10_mirror_prompt import read

ROOT = Path(__file__).resolve().parent.parent
VAL = ROOT / "research/b0_junk_melee_pair/validation"
SHOPS = (
    ("junk", "PTFRB0SE5J_", "bls_ina_se5_junkshop_01", 16, 17, 18, 19),
    ("melee", "PTFRB0SE5M_", "bls_ina_se5_melee_01", 17, 18, 19, 20),
)


def nodes(graph: dict) -> dict[int, dict]:
    return {item["Data"]["id"]: item["Data"] for item in graph["nodes"]}


def edges(graph: dict, handles: dict, label: str) -> set[tuple]:
    return {
        (e["source_node_id"], e["source_socket"], e["destination_node_id"], e["destination_socket"])
        for e in graph_edges(graph, label, handles)
    }


def main() -> None:
    manifest = read(VAL / "build_manifest.json")
    assert manifest["status"] == "STATIC_EXPERIMENTAL_NOT_INSTALLED"
    assert manifest["vanilla_replacements"] == []
    depots = [f"towercontinued\\b0_junk_melee_pair\\{name}_owner.questphase" for name, *_ in SHOPS]
    assert set(manifest["resources"]) == set(depots)
    assert set(manifest["enable_facts"]) == {prefix + "Enabled" for _, prefix, *_ in SHOPS}
    archive = ROOT / "build/B0_JunkMeleePair" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    xl = (ROOT / "archive/b0_junk_melee_pair/TowerContinued_B0_JunkMeleePair.archive.xl").read_text()
    assert xl.count("- path:") == 2 and xl.count("parent: ep1\\quest\\ep1.quest") == 2
    assert all(depot in xl for depot in depots)

    for name, prefix, vendor_id, scene_id, spawn_id, despawn_id, far_id in SHOPS:
        exported = read(VAL / f"{name}_owner.questphase.json")["Data"]["RootChunk"]
        outer = nodes(exported["graph"]["Data"])
        assert set(outer) == set(range(9))
        guard = outer[2]
        assert guard["$type"] == "questPauseConditionNodeDefinition"
        assert set(map(str, scalars(guard["condition"], "factName"))) == set(manifest["guard_facts"][name])
        assert set(manifest["guard_facts"][name]) >= {
            "q307_done", "q307_2079", "q307_main_game_killed", "q000_done",
            vendor_id + "_default_on", prefix + "Enabled",
        }
        near = outer[3]["condition"]["Data"]["type"]["Data"]
        assert near["comparisonType"] == "Less"
        assert near["distanceDefinition2"]["Data"]["distanceValue"] == 50
        inner = nodes(outer[5]["phaseGraph"]["Data"])
        assert set(inner) == {0, 1, 3, scene_id, spawn_id, despawn_id, far_id, 30, 31, 32, 33}
        handles = {str(v["HandleId"]): v["Data"] for v in walk(exported)
                   if "HandleId" in v and "Data" in v}
        assert edges(exported["graph"]["Data"], handles, name + "-outer") == {
            (0, "Out", 1, "In"), (1, "Out", 2, "In"), (2, "Out", 3, "In"),
            (3, "Out", 4, "In"), (4, "Out", 5, "In1"), (5, "Out1", 6, "In"),
            (6, "Out", 7, "In"), (7, "Out", 8, "In"), (8, "Out", 2, "In"),
        }
        assert edges(outer[5]["phaseGraph"]["Data"], handles, name + "-inner") == {
            (0, "Out", spawn_id, "In"), (0, "Out", 32, "In"),
            (32, "Out", far_id, "In"), (spawn_id, "Out", 30, "In"),
            (30, "Out", 3, "In"), (3, "Out", 31, "In"),
            (31, "Out", scene_id, vendor_id),
            (far_id, "Out", despawn_id, "In"), (despawn_id, "Out", 33, "In"),
            (33, "Out", 1, "In"),
        }
        for node_id, action in ((spawn_id, "Activate"), (despawn_id, "Deactivate")):
            entries = inner[node_id]["actions"]
            assert len(entries) == 1
            owner = entries[0]["type"]["Data"]
            assert owner["$type"] == "questSpawnSet_NodeType"
            assert owner["action"] == action
            assert owner["reference"]["$value"] == "#" + vendor_id
            assert owner["entryName"]["$value"] == vendor_id
            assert owner["phaseName"]["$value"] == "default"
        scene = inner[scene_id]
        assert scene["$type"] == "questSceneNodeDefinition"
        assert scene["sceneFile"]["DepotPath"]["$value"].endswith(vendor_id + "\\" + vendor_id + ".scene")
        assert scene["sceneLocation"]["nodeRef"]["$value"] == "#bls_sm_ina_se5_" + ("junkshop_01" if name == "junk" else "melee_01")
        close = inner[3]["condition"]["Data"]["type"]["Data"]
        far = inner[far_id]["condition"]["Data"]["type"]["Data"]
        assert close["comparisonType"] == "Less"
        assert close["distanceDefinition2"]["Data"]["distanceValue"] == 12
        assert far["factName"] == prefix + "Far" and far["value"] == 1
        rearm = outer[8]["condition"]["Data"]["type"]["Data"]
        assert rearm["factName"] == prefix + "Far" and rearm["value"] == 0
        print(f"{name}: native actor, scene, 50 m / 12 m gate, departure/rearm wiring PASS")
    print("Archive, registry, guard and two-resource scope PASS; in-game behavior untested")


if __name__ == "__main__":
    main()
