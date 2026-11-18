"""Independent cooked-graph, eligibility and captured-state checks."""
import copy
import hashlib
import itertools
import json
import struct
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phone_support_ph1'))
from model import model,read,sha,walk
TAG='PTFRS29_mq016_bartmoss_'

def evaluate(c,facts,journals,token=False,blocked=False):
 t=c['$type']
 if t=='questLogicalCondition':
  values=[evaluate(x,facts,journals,token,blocked) for x in c['conditions']]
  return all(values) if c['operation']=='AND' else any(values)
 t=c['type'];kind=t['$type']
 if kind=='questVarComparison_ConditionType':
  assert t['comparisonType']=='Equal'
  return facts[t['factName']]==t['value']
 if kind=='questJournalEntryState_ConditionType':
  assert t['inverted']==0
  return journals[t['path']['realPath']]==t['state']
 if kind=='questContentToken_ConditionType':
  assert t['type']=='MinorQuestAndSts';return token
 if kind=='questContentLock_ConditionType':return blocked==bool(t['isContentBlocked'])
 raise AssertionError(kind)

def main():
 pins=read(HERE/'work/inputs.json');rb=read(HERE/'work/graph_01/readback.json')
 assert sha(rb['path'])==rb['sha256'] and sha(rb['path']+'.json')==rb['export_sha256']
 before=model(pins['root']['json']);after=model(rb['path']+'.json');checks=[]
 def check(ok,label):assert ok,label;checks.append(label)
 check(before.keys()==after.keys(),'All graph identities retained')
 for gp,g in before.items():
  other=after[gp];check(g['edges']==other['edges'],gp+' edges unchanged')
  check(g['nodes'].keys()==other['nodes'].keys(),gp+' nodes unchanged')
  for nid,node in g['nodes'].items():
   if gp=='root' and nid==196:
    a=copy.deepcopy(other['nodes'][nid]);a['condition']=node['condition']
    check(a==node,'196 only condition differs')
   else:check(node==other['nodes'][nid],f'{gp}:{nid} unchanged')
 # Resource-level prefab ownership and all non-graph fields must be identical.
 olddoc,newdoc=read(pins['root']['json']),read(rb['path']+'.json')
 check({k:v for k,v in olddoc['Data']['RootChunk'].items() if k!='graph'}==
       {k:v for k,v in newdoc['Data']['RootChunk'].items() if k!='graph'},'Root support fields unchanged')
 old=before['root']['nodes'][196]['condition'];new=after['root']['nodes'][196]['condition']
 check(new['operation']=='AND' and len(new['conditions'])==2,'Original outer AND retained')
 check(new['conditions'][1]==old['conditions'][1],'mq015_active==0 retained exactly')
 alt=new['conditions'][0];check(alt['operation']=='OR' and len(alt['conditions'])==2,'Two disjoint setup states')
 prepared,fresh=alt['conditions']
 check(fresh['operation']=='AND' and fresh['conditions'][1]==old['conditions'][0],'Original fresh token retained exactly')
 check(fresh['conditions'][0]['type']['factName']=='mq016_active' and fresh['conditions'][0]['type']['value']==0,'Fresh requires active zero')
 expected=copy.deepcopy(before['root']['nodes'][65004]['condition'])
 for d in walk(expected):
  if d.get('factName')==TAG+'Issued':check(d['value']==0,'Original receipt zero');d['value']=1
 check(prepared['operation']=='AND' and prepared['conditions'][:-2]==expected['conditions'],'Entire existing guard repeated with Issued1')
 check(prepared['conditions'][-2]['type']['factName']=='mq016_active' and prepared['conditions'][-2]['type']['value']==1,'Prepared requires active one')
 check(prepared['conditions'][-1]=={'$type':'questContentCondition','type':{'$type':'questContentLock_ConditionType','isContentBlocked':0}},'Prepared waits for native content unlock')
 facts={d['factName']:d['value'] for d in walk(expected) if d.get('$type')=='questVarComparison_ConditionType'}
 facts.update(mq016_active=1,mq015_active=0)
 journals={d['path']['realPath']:d['state'] for d in walk(expected) if d.get('$type')=='questJournalEntryState_ConditionType'}
 check(len(journals)==63,'All 63 journal protections present')
 for active,token,blocked,mq015 in itertools.product((-1,0,1,2),(False,True),(False,True),(0,1)):
  f=facts|{'mq016_active':active,'mq015_active':mq015}
  want=mq015==0 and ((active==0 and token) or (active==1 and not blocked))
  check(evaluate(new,f,journals,token,blocked)==want,f'Gate matrix {active,token,blocked,mq015}')
 for name,value in facts.items():
  if name in ('mq016_active','mq015_active'):continue
  for changed in (-1,value+1):
   for token in (False,True):
    check(not evaluate(new,facts|{name:changed},journals,token),f'Prepared rejects {name}={changed}, token={token}')
 for path in journals:
  for state in ('Active','Succeeded','Failed'):
   for token in (False,True):
    check(not evaluate(new,facts,journals|{path:state},token),f'Prepared rejects journal {path}={state}, token={token}')
 owners=read(HERE.parent/'installed_qualification_20261115_02/manual31_32_owner.json')['saves']
 native=lambda s:[h for h in s['handlers'] if h['route'].startswith('0/2/82/6/5') or (h['route']=='0/2/82/6' and h['node']==5)]
 check(len(native(owners[0]))==6 and not native(owners[1]),'Six native pre-Tower handlers; none post-Tower')
 check(any(h['route']=='0/2/82/6/5/2' and h['node']==5 for h in native(owners[0])),'Pre-Tower freezer approach wait captured')
 scheduler=[]
 for s in read(HERE/'work/content_saves_02.json')['saves']:
  n,=s['selected'];raw=bytes.fromhex(n['header_hex'])
  state,timer,block_count,event_count,queued=struct.unpack('<IfIII',raw)
  check(state==block_count==event_count==queued==0,s['slot']+' idle scheduler with no queued token')
  scheduler.append(dict(slot=s['slot'],save_sha256=s['sha256'],state=state,timer=timer,block_count=block_count,event_count=event_count,queued=queued))
 proof=dict(status='PASS',checks=len(checks),check_labels=checks,readback_sha256=sha(HERE/'work/graph_01/readback.json'),
  inputs_sha256=sha(HERE/'work/inputs.json'),changed_nodes=[196],scheduler=scheduler,
  limits=['Truth-table checks do not execute the game scheduler.','Saved wait reload/rebinding and marker/quest entry remain live tests.','No completed quest, reward, scene or downstream resource changed.'],game_writes=0,save_writes=0)
 with (HERE/'work/assessment.json').open('x',encoding='utf-8') as f:json.dump(proof,f,indent=2);f.write('\n')
 print(f'PASS: {len(checks)} cooked graph, guard and captured-state checks.')
if __name__=='__main__':main()
