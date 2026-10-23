"""Independent S24 fresh guards, payload/edge fidelity and no-resume overlap tests."""
import copy,hashlib,json,sys
from pathlib import Path
from inspect import graphs,read,value,walk
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return set(map(tuple,g['edges']))
def evaluate(c,f,j,vehicle=False):
 t=c['$type']
 if t=='questLogicalCondition':
  a=[evaluate(x,f,j,vehicle) for x in c['conditions']]
  return {'AND':all(a),'OR':any(a),'NOR':not any(a)}[c['operation']]
 if t=='questFactsDBCondition':
  v=c['type'];a=f.get(v['factName']);b=v['value']
  if a is None:return False
  return {'Equal':a==b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[v['comparisonType']]
 if t=='questJournalCondition':
  v=c['type'];p=v['path'];return j.get((p['realPath'],value(p['className'])))==v['state']
 if t=='questVehicleCondition':
  assert c['type']['$type']=='questVehicleAvailable_ConditionType';assert c['type']['vehicleType']=='SpecificVehicle';return vehicle
 raise AssertionError(t)
def main():
 build=Path(sys.argv[1]);m=read(build/'component.json');spec=read(ROOT/m['contract']);checks=positive=negative=0
 for rel,h in m['source_pins'].items():assert sha(ROOT/rel)==h,rel;checks+=1
 for r in m['resource_details']:
  assert sha(build/r['relative'])==r['sha256'];assert sha(build/r['readback'])==r['readback_sha256'];checks+=2
 for c in m['native_copies']:
  old=graphs(ROOT/(c['source'].replace('/raw/','/json/')+'.json'))[c['source_graph']]
  file,gp=c['target_graph'].split('/',1);new=graphs(build/'readback'/f'{file}.json')[gp]
  assert nodes(old)[c['source_id']]==nodes(new)[c['target_id']],c;checks+=1
 # Compare all recursively embedded payloads AND edges for copied original phases.
 for o in spec['owners']:
  p=o['parent_slice'];rel='research/sidejobs_s24/ep1/native_01/json/'+p['source'].replace('\\','/')+'.json'
  oldgs=graphs(ROOT/rel);gg=graphs(build/'readback'/f"{o['key'].lower()}_boot.json");old=oldgs[p['graph']];native=gg['root/100']
  ids=set(p['ids']);expected={e for e in edges(old) if e[0] in ids and e[2] in ids}|{(0,'Out',p['entry'],p['socket'])}
  assert edges(native)==expected,(o['key'],edges(native)^expected);checks+=1
  for id in ids:
   prefix=p['graph']+'/'+str(id)
   for gp,g in oldgs.items():
    if gp==prefix or gp.startswith(prefix+'/'):
     np='root/100/'+str(id)+gp[len(prefix):];assert gg[np]['nodes']==g['nodes'];assert edges(gg[np])==edges(g);checks+=len(g['nodes'])+len(g['edges'])
  b=gg['root'];bn=nodes(b);be=edges(b)
  expected={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(4,'Out',89,'In'),(89,'Out',90,'In'),(90,'False',91,'In'),(90,'True',92,'In'),(92,'Out',102,'In'),(102,'Out',101,'In')}
  expected|={(92,'Out',93,'In'),(93,'Out',100,'In1')} if o['contact'] else {(92,'Out',100,'In1')}
  assert be==expected;checks+=1
  assert bn[89]['condition']['type']['tickCount']==2;checks+=1
  assert not any(n['$type']=='questJournalNodeDefinition' for n in b['nodes']);checks+=1
  for n in b['nodes']:
   if n['$type']=='questFactsDBManagerNodeDefinition':assert n['type']['factName'].startswith(o['tag']+'_');checks+=1
  if o['contact']:
   source=nodes(graphs(ROOT/'research/sidejobs_s24/ep1/native_01/json/ep1/quest/minor_quests/mq305/phases/mq305_01_hook_setup.questphase.json')['root'])[9]
   expected=copy.deepcopy(source);expected['id']=93;expected['type']['params'][0]['contact']['realPath']=o['contact'];expected['type']['params'][0]['sendNotification']=0
   assert bn[93]==expected;checks+=1
   assert expected['type']['params'][0]['contact']['fileEntryIndex']==1
   assert value(expected['type']['params'][0]['contact']['className'])=='gameJournalContact';checks+=2
  # Native file-entry index is contact/phone 1, quest 2. Never use quest index for SMS.
  for n in (bn[2],bn[3],bn[90],bn[102]):
   for v in walk(n):
    if v.get('$type')=='gameJournalPath':
     path=v['realPath'];assert v['fileEntryIndex']==(1 if '/contacts/' in '/'+path else 2),(o['key'],path);checks+=1
  facts=spec['common_equal']|o['facts_equal']|{k:v['min'] for k,v in o['fact_ranges'].items()}
  facts|={o['tag']+'_Permit':1,o['tag']+'_Issued':0,o['tag']+'_Fault':0,o['tag']+'_Finished':0}
  journals={(j['path'],j['class']):'Inactive' for j in o['journals']}
  assert o['journals'][0]['class']=='gameJournalQuest' and o['journals'][0]['states']==[1]
  for nodeid in (2,3,90):
   cond=bn[nodeid]['condition'];f=facts|{o['tag']+'_Issued':int(nodeid==90)}
   assert evaluate(cond,f,journals);positive+=1
   for name,num in f.items():
    if nodeid==90 and name.endswith('_Permit'):continue
    if name in o['fact_ranges']:bad=[o['fact_ranges'][name]['min']-1,o['fact_ranges'][name]['max']+1]
    else:bad=[num+1,num-1]
    for v in bad:assert not evaluate(cond,f|{name:v},journals),(o['key'],nodeid,name,v);negative+=1
    missing=f.copy();del missing[name];assert not evaluate(cond,missing,journals),(o['key'],nodeid,name,'missing');negative+=1
   for key in journals:
    for state in ('Active','Succeeded','Failed',None):
     j=journals|{key:state};assert not evaluate(cond,f,j),(o['key'],nodeid,key,state);negative+=1
   if o['key']=='MQ306_FRESH':assert evaluate(cond,f|{'mq306_active':1},journals);positive+=1
   if o['key']=='MQ305_FRESH':
    done={f'holo_{d}_{s}':7 for d in ('mr_hands_calls_v','v_calls_mr_hands') for s in ('start_done','end_done')}
    assert evaluate(cond,f|done,journals);positive+=1
   if 'vehicle_not_available' in o:assert not evaluate(cond,f,journals,True);negative+=1
  # Existing branch is progressed/completed and cannot be reset just to test.
  cap=read(ROOT/'research/sidejobs_s23/live_20261016_01/capture.json')
  old=next(j for j in cap['second']['jobs'] if j['id']==o['id'])
  jf=journals.copy();jf.update({(j['path'],j['class']):j['state'] for j in old['journals']})
  ff=facts|old['facts'];assert not evaluate(bn[3]['condition'],ff,jf);negative+=1
  # Once native root is Active (or Succeeded), preserved legacy resume cannot admit.
  if o['key']=='MQ306_FRESH':
   prior=next(x for x in read(ROOT/'prealpha/sidejobs_s23/ep1/contract.json')['owners'] if x['key']=='MQ306')
   assert prior['facts_equal']['mq306_started']==1 and o['facts_equal']['mq306_started']==0
   assert prior['facts_equal']['mq306_clinic_reached']==1 and o['facts_equal']['mq306_clinic_reached']==0
   assert o['facts_equal']['PTFRS23_MQ306_Issued']==0
   assert prior['journals'][0]['states']==[1,4];checks+=4
  if o['key']=='Q304_FRESH':
   prior=read(ROOT/'prealpha/sidejobs_s22/ep1_jobs/admission.json')
   assert prior['guard_equal']['q304_car_retrieval_started']==1 and o['facts_equal']['q304_car_retrieval_started']==0
   assert prior['guard_equal']['q304_car_retrieval_accepted']==1 and o['facts_equal']['q304_car_retrieval_accepted']==0
   assert o['facts_equal']['PTFRS22_Q304_Issued']==0;checks+=3
 # Dependency bytes remain official resources; no copied gameplay/scenes/rewards edits.
 for depot,r in m['native_resources'].items():
  assert sha(ROOT/r['raw'])==r['raw_sha256'];assert sha(ROOT/r['json'])==r['json_sha256'];checks+=2
  if depot.endswith('.questphase'):
   for g in graphs(ROOT/r['json']).values():checks+=len(g['nodes'])+len(g['edges'])
 transition=read(ROOT/m['transition_proof']);assert transition['status']=='PASS_NATIVE_FAILURE_BOUNDARIES';checks+=transition['checks']
 meta=read(ROOT/m['journal_metadata']);assert meta['status']=='PASS_USED_JOURNAL_METADATA_ALL_VARIANTS';assert m['contract'] in meta['contracts'];checks+=meta['total_used_paths']
 result={'status':'PASS_COMPONENT_NOT_LIVE','component_sha256':sha(build/'component.json'),'contract_sha256':sha(ROOT/m['contract']),'tester_sha256':sha(Path(__file__)),'native_payload_checks':checks,'policy_cases':positive+negative,'positive_policy_cases':positive,'negative_policy_cases':negative,'owners':3,'resources':3,'direct_journal_writes':0,'native_progress_resets':False,'game_writes':False,'pending':['Actual fresh-save SMS, triggers, NPCs, gameplay, reward, Johnny-hidden-voice, reload','Independent official-byte/audit/deployment checks']}
 dest=build/'tests.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
