"""Offline LuaJIT mocks for the two-run Afterlife A3 automatic bootstrap."""
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = (ROOT / "diagnostics/PTFR_Afterlife_Native_Auto_A3/init.lua").read_text(encoding="utf-8")


def runtime(quota: int, *, tower: int = 1, inside: bool = False, arm_ok: bool = True):
    sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
    from lupa.luajit21 import LuaRuntime

    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(r'''
      callbacks={}; calls={}; quota=2; tower=1; inside=false; arm_ok=true
      function registerForEvent(name, fn) callbacks[name]=fn end
      function IsDefined(value) return type(value)=="table" end
      io={open=function(path,mode)
        if path~="afterlife_native_auto_a3_quota.txt" then return nil,"bad path" end
        if mode=="r" then return {
          read=function() return tostring(quota) end,
          close=function() return true end
        } end
        if mode=="w" then return {
          write=function(self,value) quota=tonumber(value);return self end,
          flush=function(self) return self end,
          close=function(self) return true end
        } end
        return nil,"bad mode"
      end}
      facts={PTFRP0_DR13=1,PTFRALMA2_Boot=1,PTFRALMA2_Requested=0,
        PTFRB0ALM_Enabled=1,PTFRB0ALM_Near=0,PTFRB0ALM_Active=0}
      q={GetFactStr=function(self,name)
        if name=="PostTowerFreeRoamActive" then return tower end
        return facts[name] or 0
      end}
      player={GetWorldPosition=function()
          if inside then return{x=-1439,y=1039,z=16.9} end
          return{x=-1450,y=1013,z=16.5}
        end,
        IsInCombat=function()return false end,
        GetEntityID=function()return 42 end}
      Game={GetQuestsSystem=function()return q end,
        GetPlayer=function()return player end,
        GetSceneSystem=function()return{GetScriptInterface=function()
          return{IsEntityInScene=function()return false end}end}end,
        GetWorkspotSystem=function()return{IsActorInWorkspot=function()return false end}end}
      a2={Start=function(label)calls[#calls+1]="Start";return "log.jsonl" end,
        Arm=function()calls[#calls+1]="Arm";return arm_ok end,
        Mark=function(label)calls[#calls+1]="Mark:"..label end,
        Stop=function()calls[#calls+1]="Stop" end}
      function GetMod(name)
        if name=="PTFR_Afterlife_NativeScene_A2" then return a2 end
      end
    ''')
    state = lua.globals()
    state.quota = quota
    state.tower = tower
    state.inside = inside
    state.arm_ok = arm_ok
    mod = lua.execute(SOURCE)
    state.callbacks.onInit()
    return state, mod


def main() -> None:
    assert not re.search(r"SetFact(?:Str)?\s*\(", SOURCE)
    assert SOURCE.count('GetMod("PTFR_Afterlife_NativeScene_A2")') == 1
    assert 'registerForEvent("onShutdown"' not in SOURCE
    state, mod = runtime(2)
    state.callbacks.onUpdate(0.5)
    assert [state.calls[i] for i in range(1, len(state.calls) + 1)] == [
        "Start", "Arm", "Mark:a3-auto-armed"
    ]
    assert state.quota == 1 and mod.Status()["pending"] is False
    state.callbacks.onUpdate(20)
    assert len(state.calls) == 3

    state, _ = runtime(1)
    state.callbacks.onUpdate(0.5)
    assert state.quota == 0 and len(state.calls) == 3
    state, _ = runtime(0)
    state.callbacks.onUpdate(20)
    assert len(state.calls) == 0

    state, _ = runtime(2, tower=0)
    state.callbacks.onUpdate(0.5)
    assert len(state.calls) == 0 and state.quota == 2
    state, _ = runtime(2, inside=True)
    state.callbacks.onUpdate(0.5)
    assert len(state.calls) == 0 and state.quota == 2
    state, _ = runtime(2, arm_ok=False)
    state.callbacks.onUpdate(0.5)
    assert [state.calls[i] for i in range(1, len(state.calls) + 1)] == [
        "Start", "Arm", "Mark:a3-auto-arm-refused", "Stop"
    ]
    assert state.quota == 2
    print("A3 LuaJIT PASS: two one-shot cold boots, inert quota, story/area gates, refusal without quota consumption.")


if __name__ == "__main__":
    main()
