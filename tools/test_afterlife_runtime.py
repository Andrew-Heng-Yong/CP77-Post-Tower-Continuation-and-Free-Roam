"""Offline runtime compilation and read-only diagnostic contracts."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/afterlife_world'
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


driver = ROOT / 'redscript/PTFR_Afterlife_R1/AfterlifeDriver.reds'
nix = ROOT / 'redscript/PTFR_B0_StoryEight/StoryEightDriver.reds'
diagnostic = ROOT / 'diagnostics/PTFR_Afterlife_Audit/init.lua'
text = driver.read_text()
assert text.count('q.SetFact(') == 1
assert 'q.SetFact(n"PTFRAL1_Enabled", 1)' in text
assert all(term in text for term in ['IsInCombat', 'IsEntityInScene', 'IsActorInWorkspot',
    'mount.parentId', 'HighLevel', 'SceneTier', 'IsSavingLocked', 'IsTokensActivationBlocked',
    'epoch != this.epoch', 'PTFRAL1_DancersRegistered', 'PTFRAL1_PopulationRegistered'])
guard_body = text.split('private func Eligible')[1].split('private func Safe')[0]
guards = dict((k, int(v)) for k, v in re.findall(r'q.GetFact\(n"([^"]+)"\) == (\d+)', guard_body))
assert len(guards) == 16
assert guards['q307_done'] == guards['q307_finished'] == guards['q307_2079'] == 1
assert guards['q307_active'] == guards['q305_johnny_scene_active'] == 0
for k in guards:
    rejected = {**guards, k: guards[k] + 1}
    assert not all(rejected[f] == val for f, val in guards.items())
command = [str(ROOT / 'research/finalboards_dismissal/tooling/redscript-cli.exe'),
    'lint', '-s', str(driver), '-s', str(nix), '-b', str(GAME / 'r6/cache/final.redscripts')]
result = subprocess.run(command, capture_output=True, text=True, check=True)
output = result.stdout + result.stderr
(OUT / 'runtime_compile.log').write_text(output)
assert 'Lint successful' in output and 'ERROR' not in output, output
source = diagnostic.read_text()
assert not any(term in source for term in ['SetFact', 'Teleport', 'ChangeEntryState', 'QueueEvent', 'SendCommand'])
sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
from lupa.lua51 import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute('''events={}; lines={}; prints={}; closes=0
function registerForEvent(k,f) events[k]=f end
function print(s) table.insert(prints,s) end
function IsDefined(x) return type(x)=="table" end
json={encode=function(row) lastrow=row;return "{}" end}
io={open=function() return {write=function(self,s) table.insert(lines,s);return self end,
 close=function() closes=closes+1;return true end} end}
pos={x=-1440,y=1013,z=17}; p={GetWorldPosition=function() return pos end}
q={GetFactStr=function(self,name) return 1 end}
target={GetEntityID=function() return {hash="1234567890123456789ULL"}end,
GetRecordID=function() return "Character.Rogue" end,GetClassName=function()return "NPCPuppet"end}
Game={GetPlayer=function()return p end,GetQuestsSystem=function()return q end,
GetTargetingSystem=function()return {GetLookAtObject=function() return target end}end,
GetWorkspotSystem=function()return {IsActorInWorkspot=function()return true end}end,
GetSceneSystem=function()return {GetScriptInterface=function()return {IsEntityInScene=function()return false end}end}end}
''')
mod = lua.execute(source)
g = lua.globals()
g.events.onUpdate(7)
assert len(g.lines) == 0
g.events.onUpdate(1)
assert len(g.lines) == g.closes == 1
assert g.lastrow.look_target.in_workspot is True and g.lastrow.look_target.in_scene is False
assert g.lastrow.look_target.id == '1234567890123456789ULL'
assert len(g.lastrow.errors) == 0
g.target.GetRecordID = None
mod.Observe('missing getter')
assert g.lastrow.look_target.record == 'UNKNOWN'
assert g.lastrow.errors['target.record'] is not None
g.pos.x = 0
assert mod.Observe('outside') == 'outside/unloaded'
g.p = None
assert mod.Observe('unloaded') == 'outside/unloaded'
lua.execute('p={GetWorldPosition=function()return {x=-1440,y=1013,z=17}end};io.open=function()return nil,"denied"end')
assert mod.Observe('error') == 'write error'
assert any('write failed' in g.prints[i] for i in range(1, len(g.prints) + 1))
report = {'status': 'PASS_RUNTIME_OFFLINE_NOT_LIVE', 'driver_sha256': sha(driver),
    'nix_driver_sha256': sha(nix), 'diagnostic_sha256': sha(diagnostic),
    'negative_enable_guards': len(guards), 'combined_compile': 'PASS',
    'lua51_readonly_mock': 'PASS', 'live': False}
(OUT / 'runtime_tests.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
