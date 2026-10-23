"""S24 base component source/native-graph and adversarial fresh admission tests."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'prealpha/sidejobs_s23'))
from audit import graphs,walk,value
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def graph(p,path='root'):return next(g for g in graphs(p) if g['path']==path)
def node(g,i):return next(n for n in g['nodes'] if n['id']==i)
def payload(n):return {k:v for k,v in n.items() if k!='id'}
def run(build):
 m=load(build/'build.json');c=load(ROOT/m['contract']);cap=load(ROOT/c['capture_catalogue'])
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 for p,h in m['resources'].items():assert sha(build/'source'/p.replace('\\','/'))==h,p
 assert not m['mod_overrides'] and len(m['resources'])==len(m['boots'])==len(c['owners'])==3
 assert {o['id'] for o in c['owners']}=={'mq010_barry','mq019_paparazzi','mq015_wizardbook'}
 checks=0;cases=0
 catalog_source='research/sidejobs_s24/ep1/native_02/json/base/journal/cooked_journal.journal.json'
 assert catalog_source in m['source_pins']
 d=load(ROOT/catalog_source);h={x['HandleId']:x['Data'] for x in walk(d) if 'HandleId' in x and 'Data' in x};catalog={};todo=[(d['Data']['RootChunk']['entry'],[])]
 while todo:
  w,p=todo.pop();n=w.get('Data',h.get(w.get('HandleRefId'),w));k=n.get('id','');p=p+([k] if k else [])
  catalog['/'.join(p)]=n.get('$type');todo.extend((v,p) for v in n.get('entries',[]))
 for o in c['owners']:
  for j in o['journals']:assert catalog.get(j['path'])==j['class'],j;checks+=1
  if o['contact_copy']:assert catalog[o['contact_copy']['path']]=='gameJournalContact';checks+=1
 def output(depot,path='root'):return graph(build/'readback'/(Path(depot.replace('\\','/')).stem+'.json'),path)
 for cp in m['native_copies']:
  src=ROOT/(cp['source'].replace('/raw/','/json/')+'.json');out=output(cp['depot'])
  assert payload(node(graph(src,cp['source_graph']),cp['source_id']))==payload(node(out,cp['target_id'])),cp
  checks+=1
  prefix=cp['source_graph']+'/'+str(cp['source_id']);target='root/'+str(cp['target_id'])
  for sg in graphs(src):
   if sg['path']!=prefix and not sg['path'].startswith(prefix+'/'):continue
   og=output(cp['depot'],target+sg['path'][len(prefix):])
   assert sg['nodes']==og['nodes'] and sorted(sg['edges'])==sorted(og['edges'])
   checks+=len(sg['nodes'])
 for o in c['owners']:
  g=output(o['depot']);edges=g['edges'];tag=o['tag'];condition=node(g,1004)['condition']
  assert all(j['states']==[1] for j in o['journals'])
  assert o['journals'][0]['class']=='gameJournalQuest'
  actual_j={x['path']['realPath']:x['state'] for x in walk(condition) if x.get('$type')=='questJournalEntryState_ConditionType'}
  assert actual_j=={j['path']:'Inactive' for j in o['journals']}
  for x in walk(condition):
   if x.get('$type')=='questJournalEntryState_ConditionType':assert x['path']['fileEntryIndex']==(1 if x['path']['realPath'].startswith('contacts/') else 2)
  actual_f={x['factName']:x['value'] for x in walk(condition) if x.get('$type')=='questVarComparison_ConditionType' and x['comparisonType']=='Equal'}
  owned={tag+'_Permit':1,tag+'_Issued':0,tag+'_Finished':0,tag+'_Fault':0}
  expected={**m['common'],**o['facts_equal'],**owned}
  assert actual_f==expected
  ranges={(x['factName'],x['comparisonType']):x['value'] for x in walk(condition) if x.get('$type')=='questVarComparison_ConditionType' and x['comparisonType']!='Equal'}
  assert ranges=={(k,op):v[b] for k,v in o['fact_ranges'].items() for op,b in [('GreaterOrEqual','min'),('LessOrEqual','max')]}
  assert node(g,1002)['condition']==condition
  assert node(g,1001)['type']['factName']==tag+'_Ready'
  assert [1000,'Out',1001,'In'] in edges and [1001,'Out',1002,'In'] in edges
  assert [1002,'Out',1003,'In'] in edges and [1003,'Out',o['parent_start'],'In'] in edges
  assert [1004,'False',1002,'In'] in edges and [1004,'True',1005,'In'] in edges
  assert node(g,1005)['type']['factName']==tag+'_Issued' and [1005,'Out',1006,'In'] in edges
  assert all(e in edges for e in o['parent_edges'])
  dependencies={x['factName']:x['value'] for x in walk(node(g,1003)) if x.get('$type')=='questVarComparison_ConditionType'}
  assert dependencies==({'PTFRS24_PHONE_'+p+'_Issued':1 for p in o['phone_dependencies']} or {'PTFRPA2_Finished':1})
  # Exact copied silent AddContact; no early native reveal path, no SMS resend.
  if o['contact_copy']:
   n=node(g,1010);param=n['type']['params'][0]
   assert n['type']['$type']=='questAddRemoveContact_NodeType'
   assert len(n['type']['params'])==1 and param['addContact']==1 and param['sendNotification']==0
   assert param['contact']['realPath']==o['contact_copy']['path'] and param['contact']['fileEntryIndex']==1
   assert [1006,'Out',1010,'In'] in edges
   assert [1010,'Out',o['issue_target'],'In' if o['key']=='MQ015' else 'In1'] in edges
  else:assert [1006,'Out',o['issue_target'],'In1'] in edges
  # Native root reference and gameplay/scenes remain stock, never copy-edited.
  assert value(node(g,o['parent_node'])['phaseResource']['DepotPath'])==o['native_depot']
  for n in g['nodes']:
   if n['id']>=1000:
    for x in walk(n):
     if x.get('$type')=='questSetVar_NodeType':assert x['factName'].startswith(tag+'_')
     assert x.get('$type') not in ('questJournalNodeDefinition','questItemManagerNodeDefinition','questRewardsManagerNodeDefinition')
  f={**expected,**{k:v['min'] for k,v in o['fact_ranges'].items()}};j={x['path']:1 for x in o['journals']}
  def admitted(fs,js):
   return all(fs.get(k)==v for k,v in expected.items()) and all(isinstance(fs.get(k),int) and r['min']<=fs[k]<=r['max'] for k,r in o['fact_ranges'].items()) and all(js.get(k)==1 for k in j)
  assert admitted(f,j);cases+=1
  for k,v in expected.items():
   for wrong in (-1,v+1,None):
    q=dict(f);q[k]=wrong;assert not admitted(q,j),(o['id'],k,wrong);cases+=1
  for k,r in o['fact_ranges'].items():
   for v in range(r['min'],r['max']+1):q=dict(f);q[k]=v;assert admitted(q,j);cases+=1
   for v in (None,r['min']-1,r['max']+1):q=dict(f);q[k]=v;assert not admitted(q,j);cases+=1
  for p in j:
   for state in (-1,0,2,3,4,None):q=dict(j);q[p]=state;assert not admitted(f,q);cases+=1
  # Native state can change during stock parent waits; final recheck rejects it.
  for p in j:
   q=dict(j);q[p]=2;assert not admitted(f,q);cases+=1
  # Save/reload of Issued cannot re-enter, including untouched root before hook.
  q=dict(f);q[tag+'_Issued']=1;assert not admitted(q,j);cases+=1
  current=next(x for x in cap['first']['jobs'] if x['id']==o['id'])
  assert current['rootState']=='Succeeded'
  q=dict(j);q[o['journals'][0]['path']]=3;assert not admitted(f,q);cases+=1
  q=dict(f);q.update(current['facts']);assert not admitted(q,j);cases+=1
  assert not set(o['facts_equal']) & {'q000_done','q101_done','codex_nix','nix_old_school_expert'},'Do not gate unrelated prior history'
  checks+=len(g['nodes'])
 # Exact parent prerequisites: delayed entrances never bypass native story gates.
 assert [133,'Out1',94,'In'] in output(c['owners'][1]['depot'])['edges']
 assert [174,'False',1004,'In'] in output(c['owners'][2]['depot'])['edges']
 assert [134,'Out',36,'In1'] in output(c['owners'][2]['depot'])['edges']
 # Original Nix native coordination retained; B0 watcher remains old installed body.
 nix=ROOT/'research/b0_story_eight/validation/nix.questphase.json'
 watcher=graph(nix,'root/5')
 assert any(x.get('factName')=='nix_default_on' and x.get('comparisonType')=='Less' for x in walk(node(watcher,11)))
 hook=load(ROOT/'research/sidejobs_s23/native_01/json/base/quest/minor_quests/mq015/scenes/mq015_01_hook.scene.json')
 assert {x['value'] for x in walk(hook) if x.get('$type')=='questSetVar_NodeType' and x.get('factName')=='nix_default_on'}=={0,1}
 checks+=5
 result={'status':'PASS_COMPONENT_OFFLINE_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),
  'native_payload_checks':checks,'policy_cases':cases,'owners':3,'roots':3,'resources':3,'completed_current_controls':3,
  'limits':['No fresh live test fixture was fabricated. Current captured roots remain Succeeded.','Live NPCs, phone/SMS visibility, rewards, native Nix handoff, Johnny visibility and reload still require playtest.','Prophet fresh owner deferred to avoid overlap with S23 captured-progress owner.']}
 out=build/'tests.json'
 if out.exists():raise RuntimeError('Immutable test result exists')
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':run(Path(sys.argv[1]))
