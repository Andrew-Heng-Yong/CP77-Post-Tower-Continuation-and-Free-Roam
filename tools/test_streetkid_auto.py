"""Offline structural/lifecycle contracts. Not an engine or live save-load test."""
import json,sys,binascii,re
from pathlib import Path
from audit_scene_actor_ids import audit_scene_actor_ids,walk
from test_streetkid_scene_load_s3 import quest_edges
R=Path(__file__).resolve().parent.parent
A=R/'research/b0_streetkid_auto'
def read(n):return json.loads((A/(n+'.json')).read_text())['Data']['RootChunk']
s=read('seat_mirror');g=read('gate');o=read('owner')
audit_scene_actor_ids(s)
nodes={n['Data']['nodeId']['id']:n['Data'] for n in s['sceneGraph']['Data']['graph']}
assert len(nodes)==30
def dest(i,j=0):return [d['nodeId']['id'] for d in nodes[i]['outputSockets'][j]['destinations']]
assert dest(1)==[4,3030] and dest(4)==[3031] and dest(3031)==[595] and dest(3030)==[2000]
assert nodes[3031]['questNode']['Data']['type']['Data']['factName']=='PTFRSKA_Using'
conditions=nodes[3030]['questNode']['Data']['condition']['Data']['conditions']
assert {c['Data']['type']['Data']['factName']:c['Data']['type']['Data']['value'] for c in conditions}=={'PTFRSKA_Depart':1,'PTFRSKA_Using':0}
edges,onodes=quest_edges(o)
assert {(0,'Out',10,'In'),(10,'Out',26,'In'),(26,'Out',27,'In'),(27,'Out',28,'In'),(28,'Out',1,'In'),(6,'Out',9,'In'),(9,'Out',10,'In')} <= edges
assert not any(e[0]==8 for e in edges) # interruptions cannot automatically rearm
assert next(n for n in onodes if n['id']==9)['condition']['Data']['type']['Data']['seconds']==1
for root in [g,o,s]:
 for _,v in walk(root):
  if isinstance(v,dict) and v.get('$type')=='questSetVar_NodeType': assert v['factName'].startswith('PTFRSKA_')
guard=next(n['Data'] for n in g['graph']['Data']['nodes'] if n['Data']['id']==2)['condition']['Data']
loop=next(n for n in onodes if n['id']==10)['condition']['Data']
assert {x['Data']['type']['Data']['factName']:x['Data']['type']['Data']['value'] for x in guard['conditions']}=={x['Data']['type']['Data']['factName']:x['Data']['type']['Data']['value'] for x in loop['conditions']}
facts={x['Data']['type']['Data']['factName']:x['Data']['type']['Data']['value'] for x in guard['conditions']}
for k in ['PTFRSKS2_Enabled','PTFRSKS2_Active','PTFRBASE_Suspended','PTFRSKA_Suspended','PTFRSKA_Interrupted']:assert facts[k]==0
assert facts['q307_done']==facts['q307_2079']==facts['q000_done']==1
# All pre-existing action payloads survive modulo private identities/added links.
prior=json.loads((R/'research/b0_streetkid_seat_mirror_s2/scene.json').read_text())['Data']['RootChunk']
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in ['HandleId','HandleRefId']}
 if isinstance(v,list):return [clean(x) for x in v]
 if isinstance(v,str):return v.replace('PTFRSKS2','PTFRSKA').replace('streetkid_seat_mirror_s2','streetkid_seat_auto')
 return v
for n in prior['sceneGraph']['Data']['graph']:
 ident=n['Data']['nodeId']['id']
 if ident not in [1,4]:assert clean(n['Data'])==clean(nodes[ident]),ident
for key in ['actors','playerActors','props','workspots','workspotInstances','locStore','screenplayStore']:assert clean(prior[key])==clean(s[key]),key
lua=(R/'diagnostics/PTFR_Streetkid_Auto/init.lua').read_text()
assert 'SetFact' not in lua
driver=(R/'redscript/PTFR_Streetkid_Auto/StreetkidAuto.reds').read_text()
assert set(re.findall(r'this.Set\(q,n"([^"]+)"',driver))=={'PTFRSKA_Depart','PTFRSKA_Enabled'}
assert 'this.Safe(p)' in driver and 'd2 <= 4.84' in driver and 'd2 > 49.0' in driver
# Registration identity must not collide with any other project phase path.
path='towercontinued\\streetkid_seat_auto\\gate.questphase'
crc=binascii.crc_hqx((path+':1').encode(),65535)
for f in (R/'archive').rglob('*.xl'):
 for p in re.findall(r'path:\s*([^\s#]+\.questphase)',f.read_text(encoding='utf-8-sig')):
  if p!=path:assert binascii.crc_hqx((p+':1').encode(),65535)!=crc,(f,p)
# Read-only Lua syntax/lifecycle smoke test using existing Lua51 runtime.
sys.path.insert(0,str(R/'research/phase2b_p0/tooling/python'))
from lupa.lua51 import LuaRuntime
l=LuaRuntime();l.execute('events={};writes=0; function registerForEvent(n,f) events[n]=f end; json={encode=function(v) return "{}" end}; io={open=function() return {write=function() return true end,close=function() end} end}; Game={GetQuestsSystem=function() return {GetFactStr=function() return 0 end,SetFactStr=function() writes=writes+1 end} end}')
m=l.execute(lua);l.globals().events['onInit']();l.globals().events['onUpdate'](1)
for name in ['Start','Stop','Finish','Inspect']:m[name]()
assert l.globals().writes==0
print('PASS: native repeat/unused-prompt departure/fail-closed interrupt, unchanged actions, scoped runtime, registration',crc,'and read-only Lua51')
