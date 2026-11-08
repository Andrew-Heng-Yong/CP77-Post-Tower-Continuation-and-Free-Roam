"""Bounded, evidence-producing static analysis. Unknowns are results, not exceptions."""
from common import *
from model import Resource,compare_graph,reachable,digest
from checks import *
import collections,gzip,functools,itertools
class Models:
 def __init__(self,root,fallback=None):self.root=root;self.fallback=fallback
 @functools.lru_cache(maxsize=20)
 def get(self,d):
  p=self.root/(fnv(d)+'.json.gz')
  if not p.exists():return self.fallback.get(d) if self.fallback else None
  with gzip.open(p,'rt',encoding='utf-8') as f:return json.load(f)
 def put(self,d,m):
  p=self.root/(fnv(d)+'.json.gz');p.parent.mkdir(parents=True,exist_ok=True)
  with gzip.open(p,'wt',encoding='utf-8') as f:json.dump(m,f,separators=(',',':'))
def registrations(g):
 result=[];errors=[];files=[]
 for p in sorted((g/'archive/pc/mod').glob('*.xl')):
  text=p.read_text(encoding='utf-8-sig');files.append({'path':str(p),'sha256':sha(p)})
  if not re.search(r'^quest:',text,re.M):continue
  section=re.split(r'(?m)^[a-zA-Z_]+:',text.split('quest:',1)[1])[0]
  blocks=re.split(r'(?m)^    - path:\s*',section)[1:]
  if not blocks:errors.append({'file':str(p),'error':'UNSUPPORTED_QUEST_YAML'});continue
  for block in blocks:
   d=block.splitlines()[0].strip();parent=re.search(r'^      parent: (.+)$',block,re.M);node=re.search(r'^        node: \[([^\]]+)\]',block,re.M);sock=re.search(r'^        socket: (.+)$',block,re.M)
   if not parent or not node or not sock:errors.append({'file':str(p),'depot':d,'error':'UNSUPPORTED_BINDING'});continue
   result.append({'path':d,'parent':parent[1].strip(),'input_node':node[1].strip(),'source_socket':sock[1].strip(),'file':str(p)})
 return result,errors,files
def allnodes(m):
 for gp,g in m.get('graphs',{}).items():
  for i,n in g['nodes'].items():yield gp,i,n
def active_contexts(store,roots):
 """Structural MAY-execution closure, preserving caller-selected scene/phase inputs.
 Ignores condition feasibility; never claims executing saved owners.
 """
 contexts=collections.defaultdict(set);nodes=collections.defaultdict(set);unknown=[];todo=[]
 def add(d,gp,entry):
  key=(gp,entry)
  if key not in contexts[d]:contexts[d].add(key);todo.append((d,gp,entry))
 for d in roots:
  m=store.get(d)
  if not m:unknown.append({'resource':d,'reason':'ROOT_MODEL_MISSING'});continue
  gp='root' if 'root'in m['graphs'] else 'scene';entries=m['graphs'].get(gp,{}).get('entries',{})
  if len(entries)!=1:unknown.append({'resource':d,'reason':'ROOT_DEFAULT_INPUT_AMBIGUOUS','entries':list(entries)})
  for e in entries:add(d,gp,e)
 while todo:
  d,gp,e=todo.pop();m=store.get(d);g=(m or {}).get('graphs',{}).get(gp)
  if not g or e not in g['entries']:unknown.append({'resource':d,'graph':gp,'entry':e,'reason':'ENTRY_UNRESOLVED'});continue
  ids=reachable(g['nodes'],g['edges'],[g['entries'][e]])
  for i in ids:
   nodes[d].add((gp,i));n=g['nodes'][i];p=n['payload'];incoming={edge[3] for edge in g['edges'] if edge[2]==i and edge[0] in ids and edge[1]!='CutSource' and edge[3]!='CutDestination'}
   child=gp+'/'+i
   if child in m['graphs']:
    for entry in incoming:
     if entry in m['graphs'][child]['entries']:add(d,child,entry)
   for field in ['phaseResource','sceneFile']:
    ref=p.get(field,{});target=str(value(ref.get('DepotPath','')))
    if target in ('','0','None'):continue
    tm=store.get(target)
    if not tm:unknown.append({'resource':d,'graph':gp,'node':i,'target':target,'reason':'EXTERNAL_GRAPH_MODEL_MISSING'});continue
    tg='scene' if field=='sceneFile' else 'root'
    for entry in incoming:
     if entry in tm['graphs'].get(tg,{}).get('entries',{}):add(target,tg,entry)
     else:unknown.append({'resource':d,'graph':gp,'node':i,'target':target,'entry':entry,'reason':'EXTERNAL_INPUT_NOT_FOUND'})
 return contexts,nodes,unknown
