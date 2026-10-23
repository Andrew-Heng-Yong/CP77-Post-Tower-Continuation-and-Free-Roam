"""Auto bootstrap contracts; not a live engine/save-reload simulation."""
import binascii
import hashlib
import json
import re
import sys
from pathlib import Path
from test_streetkid_scene_load_s3 import quest_edges

root = Path(__file__).resolve().parents[1]
audit = root / 'research/b0_red_dirt_auto'
def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
manifest = read(audit / 'manifest.json')
auto = read(audit / 'bootstrap.json')['Data']['RootChunk']
c5 = read(root / 'research/b0_mirror_rollout/validation_c5_red_dirt/gate.json')['Data']['RootChunk']
edges, nodes = quest_edges(auto)
assert len(nodes) == 4
assert edges == {(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In')}
assert auto['phasePrefabs'] == []
assert {n['$type'] for n in nodes} == {'questInputNodeDefinition','questPauseConditionNodeDefinition','questFactsDBManagerNodeDefinition','questOutputNodeDefinition'}

def normalize(x):
    if isinstance(x, dict):
        return {k: normalize(v) for k,v in x.items() if k not in ('HandleId','HandleRefId')}
    if isinstance(x, list):
        return [normalize(v) for v in x]
    return x

base_guard = next(n['Data']['condition']['Data'] for n in c5['graph']['Data']['nodes'] if n['Data']['id'] == 1)
base_guard['conditions'] = [c for c in base_guard['conditions'] if c['Data'].get('type',{}).get('Data',{}).get('factName') != 'PTFRBM42_Enabled']
guard = next(n['condition']['Data'] for n in nodes if n['id'] == 1)
assert normalize(guard) == normalize(base_guard), 'Only remove the manual permission prerequisite'
assert guard['operation'] == 'AND'
facts = {c['Data']['type']['Data']['factName']:c['Data']['type']['Data']['value'] for c in guard['conditions'] if c['Data']['$type']=='questFactsDBCondition'}
assert len(facts) == 13
assert facts['sq011_mirror_off '] == facts['PTFRBM42_Interrupted'] == facts['PTFRBASE_Suspended'] == 0
assert facts['q307_done'] == facts['q307_2079'] == facts['q307_finished'] == 1
writer = next(n['type']['Data'] for n in nodes if n['id'] == 2)
assert writer['factName'] == 'PTFRBM42_Enabled' and writer['value'] == 1 and writer['setExactValue'] == 1
path = manifest['resource']
crc = binascii.crc_hqx((path + ':1').encode(), 65535)
assert crc == manifest['registration_id']
for f in (root/'archive').rglob('*.xl'):
    for p in re.findall(r'path:\s*([^\s#]+\.questphase)', f.read_text(encoding='utf-8-sig')):
        if p != path:
            assert binascii.crc_hqx((p+':1').encode(),65535) != crc, (f,p)
archive = root/'build/RedDirt_Auto/TowerContinued_RedDirt_Auto.archive'
assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest['archive_sha256']
# Existing native resources have not been rebuilt for auto integration.
receipt = read(root/'research/b0_mirror_rollout/validation_c5_red_dirt/install_receipt.json')
for i,name in enumerate(['TowerContinued_OrdinaryMirrors_C5_RED_DIRT.archive','TowerContinued_OrdinaryMirrors_C5_RED_DIRT.archive.xl']):
    assert hashlib.sha256((root/'build/OrdinaryMirrors_C5_RED_DIRT'/name).read_bytes()).hexdigest().upper() == receipt['sha256'][i]

lua_source=(root/'diagnostics/PTFR_RedDirt_Auto/init.lua').read_text()
assert 'SetFact' not in lua_source and 'Teleport' not in lua_source
sys.path.insert(0,str(root/'research/phase2b_p0/tooling/python'))
from lupa.lua51 import LuaRuntime
l=LuaRuntime()
l.execute('''
 events={}; writes=0
 function registerForEvent(n,f) events[n]=f end
 json={encode=function(v) return '{}' end}
 io={open=function() return {write=function() return true end,flush=function() return true end,close=function() end} end}
 Game={GetQuestsSystem=function() return {GetFactStr=function() return 0 end,SetFactStr=function() writes=writes+1 end} end}
''')
m=l.execute(lua_source)
l.globals().events.onInit()
l.globals().events.onUpdate(1)
for name in ('Observe','Inspect','Start','Stop','Finish'):
    m[name]()
l.globals().events.onShutdown()
assert l.globals().writes == 0
print('PASS: automatic bootstrap preserves C5 guard/owner, sole mod-permission writer, collision-free registration, archive hashes and read-only Lua51 lifecycle')
