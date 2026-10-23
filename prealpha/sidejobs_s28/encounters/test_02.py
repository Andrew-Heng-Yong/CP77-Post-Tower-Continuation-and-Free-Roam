"""Source-bound native S28 encounter payload, ownership, and admission checks."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,walk,value
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten

def graphs(p):
 r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def jsonraw(p):return ROOT/(p.replace('/raw/','/json/')+'.json')
def main():
 folder=Path(sys.argv[1]).resolve();out=folder/'tests.json';assert not out.exists();c=read(folder/'component.json');ct=read(ROOT/c['contract']);plan=read(ROOT/'research/sidejobs_s28/encounters/build_plan_02.json');checks=0;native=0;cases=0
 def check(ok,why):
  nonlocal checks
  assert ok,why;checks+=1
 for p,h in c['source_pins'].items():check(sha(ROOT/p)==h,('pin',p))
 for dep,h in c['resources'].items():check(sha(folder/'source'/dep)==h,('resource',dep))
 check(len(c['resources'])==4 and len(c['boots'])==2,'two entries and two source clones')
 check(not c['mod_overrides'] and c['official_overrides']==0,'no override')
 for clone in c['clones']:
  old=graphs(jsonraw(clone['raw']));new=graphs(folder/'readback'/clone['readback']);check(old.keys()==new.keys(),'same clone graph IDs')
  src=read(jsonraw(clone['raw']))['Data']['RootChunk'];dst=read(folder/'readback'/clone['readback'])['Data']['RootChunk'];check({k:v for k,v in src.items() if k!='graph'}=={k:v for k,v in dst.items() if k!='graph'},'full root prefab/context equality')
  for gp,g in old.items():
   expected=copy.deepcopy(g);ns={n['id']:n for n in expected['nodes']}
   if gp=='root' and clone['kind']=='reference':ns[clone['source_node']]['phaseResource']['DepotPath']['$value']=clone['target']
   if gp=='root' and clone['kind']=='diner_signal':
    expected['nodes'].append({'$type':'questFactsDBManagerNodeDefinition','id':65000,'type':{'$type':'questSetVar_NodeType','factName':clone['signal'],'setExactValue':1,'value':1}})
    expected['edges'].remove(clone['source_edge']);expected['edges']+= [[58,'Out',65000,'In'],[65000,'Out',71,'In']];expected['edges'].sort()
   check(expected==new[gp],('exact clone delta',clone['kind'],gp));native+=len(g['nodes'])
 for recipe in c['recipes']:
  job=next(j for j in plan['jobs'] if j['id']==recipe['id']);o=next(o for o in ct['owners'] if o['id']==recipe['id']);name=recipe['depot'].rsplit('\\',1)[-1].removesuffix('.questphase');new=graphs(folder/'readback'/(name+'.json'));ns={n['id']:n for n in new['root']['nodes']};source=graphs(jsonraw(recipe['parent_raw']));on={n['id']:n for n in source['root']['nodes']}
  check(new['root']['edges']==sorted(recipe['edges']),('compiled edges',name))
  for ident in recipe['parent_ids']:
   expected=copy.deepcopy(on[ident])
   if ident==recipe['parent_child']:expected['phaseResource']['DepotPath']['$value']=recipe['native']
   check(expected==ns[ident],('exact native parent',name,ident));native+=1
  check(set(recipe['parent_ids'])=={47,54,55,59,62,70,73,80,81,83,84,86,recipe['parent_child']},'normal parent input closure only')
  check([65004,'True',65005,'In'] in new['root']['edges'],'synchronous claim before native parent')
  check([65005,'Out',81,'In1'] in new['root']['edges'],'claimed before native original parent')
  check([65006,'Out',recipe['parent_child'],'In1'] in new['root']['edges'],'normal main input only')
  check(not any(n['$type']=='questOutputNodeDefinition' for n in ns.values()),'wrapper retains service lifecycle')
  check(ns[65003]['condition']==ns[65004]['condition'],'pause/synchronous guard equality')
  factconditions=[v for v in walk(ns[65003]['condition']) if v.get('$type')=='questVarComparison_ConditionType']
  for f,v in recipe['guard'].items():check({'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':f,'value':v} in factconditions,('exactguard',f))
  for f,v in o['facts_equal'].items():check(recipe['guard'].get(f)==v,('runtime/native consistency',f))
  journals={(v['path']['realPath'],value(v['path']['className']),v['state']) for v in walk(ns[65003]['condition']) if v.get('$type')=='questJournalEntryState_ConditionType'};states={1:'Inactive',3:'Succeeded'}
  check(journals=={(j['path'],j['class'],states[j['states'][0]]) for j in o['journals']},'all exact journal guards')
  inventory=[v for v in walk(ns[65003]['condition']) if v.get('$type')=='questInventory_ConditionType'];expected=[]
  for i in o['inventory_native']:
   v=copy.deepcopy(i['source_condition']['type']);v.update(comparisonType='Equal',quantity=0);expected.append(v)
  check(inventory==expected,'exact player item guards')
  for f,r in o['fact_ranges'].items():check({(v['comparisonType'],v['value']) for v in factconditions if v['factName']==f}=={('GreaterOrEqual',r['min']),('LessOrEqual',r['max'])},('bounded fact',f))
  # Exercise independent field contradictions against the conjunctive contract.
  expectedFacts=dict(recipe['guard']);expectedRanges={k:v['min'] for k,v in o['fact_ranges'].items()};expectedJournal={j['path']:j['states'][0] for j in o['journals']};expectedItems={i['record']:0 for i in o['inventory_zero']}
  def admits(fs,rs,js,items):return all(fs.get(k)==v for k,v in expectedFacts.items()) and all(k in rs and isinstance(rs[k],int) and r['min']<=rs[k]<=r['max'] for k,r in o['fact_ranges'].items()) and all(js.get(k)==v for k,v in expectedJournal.items()) and all(items.get(k)==0 for k in expectedItems)
  check(admits(expectedFacts,expectedRanges,expectedJournal,expectedItems),'positive admission');cases+=1
  for base,kind in [(expectedFacts,'facts'),(expectedRanges,'ranges'),(expectedJournal,'journals'),(expectedItems,'items')]:
   for key,val in base.items():
    values=[None,-1,2147483648] if kind=='ranges' else ([None,1,2,3,4] if kind=='journals' else [None,val-1,val+1])
    for replacement in values:
     if replacement==val:continue
     neg=dict(base);neg[key]=replacement;args=[expectedFacts,expectedRanges,expectedJournal,expectedItems];args[['facts','ranges','journals','items'].index(kind)]=neg
     check(not admits(*args),('contradiction defers',name,kind,key,replacement));cases+=1
  if recipe['service']:
   service=recipe['service'];old=graphs(jsonraw(service['source_raw']));oldnode=next(n for n in old[service['source_graph']]['nodes'] if n['id']==service['source_node']);expected=copy.deepcopy(oldnode);expected['id']=service['target_node'];root=read(jsonraw(service['source_raw']))['Data']['RootChunk'];check(expected['phaseInstancePrefabs']==[],'native diner own prefab empty');expected['phaseInstancePrefabs']=copy.deepcopy(root['phasePrefabs']);check(expected==ns[64000],'exact native diner with inherited prefab context');check([value(x['prefabNodeRef']) for x in root['phasePrefabs']]==['#loading_conditions'],'only inherited loading marker prefab');check(read(folder/'readback'/(name+'.json'))['Data']['RootChunk']['phasePrefabs']==[],'entry root prefab-free before claim')
   prefix=service['source_graph']+'/'+str(service['source_node'])
   for gp,g in old.items():
    if gp==prefix or gp.startswith(prefix+'/'):
     np='root/64000'+gp[len(prefix):];check(new[np]['nodes']==g['nodes'] and new[np]['edges']==g['edges'],('diner leaf unchanged',gp));native+=len(g['nodes'])
   check(service['guard']=={o['tag']+'_Issued':1,o['tag']+'_DinerStartReady':1,o['tag']+'_DinerIssued':0,o['tag']+'_Fault':0,'std_arr_foodshop_04_default_on':0},'source disabled before service spawn')
   check([65005,'Out',65020,'In'] in new['root']['edges'] and [65021,'Out',64000,'In1'] in new['root']['edges'],'single owned actor support branch')
 result={'status':'PASS_S28_ENCOUNTER_SOURCE_POLICY_NOT_GAMEPLAY','component_sha256':sha(folder/'component.json'),'tester_sha256':sha(__file__),'checks':checks,'native_payload_checks':native,'policy_cases':cases,'limitations':['Actual gameplay/reward/reload untested; static source equality is not engine simulation.','Unsupported partial progress is preserved and deferred.']}
 out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
