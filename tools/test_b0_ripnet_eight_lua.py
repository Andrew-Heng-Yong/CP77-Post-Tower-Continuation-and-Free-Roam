"""Offline Lua 5.1 simulation of two distinct ripperdoc/netrunner owners."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.lua51 import LuaRuntime  # type: ignore[import-not-found]  # noqa: E402

SITES = {
    "rip_hil": ("PTFRB0RIPHIL_", "wbr_hil_ripdoc_01_default_on", -41.7054405, -53.5234756, 7.18342638),
    "net_cvi": ("PTFRB0NETCVI_", "pac_cvi_techstore_01", -1908.16333, -1924.15247, 49.3091621),
}


def main() -> None:
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute("""
      events={}; facts={}; scene_active=false
      function registerForEvent(name,fn) events[name]=fn end
      function IsDefined(value) return value~=nil end
      json={encode=function(value) return '{}' end}
      io={open=function(path,mode) return {
        write=function(self,s) return true end,flush=function(self) return true end,
        close=function(self) end
      } end}
      player={position={x=1000,y=1000,z=0}}
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
    }.items():
        facts[name] = value
    for prefix, gate, *_ in SITES.values():
        facts[gate] = 1
        facts[prefix + "Ready"] = 1
    mod = lua.execute((ROOT / "diagnostics/PTFR_B0_RipNet_Eight/init.lua").read_text())
    lua.globals().events.onInit()
    lua.globals().scene_active = True
    assert mod.Enable("rip_hil") is False
    lua.globals().scene_active = False
    assert mod.Inspect("rip_hil")["ready"] is True
    assert mod.Enable("rip_hil") is True
    assert mod.Enable("net_cvi") is True
    lua.globals().events.onUpdate(0.5)
    assert all((facts[p + "Far"] or 0) == 0 for p, *_ in SITES.values())
    for prefix, _, x, y, z in SITES.values():
        player = lua.globals().player
        player.position.x, player.position.y, player.position.z = x, y, z
        lua.globals().events.onUpdate(0.5)
        assert (facts[prefix + "Far"] or 0) == 0
        facts[prefix + "Near"] = 1  # Native phase entered.
        player.position.x = x + 80
        lua.globals().events.onUpdate(0.5)
        assert facts[prefix + "Far"] == 1
        facts[prefix + "Near"] = 0  # Native exit completed.
        player.position.x = x
        lua.globals().events.onUpdate(0.5)
        assert facts[prefix + "Far"] == 0
        player.position.x, player.position.y, player.position.z = 1000, 1000, 0
    assert mod.Disable("rip_hil") is True
    assert mod.Disable("net_cvi") is True
    assert all(facts[p + "Enabled"] == 0 and facts[p + "Far"] == 0 for p, *_ in SITES.values())
    lua.globals().events.onShutdown()
    print("Eight-site CET syntax, guards, two-type enable, Far cycles and disable PASS")


if __name__ == "__main__":
    main()
