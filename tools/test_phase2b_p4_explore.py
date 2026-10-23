"""Adversarial offline LuaJIT checks of the P4 relocation-only probe.

These are mocks, not game/runtime validation. Native exposure, safe arrival,
surrounding-world functionality and save persistence require human testing.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime

MODULE = ROOT / "diagnostics/PTFR_Phase2B_P4_Explore"
SOURCE = MODULE / "init.lua"
TARGET = MODULE / "ptfr_p4_target.lua"
EXPECTED_TARGET = {"x": -1658.87463, "y": 997.365662, "z": 23.6999989}
EXPECTED_QUATERNION = {"i": 0, "j": 0, "k": -0.99619472, "r": 0.0871557295}


def plain(value):
    if hasattr(value, "items"):
        return {str(k): plain(v) for k, v in value.items()}
    return value


SETUP = r'''
events={};hooks={};hotkeys={};lines={};calls={};messages={};rays={};overlaps={};nav_queries={}
function print(s) messages[#messages+1]=s end
function IsDefined(v) return type(v)=="table" end
function EnumInt(v) if type(v)=="table" then return v.value end return v end
function EnumValueToString(_,v) return tostring(v) end
CName={new=function(v) return v end};TweakDBID=CName
entEntityID={new=function(v) return v end}
function registerForEvent(n,cb) events[n]=cb end
function registerHotkey(n,label,cb) hotkeys[n]=cb end
function ObserveAfter(c,m,cb) hooks[c.."."..m..":after"]=cb end
function ObserveBefore(c,m,cb) hooks[c.."."..m..":before"]=cb end
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
function record(kind,detail) detail.kind=kind;calls[#calls+1]=detail end
Vector4={new=function(x,y,z,w)
  if type(x)=="table" then return x end
  return {x=x,y=y,z=z,w=w or 1}
end}
Quaternion={new=function(i,j,k,r)
  if type(i)=="table" then return i end
  return {i=i,j=j,k=k,r=r}
end}
Quaternion.ToEulerAngles=function(q) last_converted_quaternion=q;return {roll=0,pitch=0,yaw=-170} end
EulerAngles={new=function(roll,pitch,yaw) return {roll=roll,pitch=pitch,yaw=yaw} end}
facts={PostTowerFreeRoamActive=1,q307_active=0,q307_done=1,q307_finished=1,q307_2079=1}
playerPos={x=-1545.477905,y=1228.457642,z=11.520233,w=1}
bb={HighLevel=2,SceneTier=2,Locomotion=0,LocomotionDetailed=0,UpperBody=0}
function bb:GetInt(k) return self[k] or 0 end
function bb:GetBool(k) return false end
function GetAllBlackboardDefs() return {PlayerStateMachine={HighLevel="HighLevel",SceneTier="SceneTier",Locomotion="Locomotion",LocomotionDetailed="LocomotionDetailed",UpperBody="UpperBody",IsMovingHorizontally="moving"}} end
player={GetEntityID=function() return {hash=13806931541592989805ULL} end,
 GetWorldPosition=function() return playerPos end,
 GetWorldOrientation=function() return {i=0,j=0,k=0,r=1} end,
 GetPlayerStateMachineBlackboard=function() return bb end}
scene={IsEntityInScene=function() return false end,IsEntityInDialogue=function() return false end}
workspot={IsActorInWorkspot=function() return false end}
mounting={GetMountingInfoSingleWithObjects=function() return {parentId={hash=0ULL},childId={hash=13806931541592989805ULL},slotId={id="None"}} end}
teleporter={Teleport=function(self,p,position,orientation)
  assert(p==player)
  record("Teleport",{position=position,orientation=orientation})
  if teleport_error then error("MOCK native teleport failure") end
  -- Deliberately do not change playerPos. Requested is not arrived.
end}
Game={GetPlayer=function() return player end,
 GetQuestsSystem=function() return {GetFactStr=function(self,n) return facts[n] end} end,
 GetSceneSystem=function() return {GetScriptInterface=function() return scene end} end,
 GetWorkspotSystem=function() return workspot end,
 GetMountingFacility=function() return mounting end,
 GetTeleportationFacility=function() return teleporter end}
function attach() hooks["PlayerPuppet.OnGameAttached:after"](player) end
function detach() hooks["PlayerPuppet.OnDetach:before"](player) end
spatial={SyncRaycastByCollisionGroup=function(self,start,finish,group,a,b)
  assert(group=="Static" and a==true and b==false)
  rays[#rays+1]={start=start,finish=finish,group=group}
  return true,{position={x=start.x,y=start.y,z=23.2792433883},normal={x=0,y=0,z=1}}
end,Overlap=function(self,half,center,rotation,group)
  assert(group=="Static" or group=="Vehicle")
  assert(half.x==0.35 and half.y==0.35 and half.z>0.95 and half.w==0)
  overlaps[#overlaps+1]={half=half,center=center,rotation=rotation,group=group}
  return false
end}
NavGenAgentSize={Human=1};worldNavigationRequestStatus={OK=1}
navigation={IsNavmeshStreamedInLocation=function(self,p,radius)
  assert(radius==1.0);nav_queries[#nav_queries+1]=p;return true
end,FindPointInSphereOnlyHumanNavmesh=function(self,p,radius,agent,a)
  assert(radius==1.0 and agent==NavGenAgentSize.Human and a==false)
  return {status=worldNavigationRequestStatus.OK,point={x=p.x,y=p.y,z=23.2792433883}}
end,IsOnGround=function(self,p,radius) assert(p==player and radius==0.7);return true end}
Game.GetSpatialQueriesSystem=function() return spatial end
Game.GetNavigationSystem=function() return navigation end
survey={core=function()
  if core_error then error("MOCK required read failed") end
  local p=Game.GetPlayer()
  local mount=mounting:GetMountingInfoSingleWithObjects()
  return {facts=facts,player_exists=IsDefined(p),
    player_id=p and tostring(p:GetEntityID().hash):gsub("ULL$","") or "UNKNOWN",
    player_position=p and p:GetWorldPosition() or "UNKNOWN",orientation={i=0,j=0,k=0,r=1},
    in_scene=scene:IsEntityInScene(),in_dialogue=scene:IsEntityInDialogue(),
    in_workspot=workspot:IsActorInWorkspot(),
    mount_parent_id=tostring(mount.parentId.hash):gsub("ULL$","")},{},{player=p}
end,full=function(state,errors)
  if optional_error then error("MOCK optional survey unavailable") end
  state.optional_survey={status="UNKNOWN",not_runtime=true}
end,register=function(emit)
  if observer_register_error then error("MOCK optional observer registration unavailable") end
  optional_emit=emit;return {mock_observer=true}
end}
'''


class Fixture:
    def __init__(self, setup="", attached=True, wait=5, real_survey=False):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.globals().py_encode = lambda v: json.dumps(plain(v), sort_keys=True)
        self.lua.execute(SETUP)
        if real_survey:
            self.lua.globals().survey = self.lua.execute((MODULE / "ptfr_p4_survey.lua").read_text(encoding="utf-8"))
        target = self.lua.execute(TARGET.read_text(encoding="utf-8"))
        self.lua.globals().real_target = target
        self.lua.execute('function require(name) if name=="ptfr_p4_target" then return real_target elseif name=="ptfr_p4_survey" then return survey end error("unexpected module:"..name) end')
        self.run(setup)
        self.module = self.lua.execute(SOURCE.read_text(encoding="utf-8"))
        self.lua.globals().probe = self.module
        self.run("events.onInit()")
        if attached:
            self.run(f"attach();events.onUpdate({wait})")

    def run(self, code):
        return self.lua.execute(code)

    def calls(self):
        return [plain(v) for _, v in sorted(self.lua.globals().calls.items())]

    def rows(self, event=None):
        rows = [json.loads(v) for _, v in sorted(self.lua.globals().lines.items())]
        return [r for r in rows if event is None or r["event"] == event]

    def relocate(self):
        return self.module.RelocateToPersistentWorld()


def test_source_and_target():
    source = SOURCE.read_text(encoding="utf-8")
    mutations = re.findall(r":((?:Set|Change|Queue|Execute|Track|Untrack|Remove|Apply|Teleport|Force|Enable|Disable)\w*)\s*\(", source)
    assert mutations == ["Teleport"], mutations
    assert "Override(" not in source
    f = Fixture()
    target = plain(f.lua.globals().real_target)
    assert target["position"] == EXPECTED_TARGET
    assert target["orientation"] == EXPECTED_QUATERNION
    assert target["key"] == "wat_lch_dataterm_11"
    assert target["node_ref"].endswith("/#wat_lch_dataterm_11")
    assert math.isclose(target["support_z"], 23.2792433883, abs_tol=1e-10)


def test_automatic_baseline_is_read_only():
    f = Fixture(wait=2)
    assert not f.rows("BASELINE") and not f.calls()
    f.run("events.onUpdate(1)")
    row = f.rows("BASELINE")[-1]
    assert row["detail"]["automatic_read_only"] is True
    assert row["state"]["guard"]["passed"] is True
    assert row["state"]["player_id"] == "13806931541592989805"
    assert row["state"]["player_position"]["x"] == -1545.477905
    f.module.Inspect(); f.run("events.onUpdate(300);detach();attach();events.onUpdate(300)")
    assert not f.calls() and not f.rows("RELOCATION_REQUEST")


def test_exact_manual_single_request_no_fake_arrival():
    f = Fixture(); assert f.relocate() is True
    assert len(f.calls()) == 1
    call = f.calls()[0]
    assert call["kind"] == "Teleport"
    assert {k: call["position"][k] for k in EXPECTED_TARGET} == EXPECTED_TARGET
    assert plain(f.lua.globals().last_converted_quaternion) == EXPECTED_QUATERNION
    assert call["orientation"] == {"roll": 0, "pitch": 0, "yaw": -170}
    assert f.rows("RELOCATION_RETURNED")[-1]["detail"]["arrival_confirmed"] is False
    f.run("for i=1,100 do events.onUpdate(0.1) end;events.onUpdate(1)")
    assert not any(r["detail"].get("initial_arrival_evidence") == "SUPPORTED_TARGET_SAMPLES" for r in f.rows("ARRIVAL_SAMPLE"))
    assert f.rows("ARRIVAL_SAMPLE")[-1]["detail"]["near_target"] is False
    f.relocate(); f.run("detach();attach();events.onUpdate(5)"); f.module.Inspect(); f.relocate()
    assert len(f.calls()) == len(f.rows("RELOCATION_REQUEST")) == 1


def test_guards_and_fixture_neighborhood():
    facts = {"PostTowerFreeRoamActive": 1, "q307_active": 0, "q307_done": 1, "q307_finished": 1, "q307_2079": 1}
    for name, expected in facts.items():
        for value in (str(1-expected), "nil", '"UNKNOWN"'):
            f = Fixture(f"facts.{name}={value}"); assert f.relocate() is False
            assert not f.calls(), (name, value)
    for code in (
        "Game.GetPlayer=function() return nil end",
        "core_error=true",
        "scene.IsEntityInScene=function() return true end",
        "scene.IsEntityInDialogue=function() return true end",
        "workspot.IsActorInWorkspot=function() return true end",
        "scene.IsEntityInScene=function() return nil end",
        "mounting.GetMountingInfoSingleWithObjects=function() return {parentId={hash=2ULL}} end",
        "mounting.GetMountingInfoSingleWithObjects=function() error('missing') end",
        "playerPos.x=playerPos.x+26",
        "playerPos.z=playerPos.z+26",
        "playerPos.x=0/0",
        "playerPos.z=math.huge",
    ):
        f = Fixture(code); assert f.relocate() is False
        assert not f.calls(), code
    for options in ({"attached": False}, {"wait": 2}):
        f = Fixture(**options); assert f.relocate() is False and not f.calls()
    f = Fixture("ObserveBefore=function() error('missing detach hook') end")
    assert f.rows("INIT")[-1]["detail"]["hooks_registered"] is False
    assert f.relocate() is False and not f.calls()


def test_five_physical_samples_and_clearance_shapes():
    f = Fixture(); assert f.relocate() is True
    rays = [plain(v) for _, v in sorted(f.lua.globals().rays.items())]
    assert len(rays) == 5
    expected = [(0, 0), (0.3, 0), (-0.3, 0), (0, 0.3), (0, -0.3)]
    for ray, (dx, dy) in zip(rays, expected):
        assert math.isclose(ray["start"]["x"], EXPECTED_TARGET["x"]+dx, abs_tol=1e-8)
        assert math.isclose(ray["start"]["y"], EXPECTED_TARGET["y"]+dy, abs_tol=1e-8)
        assert math.isclose(ray["start"]["z"], EXPECTED_TARGET["z"]+0.20, abs_tol=1e-8)
        assert math.isclose(ray["finish"]["z"], 23.2792433883-0.15, abs_tol=1e-8)
    overlaps = [plain(v) for _, v in sorted(f.lua.globals().overlaps.items())]
    assert [v["group"] for v in overlaps] == ["Static", "Vehicle"]
    bottom, top = 23.2792433883+0.10, EXPECTED_TARGET["z"]+2.0
    assert all(math.isclose(v["center"]["z"], (top+bottom)/2, abs_tol=1e-8) for v in overlaps)
    assert all(math.isclose(v["half"]["z"], (top-bottom)/2, abs_tol=1e-8) for v in overlaps)
    preflight = f.rows("PREFLIGHT")[-1]["detail"]["target_check"]
    assert preflight["passed"] is True and preflight["floor_height_spread"] == 0


def test_bad_physics_shapes_and_nonfinite_fail_closed():
    ray_bodies = [
        "return false,nil", "return true,nil", "return nil,nil",
        "return {position={x=start.x,y=start.y,z=23.3}},true",
        "return true,{}", "return true,{position={},normal={}}",
        "error('query unavailable')",
    ]
    for z, nx, nz, x in (
        ("23.0", "0", "1", "start.x"),
        ("24.0", "0", "1", "start.x"),
        ("23.3", "0", "0.9", "start.x"),
        ("23.3", "0", "1.5", "start.x"),
        ("0/0", "0", "1", "start.x"),
        ("math.huge", "0", "1", "start.x"),
        ("23.3", "0/0", "1", "start.x"),
        ("23.3", "100", "1", "start.x"),
        ("23.3", "0", "1", "start.x+0.1"),
        ("23.3", "0", "1", "math.huge"),
    ):
        ray_bodies.append("return true,{position={x=%s,y=start.y,z=%s},normal={x=%s,y=0,z=%s}}" % (x, z, nx, nz))
    for body in ray_bodies:
        f = Fixture(f"spatial.SyncRaycastByCollisionGroup=function(self,start,finish,group,a,b) {body} end")
        assert f.relocate() is False and not f.calls(), body
    f = Fixture("raycount=0;spatial.SyncRaycastByCollisionGroup=function(self,start) raycount=raycount+1;return true,{position={x=start.x,y=start.y,z=raycount==1 and 23.2 or 23.5},normal={x=0,y=0,z=1}} end")
    assert f.relocate() is False and not f.calls(), "inconsistent accepted floor heights"
    for code in (
        "navigation.IsNavmeshStreamedInLocation=function() return false end",
        "navigation.IsNavmeshStreamedInLocation=function() return nil end",
        "navigation.IsNavmeshStreamedInLocation=function() return 1 end",
        "navigation.IsNavmeshStreamedInLocation=function() error('no residency') end",
        "navigation.FindPointInSphereOnlyHumanNavmesh=function() return nil end",
        "navigation.FindPointInSphereOnlyHumanNavmesh=function() return false end",
        "navigation.FindPointInSphereOnlyHumanNavmesh=function() return {} end",
        "navigation.FindPointInSphereOnlyHumanNavmesh=function() error('unsupported') end",
        "navigation.FindPointInSphereOnlyHumanNavmesh=function(self,p) return {status=99,point=p} end",
        "navigation.FindPointInSphereOnlyHumanNavmesh=function(self,p) return {status=1,point={x=p.x+1.1,y=p.y,z=p.z}} end",
        "navigation.FindPointInSphereOnlyHumanNavmesh=function(self,p) return {status=1,point={x=p.x,y=p.y,z=p.z+2}} end",
        "navigation.FindPointInSphereOnlyHumanNavmesh=function(self,p) return {status=1,point={x=p.x,y=p.y,z=p.z-0.7}} end",
        "navigation.FindPointInSphereOnlyHumanNavmesh=function(self,p) return {status=1,point={x=0/0,y=p.y,z=p.z}} end",
        "spatial.Overlap=function() return true end",
        "spatial.Overlap=function() return nil end",
        "spatial.Overlap=function() return 0 end",
        "spatial.Overlap=function() error('no overlap') end",
    ):
        f = Fixture(code); assert f.relocate() is False and not f.calls(), code


def test_optional_failure_does_not_block_core():
    f = Fixture("optional_error=true;observer_register_error=true")
    assert f.rows("BASELINE")[-1]["read_errors"]["optional_survey"]
    assert f.relocate() is True and len(f.calls()) == 1


def test_real_survey_absent_optional_services_smoke():
    # All three shipped Lua modules execute here. Most optional native APIs are
    # intentionally absent; valid core/physics mocks alone must permit request.
    survey_source = (MODULE / "ptfr_p4_survey.lua").read_text(encoding="utf-8")
    assert not re.search(r":(?:Set|Change|Queue|Execute|Track|Untrack|Remove|Apply|Teleport|Force|Enable|Disable)\w*\s*\(", survey_source)
    f = Fixture(real_survey=True)
    row = f.rows("BASELINE")[-1]
    assert row["state"]["guard"]["passed"] is True
    assert row["state"]["player_id"] == "13806931541592989805"
    assert row["state"]["saving_locked"] == "UNKNOWN"
    assert row["state"]["journal"]["active_quests"] == "UNKNOWN"
    assert row["state"]["systems"]["vehicles"]["owned"] == "UNKNOWN"
    assert row["read_errors"]
    f.run('hooks["NPCPuppet.OnGameAttached:after"](nil);hooks["VehicleObject.OnGameAttached:after"](nil)')
    assert f.rows("NPC_ATTACHED")[-1]["detail"]["id"] == "UNKNOWN"
    assert f.rows("NPC_ATTACHED")[-1]["detail"]["read_errors"]
    assert f.relocate() is True and len(f.calls()) == 1


def test_nil_physics_values_are_explicit_unknown():
    f = Fixture("spatial.SyncRaycastByCollisionGroup=function() return nil,nil end;navigation.IsNavmeshStreamedInLocation=function() return nil end;spatial.Overlap=function() return nil end")
    assert f.relocate() is False and not f.calls()
    row = f.rows("PREFLIGHT")[-1]
    target = row["detail"]["target_check"]
    assert target["navmesh"] == "UNKNOWN"
    assert target["clearance"] == {"Static": "UNKNOWN", "Vehicle": "UNKNOWN"}
    assert all(sample["hit"] == "UNKNOWN" for sample in target["floor_samples"].values())
    assert row["read_errors"]["navmesh"] and row["read_errors"]["clearance_Static"]
    assert all(row["read_errors"][f"floor_{i}"] for i in range(1, 6))


def test_error_consumes_once_before_dispatch_and_reload():
    f = Fixture("teleport_error=true")
    assert f.relocate() is False and len(f.calls()) == 1
    returned = f.rows("RELOCATION_RETURNED")[-1]["detail"]
    assert returned["call_returned"] is False and returned["arrival_confirmed"] is False
    f.run("teleport_error=false"); f.relocate()
    f.run("detach();attach();events.onUpdate(5)"); f.module.Inspect(); f.relocate()
    assert len(f.calls()) == 1
    f = Fixture("teleporter.Teleport=function(self,p,pos,orientation) record('Teleport',{});assert(probe.RelocateToPersistentWorld()==false);error('side effect already issued') end")
    f.relocate(); f.relocate(); assert len(f.calls()) == 1


def test_logging_failures_stop_before_world_write():
    for event in ("RELOCATION_BEFORE", "PREFLIGHT", "RELOCATION_REQUEST"):
        for mode in ("fail_write", "fail_flush"):
            f = Fixture(); f.run(f'{mode}="{event}"'); f.relocate()
            assert not f.calls(), (event, mode)
            f.run(f"{mode}=nil"); f.module.Inspect(); f.relocate()
            assert not f.calls(), "failed trace must latch guard closed"
    f = Fixture("fail_open=true", attached=False); f.relocate()
    assert not f.calls() and not f.rows()
    f = Fixture(); f.run('fail_write="OBSERVER_EVENT";optional_emit("OBSERVER_EVENT",{})')
    f.relocate(); assert not f.calls(), "observer log failure must not crash or allow relocation"


def test_load_invalidates_pending_and_identity():
    f = Fixture(); f.relocate(); f.run("detach();events.onUpdate(30);attach();events.onUpdate(30)")
    assert not f.rows("ARRIVAL_SAMPLE") and len(f.calls()) == 1
    f = Fixture(); f.relocate()
    f.run("player.GetEntityID=function() return {hash=2ULL} end;events.onUpdate(0.1)")
    assert f.rows("ARRIVAL_CANCELLED") and not f.rows("ARRIVAL_SAMPLE")


def test_arrival_is_readback_and_reports_are_nonmutating():
    f = Fixture(); f.relocate()
    f.run("playerPos={x=-1658.87463,y=997.365662,z=23.3,w=1};for i=1,120 do events.onUpdate(0.11) end")
    samples = f.rows("ARRIVAL_SAMPLE")
    assert any(r["detail"].get("initial_arrival_evidence") == "SUPPORTED_TARGET_SAMPLES" for r in samples)
    milestone = next(r for r in samples if r["detail"].get("milestone") == 10)
    assert 10 <= milestone["detail"]["seconds_after_request"] < 10.2
    assert len(f.calls()) == 1
    f.module.Report("traffic", "WORKING", "human test note")
    f.module.Report("phone", "UNKNOWN", "not tried")
    assert len(f.rows("HUMAN_REPORT")) == 2
    assert f.module.Report("invalid", "WORKING", "no") is False
    assert f.module.Report("map", "SUCCESS", "no") is False
    assert len(f.calls()) == 1 and len(f.rows("HUMAN_REPORT")) == 2
    f.run("events.onShutdown()")
    assert f.rows("SHUTDOWN")


def main():
    tests = [test_source_and_target, test_automatic_baseline_is_read_only,
             test_exact_manual_single_request_no_fake_arrival, test_guards_and_fixture_neighborhood,
             test_five_physical_samples_and_clearance_shapes, test_bad_physics_shapes_and_nonfinite_fail_closed,
             test_optional_failure_does_not_block_core, test_nil_physics_values_are_explicit_unknown,
             test_real_survey_absent_optional_services_smoke,
             test_error_consumes_once_before_dispatch_and_reload,
             test_logging_failures_stop_before_world_write, test_load_invalidates_pending_and_identity,
             test_arrival_is_readback_and_reports_are_nonmutating]
    for test in tests:
        test(); print("PASS:", test.__name__)
    print("NOT RUNTIME VALIDATION: real init/target, mostly mocked survey plus real-survey missing-service smoke; all CET APIs mocked. No game/save writes or actual arrival.")


if __name__ == "__main__":
    main()
