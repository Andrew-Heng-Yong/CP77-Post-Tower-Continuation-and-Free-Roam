"""Offline scope and CET controller checks for the isolated Afterlife A2 trial."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    val = ROOT / "research/b0_afterlife_native_audit/validation_a2"
    manifest = json.loads((val / "build_manifest.json").read_text(encoding="utf-8"))
    gate = json.loads((val / "gate.json").read_text(encoding="utf-8"))["Data"]["RootChunk"]
    owner = json.loads((val / "owner.json").read_text(encoding="utf-8"))["Data"]["RootChunk"]
    scene = json.loads((val / "scene.json").read_text(encoding="utf-8"))["Data"]["RootChunk"]
    assert len(manifest["resources"]) == 3 and manifest["vanilla_replacements"] == []
    assert gate["phasePrefabs"] == []
    assert len(owner["phasePrefabs"]) == 1
    assert owner["phasePrefabs"][0]["prefabNodeRef"]["$value"] == "#mirror_scene_afterlife"

    def nodes(root):
        return {item["Data"]["id"]: item["Data"] for item in root["graph"]["Data"]["nodes"]}

    gn, on = nodes(gate), nodes(owner)
    assert set(gn) == set(range(5)) and set(on) == set(range(13))
    native = [item["Data"] for item in on[2]["condition"]["Data"]["conditions"]
              if item["Data"]["$type"] == "questTriggerCondition"]
    assert len(native) == 1 and native[0]["type"] == "IsInside"
    assert native[0]["triggerAreaRef"]["$value"] == manifest["entry_gate"].removeprefix("IsInside ")
    assert on[4]["sceneFile"]["DepotPath"]["$value"] == manifest["resources"][2] or (
        on[4]["sceneFile"]["DepotPath"]["$value"] in manifest["resources"]
    )
    exit_nodes = [item["Data"] for item in scene["sceneGraph"]["Data"]["graph"]
                  if item["Data"]["nodeId"]["id"] == 4398]
    assert len(exit_nodes) == 1
    exit_condition = exit_nodes[0]["questNode"]["Data"]["condition"]["Data"]
    assert exit_condition["type"] == "IsOutside"
    assert exit_condition["triggerAreaRef"]["$value"] == native[0]["triggerAreaRef"]["$value"]
    for root in (gate, owner):
        for node in nodes(root).values():
            if node["$type"] == "questFactsDBManagerNodeDefinition":
                assert node["type"]["Data"]["factName"].startswith("PTFRALMA2_")
    assert manifest["guard_facts"]["PTFRB0ALM_Enabled"] == 0
    assert manifest["guard_facts"]["PTFRALMA1_Requested"] == 0
    assert manifest["guard_facts"]["PTFRALMA2_Requested"] == 1
    assert "10.Out -> 4.mirror_interaction" in manifest["graphs"]["owner"]["edges"]
    assert "4.mirror_interaction_out -> 5.In" in manifest["graphs"]["owner"]["edges"]
    assert "7.Out -> 12.In" in manifest["graphs"]["owner"]["edges"]
    print("Static PASS: fresh gate, one prefab/scene, native entry and exit, lifecycle counters, isolated old owner.")

    source = (ROOT / "diagnostics/PTFR_Afterlife_NativeScene_A2/init.lua").read_text(encoding="utf-8")
    setters = re.findall(r'SetFactStr\("([^"]+)"', source)
    assert set(setters) == {"PTFRB0ALM_Enabled", "PTFRALMA2_Requested"}
    assert 'registerForEvent("onUpdate"' not in source
    sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
    try:
        from lupa.luajit21 import LuaRuntime
    except (ImportError, OSError) as error:
        print(f"LuaJIT mocks NOT RUN: {error}")
        return
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(r'''
      facts={PostTowerFreeRoamActive=1,PTFRP0_DR13=1,q307_active=0,q307_done=1,
        q307_finished=1,q307_2079=1,q307_main_game_killed=1,
        q305_johnny_scene_active=0,mirror_interaction_disabled=0,
        q115_point_of_no_return=0,PTFRB0ALM_Enabled=1,PTFRB0ALM_Interrupted=0,
        PTFRALMA1_Requested=0,PTFRALMA2_Boot=1}
      writes={};callbacks={};json={encode=function(row)return "{}" end}
      function registerForEvent(name,fn)callbacks[name]=fn end
      function IsDefined(value)return type(value)=="table" end
      io={open=function(path,mode)
        return {seek=function()return 0 end,write=function(self,line)return self end,
          flush=function(self)return self end,close=function(self)return true end}
      end}
      q={GetFactStr=function(self,name)return facts[name] or 0 end,
        SetFactStr=function(self,name,value)facts[name]=value;
          writes[#writes+1]={name=name,value=value}end}
      player={GetWorldPosition=function()return{x=-1450,y=1013,z=16.5}end,
        IsInCombat=function()return false end,GetEntityID=function()return 42 end}
      Game={GetQuestsSystem=function()return q end,GetPlayer=function()return player end,
        GetSceneSystem=function()return{GetScriptInterface=function()
          return{IsEntityInScene=function()return false end}end}end,
        GetWorkspotSystem=function()return{IsActorInWorkspot=function()return false end}end}
    ''')
    mod = lua.execute(source)
    assert mod.Start("test") is not None
    assert mod.Arm() is True
    writes = lua.globals().writes
    assert len(writes) == 2
    assert writes[1]["name"] == "PTFRB0ALM_Enabled" and writes[1]["value"] == 0
    assert writes[2]["name"] == "PTFRALMA2_Requested" and writes[2]["value"] == 1
    assert mod.Arm() is False and len(writes) == 2
    mod.Stop()
    facts = lua.globals().facts
    facts["PTFRB0ALM_Enabled"] = 1
    facts["PTFRALMA2_Requested"] = 0
    facts["PTFRALMA1_Requested"] = 1
    mod2 = lua.execute(source)
    mod2.Start("refusal-test")
    assert mod2.Arm() is False and len(writes) == 2
    mod2.Stop()
    print("LuaJIT PASS: controller syntax, two mod-owned writes only, duplicate-arm and active-A1 refusal.")


if __name__ == "__main__":
    main()
