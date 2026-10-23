"""Read-only diagnostic behavior checks; mocks do not prove live CET bindings."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime


def main():
    source = (ROOT / "diagnostics/PTFR_Zetatech_Access_Audit/init.lua").read_text()
    assert not re.search(
        r"(?:\bOverride\s*\(|:\s*(?:Set\w*|Queue\w*|Activate\w*|Deactivate\w*|"
        r"Reset\w*|Toggle\w*|Spawn\w*|Despawn\w*|Teleport\w*|Save\w*)\s*\()",
        source,
    ), "game-state mutation in read-only probe"
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
      events={};writes=0;communityReads=0;targetReads=0
      function registerForEvent(n,fn) events[n]=fn end
      function IsDefined(v) return type(v)=="table" end
      function NameToString(v) return v end
      function NameToHash(v) return v end
      function CreateNodeRef(v) return v end
      CName={new=function(v) return v end}
      json={encode=function(v) lastRow=v;return "mock json" end}
      io.open=function(path,mode)
        if mode=="r" then return nil end
        return {write=function(self,v) writes=writes+1;return self end,
          flush=function() return true end,close=function() return true end}
      end
      facts={PostTowerFreeRoamActive=1,PTFRP0_DR13=1,q307_active=0,q307_done=1,
        q307_finished=1,q307_2079=1,q307_main_game_killed=1,q307_ep1_killed=1,
        q305_johnny_scene_active=0,q115_point_of_no_return=0,PTFRMV_AccessRevision=11}
      pos={x=-1548,y=1191,z=16}
      player={GetWorldPosition=function() return pos end}
      npc={GetEntityID=function() return {hash="18446744073709551610ULL"} end,
        GetWorldPosition=function() return {x=-1543,y=1194,z=16} end,
        GetClassName=function() return "NPCPuppet" end,
        GetRecordID=function() return "Character.q307_zetatech_guard" end}
      ps={IsA=function() return true end,GetDoorType=function() return "INTERACTIVE" end}
      for _,k in ipairs({"IsOpen","IsLocked","IsSealed","IsInteractive",
        "IsDisabled","IsUnpowered","IsOFF","IsBusy","IsPlayerAuthorized"}) do
        ps[k]=function() return k=="IsOpen" or k=="IsInteractive" end
      end
      door={GetEntityID=function() return {hash="13806931541592989805ULL"} end,
        GetWorldPosition=function() return pos end,GetClassName=function() return "Door" end,
        GetRecordID=function() return "Door" end,GetDevicePS=function() return ps end}
      function entry(n)
        return {GetName=function() return n end,IsActive=function() return true end,
          GetPhases=function() return {"return"} end,
          GetSpawnedEntityIDs=function() return {{hash="18446744073709551610ULL"}} end,
          GetRestoredEntityIDs=function() return {} end,
          GetSpawningEntityIDs=function() return {} end,GetReservedEntityIDs=function() return {} end}
      end
      function community(ref)
        local rows={entry("ignored")}
        if ref=="#q307_com_main" then rows[#rows+1]=entry("q307_zetatech_clerk")
        else
          for _,n in ipairs({"01","12","13","14","15"}) do
            rows[#rows+1]=entry("q307_alley_extra_"..n)
          end
        end
        return {GetEntries=function() return rows end}
      end
      Game={GetPlayer=function() return player end,
        GetQuestsSystem=function() return {GetFactStr=function(self,n) return facts[n] or 0 end} end,
        GetTargetingSystem=function() return {GetLookAtObject=function()
          targetReads=targetReads+1;return door end} end,
        GetWorldStateSystem=function() return {GetCommunity=function(self,ref)
          communityReads=communityReads+1;return community(ref) end} end,
        GetDynamicEntitySystem=function() return {GetTaggedIDs=function(self,tag)
          assert(tag=="PTFRMV11_Terry");return {{hash="18446744073709551610ULL"}} end} end,
        FindEntityByID=function() return npc end,
        GetWorkspotSystem=function() return {IsActorInWorkspot=function() return true end} end,
        GetSceneSystem=function() return {GetScriptInterface=function()
          return {IsEntityInScene=function() return false end} end} end}
    ''')
    lua.globals().audit = lua.execute(source)
    lua.execute('events.onUpdate(1);assert(writes==0);events.onUpdate(1);assert(writes==1)')
    lua.execute('''
      assert(lastRow.facts.PTFRMV_AccessRevision==11)
      assert(lastRow.look_target.device.IsOpen==true)
      assert(lastRow.look_target.id=="13806931541592989805")
      local guard=lastRow.communities["#q307_com_alley"].entries.q307_alley_extra_01
      assert(guard.present and guard.active and guard.phases[1]=="return")
      assert(guard.GetSpawnedEntityIDs[1]=="18446744073709551610")
      assert(guard.entities["18446744073709551610"].in_workspot==true)
      assert(lastRow.communities["#q307_com_alley"].entries.ignored==nil)
      assert(lastRow.communities["#q307_com_main"].entries.q307_zetatech_clerk.present)
      assert(lastRow.communities["$/03_night_city/#PTFRMV_StreetCommunity"].entries.q307_alley_extra_15.present)
      assert(lastRow.terry.ids[1]=="18446744073709551610")
      assert(lastRow.terry.entities["18446744073709551610"].present)
      local before=writes
      for _,key in ipairs({"PostTowerFreeRoamActive","PTFRP0_DR13","q307_active",
        "q307_done","q307_finished","q307_2079","q307_main_game_killed",
        "q307_ep1_killed","q305_johnny_scene_active","q115_point_of_no_return"}) do
        local old=facts[key];facts[key]=old==0 and 1 or 0
        events.onUpdate(2);assert(writes==before);facts[key]=old
      end
      assert(communityReads==4 and targetReads==1)
      assert(lastRow.version=="ZetatechAccessAudit-R12")
      assert(lastRow.communities["$/03_night_city/#PTFRMV12_Population"].entries.q307_alley_extra_12==nil)
      assert(lastRow.communities["$/03_night_city/#PTFRMV12_Population"].entries.q307_alley_extra_31~=nil)
      pos.x=0;events.onUpdate(2);assert(writes==before);pos.x=-1548
      ps.IsOpen=nil;events.onUpdate(2)
      assert(lastRow.look_target.device.IsOpen=="UNKNOWN")
      assert(lastRow.errors["look_target.IsOpen"]~=nil)
      Game.GetWorldStateSystem=nil;events.onUpdate(2)
      assert(lastRow.communities["#q307_com_main"].present=="UNKNOWN")
      assert(lastRow.communities["#q307_com_main"].entries.q307_zetatech_clerk.present=="UNKNOWN")
    ''')
    print("PASS: LuaJIT syntax/load; read-only API audit; 2s sampling; ten Tower guards; "
          "100m boundary; exact community filters; 64-bit IDs; unavailable APIs stay UNKNOWN")


if __name__ == "__main__":
    main()
