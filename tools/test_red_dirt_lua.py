"""Lua51 sandbox tests; no game or filesystem writes by the simulated helper."""
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'research/phase2b_p0/tooling/python'))
from lupa.lua51 import LuaRuntime

lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
events={}; facts={}; writes={}; busy=false; combat=false; workspot=false; openFail=false; writeFail=false; dist=3
function registerForEvent(n,f) events[n]=f end
json={encode=function(v) return '{}' end}
io={open=function()
 if openFail then return nil end
 return {seek=function() return 0 end,write=function() if writeFail then return nil end return true end,
 flush=function() return true end,close=function() end}
end}
q={GetFactStr=function(self,n) return facts[n] or 0 end,
 SetFactStr=function(self,n,v) facts[n]=v; writes[#writes+1]=n end}
p={GetWorldPosition=function() return {x=-733.1105+dist,y=-983.636,z=8.011} end,
 IsInCombat=function() return combat end,GetEntityID=function() return 1 end}
Game={GetPlayer=function() return p end,GetQuestsSystem=function() return q end,
 GetSceneSystem=function() return {GetScriptInterface=function() return {IsEntityInScene=function() return busy end} end} end,
 GetWorkspotSystem=function() return {IsActorInWorkspot=function() return workspot end} end}
''')
g = lua.globals()
expected = dict(PostTowerFreeRoamActive=1, PTFRP0_DR13=1, q307_active=0,
                q307_done=1, q307_finished=1, q307_2079=1, q307_main_game_killed=1,
                q305_johnny_scene_active=0, q115_point_of_no_return=0,
                mirror_interaction_disabled=0, PTFRBASE_Suspended=0,
                PTFRBM42_Interrupted=0, PTFRBM42_Enabled=0, PTFRBM42_Active=0)
expected['sq011_mirror_off '] = 0
for name, value in expected.items():
    g.facts[name] = value
m = lua.execute((root / 'diagnostics/PTFR_RedDirt_Mirror/init.lua').read_text())
for name, value in expected.items():
    g.facts[name] = 1 - value
    assert m.Start() is False, name
    g.facts[name] = value
assert len(g.writes) == 0
for flag in ('busy', 'combat', 'workspot'):
    g[flag] = True
    assert m.Start() is False, flag
    g[flag] = False
# Regression: arming is permission only; allow it far from the bartender.
g.dist = 2000
g.openFail = True
assert m.Start() is False
g.openFail = False
g.writeFail = True
assert m.Start() is False
g.writeFail = False
assert len(g.writes) == 0
assert m.Start() is True
assert m.Start() is False
assert g.facts.PTFRBM42_Enabled == 1
g.events.onUpdate(1)
g.dist = 3
assert m.Stop() is False  # still near
g.dist = 20
g.facts.PTFRBM42_Active = 1
assert m.Stop() is False
g.facts.PTFRBM42_Active = 0
g.busy = True
assert m.Stop() is False
g.busy = False
assert m.Stop() is True
assert g.facts.PTFRBM42_Enabled == 0
assert set(g.writes.values()) == {'PTFRBM42_Enabled'}
before = len(g.writes)
g.events.onShutdown()
assert len(g.writes) == before
print('PASS: Lua51 remote arm at 2000m, independent busy guards, logging failure before arm, busy/near Stop refusals, scoped writes and shutdown')
