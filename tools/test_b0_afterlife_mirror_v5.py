"""Static and mocked checks for CET-dev proximity + native Afterlife loop."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime  # noqa: E402
from report_scene_route import scalars  # noqa: E402
from test_b0_h10_mirror_prompt import read  # noqa: E402
from test_b0_afterlife_mirror_v2 import graph_nodes, scene_nodes  # noqa: E402

VAL = ROOT / "research/b0_afterlife_mirror/validation_v5"


def main() -> None:
    manifest = read(VAL / "build_manifest.json")
    assert manifest["status"] == "EXPERIMENTAL_V5_CET_PROXIMITY_NOT_INSTALLED"
    assert manifest["vanilla_replacements"] == []
    assert manifest["resources"] == [
        "towercontinued\\b0_afterlife_mirror\\afterlife_mirror_owner.questphase",
        "towercontinued\\b0_afterlife_mirror\\afterlife_mirror_scene.scene",
    ]
    archive = ROOT / "build/B0_Afterlife_Mirror_V5" / manifest["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest["sha256"]
    graph = graph_nodes(read(VAL / "afterlife_mirror_owner.questphase.json"))
    assert set(graph) == set(range(10))
    writers = [n["type"]["Data"]["factName"] for n in graph.values()
               if n["$type"] == "questFactsDBManagerNodeDefinition"]
    assert writers and all(name.startswith("PTFRB0ALM_") for name in writers)
    guard = graph[2]["condition"]
    assert set(str(v) for v in scalars(guard, "factName")) == (
        set(manifest["guard_facts"]) | {"PTFRB0ALM_Near"}
    )
    assert "questDistanceCondition" not in set(str(v) for v in scalars(guard, "$type"))
    assert "questTriggerCondition" not in set(str(v) for v in scalars(guard, "$type"))
    assert graph[4]["sceneFile"]["DepotPath"]["$value"] == manifest["scene"]
    delay = graph[7]["condition"]["Data"]["type"]["Data"]
    assert delay["$type"] == "questRealtimeDelay_ConditionType" and delay["seconds"] == 1
    scene = scene_nodes(read(VAL / "afterlife_mirror_scene.scene.json"))
    exit_condition = scene[4398]["questNode"]["Data"]["condition"]["Data"]
    assert exit_condition["$type"] == "questFactsDBCondition"
    assert exit_condition["type"]["Data"]["factName"] == "PTFRB0ALM_Near"
    assert exit_condition["type"]["Data"]["value"] == 0
    assert exit_condition["type"]["Data"]["comparisonType"] == "Equal"

    addon = (ROOT / "diagnostics/PTFR_B0_Afterlife_Mirror/init.lua").read_text(encoding="utf-8")
    assert 'SetFactStr(PREFIX.."Enabled",1)' in addon
    assert 'SetFactStr(PREFIX.."Near",desired)' in addon
    assert addon.count("SetFactStr(") == 2, "unexpected fact writer in CET helper"
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("""
      callbacks={}
      registerForEvent=function(name,fn) callbacks[name]=fn end
      json={encode=function() return '{}' end}
      io={open=function() return {write=function() return true end,
        flush=function() return true end,close=function() return true end} end}
      IsDefined=function(value) return value~=nil end
      playerPos={x=-1438.97,y=1039.22,z=16.92}
      writes={}
      facts={}
      q={GetFactStr=function(self,name) return facts[name] or 0 end,
        SetFactStr=function(self,name,value) facts[name]=value
          writes[#writes+1]={name=name,value=value} end}
      player={GetWorldPosition=function() return playerPos end,
        IsInCombat=function() return false end,GetEntityID=function() return 1 end}
      Game={GetPlayer=function() return player end,GetQuestsSystem=function() return q end,
        GetSceneSystem=function() return {GetScriptInterface=function()
          return {IsEntityInScene=function() return false end} end} end,
        GetWorkspotSystem=function() return {IsActorInWorkspot=function() return false end} end,
        GetTimeSystem=function() return {GetGameTimeStamp=function() return 0 end} end}
    """)
    facts = lua.globals().facts
    for name, value in manifest["guard_facts"].items():
        facts[name] = value
    facts["PTFRB0ALM_Enabled"] = 0
    facts["PTFRB0ALM_Ready"] = 1
    mod = lua.execute(addon)
    assert mod["Inspect"] is not None and mod["Enable"] is not None and mod["Observe"] is not None
    callbacks = lua.globals().callbacks
    callbacks["onInit"]()
    callbacks["onUpdate"](6)
    callbacks["onUpdate"](6)
    assert mod["Inspect"]()["ready"] is True
    assert mod["Enable"]() is True
    callbacks["onUpdate"](0.5)
    assert facts["PTFRB0ALM_Near"] == 1
    lua.globals().playerPos["x"] = -1430.0
    callbacks["onUpdate"](0.5)
    assert facts["PTFRB0ALM_Near"] == 0
    writes = lua.globals().writes
    assert [(writes[i]["name"], writes[i]["value"]) for i in range(1, 4)] == [
        ("PTFRB0ALM_Enabled", 1), ("PTFRB0ALM_Near", 1), ("PTFRB0ALM_Near", 0)
    ]
    print("Afterlife v5: mod-owned proximity fact, native scene exit and one-second rearm")
    print("Static/Lua proximity mock PASS. CET is development-only; live durability unproven.")


if __name__ == "__main__":
    main()