def analyze(w,o,reuse=None):
 assert not (o/'summary.json').exists(),'Use a fresh analysis directory or an explicit successor'
 assert (o/'capture_pointer.json').exists(),'Independent closure certification is required; partial captures cannot silently substitute'
 capture_path=o/read(o/'capture_pointer.json')['capture']
 if not capture_path.exists():raise FileNotFoundError('Expanded capture missing; initial pass is not a certified closure')
 capture=read(capture_path);prep=read(o/'prepared.json');q=read(o/'queries.json');catalogue=read(o/'catalogues.json');g=Path(prep['game']);private={r['depot']:r for r in q['private']};providers=collections.defaultdict(list)
 for r in capture['resources']:providers[r['depot']].append(r)
 parent_rows=read(o/'parents.json');parent_rows=[parent_rows] if isinstance(parent_rows,dict) else parent_rows
 for r in parent_rows:providers[r['depot']].append(r)
 old_index=read(reuse/'resource_inventory.json') if reuse else {};old_store=Models(reuse/'models') if reuse else None;old_native=Models(reuse/'vanilla_models') if reuse else None
 invalidated=set()
 if reuse and read(reuse/'normalizer_provenance.json')['model_sha256']!=sha(Path(__file__).with_name('model.py')):
  migration=read(reuse/'cache_migration.json');assert migration['old_model_sha256']==read(reuse/'normalizer_provenance.json')['model_sha256'] and migration['new_model_sha256']==sha(Path(__file__).with_name('model.py')),'Normalizer changed without an explicit, evidence-backed cache invalidation';invalidated=set(migration['invalidate_resources'])
 findings=[];exceptions=[];index={};store=Models(o/'models',old_store);native_store=Models(o/'vanilla_models',old_native);chosen={};native_chosen={};ambiguities=[]
 def issue(kind,status,resource=None,**kw):
  f={'id':'F'+str(len(findings)+1).zfill(6),'kind':kind,'status':status,'resource':resource,**kw};findings.append(f);return f
 for r in prep['errors']:issue(r['kind'],'FAIL',evidence=r)
 for z in prep['zip_proofs']:
  if z['crc_failure'] or z['unexpected'] or z['missing'] or z['hash_mismatches']:issue('PACKAGED_FILE_MISMATCH','FAIL',evidence=z)
 # Never choose an ambiguous differing native provider by arbitrary filename order.
 for d,rs in sorted(providers.items()):
  owned=[r for r in rs if r['archive'].endswith('zzzz_PTFR_Combined.archive')];stock=[r for r in rs if r['stock']]
  if stock:
   native_chosen[d]=next((r for r in stock if r.get('json')),stock[0])
   if owned and native_chosen[d].get('json'):
    nr=native_chosen[d]
    if sha(nr['json'])==nr['json_sha256'] and sha(nr['raw'])==nr['sha256'] and not (reuse and native_store.get(d)):native_store.put(d,Resource(read(nr['json'])).normalize())
  eligible=owned or stock or rs;hs={r.get('sha256') for r in eligible}
  all_hashes={r.get('sha256') for r in rs};ambiguous=len(rs)>1 and (len(all_hashes)>1 or all_hashes=={None})
  if ambiguous:ambiguities.append(provider_ambiguity(d,rs,eligible));issue('PROVIDER_PRECEDENCE_UNRESOLVED','UNKNOWN',d,providers=[r['archive'] for r in rs])
  row=next((r for r in eligible if r.get('json')),eligible[0]);chosen[d]=row
  if row.get('json'):
   try:
    if sha(row['json'])!=row['json_sha256'] or sha(row['raw'])!=row['sha256']:raise ValueError('cached/raw/export hash mismatch')
    old=old_index.get(d,{});m=store.get(d) if reuse and d not in invalidated and old.get('sha256')==row['sha256'] and old.get('json')==row['json'] else None
    if m is None:m=Resource(read(row['json'])).normalize();store.put(d,m)
    index[d]={'depot':d,'sha256':row['sha256'],'archive':row['archive'],'json':row['json'],'private':d in private,'type':m['type'],'graphs':[{'path':p,'nodes':len(x['nodes']),'edges':len(x['edges']),'entries':x['entries'],'unreachable_nodes':x['unreachable']} for p,x in m['graphs'].items()],'refs':m['refs'],'root_prefabs':m['root_prefabs'],'journal_paths':sorted({s for _,_,n in allnodes(m) for s in n['journal_paths']}),'errors':m['errors'],'node_count':sum(len(x['nodes']) for x in m['graphs'].values()),'provider_ambiguous':ambiguous}
    index[d]['embedded_files']=m.get('embedded_files',[])
    for error in m['errors']:issue('STRUCTURAL_'+error['kind'],'FAIL' if d in private else 'UNKNOWN',d,evidence=error)
   except (OSError,ValueError,KeyError,TypeError,RecursionError) as e:issue('RESOURCE_MODEL_FAILED','OPAQUE',d,error=str(e));index[d]={'depot':d,'status':'OPAQUE','refs':[],'private':d in private,'sha256':row.get('sha256')}
  else:index[d]={'depot':d,'status':row['status'],'refs':[],'private':d in private,'sha256':row.get('sha256')}
  if len(index)%400==0:print(json.dumps({'stage':'normalize','resources':len(index),'findings':len(findings)}),flush=True)
 write(o/'resource_inventory.json',index);write(o/'provider_inventory.json',{'all_providers':dict(providers),'ambiguous':ambiguities,'precedence_rule':'Current PTFR payload checked against installed/source; unique or byte-identical stock providers used as vanilla; differing providers are UNKNOWN, never silently ranked.'})
 regs,reg_errors,xlfiles=registrations(g)
 for e in reg_errors:issue('REGISTRATION_FORMAT_UNSUPPORTED','UNKNOWN',evidence=e)
 parents={r['depot'] for r in parent_rows};native_ids=set()
 for p in parents:
  m=store.get(p)
  if m:native_ids.update(map(int,m['graphs']['root']['nodes']))
  else:issue('NATIVE_REGISTRATION_PARENT_MISSING','UNKNOWN',p)
 for c in registration_collisions([r for r in regs if r['parent']in parents],native_ids):issue('GENERATED_ID_COLLISION','FAIL',evidence=c)
 roots=[r['path'] for r in regs if r['path']in private];contexts,active,unresolved_entries=active_contexts(store,roots)
 write(o/'execution_contexts.json',{'scope':'MAY reachability from installed XL roots, specific connected input sockets, conditions not solved','contexts':{d:sorted(v) for d,v in contexts.items()},'nodes':{d:sorted(v) for d,v in active.items()},'unresolved':unresolved_entries})
 for u in unresolved_entries:issue('EXECUTION_'+u['reason'],'UNKNOWN',u['resource'],evidence=u)
 features=[];producers=collections.defaultdict(list);readers=collections.defaultdict(list);acks=collections.defaultdict(list);counterfacts=set();cleanupreads=set();owned_prefabs=set()
 for d,locs in active.items():
  m=store.get(d);owned_prefabs.update(m['root_prefabs'])
  for gp,i in sorted(locs):
   n=m['graphs'][gp]['nodes'][i];site={'resource':d,'graph':gp,'node':i,'sha256':chosen[d].get('sha256')};owned_prefabs.update(n['prefabs'])
   if n['writes'] or n['reads'] or n['sms'] or n['reward'] or n['prefabs']:features.append({**site,'type':n['type'],'writes':n['writes'],'reads':n['reads'],'sms':n['sms'],'reward':n['reward'],'prefabs':n['prefabs'],'journal_paths':n['journal_paths'],'refs':n['refs']})
   for x in n['writes']:
    f=x.get('factName','')
    if re.fullmatch(r'(?:holo|audio)_.+_calls_.+_(?:start|end)_activate',f) and x.get('value',0)>0:producers[f].append(site)
    if re.fullmatch(r'holo_.+_calls_.+_(?:start|end)_done',f) and x.get('value',0)>0:acks[f].append(site)
    if re.fullmatch(r'holo_.+_calls_.+_(?:start|end)_count',f):counterfacts.add(f)
   for x in n['reads']:
    if 'factName'in x:readers[x['factName']].append(site)
    if 'cleanup' in d:
     cleanupreads.update(str(x[k]) for k in ['factName','factName1','factName2'] if k in x)
 protocols=native_phone_protocols(store,index,producers)
 write(o/'native_phone_protocols.json',protocols)
 contracts=phone_contract(producers,readers,acks,protocols)
 for c in contracts:
  for missing,kind in [('missing_listener','PHONE_LISTENER_MISSING'),('missing_ack','PHONE_ACK_WRITER_MISSING')]:
   if c[missing]:
    for site in c['producers']:issue(kind,'FAIL',site['resource'],graph=site['graph'],node=site['node'],fact=c['request'],expected_ack=c['expected_ack'])
 for f in cleanup_gap(counterfacts,cleanupreads):issue('CLEANUP_COUNTER_NOT_IN_ACTIVE_CLEANUP_CLOSURE','UNKNOWN',fact=f,reason='May be handled by different reset mechanism; not automatically a missing runtime cleanup')
 native_studios=set()
 for d in ['base\\quest\\holocalls\\holocall_initializers.questphase','ep1\\quest\\holocalls\\holocall_initializers_ep1.questphase']:
  m=store.get(d)
  if m:native_studios.update(m['root_prefabs'])
 for p in native_studios:
  if not any(v==p or v.endswith('/'+p) for v in owned_prefabs):issue('SHARED_PHONE_STUDIO_OWNERSHIP_MISSING','FAIL',prefab=p)
 write(o/'handler_inventory.json',features);write(o/'phone_contracts.json',contracts)
 # Every JSON reference independently checked against capture. Parent metadata is intentionally not followed.
 missing_refs=[];hashed_refs=[];references=[];embedded_providers=collections.defaultdict(list)
 for parent,info in index.items():
  for e in info.get('embedded_files',[]):embedded_providers[e['depot']].append({'container':parent,'graph_prefix':e['graph_prefix'],'container_sha256':info['sha256']})
 write(o/'embedded_provider_inventory.json',dict(embedded_providers))
 for d,info in index.items():
  if d in parents:continue
  for ref in info.get('refs',[]):
   status='RESOLVED_PRESENCE' if ref in providers else ('CONDITIONAL_EMBEDDED' if ref in embedded_providers else ('UNRESOLVED_HASH' if ref.isdecimal() else 'MISSING'))
   rec={'resource':d,'target':ref,'status':status};references.append(rec)
   if status=='CONDITIONAL_EMBEDDED':issue('EMBEDDED_RESOURCE_OWNER_LIFETIME_UNPROVED','CONDITIONAL',d,target=ref,containers=embedded_providers[ref])
   elif status!='RESOLVED_PRESENCE':
    (hashed_refs if ref.isdecimal() else missing_refs).append(rec)
    issue('UNRESOLVED_HASHED_REFERENCE' if ref.isdecimal() else 'DEPENDENCY_NOT_CAPTURED','UNKNOWN',d,target=ref)
 write(o/'dependency_inventory.json',references)
 # Infer identity from explicit mappings, encoded paths, exact native hash, then unique basename.
 candidates=collections.defaultdict(set);evidence=collections.defaultdict(list)
 for r in q['mapping_candidates']:
  if r['private']in private and r['native']in index:candidates[r['private']].add(r['native']);evidence[r['private']].append(r['evidence'])
 native_by_hash=collections.defaultdict(list);native_by_name=collections.defaultdict(list)
 for d,r in native_chosen.items():
  if r['stock']:
   if r.get('sha256'):native_by_hash[r['sha256']].append(d)
   native_by_name[d.split('\\')[-1]].append(d)
 for d,r in private.items():
  if d in native_chosen:candidates[d].add(d);evidence[d].append('Official-depot override with separately decoded stock provider')
  if not candidates[d]:candidates[d].update(native_by_hash.get(r['sha256'],[]))
  if not candidates[d]:
   hits=native_by_name.get(d.split('\\')[-1],[])
   if len(hits)==1:candidates[d].add(hits[0]);evidence[d].append('UNIQUE_BASENAME_CANDIDATE_NOT_AUTHORIZATION')
 native_targets=collections.defaultdict(set)
 for d,v in candidates.items():
  if len(v)==1:native_targets[next(iter(v))].add(d)
 relocation={n:next(iter(ds)) for n,ds in native_targets.items() if len(ds)==1}
 repairs=read(w/'prealpha/consolidation_repair_cr1/candidate_01/selected_resources_01.json')['resources'];corrected={r['depot']:r['after'] for r in repairs};repair_results=[]
 for r in repairs:
  actual=private.get(r['depot'],{}).get('sha256');state='PASS' if actual==r['after'] else 'UNKNOWN'
  if actual==r['before']:state='FAIL';issue('CORRECTED_DONOR_REGRESSION','FAIL',r['depot'],expected=r['after'],actual=actual)
  repair_results.append({'depot':r['depot'],'status':state,'expected':r['after'],'actual':actual,'rationale':r['rationale']})
 pair_results=[];diffs=[]
 for d,r in private.items():
  cs=candidates[d];record={'private':d,'private_sha256':r['sha256'],'native_candidates':sorted(cs),'evidence':evidence[d]}
  if d not in index or not index[d].get('graphs'):
   record.update(status='OPAQUE',reason='Payload readback pinned; non-graph content is presence-only or unsupported, so semantic/native asset parity is not certified');pair_results.append(record);continue
  if len(cs)!=1:record.update(status='UNKNOWN',reason='No unique source identity; wrapper or unsupported mapping');pair_results.append(record);continue
  n=next(iter(cs));a=native_store.get(n) if n in private else store.get(n);b=store.get(d)
  if not a or not b:record.update(status='OPAQUE',reason='Missing decoded baseline/model');pair_results.append(record);continue
  delta=compare_graph(a,b);relocated=compare_graph(a,b,relocation);approved_corrected=corrected.get(d)==r['sha256']
  if index[d].get('provider_ambiguous') or index.get(n,{}).get('provider_ambiguous'):status='UNKNOWN';reason='Differing or unhashed providers prevent effective-provider parity certification'
  elif not delta:status='PASS';reason='Full normalized graph/metadata parity'
  elif not relocated:status='APPROVED_DEVIATION';reason='Exact private-reference relocation only; target semantics audited separately'
  elif approved_corrected:status='APPROVED_DEVIATION';reason='Exact explicitly selected corrected CR1 donor; native delta retained in registry'
  else:status='UNKNOWN';reason='Difference needs exact approved scope; not automatically a gameplay defect'
  record.update(native=n,native_sha256=native_chosen[n].get('sha256'),status=status,reason=reason,difference_count=len(delta));pair_results.append(record)
  for x in delta:
   rec={'resource':d,'native':n,'native_sha256':native_chosen[n].get('sha256'),'private_sha256':r['sha256'],**x};diffs.append(rec)
   exceptions.append({**rec,'status':'APPROVED_DEVIATION' if status=='APPROVED_DEVIATION' else 'UNKNOWN','authorization_evidence':str(w/'prealpha/consolidation_repair_cr1/candidate_01/selected_resources_01.json') if approved_corrected else ('Root additive-private-resource policy plus exact identity mapping; does not approve target semantic differences' if not relocated else None),'evidence_sources':evidence[d],'reason':reason})
 write(o/'resource_parity.json',pair_results);write(o/'differences.json',diffs);write(o/'intentional_differences.json',{'rule':'Only exact reference-only relocation or hash-matching explicit corrected donor approved. All other deltas require evidence and stay UNKNOWN. No current-payload-is-installed tautological approval.','entries':exceptions});write(o/'corrected_donor_checks.json',repair_results)
 # Quest association is deliberately conservative and exposes shared/ambiguous roots.
 pair_map={r['private']:r for r in pair_results};stages=[];quests=[];known_native=set(d for d,r in chosen.items() if r['stock'])
 for quest in catalogue['quests']:
  qid=quest['id'];jp=quest.get('journal_path','');short=re.match(r'^(mq\d+|sq\d+)',qid);short=short[0] if short else qid
  direct={d for d,info in index.items() if info.get('private') and (qid.lower() in d.lower() or (short!=qid and re.search(r'(?<![a-z0-9])'+re.escape(short)+r'(?!\d)',d,re.I)) or (jp and any(p==jp or p.startswith(jp+'/') for p in info.get('journal_paths',[]))))}
  native_roots={d for d,info in index.items() if d in known_native and (qid.lower() in d.lower() or (jp and any(p==jp or p.startswith(jp+'/') for p in info.get('journal_paths',[]))))}
  native_roots.update(d for d in q.get('quest_seeds',{}).get(qid,[]) if d in known_native)
  closure=set(direct);todo=list(direct)
  while todo:
   for dep in index.get(todo.pop(),{}).get('refs',[]):
    if dep in index and dep not in closure:closure.add(dep);todo.append(dep)
  ps=[pair_map[d] for d in direct if d in pair_map];unreviewed=[p for p in ps if p['status']in ('UNKNOWN','OPAQUE')];uncompared=direct-set(pair_map);qs=[f for f in findings if f.get('resource')in closure]
  result={'id':qid,'title':quest.get('title'),'selection':quest['decision'],'held':quest['held'],'requirements':quest.get('requirements'),'private_root_candidates':sorted(direct),'native_root_candidates':sorted(native_roots),'dependency_closure':sorted(closure),'mapped_comparisons':len(ps),'unresolved_comparisons':len(unreviewed),'findings':[f['id'] for f in qs],'root_association_limit':'Journal/path/ID associations are candidate evidence; shared roots and current live ownership need further validation.'}
  for stage in ['entry','phone','sms','progression','cleanup','rewards','assets','saved_owners']:
   st='CONDITIONAL';reason='Native route/owner constraints retained; condition feasibility and exact stage admission not proved'
   if quest['decision']!='INCLUDE':st='CONDITIONAL';reason='Excluded/held/separate-scope catalogue row; no restoration activation inferred'
   elif not direct or not native_roots:st='UNKNOWN';reason='Restored or vanilla root identity unresolved'
   elif stage=='assets':st='OPAQUE';reason='Referenced assets checked for presence; full actor/world/prefab placement semantics not decoded by this pass'
   elif stage=='saved_owners':st='LIVE_ONLY';reason='Persistent identities recorded; actual serialized owner liveness/migration requires save/runtime evidence'
   elif stage in ('progression','rewards','sms'):
    st='UNKNOWN' if unreviewed or uncompared or not ps else 'CONDITIONAL';reason='Direct-root comparisons only; complete stage dependencies, ownership and lifecycle postconditions are not proved'
   elif stage=='phone':
    pc=[c for c in contracts if any(s['resource']in closure for s in c['producers'])];st='FAIL' if any(c['missing_listener'] or c['missing_ack'] for c in pc) else 'CONDITIONAL';reason='Active MAY-closure request/listener/ack presence; listener admission, UI and playback remain unproved'
   elif stage=='cleanup':st='UNKNOWN' if unreviewed else 'CONDITIONAL';reason='Counter/reset and graph inventory; exact lifecycle exits and reward uniqueness not universally proved'
   ids=[f['id'] for f in qs if f['status']=='FAIL']
   if quest['decision']=='INCLUDE' and ids and stage in ('progression','cleanup'):st='FAIL';reason='Structural/contract failures in associated dependency closure; see evidence'
   stages.append({'quest_id':qid,'stage':stage,'status':st,'reason':reason,'private_roots':sorted(direct),'native_roots':sorted(native_roots),'findings':ids,'mapped_resources':len(ps),'unknown_resources':len(unreviewed)})
  own=[s for s in stages if s['quest_id']==qid and s['stage']!='saved_owners'];result['status']=next((s for s in ['FAIL','UNKNOWN','OPAQUE','CONDITIONAL','APPROVED_DEVIATION','PASS'] if any(x['status']==s for x in own)),'UNKNOWN');quests.append(result)
  if len(quests)%40==0:print(json.dumps({'stage':'quests','done':len(quests)}),flush=True)
 write(o/'quest_results.json',quests);csvwrite(o/'quest_results.csv',[{k:v for k,v in r.items() if k!='dependency_closure'} for r in quests]);write(o/'stage_results.json',stages);csvwrite(o/'stage_results.csv',stages);write(o/'findings.json',findings);csvwrite(o/'findings.csv',findings_as_rows(findings))
 coverage={'json_references':len(references),'not_in_capture':missing_refs,'hashed_unresolved':hashed_refs,'capture_missing':capture['missing'],'capture_truncated':capture['truncated'],'catalogue_name_disagreements':[r['id'] for r in catalogue['quests'] if not r['selected_name_agrees']],'unresolved_entry_bindings':len(unresolved_entries),'private_models':sum(d in private and bool(v.get('graphs')) for d,v in index.items()),'private_resource_readbacks':len(capture['private_readback']),'total_private':len(private),'decode_error_count':len(capture['decode_errors']),'registration_errors':reg_errors}
 write(o/'coverage.json',coverage)
 summary={'status':'STATIC_AUDIT_COMPLETE_WITH_UNRESOLVED_COVERAGE','blanket_pass':False,'catalogue':catalogue['derived_counts'],'held':catalogue['held_ids'],'quest_results':dict(collections.Counter(r['status'] for r in quests)),'selected_quest_results':dict(collections.Counter(r['status'] for r in quests if r['selection']=='INCLUDE')),'stage_results':dict(collections.Counter(r['status'] for r in stages)),'resource_comparisons':dict(collections.Counter(r['status'] for r in pair_results)),'findings':dict(collections.Counter(r['status'] for r in findings)),'resources_discovered':len(index),'decoded_graph_resources':sum(bool(v.get('graphs')) for v in index.values()),'graph_nodes':sum(v.get('node_count',0) for v in index.values()),'execution_context_resources':len(active),'phone_contracts':len(contracts),'root_registrations':len(regs),'native_parent_ids':sorted(native_ids),'provider_ambiguities':len(ambiguities),'all_depots_resolved':not missing_refs and not capture['truncated'] and not capture['missing'],'verification_scope':'Static structure and source identity; no gameplay or save-owner liveness claim','restrictions':'No runtime/quest resources, saves/facts, packages, builds or installs modified.'}
 write(o/'summary.json',summary);print(json.dumps(summary,indent=2))
