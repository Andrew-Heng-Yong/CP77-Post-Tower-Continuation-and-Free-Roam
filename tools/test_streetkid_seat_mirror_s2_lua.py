"""Offline Lua 5.1 contract test for the one-shot Streetkid S2 controller."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.lua51 import LuaRuntime  # type: ignore[import-not-found]  # noqa: E402


def main() -> None:
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("""
      events={}; facts={}; writes={}; scene_active=false; workspot_active=false; combat=false
      function registerForEvent(name,fn) events[name]=fn end
      function IsDefined(value) return value~=nil end
      json={encode=function(value) return '{}' end}
      io={open=function(path,mode) return {
        write=function(self,s) return true end,
        flush=function(self) return true end,
        close=function(self) end
      } end}
      player={position={x=-1262.52893,y=-1001.76685,z=12.03725}}
      function player:GetWorldPosition() return self.position end
      function player:IsInCombat() return combat end
      function player:GetEntityID() return 1 end
      q={}
      function q:GetFactStr(name) return facts[name] or 0 end
      function q:SetFactStr(name,value) facts[name]=value; writes[#writes+1]=name end
      Game={}
      function Game.GetPlayer() return player end
      function Game.GetQuestsSystem() return q end
      function Game.GetSceneSystem() return {GetScriptInterface=function()
        return {IsEntityInScene=function() return scene_active end}
      end} end
      function Game.GetWorkspotSystem() return {IsActorInWorkspot=function() return workspot_active end} end
    """)
    facts = lua.globals().facts
    for name, value in {
        "PostTowerFreeRoamActive": 1, "PTFRP0_DR13": 1,
        "q307_active": 0, "q307_done": 1, "q307_finished": 1,
        "q307_2079": 1, "q305_johnny_scene_active": 0,
        "q000_done": 1, "PTFRSKS1_Enabled": 0, "PTFRSKS2_Boot": 1, "PTFRSKS2_Revision": 4,
    }.items():
        facts[name] = value
    module = lua.execute((ROOT / "diagnostics/PTFR_Streetkid_Seat_Mirror_S2/init.lua").read_text(encoding="utf-8"))
    events = lua.globals().events
    events["onInit"]()
    events["onUpdate"](0.5)
    facts['PTFRSKS2_Revision']=0
    assert module.Start() is False
    facts['PTFRSKS2_Revision']=4
    facts['PTFRSKS3_Active']=1
    assert module.Start() is False
    facts['PTFRSKS3_Active']=0
    assert module.Start() is True
    assert facts["PTFRSKS2_Enabled"] == 1
    facts["PTFRSKS2_Active"] = 1
    lua.globals().scene_active = True
    lua.globals().workspot_active = True
    assert module.Stop() is False
    lua.globals().scene_active = False
    lua.globals().workspot_active = False
    facts["PTFRSKS2_Active"] = 0
    facts["PTFRSKS2_Ready"] = 1
    facts["PTFRSKS2_Completed"] = 1
    facts["PTFRSKS2_SceneRequests"] = 1
    facts["PTFRSKS2_SceneReturns"] = 1
    assert module.Finish() is True
    assert module.Start() is False
    assert facts["PTFRSKS2_Enabled"] == 0
    assert set(lua.globals().writes.values()) == {"PTFRSKS2_Enabled"}
    events["onShutdown"]()
    print("Streetkid S2 Lua 5.1 lifecycle and write-scope OK")


if __name__ == "__main__":
    main()
