"""Offline LuaJIT checks for the two explicit, position-guarded shop exits."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime
from test_phase2b_p2_probe import SETUP, plain

SOURCE = ROOT / "diagnostics/PTFR_Phase2B_P3_ShopExitProbe/init.lua"

EXTRA = r'''
shopID=4444ULL
doorPos={x=-1541.55261,y=1203.99646,z=15.8699999}
playerPos={x=-1540.8,y=1203.8,z=15.87}
player.GetWorldPosition=function() return playerPos end
shopdoor={GetEntityID=function() return {hash=shopID} end,
 GetWorldPosition=function() return doorPos end,
 GetClassName=function() return "Door" end,
 GetDevicePS=function() return ps end}
Game.GetTargetingSystem=function() return {GetLookAtObject=function() return shopdoor end} end
action.IsA=function(self,name) return name=="QuestForceOpen" end
ps.GetQuestActionByName=function(self,name)
 assert(self==ps and name=="ForceOpen")
 return action
end
ps.ExecutePSAction=function(self,a,target)
 assert(self==ps and target==ps and a==action)
 record("ForceOpen",{id=tostring(shopID),same_ps=true})
 if forceError then error("mock native queue failed") end
 if not asyncForce then
  doorState.IsOpen=true;doorState.IsLocked=false;doorState.IsSealed=false
 end
end
'''


class Fixture:
    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.globals().py_encode = lambda value: json.dumps(plain(value), sort_keys=True)
        self.lua.execute(SETUP)
        self.lua.execute(EXTRA)
        self.module = self.lua.execute(SOURCE.read_text(encoding="utf-8"))
        self.run("events.onInit();attach();events.onUpdate(5)")

    def run(self, text):
        return self.lua.execute(text)

    def calls(self):
        return [plain(value) for _, value in sorted(self.lua.globals().calls.items())]

    def rows(self, event=None):
        rows = [json.loads(value) for _, value in sorted(self.lua.globals().lines.items())]
        return [row for row in rows if event is None or row["event"] == event]


def test_no_automatic_action():
    f = Fixture()
    f.run("events.onUpdate(15)")
    assert not f.calls()
    assert not f.rows("EXIT_REQUESTED")


def test_back_then_front_once_each():
    f = Fixture()
    f.module.InspectDoor()
    row = f.rows("EXIT_BASELINE")[-1]
    assert row["state"]["exit_target"]["slot"] == "BACK"
    assert row["state"]["exit_target"]["alias_runtime_verified"] == "UNKNOWN"
    f.module.OpenDoor()
    f.run("events.onUpdate(2);events.onUpdate(8)")
    assert len(f.calls()) == 1
    assert [r["detail"]["delay_s"] for r in f.rows("EXIT_STABILITY")] == [2, 10]
    assert f.rows("EXIT_STABILITY")[-1]["state"]["exit_target"]["device"]["IsOpen"] is True
    f.module.OpenDoor()
    assert len(f.calls()) == 1
    f.run('shopID=5555ULL;doorPos={x=-1547.74341,y=1190.8916,z=16.2615986};playerPos={x=-1547,y=1191,z=16.26};doorState.IsOpen=false;doorState.IsLocked=true')
    f.module.InspectDoor();f.module.OpenDoor()
    assert [c["kind"] for c in f.calls()] == ["ForceOpen", "ForceOpen"]
    assert [r["stage"] for r in f.rows("EXIT_REQUESTED")] == ["BACK", "FRONT"]


def test_wrong_location_and_missing_target_rejected():
    for code in (
        "doorPos.x=doorPos.x+3",
        "playerPos.x=playerPos.x+10",
        "shopdoor.GetDevicePS=function() return nil end",
        "Game.GetTargetingSystem=function() return {GetLookAtObject=function() return nil end} end",
        "ps.IsA=function() return false end",
    ):
        f=Fixture();f.run(code);f.module.InspectDoor();f.module.OpenDoor()
        assert not f.calls(), code
        assert not f.rows("EXIT_REQUESTED"), code


def test_guard_baseline_and_gates():
    f=Fixture();f.module.OpenDoor();assert not f.calls()
    for code in ("facts.q307_2079=0", "facts.q307_done=nil", "doorState.IsDisabled=true", "doorState.IsBusy=true", "doorState.IsUnpowered=true"):
        f=Fixture();f.module.InspectDoor();f.run(code);f.module.OpenDoor()
        assert not f.calls(), code


def test_error_has_no_retry_and_load_invalidates_baseline():
    f=Fixture();f.module.InspectDoor();f.run("forceError=true");f.module.OpenDoor()
    assert len(f.calls())==1
    f.run("forceError=false");f.module.OpenDoor()
    assert len(f.calls())==1
    f.run("detach();attach();events.onUpdate(5)")
    f.module.OpenDoor()
    assert len(f.calls())==1


def test_no_door_identity_rounding():
    f=Fixture()
    f.run("shopID=13806931541592989805ULL")
    f.module.InspectDoor()
    assert f.rows("EXIT_BASELINE")[-1]["state"]["exit_target"]["id"] == "13806931541592989805"


def test_room_requires_original_exact_entity_id():
    f=Fixture()
    f.run("doorPos={x=-1548.02454,y=1221.40918,z=12.1014214};playerPos={x=-1548,y=1221,z=12.1}")
    f.module.InspectDoor();f.module.OpenDoor()
    assert not f.calls(), "same-position impostor must not be opened"
    f.run("shopID=13806931541592989805ULL")
    f.module.InspectDoor()
    assert f.rows("EXIT_BASELINE")[-1]["state"]["exit_target"]["position_match_verified"] is True
    f.module.OpenDoor()
    assert len(f.calls())==1
    assert f.rows("EXIT_REQUESTED")[-1]["stage"]=="ROOM"


def main():
    for test in (test_no_automatic_action,test_back_then_front_once_each,
                 test_wrong_location_and_missing_target_rejected,test_guard_baseline_and_gates,
                 test_error_has_no_retry_and_load_invalidates_baseline,test_no_door_identity_rounding,
                 test_room_requires_original_exact_entity_id):
        test()
        print("PASS:",test.__name__)
    print("Offline mocks only; CET target resolution and native door effects remain untested.")


if __name__ == "__main__":
    main()