def findings_as_rows(fs):
 for f in fs:yield {'id':f['id'],'status':f['status'],'kind':f['kind'],'resource':f.get('resource'),'graph':f.get('graph'),'node':f.get('node'),'detail':{k:v for k,v in f.items() if k not in ('id','status','kind','resource','graph','node')}}

def native_phone_protocols(store,index,requests):
 """Derive ACK names from native listener + its referenced holocall scene, not request spelling."""
 result={};wanted=set(requests)
 for d,r in index.items():
  if r.get('private') or '\\holocalls\\'not in d or not d.endswith('.questphase') or not r.get('graphs'):continue
  m=store.get(d);listens={x.get('factName') for _,_,n in allnodes(m) for x in n['reads']} & wanted
  if not listens:continue
  refs={d}|{x for x in m['refs'] if '\\holocalls\\'in x and x in index and index[x].get('graphs')};writers=collections.defaultdict(list)
  for ref in refs:
   for gp,i,n in allnodes(store.get(ref)):
    for x in n['writes']:
     if x.get('value',0)>0 and re.fullmatch(r'holo_.+_calls_.+_(?:start|end)_done',x.get('factName','')):writers[x['factName']].append({'resource':ref,'graph':gp,'node':i,'sha256':index[ref]['sha256']})
  for fact in listens:
   part='start' if fact.endswith('_start_activate') else 'end';incoming='_calls_v_' in fact;expected=[f for f in writers if f.endswith('_'+part+'_done') and ('_calls_v_'in f)==incoming]
   if len(expected)==1:result[fact]={'ack':expected[0],'native_listener_resource':d,'listener_sha256':r['sha256'],'ack_sources':writers[expected[0]],'limit':'Unique native contact/direction protocol inferred from listener scene; conditions and runtime playback not proved'}
 return result
