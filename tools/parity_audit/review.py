"""Separate adversarial checks using raw exports, catalogue and archive indexes.
No Resource/compare_graph calls: this intentionally has an independent oracle.
"""
from common import *
import collections

def raw_oracle(obj):
 stack=[obj];graphs=[];refs=set();features=collections.Counter();types=collections.Counter()
 while stack:
  x=stack.pop()
  if isinstance(x,list):stack.extend(x);continue
  if not isinstance(x,dict):continue
  t=x.get('$type','');types[t]+=1
  if t=='questGraphDefinition' and isinstance(x.get('nodes'),list):graphs.append({'type':'phase','nodes':len(x['nodes'])})
  if t=='scnSceneGraph' and isinstance(x.get('graph'),list):graphs.append({'type':'scene','nodes':len(x['graph'])})
  if 'DepotPath'in x:
   d=x['DepotPath'];d=d.get('$value',d) if isinstance(d,dict) else d
   if str(d).lower() not in ('','0','none'):refs.add(str(d).replace('/','\\'))
  for k in ('factName','factName1','factName2','prefabNodeRef','actorId','workspot','camera'):
   if k in x:features[k]+=1
  stack.extend(x.values())
 return graphs,refs,features,types

def review(w,o):
 idx=read(o/'resource_inventory.json');qs=read(o/'quest_results.json');stages=read(o/'stage_results.json');cat=read(o/'catalogues.json');c=read(o/read(o/'capture_pointer.json')['capture']);mismatches=[];refs=set();types=collections.Counter();checked=0;seen={};raw_details=[];cache=read(o/'raw_oracle_cache.json')['exports'] if (o/'raw_oracle_cache.json').exists() else {}
 for d,r in sorted(idx.items()):
  if not r.get('json'):continue
  name=r['json']
  if name not in seen:
   if name in cache:
    z=cache[name];assert sha(name)==z['json_sha256'],'Independent raw oracle cache changed';seen[name]=(z['graphs'],set(z['refs']),z['features'],z['types'])
   else:seen[name]=raw_oracle(read(name))
  gs,ds,fs,ts=seen[name];expected=sum(g['nodes'] for g in gs);actual=r.get('node_count',0)
  if expected!=actual:mismatches.append({'resource':d,'json':name,'raw_graph_nodes':expected,'normalized_nodes':actual,'raw_graphs':gs,'reason':'Embedded/unsupported graph may be omitted; parity cannot be certified'})
  refs.update(d for d in ds if d.lower()not in ('none','0',''));types.update(ts);checked+=1
  raw_details.append({'resource':d,'raw_graph_nodes':expected,'normalized_nodes':actual,'reference_count':len(ds),'features':dict(fs)})
  if checked%800==0:print(json.dumps({'stage':'independent_review','exports':checked}),flush=True)
 # Independent registry load; never rely on engine's reported count.
 pointer=read(w/'research/gig_restoration/lore_whitelist_current.json');active=read(w/pointer['selection_file']);expected_ids={r['id'] for r in active['decision_registry']};actual_ids={r['id'] for r in qs};duplicates=[k for k,n in collections.Counter(r['id'] for r in qs).items() if n!=1]
 stage_errors=[];required={'entry','phone','sms','progression','cleanup','rewards','assets','saved_owners'}
 for q in qs:
  ss=[s for s in stages if s['quest_id']==q['id']]
  if {s['stage'] for s in ss}!=required or len(ss)!=len(required):stage_errors.append({'quest':q['id'],'error':'MISSING_OR_DUPLICATE_STAGE'})
  for s in ss:
   if s['status']in ('PASS','APPROVED_DEVIATION') and (not s['mapped_resources'] or s['unknown_resources']):stage_errors.append({'quest':q['id'],'stage':s['stage'],'error':'VACUOUS_PASS'})
 private={r['depot'] for r in read(o/'queries.json')['private']};captured={r['depot'] for r in c['private_readback']};available={r['depot'] for r in c['resources']};looked=available|set(c['missing']);unqueried=sorted(refs-looked)
 report={'status':'PASS_WITH_DECLARED_LIMITS' if not mismatches and not stage_errors and expected_ids==actual_ids and not duplicates and not unqueried and captured==private else 'COVERAGE_GAPS','method':'Independent stack traversal of raw JSON, separate active registry reload and archive readback reconciliation; no normalizer/comparator reuse','raw_exports_checked':checked,'raw_node_mismatches':mismatches,'catalogue_missing':sorted(expected_ids-actual_ids),'catalogue_unexpected':sorted(actual_ids-expected_ids),'catalogue_duplicates':duplicates,'stage_errors':stage_errors,'private_readback_missing':sorted(private-captured),'private_readback_extra':sorted(captured-private),'references_unqueried':unqueried,'raw_reference_count':len(refs),'semantic_limits':['Condition satisfiability, shared leases and interrupted lifecycle postconditions are not formally solved','Actor bindings, prefab placement and variant semantics require deeper asset decode','Saved owner liveness and playback remain LIVE_ONLY','Path/journal association is candidate identity, not universal proof of exact selected root','No adversarial second agent or human review was performed; this is a separately implemented review pass']}
 write(o/'adversarial_review.json',report);write(o/'raw_coverage_oracle.json',raw_details);write(o/'raw_type_inventory.json',dict(types));print(json.dumps({k:v for k,v in report.items() if not isinstance(v,list)},indent=2))

def precompute(o):
 c=read(o/read(o/'capture_pointer.json')['capture']);out={}
 for r in c['resources']:
  p=r.get('json')
  if not p or p in out:continue
  assert sha(p)==r['json_sha256'];gs,refs,fs,ts=raw_oracle(read(p));out[p]={'json_sha256':r['json_sha256'],'graphs':gs,'refs':sorted(refs),'features':dict(fs),'types':dict(ts)}
  if len(out)%800==0:print(json.dumps({'stage':'raw_oracle','exports':len(out)}),flush=True)
 write(o/'raw_oracle_cache.json',{'scope':'Independent raw traversal of every distinct captured export, no model/comparator imports','exports':out});print('RAW_ORACLE_COMPLETE',len(out),flush=True)

if __name__=='__main__':
 import sys
 precompute(Path(sys.argv[1]))
