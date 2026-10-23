"""Offline adversarial LuaJIT tests of the writable P2 probe.

Mocks establish fail-closed control flow and exact requested calls, not native
CET exposure, native repair behavior, or save safety in a running game.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime

SOURCE = ROOT / "diagnostics/PTFR_Phase2B_P2_RepairProbe/init.lua"
OBJECTIVE = "ep1/quests/main_quest/q307_tomorrow/02_mistys_alley/05_take_walk"
DOOR_ID = "13806931541592989805"


def plain(value):
    if hasattr(value, "items"):
        return {str(k): plain(v) for k, v in value.items()}
    return value


SETUP = r'''
events={};hooks={};hotkeys={};lines={};calls={};messages={}
function print(s) messages[#messages+1]=s end
function IsDefined(x) return type(x)=="table" end
function EnumInt(x) if type(x)=="table" then return x.value end return x end
CName={new=function(x) return x end}
entEntityID={new=function(x) return x end}
gameJournalEntryState={Succeeded=3};JournalNotifyOption={Notify=7};EDoorType={INTERACTIVE=0}
function registerForEvent(n,cb) events[n]=cb end
function registerHotkey(n,label,cb) hotkeys[n]=cb end
function ObserveBefore(c,m,cb) hooks[c.."."..m..":before"]=cb end
function ObserveAfter(c,m,cb) hooks[c.."."..m..":after"]=cb end
json={encode=function(t) encoding_event=t.event;return py_encode(t) end}
io.open=function()
  if fail_open then return nil,"MOCK open failure" end
  return {write=function(self,s)
    if fail_write==encoding_event then return nil,"MOCK write failure" end
    lines[#lines+1]=s;return self
  end,flush=function(self)
    if fail_flush==encoding_event then return nil,"MOCK flush failure" end
    return true
  end,close=function() return true end}
end
function record(kind,t) t.kind=kind;calls[#calls+1]=t end
bb={HighLevel=2,SceneTier=2,GetInt=function(self,k) return self[k] end}
function GetAllBlackboardDefs() return {PlayerStateMachine={HighLevel="HighLevel",SceneTier="SceneTier"}} end
player={GetEntityID=function() return {hash=1ULL} end,
  GetWorldPosition=function() return {x=-1548,y=1222,z=12.1} end,
  GetPlayerStateMachineBlackboard=function() return bb end}
facts={PostTowerFreeRoamActive=1,q307_active=0,q307_done=1,q307_finished=1,q307_2079=1}
objective={id="05_take_walk",hash=-954297364,state=2}
phase={id="02_mistys_alley",hash=555,state=2}
quest={id="q307_tomorrow",hash=-984135344,state=2}
local root="ep1/quests/main_quest/q307_tomorrow"
jm={
 GetEntryByString=function(self,path,class)
   if path==root.."/02_mistys_alley/05_take_walk" and class=="gameJournalQuestObjective" then return objective end
   if path==root.."/02_mistys_alley" and class=="gameJournalQuestPhase" then return phase end
   if path==root and class=="gameJournalQuest" then return quest end
   error("unexpected journal lookup: "..path.." / "..class)
 end,
 GetParentEntry=function(self,e) if e==objective then return phase elseif e==phase then return quest end end,
 GetEntryHash=function(self,e) return e.hash end,
 GetEntryState=function(self,e) return e.state end,
 IsEntryTracked=function(self,e) return e==objective end,
 GetTrackedEntry=function() return objective end,
 HasAnyDelayedStateChanges=function() return false end,
 ChangeEntryState=function(self,path,class,state,notify)
   record("journal",{path=path,class=class,state=state,notify=notify})
   assert(path==root.."/02_mistys_alley/05_take_walk" and class=="gameJournalQuestObjective")
   assert(state==3 and notify==7)
   if j_error then error("MOCK journal request error") end
   if not j_async then objective.state=3 end
 end
}
doorState={IsLocked=true,IsSealed=false,IsOpen=false,IsInteractive=true,IsDisabled=false,
 IsUnpowered=false,IsOFF=false,IsBusy=false,IsPlayerAuthorized=true}
action={IsA=function(self,n) return n=="QuestForceUnlock" end}
ps={GetClassName=function() return "DoorControllerPS" end,IsA=function(self,n) return n=="DoorControllerPS" end,
 GetDoorType=function() return 0 end,
 GetQuestActionByName=function(self,name)
   factory_calls=(factory_calls or 0)+1;assert(self==ps and name=="ForceUnlock")
   if factory_error then error("MOCK factory unavailable") end
   if factory_null then return nil end
   return action
 end,
 ExecutePSAction=function(self,a,target)
   assert(self==ps and target==ps and a==action)
   record("door",{same_ps=self==target,action_verified=a==action})
   if d_error then error("MOCK queue error") end
   if not d_async then doorState.IsLocked=false end
 end}
for k in pairs(doorState) do local name=k;ps[name]=function() return doorState[name] end end
door={GetEntityID=function() return {hash=13806931541592989805ULL} end,
 GetWorldPosition=function() return {x=-1548.0245361328,y=1221.4091796875,z=12.101425170898} end,
 GetDevicePS=function() return ps end}
Game={GetPlayer=function() return player end,GetJournalManager=function() return jm end,
 GetQuestsSystem=function() return {GetFactStr=function(self,n) return facts[n] end} end,
 GetSceneSystem=function() return {GetScriptInterface=function() return {IsEntityInScene=function() return false end} end} end,
 FindEntityByID=function(id)
   assert(type(id.hash)=="cdata","64-bit lookup must use LuaJIT cdata")
   lookup_id=tostring(id.hash)
   assert(lookup_id=="13806931541592989805ULL","exact ID lost")
   return door
 end}
function attach() hooks["PlayerPuppet.OnGameAttached:after"](player) end
function detach() hooks["PlayerPuppet.OnDetach:before"](player) end
'''


class Fixture:
    def __init__(self, setup="", loaded=True, baseline=True):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.globals().py_encode = lambda v: json.dumps(plain(v), sort_keys=True)
        self.lua.execute(SETUP)
        self.lua.execute(setup)
        self.module = self.lua.execute(SOURCE.read_text(encoding="utf-8"))
        self.lua.globals().probe = self.module
        self.run("events.onInit()")
        if loaded:
            self.run("attach(); events.onUpdate(5)")
        if baseline:
            self.module.Inspect()

    def run(self, code):
        return self.lua.execute(code)

    def trigger(self, stage):
        getattr(self.module, "RepairJournal" if stage == "J" else "RepairDoor")()

    def advance(self):
        self.run("events.onUpdate(2); events.onUpdate(8)")

    def calls(self):
        return [plain(v) for _, v in sorted(self.lua.globals().calls.items())]

    def rows(self):
        return [json.loads(v) for _, v in sorted(self.lua.globals().lines.items())]

    def events(self, event, stage=None):
        return [r for r in self.rows() if r["event"] == event and (stage is None or r["stage"] == stage)]


def test_source_audit():
    source = SOURCE.read_text(encoding="utf-8")
    mutations = re.findall(r":((?:Set|Change|Queue|Execute|Track|Untrack|Remove|Apply|Teleport|OnQuest|Force)\w*)\s*\(", source)
    assert mutations == ["ChangeEntryState", "ExecutePSAction"], mutations
    assert "Override(" not in source and "SetFact" not in source
    assert "13806931541592989805ULL" in source
    assert not re.search(r"tonumber\s*\(\s*(?:id|DOOR_ID|id\.hash)", re.sub(r"--[^\n]*", "", source))


def test_no_automatic_writes():
    f = Fixture(baseline=False)
    f.run("events.onUpdate(60); detach(); attach(); events.onUpdate(60); events.onShutdown()")
    assert not f.calls()
    assert {r["event"] for r in f.rows()} >= {"INIT", "SESSION_ATTACHED", "HEARTBEAT", "SHUTDOWN"}


def test_guards():
    facts = {"PostTowerFreeRoamActive": 1, "q307_active": 0, "q307_done": 1, "q307_finished": 1, "q307_2079": 1}
    for name, expected in facts.items():
        for value in (str(1 - expected), "nil", '"UNKNOWN"'):
            f = Fixture(f"facts.{name}={value}")
            for stage in "JD":
                f.trigger(stage)
                assert f.events("STAGE_REJECTED", stage)
            assert not f.calls(), (name, value)
    for options in ({"loaded": False}, {"baseline": False}):
        f = Fixture(**options)
        f.trigger("J"); f.trigger("D")
        assert not f.calls() and len(f.events("STAGE_REJECTED")) == 2
    for setup in ("Game.GetPlayer=function() return nil end", "Game.GetSceneSystem=function() error('unavailable') end"):
        f = Fixture(setup)
        f.trigger("J"); f.trigger("D")
        assert not f.calls()
    f = Fixture(loaded=False, baseline=False)
    f.run("attach(); events.onUpdate(2)"); f.module.Inspect(); f.trigger("J")
    assert not f.calls()


def test_happy_path():
    f = Fixture()
    assert not f.calls()
    baseline = f.events("BASELINE")[-1]
    assert baseline["state"]["guard"]["passed"] is True
    assert baseline["state"]["door"]["id"] == DOOR_ID
    assert f.lua.globals().lookup_id == DOOR_ID + "ULL"
    f.trigger("J")
    assert f.calls() == [{"kind": "journal", "path": OBJECTIVE, "class": "gameJournalQuestObjective", "state": 3, "notify": 7}]
    j_after = f.events("STAGE_AFTER", "J")[-1]["state"]
    assert j_after["journal"]["objective"]["state_value"] == 3
    assert j_after["journal"]["phase"]["state_value"] == j_after["journal"]["quest"]["state_value"] == 2
    assert j_after["door"] == baseline["state"]["door"]
    f.trigger("D")
    assert len(f.calls()) == 1 and f.events("STAGE_REJECTED", "D")
    f.advance()
    f.trigger("J")
    assert len(f.calls()) == 1 and f.events("ALREADY_TARGET", "J")
    f.trigger("D")
    assert f.calls()[-1] == {"kind": "door", "same_ps": True, "action_verified": True}
    d_after = f.events("STAGE_AFTER", "D")[-1]["state"]
    assert d_after["door"]["device"]["IsLocked"] is False
    assert d_after["door"]["device"]["IsOpen"] is False
    assert d_after["journal"] == j_after["journal"]
    f.advance(); f.trigger("D")
    assert len(f.calls()) == 2 and f.events("ALREADY_TARGET", "D")
    assert f.lua.globals().factory_calls == 1
    for stage in "JD":
        assert [r["detail"]["delay_s"] for r in f.events("STABILITY_CHECK", stage)] == [2, 10]
    for r in f.rows():
        assert r["state"]["facts"] == baseline["state"]["facts"]
        assert r["state"]["human"]["normal_opening"] == "UNKNOWN"
    return f


def test_identity_and_gate_failures():
    conditions = [
        "door.GetEntityID=function() return {hash=13806931541592989804ULL} end",
        "door.GetEntityID=function() return {hash=tonumber(13806931541592989805ULL)} end",
        "door.GetWorldPosition=function() return {x=1,y=2,z=3} end",
        "Game.FindEntityByID=function() return nil end",
        "door.GetDevicePS=function() return nil end",
        "ps.IsA=function() return false end",
        "ps.GetDoorType=function() return 99 end",
        "factory_null=true", "factory_error=true",
        "action.IsA=function() return false end",
    ]
    for name in ("IsLocked", "IsOpen", "IsInteractive", "IsDisabled", "IsUnpowered", "IsOFF", "IsBusy", "IsSealed"):
        conditions += [f"ps.{name}=nil", f"ps.{name}=function() return nil end"]
    for name, value in {"IsInteractive": "false", "IsDisabled": "true", "IsUnpowered": "true", "IsOFF": "true", "IsBusy": "true", "IsSealed": "true", "IsOpen": "true"}.items():
        conditions.append(f"doorState.{name}={value}")
    for setup in conditions:
        f = Fixture(setup); f.trigger("D")
        assert not f.calls(), setup
        assert f.events("STAGE_REJECTED", "D"), setup
    for setup in ("objective.hash=1", "objective.id='wrong'", "quest.hash=1", "jm.GetParentEntry=function() return quest end", "objective.state=4", "objective.state=nil"):
        f = Fixture(setup); f.trigger("J")
        assert not f.calls() and f.events("STAGE_REJECTED", "J"), setup


def test_independent_repairs():
    f = Fixture("doorState.IsInteractive=false")
    f.trigger("J")
    assert len(f.calls()) == 1 and f.calls()[0]["kind"] == "journal"
    f = Fixture("objective.state=3")
    f.trigger("D")
    assert len(f.calls()) == 1 and f.calls()[0]["kind"] == "door"


def test_once_even_if_uncertain():
    for stage, setup in (("J", "j_error=true"), ("J", "j_async=true"), ("D", "d_error=true"), ("D", "d_async=true")):
        f = Fixture(setup); f.trigger(stage); f.advance(); f.trigger(stage)
        assert len(f.calls()) == 1, (stage, setup)
        assert len(f.events("OPERATION_REQUESTED", stage)) == 1
        assert f.events("STAGE_REJECTED", stage)[-1]["detail"]["reason"].startswith("operation already attempted")
        f.run("detach(); attach(); events.onUpdate(5)"); f.module.Inspect(); f.trigger(stage)
        assert len(f.calls()) == 1, "reload in same process must not retry uncertain request"


def test_fail_closed_logging():
    for stage in "JD":
        for mode in ("fail_write", "fail_flush"):
            for event in ("STAGE_BEFORE", "OPERATION_REQUESTED"):
                f = Fixture(); f.run(f'{mode}="{event}"'); f.trigger(stage)
                assert not f.calls(), (stage, mode, event)
                f.run(f"{mode}=nil"); f.trigger(stage)
                assert not f.calls(), "logging failure must latch repairs disabled"
    f = Fixture("fail_open=true", loaded=False); f.trigger("J"); f.trigger("D")
    assert not f.calls() and not f.rows()


def test_detach_cancels_attribution():
    f = Fixture(); f.trigger("J"); f.run("detach(); events.onUpdate(12)")
    assert not f.events("STABILITY_CHECK")
    assert f.events("SESSION_DETACHED")[-1]["detail"]["pending_cancelled"] == 2
    f.run("attach(); events.onUpdate(5)"); f.trigger("D")
    assert len(f.calls()) == 1, "new load requires new baseline"
    f.module.Inspect(); f.trigger("D"); f.advance()
    assert len(f.calls()) == 2
    assert all(r["session_id"].endswith("/load-2") for r in f.events("STABILITY_CHECK"))


def test_partial_hook_failure_and_large_dt():
    # Attach hook registers, detach hook fails: a delivered attach must not
    # reopen the guard without reliable session invalidation.
    f = Fixture("ObserveBefore=function() error('MOCK hook unavailable') end")
    assert f.events("INIT")[-1]["detail"]["hooks_registered"] is False
    f.trigger("J"); f.trigger("D")
    assert not f.calls() and len(f.events("STAGE_REJECTED")) == 2
    f = Fixture(); f.trigger("J"); f.run("events.onUpdate(12)")
    assert [r["detail"]["delay_s"] for r in f.events("STABILITY_CHECK", "J")] == [2, 10]


def test_cdata_snapshot_uses_numeric_readbacks_and_exact_id():
    setup = '''
      local ffi=require("ffi")
      for k,v in pairs(facts) do facts[k]=v+0LL end
      objective.state=2LL;phase.state=2LL;quest.state=2LL
      objective.hash=-954297364LL;phase.hash=555LL;quest.hash=-984135344LL
      bb.HighLevel=2LL;bb.SceneTier=2LL
      player.GetWorldPosition=function() return {x=ffi.new("double",-1548.02454),y=ffi.new("double",1221.40918),z=ffi.new("double",12.1014214)} end
      door.GetWorldPosition=function() return {x=ffi.new("double",-1548.02454),y=ffi.new("double",1221.40918),z=ffi.new("double",12.1014214)} end
      ps.GetDoorType=function() return 0LL end
    '''
    f=Fixture(setup)
    assert f.events("INIT") and f.events("BASELINE"), "cdata must not disable startup logging"
    baseline=f.events("BASELINE")[-1]["state"]
    assert baseline["guard"]["passed"] is True
    assert baseline["journal"]["hierarchy_verified"] is True
    assert baseline["journal"]["objective"]["state_value"]==2
    assert baseline["door"]["identity_verified"] is True, baseline["door"]
    assert baseline["door"]["id"]==DOOR_ID
    f.trigger("J");f.advance();f.trigger("D");f.advance()
    assert [call["kind"] for call in f.calls()]==["journal","door"]
    assert f.events("STABILITY_CHECK","D")


def test_parser(f):
    from analyze_phase2b_p2 import readiness_failures, summarize
    rows = f.rows()
    assert readiness_failures(rows) == []
    result = summarize(rows)
    for name in ("journal_repair", "door_repair"):
        successful = [a for a in result[name]["attempts"] if a["operation_requests"]]
        assert len(successful) == 1
        assert successful[0]["target_change_observed_after_request"] is True
        assert successful[0]["stable_at_10s"] is True
        assert all(d["changed"] is False for d in successful[0]["other_issue_deltas"].values())
    # The mutable game state remains wholly mocked; append an explicit artifact label.
    for row in rows:
        row["validation_context"] = "OFFLINE_LUAJIT_MOCK_NOT_GAME_RUNTIME"
    target = ROOT / "research/phase2b_p2/probe_validation/mock_runtime.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    return len(rows)


def main():
    tests = [test_source_audit, test_no_automatic_writes, test_guards,
             test_identity_and_gate_failures, test_independent_repairs,
             test_once_even_if_uncertain, test_fail_closed_logging,
             test_detach_cancels_attribution, test_partial_hook_failure_and_large_dt,
             test_cdata_snapshot_uses_numeric_readbacks_and_exact_id]
    for test in tests:
        test(); print("PASS:", test.__name__)
    result = test_happy_path(); print("PASS: test_happy_path")
    count = test_parser(result); print(f"PASS: automatic parser compatibility ({count} mock records)")
    print("NOT runtime validation: CET exposure, native side effects, human door use and save persistence remain untested.")


if __name__ == "__main__":
    main()
