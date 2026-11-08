"""Independent raw-source CVI02 EP1 controller and input-scoped context adjudication."""
from pathlib import Path
import json,sys,gzip,copy,argparse,collections,zlib
H=Path(__file__).resolve().parent;W=H.parents[5];F=W/'prealpha/quest_restoration_qr5'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value,fnv
from model import Resource
B=r'base\open_world\street_stories\pacifica\coastview\sts_pac_cvi_02\phases\sts_pac_cvi_02.questphase'
C=r'base\open_world\fixers\mr_hands\scenes\mr_hands_new_scenes_activators.questphase'
S=r'ep1\openworld\fixers\mr_hands\scenes\mr_hands_combat_zone_default.scene'
OW=r'ep1\openworld\ep1_open_world.questphase';EP=r'ep1\quest\ep1.questphase'
E=r'towercontinued\native_gigs_u9\sts_pac_cvi_02_entry.questphase'
DEF=r'ep1\openworld\fixers\mr_hands\phases\mr_hands_combat_zone_default.questphase'
FO=r'towercontinued\fixer_offices_fo1\mr_hands.questphase'
V=r'ep1\openworld\vendors\vehicle_metaquest\phases\vehicle_metaquest_ep1_bugfixing.questphase'
ROUTES=[(205,162,208,'new_sts_pac_cvi_02_holocall_prebrief',17,'prebrief_in',6,'new_q110_prebrief_rejected_or_end',221),(213,158,215,'new_sts_pac_cvi_02_holocall_debrief_failed',16,'debrief_failed_in',11,'new_q110_debrief_failed_end',220),(214,157,217,'new_sts_pac_cvi_02_holocall_debrief_perfect',18,'debrief_perfect_in',10,'new_q110_debrief_perfect_end',218)]

