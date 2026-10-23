"""Static scope and wiring checks for the one-site Afterlife mirror owner."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime  # noqa: E402

from report_scene_route import scalars, unwrap
from test_b0_h10_mirror_prompt import read


VAL = ROOT / "research/b0_afterlife_mirror/validation"
PREFIX = "PTFRB0ALM_"


def main() -> None:
    manifest = read(VAL / "build_manifest.json")
    assert manifest["status"] == "EXPERIMENTAL_OPT_IN_SINGLE_SITE_DISPOSABLE_ONLY"
    assert manifest["vanilla_replacements"] == []
    assert manifest["resources"] == [
        "towercontinued\\b0_afterlife_mirror\\afterlife_mirror_owner.questphase"
    ]
    archive = ROOT / "build/B0_Afterlife_Mirror" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    xl = (ROOT / "archive/b0_afterlife_mirror/TowerContinued_B0_Afterlife_Mirror.archive.xl").read_text(encoding="utf-8")
    assert xl.count("- path:") == 1
    assert manifest["resources"][0] in xl
    assert "parent: ep1\\quest\\ep1.quest" in xl

    doc = read(VAL / "afterlife_mirror_owner.questphase.json")
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
    graph = {item["Data"]["id"]: item["Data"]
             for item in doc["Data"]["RootChunk"]["graph"]["Data"]["nodes"]}
    assert set(graph) == set(range(10)), set(graph)
    writers = [node["type"]["Data"]["factName"] for node in graph.values()
               if node["$type"] == "questFactsDBManagerNodeDefinition"]
    assert writers and all(name.startswith(PREFIX) for name in writers), writers
    wait = graph[2]
    assert wait["$type"] == "questPauseConditionNodeDefinition"
    facts = set(str(value) for value in scalars(wait["condition"], "factName"))
    assert facts == set(manifest["guard_facts"]), facts ^ set(manifest["guard_facts"])
    condition_types = set(str(value) for value in scalars(wait["condition"], "$type"))
    assert {"questTriggerCondition", "questCharacterCondition", "questFactsDBCondition"} <= condition_types
    assert "#mirror_tr_afterlife" in set(str(value) for value in scalars(wait["condition"], "$value"))
    combat = [value for value in scalars(wait["condition"], "inverted")]
    assert combat == [1], combat
    scene = graph[4]
    assert scene["$type"] == "questSceneNodeDefinition"
    assert scene["sceneFile"]["DepotPath"]["$value"] == manifest["scene"]
    assert scene["sceneLocation"]["nodeRef"]["$value"] == "#mirror_sm_scene_afterlife"
    sockets = {
        unwrap((socket.get("Data") or handles[str(socket["HandleRefId"])])["name"]):
            (socket.get("Data") or handles[str(socket["HandleRefId"])]).get("connections", [])
        for socket in scene["sockets"]
    }
    assert sockets["mirror_interaction"] and sockets["mirror_interaction_out"]
    assert sockets["Default INT"] and not sockets["Default RET"]
    delay = graph[7]["condition"]["Data"]["type"]["Data"]
    assert delay["$type"] == "questRealtimeDelay_ConditionType"
    assert delay["seconds"] == 1 and delay["miliseconds"] == 0
    assert graph[8]["type"]["Data"]["factName"] == PREFIX + "Interrupted"
    print("Afterlife owner: single vanilla scene, Tower/local/combat guard, native rearm, interruption stop")

    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("registerForEvent = function() end")
    addon = (ROOT / "diagnostics/PTFR_B0_Afterlife_Mirror/init.lua").read_text(encoding="utf-8")
    module = lua.execute(addon)
    assert module["Inspect"] is not None and module["Enable"] is not None and module["Observe"] is not None
    print("Static checks PASS. Live trigger, prompt, exit and reload remain unproven.")


if __name__ == "__main__":
    main()
