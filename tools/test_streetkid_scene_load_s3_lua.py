"""Mocked Lua51 safety and write-scope checks for the action-free S3 probe."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.lua51 import LuaRuntime


def main():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("""
      events={};facts={};writes={};scene=false;flushes=0
      function registerForEvent(n,f) events[n]=f end
      function IsDefined(v) return v~=nil end
      json={encode=function(v) return '{}' end}
      io={open=function() return {write=function() return true end,
        flush=function() flushes=flushes+1;return true end,close=function() end} end}
      q={GetFactStr=function(self,n) return facts[n] or 0 end,
        SetFactStr=function(self,n,v) facts[n]=v;writes[#writes+1]=n end}
      p={GetWorldPosition=function() return {x=-1261.891,y=-1001.635,z=12.03} end,
        IsInCombat=function() return false end,GetEntityID=function() return 1 end}
      Game={GetPlayer=function() return p end,GetQuestsSystem=function() return q end,
        GetSceneSystem=function() return {GetScriptInterface=function()
          return {IsEntityInScene=function() return scene end} end} end,
        GetWorkspotSystem=function() return {IsActorInWorkspot=function() return false end} end}
    """)
    facts = lua.globals().facts
    required = {"PostTowerFreeRoamActive":1,"PTFRP0_DR13":1,"q307_active":0,
                "q307_done":1,"q307_finished":1,"q307_2079":1,"q305_johnny_scene_active":0,"q000_done":1,"PTFRSKS3_Revision":2}
    for n, v in required.items():
        facts[n] = v
    facts["PTFRSKS3_Boot"] = 1
    module = lua.execute((ROOT / "diagnostics/PTFR_Streetkid_Scene_Load_S3/init.lua").read_text(encoding="utf-8"))
    events = lua.globals().events
    events["onInit"](); events["onUpdate"](0.5)
    facts['PTFRSKS3_Revision'] = 0
    assert module.Start() is False
    facts['PTFRSKS3_Revision'] = 2
    facts["PTFRSKS2_Enabled"] = 1
    assert module.Start() is False
    facts["PTFRSKS2_Enabled"] = 0
    assert module.Start() is True
    facts["PTFRSKS3_Active"] = 1
    lua.globals().scene = True
    assert module.Finish() is False and facts["PTFRSKS3_Enabled"] == 1
    lua.globals().scene = False
    for n, v in {"Ready":1,"Active":0,"Completed":1,"SceneRequests":1,"SceneReturns":1}.items():
        facts["PTFRSKS3_" + n] = v
    assert module.Finish() is True and facts["PTFRSKS3_Enabled"] == 0
    assert module.Start() is False
    assert all(facts[n] == v for n, v in required.items())
    assert set(lua.globals().writes.values()) == {"PTFRSKS3_Enabled"}
    assert lua.globals().flushes >= 8
    events["onShutdown"]()
    print("S3 Lua51: concurrent-owner refusal, active-scene refusal, one-shot return, flushed logging, mod-only writes OK")


if __name__ == "__main__":
    main()
