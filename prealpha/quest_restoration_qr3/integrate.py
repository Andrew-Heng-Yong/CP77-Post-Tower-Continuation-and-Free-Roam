"""Integrate reviewed QR3 findings and explicit repair adjudications centrally."""
from pathlib import Path
import sys,copy,collections,datetime
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,csvwrite
OLD=W/'prealpha/quest_restoration_qr2';assert not (O/'queue.json').exists(),'Preserve final queue'
q=read(OLD/'queue.json');rows=read(OLD/'contract_status_matrix.json');assign=read(O/'assignments.json')['assignments']
reviews={'agent_a':'agent_d/reviews/racing.json','agent_b':'agent_e/reviews/vehicles.json','agent_c':'agent_b/reviews/brendan_quarantine.json','agent_d':'agent_f/reviews/communications.json','agent_e':'agent_b/reviews/progression.json','agent_f':'agent_e/reviews/boxing.json'}
approved=read(O/'approved_changes_02.json')['resources'];repair_by={r['depot']:r for r in approved}
defs=[{'id':'QR3-MQ037-EXCLUDED-FRESH','resource':r['depot'],'affected':['mq037_brendan','mq037_brendan_hooligan001'],'status':'CONTAINED_WITH_CONTINUATION_BLOCKER','repair':r,'blocker':'Selected later jobs still require a safe exact earned-Dumpster stage/owner adapter; current all-Inactive full-chain seam cannot provide it. No fabricated history or restart is permitted.'} if 'mq037' in r['depot'] else {'id':'QR3-MQ030-VENDOR-LEASE','resource':r['depot'],'affected':['mq030_melisa'],'status':'REPAIRED_STATIC_RUNTIME_TRANSITIONS_PENDING','repair':r,'blocker':'Saved preexisting overlaps, scene interruption and actual prefab teardown/reload require runtime fixtures; authored retirement ordering is verified.'} for r in approved]
findings={};status_counts=collections.Counter();diffs=read(OLD/'intentional_differences.json')['differences']
for agent,ids in assign.items():
 review=O/'agents'/reviews[agent];assert review.is_file(),str(review)
 for i in ids:
  f=O/'agents'/agent/'quests'/i/'contracts.json';d=read(f);cs=copy.deepcopy(d['contracts']);assert len(cs)==10
  for stage,v in cs.items():
   if v['status']=='FAIL':
    assert i in ['mq037_brendan','mq037_brendan_hooligan001','mq030_melisa'],(i,stage)
    v['pre_repair_status']='FAIL';v['baseline_proven']=v['proven'];v['pre_repair_remaining']=v.get('remaining',[])
    v['status']='CONDITIONAL'
    if i.startswith('mq037'):
     r=repair_by['towercontinued\\sidejobs_s23\\base_b\\mq037.questphase']
     v['proven']=['Serialized new-owner path changes only1004.True from1005.In to existing1008.In (owned Refused1). No new input reaches Issued1005 or nativefullIn1 node34; excluded Dumpster is not newly started by this adapter.','All13node payloads/sockets/nativebody bindings and saved1005/1006/34 descendant reachability are preserved. This is containment, not a completed later-job restoration.']
     v['remaining']=['STATIC_IMPLEMENTATION_BLOCKER: Exact earned-Dumpster native stage, retired/adoptable owner, choices, reward and identity review is required for a supported later Brendan adapter. The current all18-Inactive seam refuses new ownership.','LIVE_ONLY: Already-passed preclaim saved execution and actual node/owner restore scheduling are not reversed or certified.']
     v['evidence']+=['candidate_01/repair/verification_01/tests.json','agents/agent_d/reviews/brendan_serialized.json']
    else:
     r=repair_by['towercontinued\\sidejobs_s23\\base_b\\mq030.questphase']
     v['proven']=['Actual serialized helper pause3 and pending wait1021 retain native condition OR real Finished1. Native helper3.Out→5.Inactive→1.Terminating precedes outer1020.Out1 and1022.True lease release. Pending wait uses1023 to release without reentry after completion.','Direct1007.Out→1012 release is removed. Every old node/field/socket/nativebody binding remains; only new local decision IDs1022/1023 and two owned-finished read conditions are added.']
     v['remaining']=[x for x in v.get('remaining',[]) if not x.startswith('IMPLEMENTATION:')]+['LIVE_ONLY: Existing saved overlap, actual Terminating prefab teardown and mid-recheck extra owned epoch remain runtime transition boundaries.']
     v['evidence']+=['candidate_01/repair_mq030/verification_01/tests.json','agents/agent_d/reviews/mq030_serialized.json']
    v['approved_differences']=v.get('approved_differences',[])+[r['intent']]
    v['verified_candidate_resource_sha256']=r['after'];v['repair_evidence']=r
   assert v['status'] in ['PASS','APPROVED_DEVIATION','CONDITIONAL','OPAQUE','UNKNOWN','FAIL','LIVE_ONLY']
   assert v['proven'] and v['evidence'],(i,stage)
   v['findings_source']=str(f);v['findings_source_sha256']=sha(f);v['independent_review']=str(review);v['independent_review_sha256']=sha(review)
   status_counts[v['status']]+=1
   for text in v.get('approved_differences',[]):diffs.append({'quest_id':i,'contract':stage,'difference':text,'source':str(f),'source_sha256':sha(f),'new_in_qr3':bool(v.get('repair_evidence')),'evidence':v['evidence']})
  findings[i]={'contracts':cs,'source':f,'review':review}
