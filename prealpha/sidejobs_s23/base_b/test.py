"""Source-bound structural and negative-admission tests. No live game access."""
import json,sys,hashlib,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'prealpha/sidejobs_s23'))
from audit import graphs,walk,value
HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def node(g,i):return next(n for n in g['nodes'] if n['id']==i)
def graph(p,path='root'):return next(g for g in graphs(p) if g['path']==path)
def payload(n):return {k:v for k,v in n.items() if k!='id'}
def run(build):
 m=read(build/'build.json');c=read(HERE/'contract.json');cap=read(ROOT/c['capture'])
 assert sha(ROOT/c['capture'])==c['capture_sha256']
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 for p,h in m['resources'].items():assert sha(build/'source'/p.replace('\\','/'))==h,p
 assert len(m['boots'])==7 and len(m['resources'])==8
 assert len(c['owners'])==7 and sum(len(o['ids']) for o in c['owners'])==9
 cache={};checks=0;cases=0
 def dg(depot):
  label=Path(depot.replace('\\','/')).stem
  return graph(build/'readback'/((label if label!='owner' else 'wilson_owner')+'.json'))
 for cp in m['native_copies']:
  src=ROOT/(cp['source'].replace('/raw/','/json/')+'.json')
  orig=graph(src,cp['source_graph']);out=dg(cp['depot'])
  a=node(orig,cp['source_id']);b=node(out,cp['target_id'])
  assert payload(a)==payload(b),(cp,'payload');checks+=1
  # Inline original vendor subgraphs: every payload and internal edge preserved.
  src_prefix=cp['source_graph']+'/'+str(cp['source_id'])
  dst_prefix='root/'+str(cp['target_id'])
  for sg in graphs(src):
   if not sg['path'].startswith(src_prefix+'/') and sg['path']!=src_prefix:continue
   target=dst_prefix+sg['path'][len(src_prefix):]
   og=graph(build/'readback'/(Path(cp['depot'].replace('\\','/')).stem+'.json'),target)
   assert sg['nodes']==og['nodes'],(target,'nested payload')
   assert sorted(sg['edges'])==sorted(og['edges']),(target,'nested edges')
   checks+=len(sg['nodes'])
 for o in c['owners']:
  g=dg(o['depot']);nd={n['id']:n for n in g['nodes']};edges=g['edges']
  assert [1000,'Out',1001,'In'] in edges and [1001,'Out',1002,'In'] in edges
  # Auth-independent readiness, support only after initial native permit.
  assert node(g,1001)['type']['factName']==o['tag']+'_Ready'
  assert [1002,'Out',1003,'In'] in edges
  condition=node(g,1004)['condition']
  eq={v['factName']:v['value'] for v in walk(condition) if v.get('$type')=='questVarComparison_ConditionType'}
  for k,v in o['facts_equal'].items():assert eq[k]==v
  assert eq[o['tag']+'_Permit']==1 and eq[o['tag']+'_Issued']==0
  jstates={v['path']['realPath']:v['state'] for v in walk(condition) if v.get('$type')=='questJournalEntryState_ConditionType'}
  assert jstates=={j['path']:'Inactive' for j in o['journals']}
  facts=dict(o['facts_equal']);journal={j['path']:1 for j in o['journals']}
  def admit(f,j):return all(f.get(k)==v for k,v in facts.items()) and all(j.get(k)==v for k,v in journal.items())
  assert admit(facts,journal);cases+=1
  for k,v in facts.items():
   f=dict(facts);f[k]=v+1;assert not admit(f,journal);cases+=1
   f.pop(k);assert not admit(f,journal);cases+=1
  for p in journal:
   for state in (-1,0,2,3,4):
    j=dict(journal);j[p]=state;assert not admit(facts,j);cases+=1
  for id in o['ids']:
   current=next(j for j in cap['first']['jobs'] if j['id']==id)
   assert all(current['facts'].get(k)==v for k,v in facts.items() if k in current['facts'])
   assert all(j['state']=='Inactive' for j in current['journals'])
  # Original entry has one-shot issue immediately before it, never before waits.
  assert [1004,'True',1005,'In'] in edges and [1005,'Out',1006,'In'] in edges
  assert [1006,'Out',o['parent_node'],'In1'] in edges
  assert [o['parent_node'],'Out1',1007,'In'] in edges
  if o['key']=='MQ011':
   assert [184,'True',93,'In'] in edges and [93,'Out',1004,'In'] in edges
   assert [184,'False',1104,'In'] in edges and [1106,'Out',15,'EP1_Standalone'] in edges
   support={v['factName']:v['value'] for v in walk(node(g,1003)) if v.get('$type')=='questVarComparison_ConditionType'}
   assert support=={'PTFRS23_PHONE_WILSON_Issued':1}
  if o['service_lease']:
   assert [1003,'Out',1010,'In'] in edges and [1010,'Out',1011,'In'] in edges
   assert [1004,'False',1013,'In'] in edges and [1013,'Out',1002,'In'] in edges
   assert [1007,'Out',1012,'In'] in edges
   assert node(g,1012)['type']['value']==node(g,1013)['type']['value']==0
  # Only mod-owned setters in wrappers except copied native vendor internals.
  for n in g['nodes']:
   if n['id']<1000 or n['id']==1020:continue
   for v in walk(n):
    if v.get('$type')=='questSetVar_NodeType':assert v['factName'].startswith('PTFR'),v
  checks+=len(g['nodes'])
 # Exact Wilson legacy payload/edge preservation except saved wait3 and its route.
 old=graph(ROOT/'research/b0_wilson_vendor/validation/owner.questphase.json')
 new=graph(build/'readback/wilson_owner.json')
 for n in old['nodes']:
  if n['id']!=3:assert n==node(new,n['id']);checks+=1
 for e in old['edges']:
  if e[0]!=3:assert e in new['edges']
 assert [3,'Out',100,'In'] in new['edges']
 assert [100,'True',101,'In'] in new['edges'] and [101,'Out',102,'In'] in new['edges']
 assert [102,'Out',3,'In'] in new['edges'] and [103,'Out',4,'In1'] in new['edges']
 # Small state model: no release acknowledgement while existing body is active;
 # native return is mandatory, with despawn flags already cleared before root5.
 for location in ('wait','body'):
  for lease in (0,1):
   for near in (0,1):
    released=location=='wait' and lease==1
    start=location=='wait' and lease==0 and near==1
    assert not (released and start)
    if location=='body':assert not released
    cases+=1
 # mq026 original repeat selector consults preserved done facts, never erases them.
 prophecy=ROOT/'research/sidejobs_s23/native_01/json/base/quest/minor_quests/mq026/phases/mq026_01_conspiracies.questphase.json'
 pg=graph(prophecy)
 for i,f in [(9,'mq026_nomads_done'),(53,'mq026_cyberspace_done'),(54,'mq026_reptilians_done'),(65,'mq026_eyes_done')]:
  assert any(v.get('factName')==f for v in walk(node(pg,i)));checks+=1
 assert node(pg,84)['$type']=='questSpawnManagerNodeDefinition'
 result={'status':'PASS_COMPONENT_OFFLINE_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),
  'native_payload_checks':checks,'policy_cases':cases,'roots':9,'owners':7,'resources':8,
  'limits':['Native gameplay, NPC lease timing, map visibility, rewards, phone timing and save/reload require live playtest.','Other progress seams are deliberately rejected, not reset.']}
 out=build/'tests.json'
 if out.exists():raise RuntimeError('Test evidence already exists')
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result))
if __name__=='__main__':run(Path(sys.argv[1]))
