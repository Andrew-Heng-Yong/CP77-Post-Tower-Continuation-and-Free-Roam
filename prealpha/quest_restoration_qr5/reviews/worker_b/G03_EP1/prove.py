"""CVI02 EP1 request/controller gap, independently derived from pinned sources."""
from pathlib import Path
import sys,json,gzip,copy,collections
W=Path(__file__).resolve().parents[5];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,fnv
from model import Resource
def path(g,a,b):
 q=collections.deque([[str(a)]]);seen={str(a)}
 while q:
  p=q.popleft()
  if p[-1]==str(b):return p
  for x,s,y,t in g['edges']:
   if x==p[-1]and s!='CutSource'and t!='CutDestination'and y not in seen:seen.add(y);q.append(p+[y])
 return None
def run():
 O=H/'verification_01';assert not O.exists();ts=[];pins=[];M={};D={}
 def ck(k,v,e):ts.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e});assert v,k
 idx=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json');ep=read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json');P=W/'prealpha/quest_restoration_qr5/groups/G03';result=read(P/'results.json');catalog={p.get('depot'):p for p in read(result['source_pins'])if p.get('depot')};ck('peer_pins_frozen',sha(result['source_pins'])==result['source_pins_sha256'],result['source_pins'])
 B='base\\open_world\\street_stories\\pacifica\\coastview\\sts_pac_cvi_02\\phases\\sts_pac_cvi_02.questphase';C='base\\open_world\\fixers\\mr_hands\\scenes\\mr_hands_new_scenes_activators.questphase';OW='ep1\\openworld\\ep1_open_world.questphase';EP='ep1\\quest\\ep1.questphase';V='ep1\\openworld\\vendors\\vehicle_metaquest\\phases\\vehicle_metaquest_ep1_bugfixing.questphase';S='ep1\\openworld\\fixers\\mr_hands\\scenes\\mr_hands_combat_zone_default.scene';E='towercontinued\\native_gigs_u9\\sts_pac_cvi_02_entry.questphase'
 for d in [B,C,OW,EP,V,S,E]:
  if d in catalog:p=catalog[d]
  else:
   r=idx[d];j=Path(r['json']);raw=j.with_suffix('')
   if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
   p={'depot':d,'binary':str(raw),'sha256':r['sha256'],'json':str(j),'json_sha256':sha(j),'provider':r['archive']}
  ck('actual_source_hash '+d,sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p)
  if d.startswith('towercontinued'):ck('current_epoch_pin '+d,p['sha256']==ep['source_resources'][d],p)
  D[d]=read(p['json']);M[d]=Resource(D[d]).normalize();ck('decoded_source '+d,not M[d]['errors'],M[d]['errors']);pins.append(p)
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def e(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
 BG='root/8/10';CG='root/9'
 for ni,legacy,request in [(205,162,208),(213,158,215),(214,157,217)]:
  ck('actual_EP1_native_branch '+str(ni),n(B,ni,BG)['reads'][0]=={'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'ep1_installed','value':0}and any(x[0]==str(ni)and x[1]=='True'and x[2]==str(request)for x in g(B,BG)['edges'])and any(x[0]==str(ni)and x[1]=='False'and x[2]==str(legacy)for x in g(B,BG)['edges']),n(B,ni,BG)['payload'])
 routes=[(208,'new_sts_pac_cvi_02_holocall_prebrief',17,'prebrief_in',6,'new_q110_prebrief_rejected_or_end',221),(215,'new_sts_pac_cvi_02_holocall_debrief_failed',16,'debrief_failed_in',11,'new_q110_debrief_failed_end',220),(217,'new_sts_pac_cvi_02_holocall_debrief_perfect',18,'debrief_perfect_in',10,'new_q110_debrief_perfect_end',218)]
 trace=[]
 for producer,request,listener,socket,ackwriter,ack,wait in routes:
  ck('native_request_producer '+request,any(w.get('factName')==request and w.get('value')==1 for w in n(B,producer,BG)['writes']),n(B,producer,BG)['payload'])
  ck('real_native_EP1_consumer '+request,n(C,listener,CG)['type']=='questPauseConditionNodeDefinition'and any(r.get('factName')==request for r in n(C,listener,CG)['reads'])and e(C,listener,'Out',13,socket,CG),n(C,listener,CG)['payload'])
  ck('real_native_outcome '+ack,any(w.get('factName')==ack and w.get('value')==1 for w in n(C,ackwriter,CG)['writes'])and any(x[0]=='13'and x[2]==str(ackwriter)for x in g(C,CG)['edges']),n(C,ackwriter,CG)['payload'])
  ck('current_body_waits_actual_EP1_outcome '+ack,any(r.get('factName')==ack for r in n(B,wait,BG)['reads'])and e(B,producer,'Out',wait,'In',BG),n(B,wait,BG)['payload'])
  trace.append({'body':B,'graph':BG,'producer':producer,'request':request,'native_controller':C,'controller_graph':CG,'listener':listener,'scene_node':13,'scene_input':socket,'outcome_writer':ackwriter,'outcome':ack,'body_wait':wait})
 ck('preserved_EP1_controller_PONR_guard',n(C,15,CG)['reads'][0]['factName']=='q115_point_of_no_return'and all(e(C,15,'False',x,'In',CG)for x in [16,17,18]),n(C,15,CG)['payload'])
 ck('EP1_owner_path',e(OW,0,'Out',28,'In1')and C in n(OW,28)['refs']and OW in n(EP,5,'root/10')['refs'],'EP1root/10/5→EP1openworld28→baseMrHandsactivators9')
 ck('Tower_cuts_exact_EP1_owner',e(EP,9,'CutSource',5,'CutDestination','root/10')and e(EP,9,'Out',10,'In','root/10')and n(EP,10,'root/10')['writes'][0]['factName']=='q307_ep1_killed',n(EP,9,'root/10')['payload'])
 ck('vehicle_migration_uses_different_input',e(V,4,'False',6,'CP77-63752','root/5')and g(OW)['entries']['CP77-63752']=='47'and not path(g(OW),'47','28'),{'entry':g(OW)['entries'],'incoming28':[x for x in g(OW)['edges']if x[2]=='28'],'CP77_to28':path(g(OW),'47','28')})
 ck('no_activator_prefab_does_not_resolve_scene_context',not M[C]['root_prefabs']and not n(C,9)['prefabs']and S in n(C,13,CG)['refs']and '#mr_sm_hands_combat_zone_default'in n(C,13,CG)['node_refs'],n(C,13,CG)['payload'])
 actors={a['actorName']:{'acquisition':a['acquisitionPlan'],'spawnSet':a.get('spawnSetParams'),'context':a.get('findActorInContextParams')}for a in M[S]['metadata']['actors']};ck('exact_EP1_scene_actor_bindings',actors['mr_hands']['spawnSet']['reference']['$value']=='#mr_hands_combat_zone'and actors['mr_hands_holo']['spawnSet']['reference']['$value']=='#mr_hands_holo',actors)
 # Independent full source cache: both literal and numeric fact spellings, and all reverse refs.
 facts=set(x[1]for x in routes)|set(x[5]for x in routes)|{'new_q110_rejected_failed_out','new_q110_rejected_perfect_out','ep1_installed'};aliases={v:k for k in facts for v in [k,fnv(k)]};hits=[];parents=[];mi=W/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json';models=read(mi)
 for d,row in models.items():
  m=json.loads(gzip.decompress(Path(row['normalized_model']).read_bytes()))
  for gp,gr in m['graphs'].items():
   for ni,nd in gr['nodes'].items():
    for kind in ['reads','writes']:
     for f in nd.get(kind,[]):
      if f.get('factName')in aliases:hits.append({'depot':d,'graph':gp,'node':ni,'kind':kind,'canonical_fact':aliases[f['factName']],'fact':f})
    if any(x in [C,OW]for x in nd.get('refs',[])):parents.append({'depot':d,'graph':gp,'node':ni,'targets':[x for x in nd['refs']if x in [C,OW]]})
 for _,request,_,_,_,ack,_ in routes:
  consumers=[h for h in hits if h['canonical_fact']==request and h['kind']=='reads'];writers=[h for h in hits if h['canonical_fact']==ack and h['kind']=='writes'and h['fact'].get('value',0)>0]
  ck('source_census_consumer_and_ACK_only_native '+request,bool(consumers)and bool(writers)and {h['depot']for h in consumers+writers}=={C},{'consumers':consumers,'outcome_writers':writers})
 ck('only_indexed_original_activator_parent',{h['depot']for h in parents if C in h['targets']}=={OW},parents)
 scripts=[];matches=[]
 for f in (Path(ep['candidate'])/'package').rglob('*'):
  if f.is_file()and f.suffix.lower()in ['.reds','.lua','.yaml','.xl']:
   text=f.read_text(encoding='utf-8-sig');scripts.append({'path':str(f),'sha256':sha(f)})
   if any(v in text for v in facts):matches.append(str(f))
 ck('no_pinned_packaged_script_substitute_or_EP1_override',not matches,{'text_files':len(scripts),'matching_paths':matches,'limit':'Literal bounded source scan; unknown external/dynamic scripts are not certified.'})
 raw=copy.deepcopy(D[C]);changed=0
 for x in walk(raw):
  if x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='new_q110_prebrief_rejected_or_end'and x.get('value')==1:x['value']=0;changed+=1
 mut=Resource(raw).normalize();ck('raw_missing_real_EP1_ACK_mutation_detected',changed==1 and not any(w.get('factName')=='new_q110_prebrief_rejected_or_end'and w.get('value',0)>0 for n0 in mut['graphs'][CG]['nodes'].values()for w in n0['writes']),'Real native controller JSON mutated, generic holo ACK does not satisfy specific q110 wait');write(O/'missing_EP1_ACK_mutation.questphase.json',raw)
 write(O/'tests.json',ts);write(O/'source_pins.json',pins);write(O/'census.json',{'model_inventory':str(mi),'model_inventory_sha256':sha(mi),'models':len(models),'facts':sorted(facts),'hits':hits,'reverse_ownership':parents,'package_text_sources':scripts});write(O/'routes.json',trace);write(O/'actor_context.json',actors)
 result={'id':'QR5-CVI02-MISSING-EP1-CALL-CONTROLLER','status':'SOURCE_CONFIRMED_CONTROLLER_OWNERSHIP_GAP_PENDING_INDEPENDENT_REVIEW','quest_id':'sts_pac_cvi_02','source_epoch':'QR5epoch00','checks':len(ts),'raw_mutations':1,'source_resources':len(pins),'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'route_evidence':str(O/'routes.json'),'census':str(O/'census.json'),'counterexample':'Fresh admitted CVI02 with ep1_installed1, PONR0 and zero new_q110 outcomes:205.True→208 request→221 wait. Native consumer17 and real output6 exist only in activator9, whose original EP1openworld28/EP1root5 owner was explicitly cut before q307_ep1_killed. No equivalent private consumer/outcome writer in the pinned 5136-model universe or literal package script scan. Equivalent failure/perfect debrief routes215/217 require same absent owner. Generic holo_mr_hands ACKs do not write q110 outcomes.','affected_contracts':['communications','ownership','progression','completion_rewards_cleanup','shared_dependencies'],'original_vs_current':'The body and native EP1 route are preserved, but post-Tower adapter restores the gig and generic Hands phone owner without restoring this separate EP1 request→scene→outcome controller. Native default existed under EP1openworld before the ending cleanup.','repair_status':'BLOCKED_PENDING_INDEPENDENT_CONTEXT_AND_SAVED_OWNER_REVIEW; no runtime change','smallest_candidate_to_investigate':'Future positive CVI02 entry event only may enroll copied exact activator phase9 as a sibling, preserving q115 guard, three native requests, exact scene input/output callbacks, RET/INT and real phone ACKs. Do not rehost entire activator/root or EP1openworld, reset requests/outcomes, fabricate ACK, or change ep1_installed. No implementation proposal approved.','context_blockers':['Activator empty root/phase PIPs do not prove scene support. Exact native scene actor plans include physical #mr_hands_combat_zone, holo #mr_hands_holo, Johnny context and marker #mr_sm_hands_combat_zone_default. Establish input-specific actor/studio/camera/workspot/default scope and current effective leases before adding owner.','Already-entered/progressed owners, prior q110 outcome history and external/native saved owners need explicit conservative treatment; a late adoption must not reset or replay calls.','Independent review must reproduce full source scan/owner cut and verify no other source-based supported consumer.'], 'limits':['Source-confirmed gap within pinned static source universe; no in-game failure observation or blanket absence of external dynamic mods.','Record ep1_installed1 and zero outcome facts as explicit supported counterexample values, not inferred from missing fact serialization.','Original G03 frozen generic-controller evidence remains valid for ep1_installed0; it is insufficient for the additional EP1 branch.','Native NID02→CVI02 journal cross-writer is separate; preserved addendum required.'],'runtime_changes':[]}
 write(H/'evidence.json',result);print(json.dumps({'checks':len(ts),'evidence_sha256':sha(H/'evidence.json')},ensure_ascii=True))
if __name__=='__main__':run()