new_ids=set(findings);expected={x['id'] for x in q['quests'] if x['batch']=='Q01'}-set(q['deep_reviewed_ids']);assert new_ids==expected and len(new_ids)==13
for x in q['quests']:
 if x['id'] not in findings:continue
 f=findings[x['id']];x['contracts']=f['contracts'];x['deep_review']=str(f['source']);x['deep_review_sha256']=sha(f['source']);x['review']=str(f['review'])
 x['status']='DEEP_REVIEWED_WITH_STATIC_LIMITS';x['fully_static_verified']=all(v['status'] in ['PASS','APPROVED_DEVIATION'] for v in x['contracts'].values())
 x['defects']=[d['id'] for d in defs if x['id'] in d['affected']];x['repairs']=[d['repair'] for d in defs if x['id'] in d['affected']]
 x['remaining']=[{'contract':k,'status':v['status'],'item':t} for k,v in x['contracts'].items() for t in v.get('remaining',[])]
for row in rows:
 if row['quest_id'] not in findings:continue
 v=findings[row['quest_id']]['contracts'][row['stage']];row['prior_status']=row['status'];row['status']=v['status'];row['proven']=v['proven'];row['approved_differences']=v.get('approved_differences',[]);row['remaining']=v.get('remaining',[]);row['evidence']=v['evidence'];row['findings_source']=v['findings_source'];row['review']=v['independent_review'];row['pre_repair_status']=v.get('pre_repair_status');row['verified_candidate_resource_sha256']=v.get('verified_candidate_resource_sha256')
q['predecessor_queue']=str(OLD/'queue.json');q['predecessor_queue_sha256']=sha(OLD/'queue.json');q['deep_reviewed_ids']=[x['id'] for x in q['quests'] if x['id'] in set(q['deep_reviewed_ids'])|new_ids];q['deep_reviewed_count']=len(q['deep_reviewed_ids']);q['static_verified_count']=sum(bool(x.get('fully_static_verified')) for x in q['quests']);q['completed_count']=q['static_verified_count'];q['gameplay_repairs']=len(defs);q['changed_resources']=len(approved);q['working_candidate']=str(O/'candidate_01');q['installed_baseline']='PH3 unchanged';q['checkpoint_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
write(O/'queue.json',q);write(O/'quest_status_matrix.json',q['quests']);write(O/'contract_status_matrix.json',rows)
for filename,data in [('quest_status_matrix.csv',q['quests']),('contract_status_matrix.csv',rows)]:
 fields=list(dict.fromkeys(k for r in data for k in r));csvwrite(O/filename,[{k:r.get(k) for k in fields} for r in data])
write(O/'defects_and_repairs.json',{'confirmed_unique_defects':len(defs),'changed_resources':len(approved),'defects':defs,'scope':'Sourceconfirmed structural fixes/containment; not gameplay or save-transition success'})
write(O/'intentional_differences.json',{'scope':'QR2preserved plus13newquest investigations and2sourceconfirmedrepairs','differences':diffs})
pending=[x for x in q['quests'] if x['id'] not in q['deep_reviewed_ids']];q01=[x for x in q['quests'] if x['batch']=='Q01'];nextbatch=pending[0]['batch'];q01counts=collections.Counter(v['status'] for x in q01 for v in x['contracts'].values())
write(O/'checkpoint.json',{'state':'Q01_ALL16_DEEP_REVIEWED_STATIC_LIMITS_REMAIN','selected_quests':len(q['quests']),'newly_deep_reviewed':len(new_ids),'total_deep_reviewed':q['deep_reviewed_count'],'Q01_deep_reviewed':sum(x['id'] in q['deep_reviewed_ids'] for x in q01),'Q01_total':len(q01),'new_contract_status_counts':dict(status_counts),'Q01_contract_status_counts':dict(q01counts),'fully_static_verified':q['static_verified_count'],'confirmed_unique_defects':len(defs),'implemented_repairs_or_containment':len(approved),'working_candidate':str(O/'candidate_01'),'installed':'PH3 unchanged','queue':str(O/'queue.json'),'queue_sha256':sha(O/'queue.json'),'remaining_not_deep_reviewed':len(pending),'next_batch':nextbatch,'next_batch_quests':[{'id':x['id'],'title':x['title']} for x in pending if x['batch']==nextbatch],'restrictions':'No game/deployment/save/fact/release/Git publication writes'})
print({'Q01':str(len(q01))+'/'+str(len(q01)),'new_contracts':dict(status_counts),'Q01_contracts':dict(q01counts),'deep_total':q['deep_reviewed_count'],'remaining':len(pending),'repairs':len(defs)})
