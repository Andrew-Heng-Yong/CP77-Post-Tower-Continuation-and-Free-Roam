"""Independent NID02 raw-source/proposal review. Never imports a peer verifier."""
from pathlib import Path
import sys, copy, json, gzip, collections
W=Path(__file__).resolve().parents[5]; H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,fnv
from model import Resource

def path(g,a,b):
 q=collections.deque([[str(a)]]);seen={str(a)}
 while q:
  p=q.popleft()
  if p[-1]==str(b):return p
  for x,s,y,t in g['edges']:
   if x==p[-1] and s!='CutSource' and t!='CutDestination' and y not in seen:seen.add(y);q.append(p+[y])
 return None

def run():
 O=H/'verification_01';assert not O.exists();ts=[];pins=[]
 def ck(k,v,e):
  ts.append({'name':k,'status':'PASS' if v else 'FAIL','evidence':e});assert v,k
 D=W/'prealpha/quest_restoration_qr5/groups/G11/nid02_failure';ep=D/'verification_02/evidence.json';pp=D/'proposal_01/proposal.json'
 ck('exact_frozen_defect',sha(ep)=='8110A5D9865F62F64CBF6CB7672BDA9026D1509240A077EEDB528453BDA1207E',str(ep))
 ck('exact_frozen_proposal',sha(pp)=='FEA112924B05C2116620F3952843649693B8F6B8646692443DADAF6787D6B214',str(pp))
 P=read(pp);rows=read(D/'verification_02/source_pins.json');ms=[];docs=[]
 for r in rows:
  ck('raw_pin '+r['depot'],sha(r['raw'])==r['raw_sha256'],r['raw']);ck('export_pin '+r['depot'],sha(r['json'])==r['json_sha256'],r['json'])
  d=read(r['json']);m=Resource(d).normalize();ck('decode_integrity '+r['depot'],not m['errors'],m['errors']);docs.append(d);ms.append(m);pins.append(r)
 def g(ix,gp='root'):return ms[ix]['graphs'][gp]
 def n(ix,i,gp='root'):return g(ix,gp)['nodes'][str(i)]
 def e(ix,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(ix,gp)['edges']
 def wr(ix,i,f,v,gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(ix,i,gp)['writes'])
 G='root/23'; bg=g(0,G);ow=g(3,'root/4');cg=g(4)
 ck('actual_health_future_pause',n(0,2,G)['type']=='questPauseConditionNodeDefinition' and n(0,2,G)['payload']['condition']['type']['percent']==0 and n(0,2,G)['payload']['condition']['type']['comparisonType']=='LessOrEqual',n(0,2,G)['payload'])
 ck('actual_water_future_pause_AND_mounted',n(0,49,G)['type']=='questPauseConditionNodeDefinition' and n(0,49,G)['payload']['condition']['operation']=='AND' and {x['$type']for x in n(0,49,G)['payload']['condition']['conditions']}=={'questVehicleCondition','questCharacterCondition'},n(0,49,G)['payload'])
 ck('actual_join_classes',n(0,41,G)['type']=='questLogicalXorNodeDefinition' and n(0,9,G)['type']=='questLogicalAndNodeDefinition' and n(0,48,G)['type']=='questLogicalXorNodeDefinition',{i:n(0,i,G)['type']for i in [9,41,48]})
 for a,s,b,t in [(0,'Out',12,'In'),(12,'False',13,'In'),(13,'Out',33,'In'),(33,'Out',16,'In'),(16,'False',2,'In'),(16,'False',50,'In'),(50,'Out',49,'In'),(2,'Out',41,'In1'),(49,'Out',41,'In2'),(41,'Out1',34,'In')]:ck('native_monitor_edge '+str((a,s,b,t)),e(0,a,s,b,t,G),(a,s,b,t))
 ck('prearmed_CYB_not_started_provenance',wr(0,13,'CYB-651268',1,G) and n(0,33,G)['reads'][0]['factName']=='nid_02_start','12 snapshot prefix →13 CYB increment→33 future native start wait; CYB1 alone may be legitimate fresh history')
 ck('native_unfinished_snapshot_preserved',n(0,16,G)['type']=='questConditionNodeDefinition' and n(0,16,G)['reads'][0]=={'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'nid_02_finished','value':0},n(0,16,G)['payload'])
 ck('native_fail_writer_exact',wr(0,34,'sts_wat_nid_02_fail',1,G) and n(0,34,G)['writes'][0]['setExactValue']==0,n(0,34,G)['payload'])
 ck('one_shot_health_not_monitor',n(3,267,'root/4')['type']=='questConditionNodeDefinition' and not any(x.get('factName')=='sts_wat_nid_02_fail' for x in n(3,267,'root/4')['writes']),n(3,267,'root/4')['payload'])
 ck('native_main_future_failure_consumer',n(3,280,'root/4')['type']=='questPauseConditionNodeDefinition' and n(3,280,'root/4')['reads'][0]['factName']=='sts_wat_nid_02_fail' and e(3,280,'Out',258,'In','root/4'),n(3,280,'root/4'))
 ck('native_main_failure_wait_reachable',bool(path(ow,ow['entries']['In1'],'280')),path(ow,ow['entries']['In1'],'280'))
 ck('monitor_failure_outcomes',all(path(bg,'41',i)for i in ['34','4','3','8','9','24','44','18','20','28','29','31','35','1']),{i:path(bg,'41',i)for i in ['34','4','3','8','9','24','44','18','20','28','29','31','35','1']})
 ck('personal_link_AND_barrier',e(0,6,'Out',9,'In2',G)and e(0,7,'False',9,'In1',G)and e(0,8,'Out',9,'In1',G),{i:n(0,i,G)['payload']for i in [6,7,8,9]})
 ck('failure_SMS_and_native_retries_preserved',wr(0,26,'holo_reggie_calls_v_start_activate',1,G)and wr(0,27,'holo_reggie_calls_v_end_activate',1,G)and 'sts_wat_nid_02_debrief_fail'in str(n(0,44,G)['journal_paths']),{i:n(0,i,G)['payload']for i in [24,26,27,43,44,45,46,47,48]})
 ck('no_monitor_reward_grant',not any('questRewardManagerNode' in x['type'] for x in bg['nodes'].values()),'Native token release, finished increment and achievement are preserved; no invented monetary reward')
 ck('native_monitor_empty_root_and_instance_leases',not ms[0]['metadata']['phasePrefabs']and not n(0,23)['prefabs']and all(not x['prefabs']for x in bg['nodes'].values()),{'root':ms[0]['metadata']['phasePrefabs'],'phase23':n(0,23)['payload']})
 ck('main_exact_world_lease',ms[2]['metadata']['phasePrefabs'][0]['prefabNodeRef']['$value']=='#loc_sts_wat_nid_02_streetstory' and rows[2]['depot']in n(4,7)['refs'],{'main_root':ms[2]['metadata']['phasePrefabs'],'current7':n(4,7)['payload']})
 ck('main_completion_does_not_terminate_private_parent',not any(x['type']=='questOutputNodeDefinition' and x['payload'].get('type')=='Terminating' for x in cg['nodes'].values()) and e(4,7,'Out1',65005,'In'),cg['edges'])
 ck('genuine_original_retirement',e(5,106,'Out',109,'In')and e(5,109,'Out',107,'In')and n(5,107)['payload']['type']=='Terminating'and rows[6]['depot']in n(5,4,'root/82')['refs']and rows[7]['depot']in n(6,11)['refs'],'Original cyberpunk root106 Succeeded→109 main killed→107 Terminating; root/82/4 owns bugfixing→11 openworld')
 ck('original_district_monitor_ancestry',rows[1]['depot']in n(7,35,'root/1')['refs']and rows[0]['depot']in n(1,17)['refs'] and bool(path(g(0),'0','23')),'openworld root/1/35 →NIDparent17→bugfixroot0 deletion chain25→23')
 ck('existing_private_fresh_event_exact',e(4,65002,'Out',65003,'In')and wr(4,65003,'PTFRU9_sts_wat_nid_02_ParentEntered',1)and e(4,65003,'Out',2,'In1'),n(4,65002)['payload'])
 ck('proposal_unused_local_IDs',set(map(str,P['new_parent_local_ids'])).isdisjoint(cg['nodes']),P['new_parent_local_ids'])
 expected=[['65003','Out','1300','In'],['1300','True','1301','In'],['1301','Out','1302','In1'],['1301','Out','2','In1'],['1300','False','2','In1']]
 ck('ordered_guard_and_refusal_preserve_main',P['parent_added_edges']==expected and P['parent_removed_edges']==[['65003','Out','2','In1']],P['parent_added_edges'])
 ck('proposal_copy_scope_exact',P['native_template']['containing_node']==23 and P['native_template']['all_recursive_graphs']==[G]and P['native_template']['cloned_only_edge_replacement']=={'remove':['0','Out','12','In'],'add':['0','Out','33','In']},P['native_template'])
 req={'PTFRU9_sts_wat_nid_02_ParentEntered':1,'PTFRU9_sts_wat_nid_02_Started':0,'nid_02_start':0,'nid_02_finished':0,'sts_wat_nid_02_fail':0,'PTFRU9_sts_wat_nid_02_FailureMonitorEntered':0}
 ck('future_event_private_receipt_no_CYB_adoption',all(P['initial_guard_facts'].get(k)==v for k,v in req.items())and 'CYB-651268'not in P['initial_guard_facts'],P['initial_guard_facts'])
 # Independent cache-universe writer census, including normalized numeric FNV spelling.
 mi=W/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json';hits=[];positive=[];aliases={'sts_wat_nid_02_fail',fnv('sts_wat_nid_02_fail')}
 for depot,row in read(mi).items():
  m=json.loads(gzip.decompress(Path(row['normalized_model']).read_bytes()))
  for gp,gr in m['graphs'].items():
   for ni,nd in gr['nodes'].items():
    for w in nd.get('writes',[]):
     if w.get('factName')in aliases:
      v={'depot':depot,'graph':gp,'node':ni,'write':w};hits.append(v)
      if w.get('value',0)>0:positive.append(v)
 ck('independent_full_cache_unique_fail_writer',len(positive)==1 and positive[0]['depot']==rows[0]['depot']and positive[0]['graph']==G and positive[0]['node']=='34',positive)
 ck('effective_private_no_fail_writer',not any(w.get('factName')in aliases and w.get('value',0)>0 for gr in ms[4]['graphs'].values()for nd in gr['nodes'].values()for w in nd['writes']),rows[4])
 # Raw mutations are applied to source JSON, then independently normalized.
 muts=[]
 for name,ni,typ in [('xor_is_not_AND',41,'questLogicalAndNodeDefinition'),('future_health_is_not_snapshot',2,'questConditionNodeDefinition'),('future_water_is_not_snapshot',49,'questConditionNodeDefinition')]:
  d=copy.deepcopy(docs[0]);matches=[x for x in walk(d)if x.get('id')==ni and x.get('$type')==bg['nodes'][str(ni)]['type']];assert len(matches)==1;matches[0]['$type']=typ;changed=Resource(d).normalize()['graphs'][G]
  ok=changed['nodes'][str(ni)]['type']!=bg['nodes'][str(ni)]['type'];ck('raw_mutation_detected '+name,ok,{'node':ni,'native':bg['nodes'][str(ni)]['type'],'mutated':typ});muts.append({'name':name,'raw':rows[0]['json'],'detected':ok})
 write(O/'tests.json',ts);write(O/'source_pins.json',pins);write(O/'global_writer_scan.json',{'model_inventory':str(mi),'sha256':sha(mi),'models':len(read(mi)),'fact_aliases':sorted(aliases),'all_writers':hits});write(O/'mutations.json',muts)
 review={'status':'APPROVED_SOURCE_CONFIRMED_DEFECT_AND_EXACT_FUTURE_PROPOSAL','defect':str(ep),'defect_sha256':sha(ep),'proposal':str(pp),'proposal_sha256':sha(pp),'checks':len(ts),'raw_mutations':len(muts),'source_resources':len(pins),'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'source_scope':'Independent actual raw/export hashes and normalized graphs; no peer verifier import. No runtime implementation or package certification.','findings':['Native future health2 or water49 goes through actual XOR41 to unique fail34; current main267 is one-shot and280 waits missing writer. Genuine original global owner is retired by Tower.','Prefix13 CYB1 predates start33; no reset or receipt-based admission. Future parent event65003 is ordered before old child2; helper refusal preserves main.','No new prefab lease is needed or authorized: original monitor root23 and recursive nodes have empty PIPs; native main unchanged #loc_sts_wat_nid_02_streetstory supplies van/computer/scene context.','Keep full native monitor23 including exact XOR/AND types, failure journal/link/computer/phone/SMS/token/achievement and finished callback; change only prefix edge0→12 to0→33 in isolated fresh enrollment.'],'limits':['Exact approved declarative proposal only; root must independently validate serialized successor, guards, rejection routing, old-node preservation and final packaged bytes.','Engine scheduling, dynamic fact writers, world placement and saved native lease state are not proven. No already-entered/progressed owner adoption.','Original monitor tests unfinished16 once before arming future health/water; later normal-completion cancellation is not separately authored here. Preserve vanilla behavior rather than speculate a new stop/reset.','Native foreign CVI02 objective mutation remains a separate original cross-quest state risk; not changed by this repair.'],'runtime_changes':[]}
 write(H/'review.json',review);print(json.dumps({'checks':len(ts),'mutations':len(muts),'review_sha256':sha(H/'review.json')},ensure_ascii=True))
if __name__=='__main__':run()
