"""Independent original-payload, family ownership and fail-closed policy tests."""
import copy,json,sys
from pathlib import Path
from inspect import ROOT,read,graphs,sha,value,walk
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return set(map(tuple,g['edges']))
def evaluate(c,f,j):
 t=c['$type']
 if t=='questLogicalCondition':
  a=[evaluate(x,f,j) for x in c['conditions']];return {'AND':all(a),'OR':any(a),'NOR':not any(a)}[c['operation']]
 if t=='questFactsDBCondition':
  v=c['type'];a=f.get(v['factName']);b=v['value']
  if a is None:return False
  return {'Equal':a==b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[v['comparisonType']]
 if t=='questJournalCondition':
  v=c['type'];p=v['path'];return j.get((p['realPath'],value(p['className'])))==v['state']
 raise AssertionError(t)
def main():
 build=Path(sys.argv[1]);m=read(build/'component.json');spec=read(ROOT/m['contract']);checks=positive=negative=0
 for rel,h in m['source_pins'].items():assert sha(ROOT/rel)==h,rel;checks+=1
 for r in m['resource_details']:
  assert sha(build/r['relative'])==r['sha256'];assert sha(build/r['readback'])==r['readback_sha256'];checks+=2
 for c in m['native_copies']:
  old=nodes(graphs(ROOT/(c['source'].replace('/raw/','/json/')+'.json'))[c['source_graph']])[c['source_id']]
  file,gp=c['target_graph'].split('/',1);new=nodes(graphs(build/'readback'/f'{file}.json')[gp])[c['target_id']]
  expected=copy.deepcopy(old);expected['id']=c['target_id'];assert expected==new,c;checks+=1
 for o in spec['owners']:
  oldgs=graphs(ROOT/o['native_source']);gg=graphs(build/'readback'/f"{o['key'].lower()}.json")
  ids=set(o['selected_nodes']);native=gg['root/100'];expected={e for e in edges(oldgs['root']) if e[0] in ids and e[2] in ids}
  if o['key']=='SQ025_FRESH':expected|={(124,'Out1',1000,'In'),(1000,'Out',1001,'In'),(1001,'CutSource',147,'CutDestination'),(1001,'CutSource',142,'CutDestination'),(1001,'CutSource',114,'CutDestination'),(1001,'Out',1002,'In'),(1002,'Out',1003,'In')}
  assert edges(native)==expected,(o['key'],edges(native)^expected);checks+=1
  for gp,g in oldgs.items():
   if gp=='root' or int(gp.split('/')[1]) not in ids:continue
   new=gg['root/100'+gp[4:]];assert new['nodes']==g['nodes'];assert edges(new)==edges(g);checks+=len(g['nodes'])+len(g['edges'])
  b=gg['root'];bn=nodes(b);be=edges(b)
  expected={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(4,'Out',89,'In'),(89,'Out',90,'In'),(90,'False',91,'In'),(90,'True',92,'In')}
  if o['key']=='MQ025_FRESH':expected|={(92,'Out',93,'In'),(93,'Out',100,'In1'),(92,'Out',102,'In'),(102,'Out',101,'In')}
  else:expected|={(92,'Out',94,'In1'),(92,'Out',95,'In1'),(92,'Out',100,'In1')}
  assert be==expected;checks+=1
  assert bn[89]['condition']['type']['tickCount']==2;checks+=1
  # Owned wrapper contains no generic journal reactivation or native resets.
  assert not any(n['$type']=='questJournalNodeDefinition' for n in b['nodes']);checks+=1
  for n in b['nodes']:
   if n['$type']=='questFactsDBManagerNodeDefinition':assert n['type']['factName'].startswith(o['tag']+'_');checks+=1
  if o['contact']:
   old=nodes(graphs(ROOT/'research/sidejobs_s24/ep1/native_01/json/ep1/quest/minor_quests/mq305/phases/mq305_01_hook_setup.questphase.json')['root'])[9]
   exp=copy.deepcopy(old);exp['id']=93;exp['type']['params'][0]['contact']['realPath']=o['contact'];exp['type']['params'][0]['sendNotification']=0
   assert bn[93]==exp;assert exp['type']['params'][0]['contact']['fileEntryIndex']==1;checks+=2
  for n in b['nodes']:
   for v in walk(n):
    if v.get('$type')=='gameJournalPath':assert v['fileEntryIndex']==(1 if '/contacts/' in '/'+v['realPath'] else 2);checks+=1
  facts=spec['common_equal']|o['facts_equal']|{k:v['min'] for k,v in o['fact_ranges'].items()}
  facts|={o['tag']+'_Permit':1,o['tag']+'_Issued':0,o['tag']+'_Fault':0,o['tag']+'_Finished':0}
  journals={(j['path'],j['class']):'Inactive' for j in o['journals']}
  roots=[j for j in o['journals'] if j['class']=='gameJournalQuest'];assert len(roots)==len(o['ids']);assert all(j['states']==[1] for j in o['journals']);checks+=2
  for id in (2,3,90):
   cond=bn[id]['condition'];f=facts|{o['tag']+'_Issued':int(id==90)};assert evaluate(cond,f,journals);positive+=1
   for name,num in f.items():
    if id==90 and name.endswith('_Permit'):continue
    bounds=o['fact_ranges'].get(name);bad=[bounds['min']-1,bounds['max']+1] if bounds else [num-1,num+1]
    for v in bad:assert not evaluate(cond,f|{name:v},journals),(o['key'],id,name,v);negative+=1
    ff=f.copy();del ff[name];assert not evaluate(cond,ff,journals);negative+=1
   for key in journals:
    for state in ('Active','Succeeded','Failed',None):assert not evaluate(cond,f,journals|{key:state}),(o['key'],key,state);negative+=1
   if o['key']=='SQ025_FRESH':
    assert evaluate(cond,f|{'sq025_active':1},journals);positive+=1
    historic={f'holo_{d}_{s}':7 for d in ('delamain_calls_v','v_calls_delamain') for s in ('start_count','end_count','start_done','end_done')};assert evaluate(cond,f|historic,journals);positive+=1
  cap=read(ROOT/'research/sidejobs_s23/live_20261016_01/capture.json')['second']['jobs'];ff=facts.copy();jj=journals.copy()
  for row in cap:
   if row['id'] in o['ids']:ff.update(row['facts']);jj.update({(j['path'],j['class']):j['state'] for j in row['journals']})
  assert not evaluate(bn[3]['condition'],ff,jj);negative+=1
  # Durable mutual exclusion survives native Active/Failed transitions. The
  # separately reviewed S25 policy component supplies reciprocal old guards.
  prior='PTFRS22_MQ025' if o['key']=='MQ025_FRESH' else 'PTFRS22_SQ025'
  assert o['facts_equal'][prior+'_Issued']==0 and o['facts_equal'][prior+'_Fault']==0;checks+=2
  if o['key']=='MQ025_FRESH':
   parent=nodes(graphs(ROOT/'research/sidejobs_s25/families/native_03/json/base/quest/minor_quests/minorquests.questphase.json')['root'])
   assert parent[117]['condition']['type']['factName']=='q001_left_v_apartment' and parent[117]['condition']['type']['value']==1
   assert o['fact_ranges']['q001_left_v_apartment']=={'min':1,'max':2147483647};checks+=2
  if o['key']=='SQ025_FRESH':
   assert o['facts_equal'][prior+'_SupportIssued']==0;assert 134 not in ids and not ({80,81,82,83}&ids);checks+=2
   n=nodes(native);assert n[1000]['type']['factName']==o['tag']+'_Finished';assert n[1000]['type']['value']==1;checks+=2
   assert not any(n['type'].get('factName')=='sq025_done' for n in native['nodes'] if n['$type']=='questFactsDBManagerNodeDefinition' and n['id']>=1000);checks+=1
 # Existing Fred owner and native lifecycle remain byte-structurally exact,
 # except one explicit scene-choice edge and its two added selector nodes.
 oldgs=graphs(ROOT/'research/b0_story_services/validation/fred.questphase.json');gg=graphs(build/'readback/fred.json')
 for gp,g in oldgs.items():
  new=gg[gp]
  if gp!='root/5/14':assert new['nodes']==g['nodes'];assert edges(new)==edges(g);checks+=len(g['nodes'])+len(g['edges']);continue
  old=nodes(g);nn=nodes(new);assert all(nn[k]==v for k,v in old.items());checks+=len(old)
  ex=copy.deepcopy(old[3]);ex['id']=300;ex['sceneFile']['DepotPath']['$value']='base\\open_world\\vendors\\watson\\little_china\\wat_lch_melee_01\\wat_lch_melee_01.scene';assert ex==nn[300];checks+=1
  expected=edges(g)-{(202,'Out',3,'wat_lch_melee_01_default_start')}|{(202,'Out',301,'In'),(301,'False',3,'wat_lch_melee_01_default_start'),(301,'True',300,'wat_lch_melee_01_default_start')};assert edges(new)==expected;checks+=1
  for issued in (0,1,2):
   for fault in (0,1):assert evaluate(nn[301]['condition'],{'PTFRS25_MQ025_FRESH_Issued':issued,'PTFRS25_MQ025_FRESH_Fault':fault},{})==(issued==1 and fault==0);positive+=1
 for depot,r in m['native_resources'].items():assert sha(ROOT/r['raw'])==r['raw_sha256'];assert sha(ROOT/r['json'])==r['json_sha256'];checks+=2
 assert len(m['override_donors'])==1;checks+=1
 for dep,d in m['override_donors'].items():assert sha(ROOT/d['source'])==d['sha256'];assert d['archive']=='TowerContinued_PreAlpha.archive';checks+=2
 result={'status':'PASS_COMPONENT_NOT_LIVE','component_sha256':sha(build/'component.json'),'contract_sha256':sha(ROOT/m['contract']),'tester_sha256':sha(Path(__file__)),'native_payload_checks':checks,'policy_cases':positive+negative,'positive_policy_cases':positive,'negative_policy_cases':negative,'owners':2,'roots':16,'resources':3,'direct_new_journal_writes':0,'native_progress_resets':False,'game_writes':False,'pending':['Fresh-save full-family calls, NPCs, reward, Johnny-hidden voice, reload','Aggregate reciprocal old-owner exclusivity, official bytes, metadata, deployment checks']}
 dest=build/'tests.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
