"""Extend primary repair ledger after the independent fifth-repair package gate."""
from pathlib import Path
import sys,argparse,json,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_03'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
ap=argparse.ArgumentParser();ap.add_argument('--package-review',required=True);a=ap.parse_args()
out=O/'adjudications/moving_heat_01.json';assert not out.exists()
rp=Path(a.package_review).resolve();r=read(rp);m=read(C/'package_manifest.json');assert r['status'].startswith(('PASS','APPROVE'))and m['archive_sha256']in json.dumps(r)
resource=read(C/'source_promotion.json')['resource'];q=read(O/'queue.json');rows=read(O/'contract_status_matrix.json');item=next(x for x in q['quests']if x['id']=='q304_car_retrieval');changes=[]
common='Native whole car-retrieval root owns dedicated #q304_pr_car_retrieval; current future9.True now enters private1200 holding that exact full native entry around an exact clone of external resume10, then Terminating output1→existing11. All49 retained accepted-body handlers, source/scene/reward payloads and original resources stay unchanged.'
for stage in ['ownership','presentation','shared_dependencies']:
 v=item['contracts'][stage];assert v['status']=='FAIL';v['pre_repair_status']='FAIL';v['pre_repair_proven']=copy.deepcopy(v['proven']);v['pre_repair_remaining']=copy.deepcopy(v.get('remaining',[]))
 status='OPAQUE'if stage=='presentation'else'CONDITIONAL'
 specific={'ownership':'Already executing root10 and descendants retain their old payload, external binding, empty nested graph and Out1→11. Claimed/pending owners before future9.True may take the new wrapper if all late rechecks pass; this is not a blanket AlreadyIssuedUnchanged claim.','presentation':'The exact dedicated native prefab entry is acquired around the accepted-body lifetime; original actor, marker, scene and vehicle bindings are retained. Decoded placement/rendering/streaming and saved-entity behavior remain opaque.','shared_dependencies':'Only S24FreshIssued0 is appended to existing ANDguards2/3/9, preserving native q305_done OR q306_done and both outside-trigger predicates. This refuses a known competing fresh controller; it neither supplies missing trigger refs nor restores the q304 main-story/default parent.'}[stage]
 v.update(status=status,proven=[common,specific],remaining=['OPAQUE/LIVE_ONLY: Outside-trigger resolution before lease acquisition, actual world placement/reference-count/streaming, callbacks/reloads and save transitions remain unproved.','SAVED_SCOPE: No polling or retrospective PIP injection into already executing oldroot10 descendants; pending before future9.True follows current guards and edge.'],repair='QR5-G18-Q304-S22-MISSING-CAR-PREFAB',effective_source_epoch='QR5:08',verified_candidate_resource_sha256=resource['after'])
 v['approved_differences']=v.get('approved_differences',[])+[resource['intent']];v['evidence']+=resource['evidence']+resource['tests']+[str(rp)];changes.append({'quest_id':item['id'],'stage':stage,'before':'FAIL','after':status})
item['defects']=['QR5-G18-Q304-S22-MISSING-CAR-PREFAB'];item['repairs']=[resource]
for row in rows:
 if row['quest_id']==item['id']:row.update(copy.deepcopy(item['contracts'][row['stage']]))
did='QR5-G18-Q304-S22-MISSING-CAR-PREFAB';d=read(O/'defects_and_repairs.json');assert not any(x['id']==did for x in d['defects'])
write(O/'defects_and_repairs_primary_01.json',d)
entry={'id':did,'affected':['q304_car_retrieval'],'status':'REPAIRED_FUTURE_9_EDGE_BODY_LEASE_SERIALIZED_AND_PACKAGE_STATIC_VERIFIED_LIVE_PENDING','resources':[resource],'evidence':resource['evidence'],'tests':resource['tests'],'independent_package_review':str(rp),'saved_scope':resource['intent'],'limits':['Original already-executing root10 descendants unchanged; claimed/pending before9 may take wrapper.','Pre-lease outside-trigger availability and opaque placement/engine semantics are not repaired or certified.']}
d['defects'].append(entry);d.update(new_confirmed_unique_defects=6,new_repaired_unique_defects=5,new_blocked_unique_defects=1,new_affected_quest_count=6,new_changed_resources=5,cumulative_confirmed_unique_defects=9,cumulative_staged_repairs=8,cumulative_changed_resources_vs_PH3=9)
write(O/'defects_and_repairs.json',d)
q.update(new_unique_defects=6,new_affected_quest_count=6,new_repaired_unique_defects=5,new_blocked_unique_defects=1,gameplay_repairs=8,changed_resources=5,cumulative_changed_resources_vs_PH3=9,source_epoch=8,source_epoch_manifest=str(O/'source_epoch_08.json'),working_candidate=str(C),package_verification='PASS_INDEPENDENT_FULL_CANDIDATE03_PACKAGE_DIFF',independent_package_review={'path':str(rp),'sha256':sha(rp)})
write(O/'queue.json',q);write(O/'contract_status_matrix.json',rows)
p=read(O/'progress.json');p['new_defects']=[x for x in p['new_defects']if x['id']!=did]+[entry];p['final_package_review']=q['independent_package_review'];p['repair_epochs']+= [str(O/f'source_epoch_{i:02d}.json')for i in [6,7,8]];write(O/'progress.json',p)
write(O/'repair_queue.json',{'items':p['new_defects'],'source_epoch':8,'candidate':str(C),'installed':'PH3_UNCHANGED','remaining_blocked':1})
write(out,{'status':'MOVING_HEAT_FIFTH_PACKAGED_REPAIR_ADJUDICATED','changes':changes,'package_review':str(rp),'package_review_sha256':sha(rp),'resource':resource,'confirmed_new_unique':6,'packaged_new_repairs':5,'blocked_new':1,'Voodoo':'Three exact static unknowns; no confirmed duplicate grant or speculative repair.'})
print({'new_confirmed':6,'new_repaired':5,'new_blocked':1,'cumulative_staged_repairs':8})
