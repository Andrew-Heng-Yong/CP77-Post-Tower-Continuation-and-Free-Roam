"""Source-preserving checks for the explicitly non-dispatchable vehicle candidate."""
import copy,hashlib,json,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import walk,value
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def graphs(p):
 r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def jsonraw(p):return ROOT/(p.replace('/raw/','/json/')+'.json')
def node(gs,g,n):return next(v for v in gs[g]['nodes'] if v['id']==n)
def main():
 folder=Path(sys.argv[1]).resolve();output=folder/'tests.json';assert not output.exists()
 c=read(folder/'component.json');ct=read(ROOT/c['contract']);checks=native=cases=0
 def check(b,why):
  nonlocal checks
  assert b,why;checks+=1
 check(c['status']=='SOURCE_CANDIDATE_BLOCKED_NOT_DISPATCHABLE','candidate status')
 check(not c['boots'] and len(c['proposed_boots'])==2,'no unsupported dispatch')
 check(len(c['resources'])==2 and not c['official_overrides'] and not c['mod_overrides'],'two private prototypes')
 for p,h in c['source_pins'].items():check(sha(ROOT/p)==h,('pin',p))
 for dep,h in c['resources'].items():check(sha(folder/'source'/dep)==h,('resource',dep))
 check(sha(ROOT/c['contract'])==c['contract_sha256'],'contract binding')
 for rec in c['recipes']:
  o=next(o for o in ct['owners'] if o['id']==rec['id']);gs=graphs(folder/rec['readback']);ns={n['id']:n for n in gs['root']['nodes']};edges=gs['root']['edges']
  check(sha(folder/rec['readback'])==rec['readback_sha256'],'readback binding')
  check(edges==sorted(rec['edges']),'exact entry flow')
  check(set(gs)=={'root'},'no substituted native main graph')
  source=graphs(jsonraw(rec['parent']['raw']));expected=copy.deepcopy(node(source,rec['parent']['graph'],rec['parent']['node']));expected['id']=100
  check(expected==ns[100],'exact original native main reference payload');native+=1
  check(value(ns[100]['phaseResource']['DepotPath'])==rec['native'] and ns[100]['phaseResource']['Flags']=='Soft','standalone original native target')
  if rec['parent']['prerequisite_node'] is not None:
   expected=copy.deepcopy(node(source,rec['parent']['graph'],rec['parent']['prerequisite_node']));expected['id']=90
   check(expected==ns[90],'exact q101 original parent pause');native+=1
   check([5,'Out',90,'In'] in edges and [90,'Out',6,'In'] in edges,'prerequisite before native entry')
  check([4,'True',5,'In'] in edges and [6,'Out',100,'In1'] in edges and [100,'Out1',101,'In'] in edges,'claim before normal entry; native finish signal')
  check(not any(n['$type']=='questOutputNodeDefinition' for n in ns.values()),'wrapper lifetime not abruptly terminated')
  check(ns[3]['condition']==ns[4]['condition'],'pause/synchronous guards equal')
  cond=ns[4]['condition'];facts=[v for v in walk(cond) if v.get('$type')=='questVarComparison_ConditionType']
  for k,v in rec['guard'].items():check({'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':k,'value':v} in facts,('fact guard',k))
  for k,r in o['fact_ranges'].items():check({(f['comparisonType'],f['value']) for f in facts if f['factName']==k}=={('GreaterOrEqual',r['min']),('LessOrEqual',r['max'])},('fact range',k))
  journal={(v['path']['realPath'],value(v['path']['className']),v['state']) for v in walk(cond) if v.get('$type')=='questJournalEntryState_ConditionType'}
  check(journal=={(j['path'],j['class'],'Inactive') for j in o['journals']},'all journal descendants fresh')
  inv=[v for v in walk(cond) if v.get('$type')=='questInventory_ConditionType']
  if rec['inventory_source']:
   s=rec['inventory_source'];expected=copy.deepcopy(node(graphs(jsonraw(s['raw'])),s['graph'],s['node'])['condition']['type']);expected.update(comparisonType='Equal',quantity=0)
   check(inv==[expected],'exact native key inventory witness');native+=1
  else:check(inv==[] and o['inventory_zero']==[],'no invented inventory restriction')
  s=rec['availability_source'];avail=copy.deepcopy(node(graphs(jsonraw(s['raw'])),s['graph'],s['node'])['condition']);avail['type']['vehicleName']=o['vehicle_zero'][0]['record']
  nots=[v for v in walk(cond) if v.get('$type')=='questLogicalCondition' and v.get('operation')=='NOR']
  check(any(v['conditions']==[avail] for v in nots),'additional exact availability NOR');native+=1
  if rec['spawned_source']:
   s=rec['spawned_source'];spawn=node(graphs(jsonraw(s['raw'])),s['graph'],s['node'])['condition']
   check(any(v['conditions']==[spawn] for v in nots),'exact original pre-discovery spawned predicate NOR');native+=1
  for item in o['vehicle_zero']+o['inventory_zero']:
   b=item['record'].encode();check(str(zlib.crc32(b)+(len(b)<<32))==item['hash'],'independent typed record hash')
  writes=[v for n in ns.values() for v in walk(n) if v.get('$type')=='questSetVar_NodeType']
  check({v['factName'] for v in writes}=={o['tag']+'_'+x for x in ('Ready','Revision','Issued','Entered','Finished')},'only private ownership writes')
  check(all(v['value']==1 and v['setExactValue']==1 for v in writes),'no reset')
  fs=dict(rec['guard']);js={j['path']:1 for j in o['journals']};items={i['record']:0 for i in o['inventory_zero']};vehicles={i['record']:False for i in o['vehicle_zero']};ranges={k:r['min'] for k,r in o['fact_ranges'].items()}
  def admits(f,j,i,v,r):return all(f.get(k)==x for k,x in fs.items()) and all(j.get(k)==1 for k in js) and all(i.get(k)==0 for k in items) and all(v.get(k) is False for k in vehicles) and all(k in r and type(r[k]) is int and x['min']<=r[k]<=x['max'] for k,x in o['fact_ranges'].items())
  bases=[fs,js,items,vehicles,ranges];check(admits(*bases),'positive abstract contract');cases+=1
  for ix,base in enumerate(bases):
   for key,val in base.items():
    choices=[None,-1,val+1] if ix!=3 else [None,True]
    if ix==1:choices=[None,0,2,3,4]
    if ix==4:choices=[None,0,2147483648]
    for newval in choices:
     args=copy.deepcopy(bases);args[ix][key]=newval;check(not admits(*args),('contradiction',o['id'],key,newval));cases+=1
 check(len(c['blockers'])==4,'four explicit unresolved boundaries')
 result={'status':'PASS_SOURCE_CANDIDATE_CHECKS_DISPATCH_BLOCKED','component_sha256':sha(folder/'component.json'),'tester_sha256':sha(__file__),'checks':checks,'native_payload_checks':native,'policy_cases':cases,'limitations':c['blockers']}
 output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