def run(O):
 assert not O.exists();O.mkdir(parents=True);T=[];P=[];M={};R={};BG='root/8/10';CG='root/9'
 def ck(k,v,e):
  T.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:write(O/'failed_tests.json',T);raise AssertionError(k)
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def edge(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
 def hasfact(d,i,f,v,kind='reads',gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(d,i,gp)[kind])
 def reach(gr,a):
  q=collections.deque([str(a)]);seen=set(q)
  while q:
   v=q.popleft()
   for x,s,y,t in gr['edges']:
    if x==v and s!='CutSource'and t!='CutDestination'and y not in seen:seen.add(y);q.append(y)
  return seen
 def canon(x):
  x=json.loads(json.dumps(x))
  for z in walk(x):
   z.pop('payload_sha256',None);z.pop('metadata_sha256',None)
   if z.get('$type')=='TweakDBID':
    v=z['$value'];z['$value']=str((len(v.encode())<<32)|zlib.crc32(v.encode()))if z['$storage']=='string'else str(int(v));z['$storage']='uint64'
  return x
 old=F/'reviews/worker_b/G03_EP1/evidence.json';ck('reviewed source finding frozen',sha(old)=='84307EFA2103FB2A7C428CB69C64EE1E5AFD8A3EFC73CB0FA6E3720620B83895',str(old));P.append({'path':str(old),'sha256':sha(old)})
 ep=read(F/'source_epoch_00.json');idx=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json')
 manifests=[H/'raw_exports_01/manifest.json',H/'raw_exports_02/manifest.json']
 for mf in manifests:
  for p in read(mf):
   d=p['depot'];ck('fresh raw/hash '+d,sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256'],p);P.append(p);R[d]=read(p['json']);M[d]=Resource(R[d]).normalize();ck('fresh decode '+d,not M[d]['errors'],M[d]['errors'])
   ck('matching native/effective inventory '+d,p['raw_sha256']==(ep['source_resources'][d]if d.startswith('towercontinued')else idx[d]['sha256']),p['raw_sha256'])
   before=Resource(read(idx[d]['json'])).normalize();ck('fresh/historical exact storage-only equality '+d,canon(M[d])==canon(before),'No NodeRef/branch/condition/graph omissions')
 for cond,legacy,prod,req,listener,socket,ackwriter,ack,wait in ROUTES:
  ck('actual EP1/legacy split '+str(cond),n(B,cond,BG)['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'ep1_installed','value':0}]and edge(B,cond,'True',prod,'In',BG)and edge(B,cond,'False',legacy,{205:'Start 0',213:'debrief_failed',214:'debrief_perfect'}[cond],BG),n(B,cond,BG)['payload'])
  ck('native EP1 request/wait '+req,hasfact(B,prod,req,1,'writes',BG)and edge(B,prod,'Out',wait,'In',BG)and hasfact(B,wait,ack,0,'reads',BG),{'producer':prod,'wait':wait,'fact':ack})
  ck('native listener/scene input '+req,n(C,listener,CG)['type']=='questPauseConditionNodeDefinition'and hasfact(C,listener,req,0,'reads',CG)and edge(C,listener,'Out',13,socket,CG),n(C,listener,CG)['payload'])
  ck('actual outcome writer '+ack,hasfact(C,ackwriter,ack,1,'writes',CG)and any(e[0]=='13'and e[2]==str(ackwriter)for e in g(C,CG)['edges']),n(C,ackwriter,CG)['payload'])
 ck('native PONR guard preserved',n(C,15,CG)['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'q115_point_of_no_return','value':0}]and all(edge(C,15,'False',i,'In',CG)for i in [16,17,18]),n(C,15,CG)['payload'])
 ck('controller exact startup route',edge(C,0,'Out',20,'In',CG)and edge(C,20,'Out',15,'In',CG),'deletion marker retains native startup')
 ck('controller real generic phone bridge',edge(C,13,'Holocall RET',7,'In',CG)and edge(C,13,'Holocall INT',8,'In',CG)and hasfact(C,7,'holo_mr_hands_calls_v_start_activate',1,'writes',CG)and hasfact(C,8,'holo_mr_hands_calls_v_end_activate',1,'writes',CG),'specific q110 scene outcomes still required')
 ck('original owner exact ancestor',edge(OW,0,'Out',28,'In1')and C in n(OW,28)['refs']and OW in n(EP,5,'root/10')['refs'],'EP1 root10/5 owns openworld28→activator9')
 ck('actual Tower cuts controller ancestor',edge(EP,9,'CutSource',5,'CutDestination','root/10')and edge(EP,9,'Out',10,'In','root/10')and hasfact(EP,10,'q307_ep1_killed',1,'writes','root/10'),'not inference from killed fact alone')
 ck('migration entry does not restore controller',g(OW)['entries']['CP77-63752']=='47'and'28'not in reach(g(OW),'47')and edge(V,4,'False',6,'CP77-63752','root/5'),'separate vehicle migration input does not pulse main0')
 ck('empty ancestry prefabs still leave scene obligations',not M[C]['root_prefabs']and not n(C,9)['prefabs']and not M[OW]['root_prefabs']and not n(EP,5,'root/10')['prefabs']and S in n(C,13,CG)['refs']and '#mr_sm_hands_combat_zone_default'in n(C,13,CG)['node_refs'],n(C,13,CG)['payload'])
 # Independent inventory-wide consumers, positive outcomes and literal/FNV ownership census.
 mi_path=W/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json';mi=read(mi_path);facts={r[3]for r in ROUTES}|{r[7]for r in ROUTES}|{'new_q110_rejected_failed_out','new_q110_rejected_perfect_out'};FA={a:f for f in facts for a in[f,fnv(f)]};deps=[C,OW,DEF,FO];hits=[];refs=[];pref=[]
 needles=[a.encode()for a in FA]+[json.dumps(d)[1:-1].encode()for d in deps]+[fnv(d).encode()for d in deps]+[b'mr_hands_combat_zone_default_prefabPY55PSI']
 for d,row in mi.items():
  data=Path(row['normalized_model']).read_bytes();assert sha(row['normalized_model'])==row['normalized_sha256'];blob=gzip.decompress(data)
  if not any(a in blob for a in needles):continue
  m=json.loads(blob)
  for gp,gr in m['graphs'].items():
   for ni,nd in gr['nodes'].items():
    for kind in['reads','writes']:
     for f in nd.get(kind,[]):
      if f.get('factName')in FA:hits.append({'depot':d,'graph':gp,'node':ni,'kind':kind,'canonical_fact':FA[f['factName']],'fact':f})
    for target in deps:
     if target in nd['refs']or fnv(target)in nd['refs']:refs.append({'depot':d,'graph':gp,'node':ni,'target':target})
    if any('mr_hands_combat_zone_default_prefabPY55PSI'in p for p in nd['prefabs']):pref.append({'depot':d,'graph':gp,'node':ni,'prefabs':nd['prefabs']})
 ck('independent full model universe scanned',len(mi)==5136,{'path':str(mi_path),'sha256':sha(mi_path),'every_actual_gzip_hash_checked':True})
 for _,_,_,req,_,_,_,ack,_ in ROUTES:
  r=[x for x in hits if x['canonical_fact']==req and x['kind']=='reads'];w=[x for x in hits if x['canonical_fact']==ack and x['kind']=='writes'and x['fact'].get('value',0)>0]
  ck('sole captured native consumer/positive outcome '+req,bool(r)and bool(w)and{x['depot']for x in r+w}=={C},{'request_consumers':r,'positive_ack_writers':w})
 ck('only native activator parent', {x['depot']for x in refs if x['target']==C}=={OW},refs)
 ck('private default provider exists but is distinct',any(x['depot']==FO and x['target']==DEF for x in refs),refs)
 ck('default prefab not another private clone', {x['depot']for x in pref}=={DEF,r'ep1\openworld\fixers\mr_hands\phases\mr_hands_fixers_loop.questphase'},pref)
 package_text=[];matches=[]
 for p in(Path(ep['candidate'])/'package').rglob('*'):
  if p.is_file()and p.suffix.lower()in['.reds','.lua','.yaml','.xl']:
   tx=p.read_text(encoding='utf-8-sig');package_text.append({'path':str(p),'sha256':sha(p)})
   if any(x in tx for x in facts):matches.append(str(p))
 ck('no literal packaged script substitute',not matches,{'source_files':len(package_text),'matches':matches,'limit':'Does not certify external/dynamic mods'})
 write(O/'census.json',{'models':len(mi),'model_inventory_sha256':sha(mi_path),'facts':sorted(facts),'fact_hits':hits,'reverse_refs':refs,'prefab_owners':pref,'package_text':package_text})
 # Per-input scene analysis: do not declare Johnny/physical participant obligations from global metadata alone.
 sg=M[S]['graphs']['scene'];lines={x['itemId']['id']:x for x in M[S]['metadata']['screenplayStore']['lines']};actors={a['actorName']:a for a in M[S]['metadata']['actors']};input_results={}
 for name,expected_n in [('prebrief_in',26),('debrief_failed_in',27),('debrief_perfect_in',27)]:
  seen=reach(sg,sg['entries'][name]);nodes={i:sg['nodes'][i]for i in seen};sections={i:n for i,n in nodes.items()if n['type']=='scnSectionNode'};events=[e for n in sections.values()for e in n['payload']['events']];spoken=[lines[e['screenplayLineId']['id']]for e in events if e['$type']=='scnDialogLineEvent']
  ck('bounded scene input closure '+name,len(seen)==expected_n,{'entry':sg['entries'][name],'nodes':sorted(seen)})
  ck('selected events are holo dialogue only '+name,bool(events)and all(e['$type']=='scnDialogLineEvent'and e['voParams']['isHolocallSpeaker']==1 for e in events),events)
  ck('selected speaker only holo actor1 '+name,bool(spoken)and all(x['speaker']['id']==1 and x['addressee']['id']==3 for x in spoken),spoken)
  ck('no selected physical camera/workspot/subscene commands '+name,all(n['payload']['questNode']['$type']in['questFactsDBManagerNodeDefinition','questConditionNodeDefinition','questPauseConditionNodeDefinition']for n in nodes.values()if n['type']=='scnQuestNode')and all(b['behaviorMode']=='OnlyIfAlive'for n in sections.values()for b in n['payload']['actorBehaviors']),'actor0/Johnny global acquisition/engine semantics remain separate')
  ck('selected native start and end generic waits '+name,any(any(r.get('factName')=='holo_mr_hands_calls_v_start_done'for r in n['reads'])for n in nodes.values())and any(any(r.get('factName')=='holo_mr_hands_calls_v_end_done'for r in n['reads'])for n in nodes.values()),'generic controller supports these waits but not the missing q110 outcomes')
  input_results[name]={'entry':sg['entries'][name],'reachable':sorted(seen),'edges':[e for e in sg['edges']if e[0]in seen and e[2]in seen],'sections':sections,'dialogue_lines':spoken,'quest_nodes':{i:n for i,n in nodes.items()if n['type']=='scnQuestNode'}}
 ck('scene exact physical and holo acquisition plans',actors['mr_hands']['acquisitionPlan']=='spawnSet'and value(actors['mr_hands']['spawnSetParams']['reference'])=='#mr_hands_combat_zone'and actors['mr_hands_holo']['acquisitionPlan']=='spawnSet'and value(actors['mr_hands_holo']['spawnSetParams']['reference'])=='#mr_hands_holo',actors)
 ck('Johnny is native Voice-context actor not visible selected speaker',actors['johnny']['acquisitionPlan']=='findInContext'and actors['johnny']['findActorInContextParams']['contextualName']=='Voice','R4 selected-input proof; global actor acquisition is engine-dependent')
 ck('native actual default instance prefab retained',bool(n(DEF,2)['prefabs'])and'mr_hands_combat_zone_default_prefabPY55PSI'in n(DEF,2)['prefabs'][0]and S in n(DEF,33,'root/2')['refs']and '#mr_sm_hands_combat_zone_default'in n(DEF,33,'root/2')['node_refs'],n(DEF,2)['payload'])
 ck('existing FO1 provider connected',edge(FO,0,'Out',1,'In')and edge(FO,1,'Out',2,'In')and edge(FO,2,'Out',3,'In')and edge(FO,3,'True',4,'In')and edge(FO,4,'Out',100,'In1')and DEF in n(FO,100)['refs'],'real current provider, not a blanket missing-prefab claim')
 ck('FO1 conditional history gates',all(any(r.get('factName')==f and r.get('comparisonType')=='Greater'and r.get('value')==0 for r in n(FO,2)['reads'])for f in['mr_hands_default_on','mr_hands_default_ep1']),'requires real earned default history; do not fabricate')
 ck('CVI02 lacks proof of FO1 lease',not any(r.get('factName','').startswith('PTFRFO1_')or r.get('factName')in['mr_hands_default_on','mr_hands_default_ep1']for r in n(E,65002)['reads']),'no guaranteed active marker/default lease follows merely from CVI02 ParentEntered')
 ck('native default lifetime is conditional not permanent',edge(DEF,0,'Out',4,'In')and edge(DEF,4,'Out',5,'In')and edge(DEF,5,'Out',2,'In1')and edge(DEF,2,'Out1',6,'In')and edge(DEF,6,'Out',5,'In')and hasfact(DEF,5,'mr_hands_default_on',0),'outer receipt does not prove currently streaming instance')
 write(O/'scene_inputs.json',input_results);write(O/'actor_and_prefab_obligations.json',{'actors':actors,'native_default_instance_prefab':n(DEF,2)['payload'],'existing_FO1_guard':n(FO,2)['payload'],'existing_FO1_edges':g(FO)['edges'],'default_lifetime':g(DEF)['edges'],'scope':'Native source context only. Exact marker placement and independent scene startup actor acquisition are unresolved; no worldNode decode retry.'})
 # Raw mutations target the real listener and specific callback, then inject a forbidden physical speaker.
 mutations=[]
 for name,key,predicate,change,oracle in [('lost_specific_outcome',C,lambda x:x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='new_q110_prebrief_rejected_or_end',lambda x:x.update(value=0),lambda m:any(w.get('factName')=='new_q110_prebrief_rejected_or_end'and w.get('value')==1 for w in m['graphs'][CG]['nodes']['6']['writes'])),('wrong_holo_speaker',S,lambda x:x.get('$type')=='scnscreenplayDialogLine'and x.get('itemId',{}).get('id')==8449,lambda x:x['speaker'].update(id=0),lambda m:next(x for x in m['metadata']['screenplayStore']['lines']if x['itemId']['id']==8449)['speaker']['id']==1)]:
  raw=copy.deepcopy(R[key]);changed=0
  for x in walk(raw):
   if predicate(x):change(x);changed+=1
  ck('actual raw mutation '+name,changed==1 and oracle(M[key])and not oracle(Resource(raw).normalize()),'real source mutation caught by independent native protocol/context oracle');f=O/'mutations'/str(name+'.json');write(f,raw);mutations.append({'fault':name,'path':str(f),'sha256':sha(f),'detected':True})
 write(O/'tests.json',T);write(O/'source_pins.json',P);write(O/'mutations.json',mutations)
 review={'id':'QR5-CVI02-MISSING-EP1-CALL-CONTROLLER','status':'CONFIRMED_SOURCE_DEFECT_REPAIR_BLOCKED_BY_EXACT_CONTEXT_AND_OWNER_EVIDENCE','checks':len(T),'raw_mutations':len(mutations),'fresh_raw_resources':len(M),'reviewed_evidence_sha256':sha(old),'source_epoch':'QR5 epoch00; candidate02 does not repair this resource','affected_contracts':['communications','ownership','progression','completion_rewards_cleanup','shared_dependencies'],'counterexample':'Fresh CVI02 ep1_installed1/PONR0/real outcome0 follows205.True→208→221; the only captured request consumer/positive specific outcome owner is native activator9 under actually cut EP1openworld28. Generic Hands acknowledgement cannot satisfy new_q110 outcome. Failed/perfect debrief routes similarly depend on it.','context_adjudication':['Selected scene1110/955/949 closures have only actor1 Hands-holo dialog, no physical/Johnny speaker, camera/workspot commands or unrelated self-subscene input. No selected Johnny visual defect proved.','Global scene metadata still acquires physical Hands0 via #mr_hands_combat_zone, holo1 via #mr_hands_holo and native Voice-context Johnny2. OnlyIfAlive behaviors do not prove engine startup ignores unavailable actor plans.','Native physical-default node2 owns a specific recursive PhaseInstancePrefab and calls the same #mr_sm_hands_combat_zone_default marker. Current FO1 really references that phase, so no blanket absence claim.','FO1 requires earned mr_hands_default_on/default_ep1>0 and loops its actual prefab by native lifetime. CVI02 entry has no FO1/default lease fence. Thus current source does not guarantee independent sceneLocation/actor acquisition across the supported fresh CVI02 set.'],'repair_blockers':['Establish exact #mr_sm_hands_combat_zone_default world placement/lease and whether input-specific scene startup can run without the physical default phase; currently opaque placement/engine acquisition.','Establish safe arbitration with existing FO1/native/saved default and custom-scene owners; a new duplicate physical/default/prefab owner is not authorized by missing callback alone.','Design a source-reviewed future-only initial adapter with exact request/outcome-zero histories and positive event provenance, before native progress; do not retroactively adopt already-entered callers or reset earned q110 results.'],'prohibited_shortcuts':['No q110 ACK fabrication or ep1_installed/PONR mutation.','No broad EP1openworld/activator/default rehost or unconditional prefab import.','No assumption that scene metadata participant presence proves selected visual presentation failure.'],'source_only_proposal':None,'runtime_changes':[],'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'census':str(O/'census.json'),'scene_inputs':str(O/'scene_inputs.json')};write(O/'review.json',review);print(json.dumps({'checks':len(T),'mutations':len(mutations),'review_sha256':sha(O/'review.json')}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(Path(a.output).resolve())
