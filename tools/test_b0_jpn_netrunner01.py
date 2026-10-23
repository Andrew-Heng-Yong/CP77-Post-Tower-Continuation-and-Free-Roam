"""Static executable-edge audit of the one-site Japantown netrunner owner."""

from __future__ import annotations

import hashlib
from pathlib import Path

from audit_wilson_vendor_owner import graph_edges, walk
from report_scene_route import scalars
from test_b0_h10_mirror_prompt import read

ROOT = Path(__file__).resolve().parent.parent
VAL = ROOT / "research/b0_jpn_netrunner01/validation"


def nodes(graph: dict) -> dict[int, dict]:
    return {item["Data"]["id"]: item["Data"] for item in graph["nodes"]}


def edges(graph: dict, handles: dict, label: str) -> set[tuple]:
    return {(e["source_node_id"], e["source_socket"], e["destination_node_id"], e["destination_socket"])
            for e in graph_edges(graph, label, handles)}


def main() -> None:
    manifest = read(VAL / "build_manifest.json")
    prefix = "PTFRB0JPNNET1_"
    depot = r"towercontinued\b0_jpn_netrunner01\owner.questphase"
    assert manifest["status"] == "STATIC_EXPERIMENTAL_NOT_INSTALLED"
    assert manifest["resources"] == [depot]
    assert manifest["vanilla_replacements"] == []
    archive = ROOT / "build/B0_JpnNetrunner01" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    xl = (ROOT / "archive/b0_jpn_netrunner01/TowerContinued_B0_JpnNetrunner01.archive.xl").read_text()
    assert xl.count("- path:") == 1 and xl.count(r"parent: ep1\quest\ep1.quest") == 1
    assert depot in xl
    assert {"q307_done", "q307_2079", "q307_main_game_killed", "q000_done",
            "wbr_jpn_netrun_01_default_on", prefix + "Enabled"} <= set(manifest["guard_facts"])
    exported = read(VAL / "owner.questphase.json")["Data"]["RootChunk"]
    outer = nodes(exported["graph"]["Data"])
    assert set(outer) == set(range(9))
    assert outer[2]["$type"] == "questPauseConditionNodeDefinition"
    assert set(map(str, scalars(outer[2]["condition"], "factName"))) == set(manifest["guard_facts"])
    near = outer[3]["condition"]["Data"]["type"]["Data"]
    assert near["comparisonType"] == "Less"
    assert near["distanceDefinition2"]["Data"]["distanceValue"] == 50
    inner = nodes(outer[5]["phaseGraph"]["Data"])
    assert len(inner) == 11 and {5, 6, 9, 18, 19, 20, 21, 100, 101, 102, 103} == set(inner)
    assert inner[18]["sceneFile"]["DepotPath"]["$value"] == manifest["scene"]
    assert inner[18]["sceneLocation"]["nodeRef"]["$value"] == manifest["scene_marker"]
    for node_id, action in ((19, "Activate"), (20, "Deactivate")):
        actions = inner[node_id]["actions"]
        assert len(actions) == 1
        owner = actions[0]["type"]["Data"]
        assert owner["action"] == action
        assert owner["reference"]["$value"] == "#wbr_jpn_netrun_01"
        assert owner["entryName"]["$value"] == "wbr_jpn_netrun_01"
        assert owner["phaseName"]["$value"] == "None"
    assert inner[21]["condition"]["Data"]["type"]["Data"]["factName"] == prefix + "Far"
    assert outer[8]["condition"]["Data"]["type"]["Data"]["factName"] == prefix + "Far"
    handles = {str(v["HandleId"]): v["Data"] for v in walk(exported)
               if "HandleId" in v and "Data" in v}
    assert edges(exported["graph"]["Data"], handles, "jpn-net-outer") == {
        (0, "Out", 1, "In"), (1, "Out", 2, "In"), (2, "Out", 3, "In"),
        (3, "Out", 4, "In"), (4, "Out", 5, "In1"), (5, "Out1", 6, "In"),
        (6, "Out", 7, "In"), (7, "Out", 8, "In"), (8, "Out", 2, "In"),
    }
    assert edges(outer[5]["phaseGraph"]["Data"], handles, "jpn-net-inner") == {
        (5, "Out", 19, "In"), (5, "Out", 102, "In"), (102, "Out", 21, "In"),
        (19, "Out", 100, "In"), (100, "Out", 9, "In"), (9, "Out", 101, "In"),
        (101, "Out", 18, "wbr_jpn_netrun_01_start"), (21, "Out", 20, "In"),
        (20, "Out", 103, "In"), (103, "Out", 6, "In"),
    }
    print("Japantown netrunner 01: guard, vanilla actor/scene, 50m/12m, exit/rearm PASS")
    print("One-resource archive and registry PASS; live behavior untested")


if __name__ == "__main__":
    main()
