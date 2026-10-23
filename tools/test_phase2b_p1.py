"""Offline LuaJIT checks. Mocks do not establish CET API exposure."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime
from analyze_phase2b_p1 import summarize


def plain(v):
    if hasattr(v, "items"):
        return {str(k): plain(x) for k, x in v.items()}
    return v


def main():
    source = (ROOT / "diagnostics/PTFR_Phase2B_P1/init.lua").read_text()
    assert not re.search(r":(?:Set\w*|Change\w*|QueueEvent|TrackEntry|UntrackEntry|Remove\w*|Apply\w*|Teleport\w*)\s*\(", source)
    assert "Override(" not in source
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().encode = lambda v: json.dumps(plain(v), sort_keys=True)
    lua.execute('''
      events={};hooks={};lines={}; json={encode=encode}; CName={new=function(x) return x end};TweakDBID=CName
      function IsDefined(x) return type(x)=="table" end
      function EnumInt(x) return x end
      function registerForEvent(n,cb) events[n]=cb end
      function registerHotkey(n,label,cb) mark=cb end
      function ObserveBefore(c,m,cb) hooks[c.."."..m..":before"]=cb end
      function ObserveAfter(c,m,cb) hooks[c.."."..m..":after"]=cb end
      io.open=function() return {write=function(self,s) lines[#lines+1]=s end,flush=function() end,close=function() end} end
      bb={HighLevel=1,SceneTier=1,Locomotion=0,LocomotionDetailed=0,UpperBody=0}
      function bb:GetInt(k) return self[k] end
      function bb:GetBool(k) return false end
      function GetAllBlackboardDefs() return {PlayerStateMachine={HighLevel="HighLevel",SceneTier="SceneTier",Locomotion="Locomotion",LocomotionDetailed="LocomotionDetailed",UpperBody="UpperBody",IsMovingHorizontally="moving"}} end
      player={GetEntityID=function() return {hash="1ULL"} end,GetWorldPosition=function() return {x=1,y=2,z=3} end,GetPlayerStateMachineBlackboard=function() return bb end}
      journalEntry={id="05_take_walk"}
      jm={GetEntryHash=function() return 123 end,GetEntryState=function() return "Succeeded" end,IsEntryTracked=function() return true end,GetTrackedEntry=function() return journalEntry end,GetEntryByString=function() return journalEntry end,HasAnyDelayedStateChanges=function() return false end}
      ss={IsEntityInScene=function() return true end,IsEntityInDialogue=function() return false end,GetSceneSystemCameraControlEnabled=function() return true end,IsRewindableSectionActive=function() return false end}
      ps={IsOpen=function() return false end,IsLocked=function() return true end,IsSealed=function() return false end,IsDisabled=function() return false end,IsUnpowered=function() return false end}
      door={GetEntityID=function() return {hash="2ULL"} end,GetWorldPosition=player.GetWorldPosition,GetClassName=function() return "Door" end,GetDevicePS=function() return ps end}
      Game={GetPlayer=function() return player end,GetJournalManager=function() return jm end,GetSceneSystem=function() return {GetScriptInterface=function() return ss end} end,GetWorkspotSystem=function() return {IsActorInWorkspot=function() return false end} end,GetMountingFacility=function() return {GetMountingInfoSingleWithObjects=function() return {parentId={hash=0},childId={hash=1},slotId={id="None"}} end} end,GetStatusEffectSystem=function() return {HasStatusEffect=function() return false end} end,GetTargetingSystem=function() return {GetLookAtObject=function() return door end} end,GetQuestsSystem=function() return {GetFactStr=function(self,n) if n=="q307_active" then return 0 else return 1 end end} end}
      data={tier=2,emptyHands=true,walkType="Slow"}
      ctx={GetPermanentScriptableParameter=function() return {GetTierData=function() return data end} end,GetPermanentBoolParameter=function() return {valid=true,value=false} end,GetPermanentFloatParameter=function() return {valid=true,value=-1} end,GetStateMachineCurrentState=function(self,n) return n=="HighLevel" and "sceneTierII" or "stand" end}
      si={executionOwnerEntityID={hash=1},localBlackboard=bb,GetActionValue=function() return 0 end}
      functor={SceneTierToEnter=function() return 2 end,m_cachedSpeedValue=0,m_currentSpeedValue=0,m_currentSpeedMovementPreset="Slow"}
    ''')
    lua.execute(source)
    lua.execute('''
      events.onInit(); events.onUpdate(0.016)
      hooks["ExplorationEvents.OnEnter:after"](functor,ctx,si)
      hooks["SceneTierAbstractEvents.OnUpdate:before"](functor,0.016,ctx,si)
      hooks["SceneTierIIEvents.OnEnter:before"](functor,ctx,si)
      bb.HighLevel=2;bb.SceneTier=2
      hooks["DefaultTransition.SetBlackboardIntVariable:after"](functor,si,"HighLevel",2)
      hooks["SceneTierIIEvents.OnEnter:after"](functor,ctx,si)
      events.onUpdate(0.016)
      hooks["SceneTierIIEvents.OnUpdate:before"](functor,0.1,ctx,si)
      mark()
      Game.GetSceneSystem=function() error("unexposed") end
      jm.GetEntryByString=function() error("lookup failed") end
      events.onUpdate(1.0)
      events.onShutdown()
    ''')
    rows = [json.loads(v) for _, v in sorted(lua.globals().lines.items())]
    assert not any(r["event"] in {"CALLBACK_ERROR", "POLL_ERROR"} for r in rows)
    changes = [r["detail"]["current"] for r in rows if r["event"] == "TIER_PAIR_CHANGE"]
    assert changes == ["1:1", "2:2"]
    assert any(r["event"] == "HIGHLEVEL_CORRECTION_PENDING" for r in rows)
    mark = next(r for r in rows if r["event"] == "MANUAL_MARK")
    assert mark["state"]["look_target"]["device"]["IsLocked"] is True
    assert mark["state"]["journal"]["misty"]["state"] == "Succeeded"
    last = rows[-1]
    assert last["state"]["in_scene"] == "UNKNOWN"
    assert last["state"]["journal"]["misty"]["present"] == "UNKNOWN"
    result = summarize(rows)
    assert result["context_records_with_readable_request"] >= 4
    rows[-1]["read_errors"] = []  # Empty Lua errors may encode as [].
    rows[-1]["detail"] = []
    assert summarize(rows)["post_tower_records"] > 0
    print(f"PASS: LuaJIT syntax, read-only call audit, tier order, context hooks, door/journal reads, UNKNOWN/error handling, analyzer ({len(rows)} mock records).")
    print("NOT runtime validation: CET exposure/callback delivery require the short reload.")


if __name__ == "__main__":
    main()
