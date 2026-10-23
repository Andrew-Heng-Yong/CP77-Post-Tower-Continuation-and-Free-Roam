"""Check the executable one-site Northside owner before installation."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
from audit_wilson_vendor_owner import graph_edges, walk
from report_scene_route import scalars
from test_b0_h10_mirror_prompt import read

VAL = ROOT / "research/b0_northside_gunsmith/validation"
PREFIX = "PTFRB0NIDG_"


def nodes(graph: dict) -> dict[int, dict]:
    return {item["Data"]["id"]: item["Data"] for item in graph["nodes"]}


def main() -> None:
    manifest = read(VAL / "build_manifest.json")
    depot = "towercontinued\\b0_northside_gunsmith\\vendor_owner.questphase"
    assert manifest["status"] == "STATIC_EXPERIMENTAL_NOT_INSTALLED"
    assert manifest["resources"] == [depot]
    assert manifest["vanilla_replacements"] == []
    assert manifest["enable_fact"] == PREFIX + "Enabled"
    archive = ROOT / "build/B0_Northside_Gunsmith" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    xl = (ROOT / "archive/b0_northside_gunsmith/TowerContinued_B0_Northside_Gunsmith.archive.xl").read_text(encoding="utf-8")
    assert xl.count("- path:") == 1 and depot in xl
    assert "parent: ep1\\quest\\ep1.quest" in xl

    exported = read(VAL / "vendor_owner.questphase.json")["Data"]["RootChunk"]
    outer = nodes(exported["graph"]["Data"])
    assert set(outer) == set(range(9))
    guard = outer[2]
    assert guard["$type"] == "questPauseConditionNodeDefinition"
    assert set(str(v) for v in scalars(guard["condition"], "factName")) == set(manifest["guard_facts"])
    assert set(manifest["guard_facts"]) >= {
        "q307_done", "q307_2079", "q307_main_game_killed",
        "wat_nid_gunsmith_01_default_on", PREFIX + "Enabled",
    }
    near = outer[3]["condition"]["Data"]["type"]["Data"]
    assert near["comparisonType"] == "Less"
    assert near["distanceDefinition2"]["Data"]["distanceValue"] == 50
    assert "#wat_nid_gunsmith_01_mp" in set(str(v) for v in scalars(near, "$value"))
    inner = nodes(outer[5]["phaseGraph"]["Data"])
    assert set(inner) == {0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11}
    handles = {str(v["HandleId"]): v["Data"] for v in walk(exported)
               if "HandleId" in v and "Data" in v}
    outer_edges = {(e["source_node_id"], e["source_socket"], e["destination_node_id"], e["destination_socket"])
                   for e in graph_edges(exported["graph"]["Data"], "northside-outer", handles)}
    assert outer_edges == {
        (0, "Out", 1, "In"), (1, "Out", 2, "In"), (2, "Out", 3, "In"),
        (3, "Out", 4, "In"), (4, "Out", 5, "In1"), (5, "Out1", 6, "In"),
        (6, "Out", 7, "In"), (7, "Out", 8, "In"), (8, "Out", 3, "In"),
    }, outer_edges
    inner_edges = {(e["source_node_id"], e["source_socket"], e["destination_node_id"], e["destination_socket"])
                   for e in graph_edges(outer[5]["phaseGraph"]["Data"], "northside-inner", handles)}
    assert inner_edges == {
        (0, "Out", 5, "In"), (0, "Out", 10, "In"), (10, "Out", 7, "In"),
        (5, "Out", 8, "In"), (8, "Out", 3, "In"),
        (3, "Out", 9, "In"), (9, "Out", 2, "wat_nid_gunsmith_01_start"),
        (7, "Out", 6, "In"), (6, "Out", 11, "In"), (11, "Out", 1, "In"),
    }, inner_edges
    for node_id, action in ((5, "Activate"), (6, "Deactivate")):
        entries = inner[node_id]["actions"]
        assert len(entries) == 1
        spawn = entries[0]["type"]["Data"]
        assert spawn["$type"] == "questSpawnSet_NodeType"
        assert spawn["action"] == action
        assert spawn["reference"]["$value"] == "#wat_nid_gunsmith_01"
        assert spawn["entryName"]["$value"] == "wat_nid_gunsmith_01"
        assert spawn["phaseName"]["$value"] == "default"
    scene = inner[2]
    assert scene["$type"] == "questSceneNodeDefinition"
    assert scene["sceneFile"]["DepotPath"]["$value"] == (
        "base\\open_world\\vendors\\watson\\northside\\"
        "wat_nid_gunsmith_01\\wat_nid_gunsmith_01.scene"
    )
    assert scene["sceneLocation"]["nodeRef"]["$value"] == "#wat_sm_nid_gunsmith_01"
    close = inner[3]["condition"]["Data"]["type"]["Data"]
    far = inner[7]["condition"]["Data"]["type"]["Data"]
    assert close["comparisonType"] == "Less"
    assert close["distanceDefinition2"]["Data"]["distanceValue"] == 12
    assert far["factName"] == PREFIX + "Far" and far["value"] == 1
    rearm = outer[8]["condition"]["Data"]["type"]["Data"]
    assert rearm["factName"] == PREFIX + "Far" and rearm["value"] == 0
    assert all(node["$type"] != "questJournalNodeDefinition" for node in outer.values())
    print("Northside: one native spawn and Trade scene, valid 50 m / 12 m owner and exit wiring")
    print("Quest/archive static checks PASS; live disposable result is documented separately")


if __name__ == "__main__":
    main()
