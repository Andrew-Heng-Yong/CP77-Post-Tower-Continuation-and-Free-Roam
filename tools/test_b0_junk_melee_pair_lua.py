"""Lua 5.1 simulation of the paired opt-in and two independent Far cycles."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.lua51 import LuaRuntime  # type: ignore[import-not-found]  # noqa: E402


def main() -> None:
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("""
      events={}; facts={}; scene_active=false
      function registerForEvent(name,fn) events[name]=fn end
      function IsDefined(value) return value~=nil end
      json={encode=function(value) return '{}' end}
      io={open=function(path,mode) return {
        write=function(self,s) return true end,
        flush=function(self) return true end,
        close=function(self) end
      } end}
      player={position={x=0,y=0,z=0}}
      function player:GetWorldPosition() return self.position end
      function player:IsInCombat() return false end
      function player:GetEntityID() return 1 end
      q={}
      function q:GetFactStr(name) return facts[name] or 0 end
      function q:SetFactStr(name,value) facts[name]=value end
      Game={}
      function Game.GetPlayer() return player end
      function Game.GetQuestsSystem() return q end
      function Game.GetSceneSystem() return {GetScriptInterface=function()
        return {IsEntityInScene=function() return scene_active end}
      end} end
      function Game.GetWorkspotSystem() return {IsActorInWorkspot=function() return false end} end
    """)
    facts = lua.globals().facts
    for name, value in {
        "PostTowerFreeRoamActive": 1, "PTFRP0_DR13": 1, "q307_active": 0,
        "q307_done": 1, "q307_finished": 1, "q307_2079": 1,
        "q307_main_game_killed": 1, "q305_johnny_scene_active": 0,
        "q115_point_of_no_return": 0, "q000_done": 1,
        "bls_ina_se5_junkshop_01_default_on": 1,
        "bls_ina_se5_melee_01_default_on": 1,
    }.items():
        facts[name] = value
    shops = (
        ("PTFRB0SE5J_", -986.821716, -4418.15869, 64.3136444),
        ("PTFRB0SE5M_", 138.247818, -4671.49805, 55.0782623),
    )
    for prefix, *_ in shops:
        facts[prefix + "Ready"] = 1
    module = lua.execute((ROOT / "diagnostics/PTFR_B0_JunkMelee_Pair/init.lua").read_text())
    lua.globals().events.onInit()
    lua.globals().scene_active = True
    assert module.Start() is False
    lua.globals().scene_active = False
    assert module.Inspect()["ready"] is True
    assert module.Start() is True
    lua.globals().events.onUpdate(0.5)
    assert all(facts[p + "Enabled"] == 1 and (facts[p + "Far"] or 0) == 0 for p, *_ in shops)
    for prefix, x, y, z in shops:
        player = lua.globals().player
        player.position.x, player.position.y, player.position.z = x, y, z
        lua.globals().events.onUpdate(0.5)
        assert (facts[prefix + "Far"] or 0) == 0
        facts[prefix + "Near"] = 1  # Native phase has entered.
        player.position.x = x + 80
        lua.globals().events.onUpdate(0.5)
        assert facts[prefix + "Far"] == 1
        facts[prefix + "Near"] = 0  # Native exit branch completed.
        player.position.x = x
        lua.globals().events.onUpdate(0.5)
        assert facts[prefix + "Far"] == 0
        player.position.x = 0
        player.position.y = 0
        player.position.z = 0
    assert module.Stop() is True
    assert all(facts[p + "Enabled"] == 0 and facts[p + "Far"] == 0 for p, *_ in shops)
    lua.globals().events.onShutdown()
    print("Paired CET guards, enable, initial clear Far, two exits/rearms and stop PASS")


if __name__ == "__main__":
    main()
