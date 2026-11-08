"""Reconcile frozen QR6 per-quest evidence, after every group is peer reviewed."""
from pathlib import Path
import sys,copy,collections,datetime,argparse
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;P=W/'prealpha/quest_restoration_qr5'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,csvwrite
STAGES={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'}
STATUS={'PASS','APPROVED_DEVIATION','CONDITIONAL','OPAQUE','UNKNOWN','FAIL','LIVE_ONLY'}
ap=argparse.ArgumentParser();ap.add_argument('--expected-new',type=int,required=True);a=ap.parse_args()
assert not(O/'checkpoint.json').exists(),'Preserve frozen final checkpoint'
p=read(O/'progress.json');q=read(O/'queue.json');prior=read(P/'queue.json');defs=read(O/'defects_and_repairs.json');e=read(q['source_epoch_manifest']);allow=read(O/'approved_changes_00.json')
pkg=q['independent_package_review'];assert sha(pkg['path'])==pkg['sha256']
pk=read(pkg['path']);assert pk['status'].startswith('PASS_INDEPENDENT_ZERO_DELTA')and pk['new_changed_resources']==len(allow['resources'])==0
assert pk['source_epoch_sha256']==sha(q['source_epoch_manifest'])and pk['archive_sha256']==e['archive_sha256']
pres=read(O/'verification/preservation_01/result.json');assert pres['status']=='PASS'and not pres['protected_hash_differences']and not pres['game_metadata_differences']and not pres['save_metadata_differences']
assert all(g['status']=='REVIEWED_WITH_LIMITS'for g in p['groups'].values()),'Investigations/independent review incomplete'
selected={r['id']for r in read(q['source_catalogue'])['decision_registry']if r['decision']=='INCLUDE'}
assert selected=={x['id']for x in q['quests']}and len(q['quests'])==len(selected)==q['derived_selected_count']
old=set(prior['deep_reviewed_ids']);new=[i for g in p['groups'].values()for i in g['ids']]
assert len(new)==len(set(new))==a.expected_new and not old&set(new)and old|set(new)==selected
idx=[];allpins={};overrides=read(O/'contract_supersessions.json')if(O/'contract_supersessions.json').exists()else{'items':[]}
for gid,g in p['groups'].items():
 assert sha(g['result'])==g['result_sha256']
 assert g['review']['reviewer']!=g['worker']and sha(g['review']['path'])==g['review']['sha256']
 for fp,h in g['investigation_input_pins'].items():assert sha(fp)==h,('Frozen evidence drift',fp)
 allpins.update(g['investigation_input_pins']);allpins[g['review']['path']]=g['review']['sha256']
 for ad in g.get('adjudications',[]):
  assert sha(ad['path'])==ad['sha256'];allpins[ad['path']]=ad['sha256']
 for f in g['findings']:
  assert sha(f['contracts'])==f['sha256'];orig=read(f['contracts']);x=next(x for x in q['quests']if x['id']==f['id']);assert set(x['contracts'])==STAGES
  for stage,v in x['contracts'].items():
   assert v['status']in STATUS and v.get('proven')and v.get('evidence'),(x['id'],stage)
   base={k:v[k]for k in orig['contracts'][stage]}
   if base!=orig['contracts'][stage]:
    assert any(z['quest_id']==x['id']and z['stage']==stage for z in overrides['items']),'Unrecorded contract supersession'
   assert v['original_findings_source_sha256']==f['sha256']and v['independent_review_sha256']==g['review']['sha256']
  x['fully_static_verified']=all(v['status']in ['PASS','APPROVED_DEVIATION']for v in x['contracts'].values())
 idx.append({'group':gid,'quest_ids':g['ids'],'worker':g['worker'],'results':g['result'],'results_sha256':g['result_sha256'],'findings':g['findings'],'review':g['review'],'adjudications':g.get('adjudications',[]),'reported_check_events':g.get('reported_check_events'),'reported_mutation_events':g.get('reported_mutation_events'),'limits':'Assertion events may reuse shared checks. Not unique semantic coverage or gameplay observations.'})
for x in q['quests']:
 x['remaining']=[{'contract':k,'status':v['status'],'item':s}for k,v in x['contracts'].items()for s in v.get('remaining',[])]
# Older reviewed rows remain byte-identical as contract objects; source-epoch
# equivalence is explicit, rather than fabricating a fresh per-quest re-review.
for x in q['quests']:
 if x['id']in old:assert x['contracts']==next(y for y in prior['quests']if y['id']==x['id'])['contracts'],'Unexpected inherited contract edit'
q.update(deep_reviewed_ids=[x['id']for x in q['quests']],deep_reviewed_count=len(selected),new_investigated_count=len(new),pending_review_ids=[],static_verified_count=sum(bool(x.get('fully_static_verified'))for x in q['quests']),checkpoint_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_unique_defects=defs['new_confirmed_unique_defects'],new_repaired_unique_defects=defs['new_repaired_unique_defects'],new_blocked_unique_defects=defs['new_blocked_unique_defects'],new_affected_quest_count=defs['new_affected_quest_count'],gameplay_repairs=defs['cumulative_staged_repairs'],changed_resources=[r['depot']for r in allow['resources']],cumulative_changed_resources_vs_PH3=defs['cumulative_changed_resources_vs_PH3'],source_confirmed_defects_pending_review=0,source_authority_conflicts=defs.get('source_authority_conflicts',[]))
q['completed_count']=q['static_verified_count'];rows=[{'quest_id':x['id'],'title':x['title'],'stage':stage,**copy.deepcopy(v),'review_state':x['status']}for x in q['quests']for stage,v in x['contracts'].items()]
assert len(rows)==len(selected)*len(STAGES)and len({(x['quest_id'],x['stage'])for x in rows})==len(rows)
write(O/'queue.json',q);write(O/'quest_status_matrix.json',q['quests']);write(O/'contract_status_matrix.json',rows)
for name,data in [('quest_status_matrix.csv',q['quests']),('contract_status_matrix.csv',rows)]:
 keys=list(dict.fromkeys(k for x in data for k in x));csvwrite(O/name,[{k:x.get(k)for k in keys}for x in data])
write(O/'group_evidence_index.json',{'scope':'33 new ten-contract investigations and independent actual-resource reviews; retained128 exact prior findings.','groups':idx,'input_pins':allpins,'contract_supersessions':overrides})
diffs=copy.deepcopy(read(P/'intentional_differences.json')['differences'])
for x in q['quests']:
 if x['id']not in new:continue
 for stage,v in x['contracts'].items():
  for text in v.get('approved_differences',[]):diffs.append({'quest_id':x['id'],'contract':stage,'difference':text,'evidence':v['evidence'],'findings_source_sha256':v['findings_source_sha256'],'effective_epoch':e['epoch_key']})
write(O/'intentional_differences.json',{'source_epoch':e['epoch_key'],'differences':diffs,'inherited':str(P/'intentional_differences.json'),'inherited_sha256':sha(P/'intentional_differences.json'),'approval_boundary':'Existing source-approved Tower adaptations and separately allowlisted reviewed repairs only. Source conflicts, conditional support and report prose do not approve gameplay changes.'})
count=lambda ids:dict(collections.Counter(v['status']for x in q['quests']if x['id']in ids for v in x['contracts'].values()))
cov={'status':'COMPLETE_DEEP_SOURCE_AND_REVIEW_COVERAGE_WITH_EXPLICIT_STATIC_LIMITS','selected':len(selected),'prior_deep':len(old),'new_deep':len(new),'deep_total':len(selected),'remaining':0,'contracts':len(rows),'new_contract_status_counts':count(set(new)),'all_contract_status_counts':count(selected),'fully_static_verified':q['static_verified_count'],'fully_resolved_static_contracts':sum(r['status']in ['PASS','APPROVED_DEVIATION']for r in rows),'new_confirmed_defects':defs['new_confirmed_unique_defects'],'new_repaired_defects':defs['new_repaired_unique_defects'],'new_blocked_defects':defs['new_blocked_unique_defects'],'existing_blocked_defects':defs['existing_blocked_unique_defects'],'cumulative_confirmed_defects':defs['cumulative_confirmed_unique_defects'],'cumulative_staged_repairs':defs['cumulative_staged_repairs'],'source_authority_conflict_count':len(defs.get('source_authority_conflicts',[])),'new_runtime_resource_changes':len(allow['resources']),'groups_independently_reviewed':len(idx),'batch_counts':{b:{'total':sum(x['batch']==b for x in q['quests']),'deep':sum(x['batch']==b and x['id']in q['deep_reviewed_ids']for x in q['quests'])}for b in sorted({x['batch']for x in q['quests']})},'source_epoch':e['epoch_key'],'source_epoch_manifest':q['source_epoch_manifest'],'source_epoch_sha256':sha(q['source_epoch_manifest']),'candidate':e['candidate'],'archive_sha256':e['archive_sha256'],'queue_sha256':sha(O/'queue.json'),'limits':['Deep coverage means ten source-specific dispositions plus independent resource review, not tenPASSes or gameplay success.','Inherited source-specific failures, unknowns, conditional and opaque cases remain explicit.','No game/save/deploy/release writes; current installation isPH3.']}
write(O/'coverage.json',cov);write(O/'checkpoint.json',{**cov,'state':'ALL161_DEEP_INVESTIGATIONS_REVIEWED_FINAL_GATES_PENDING','installed':'PH3 unchanged','next_all_unreviewed':[],'remaining_final_gates':['Final independent staged package/payload comparison','Final preservation snapshot','Concise report/handoff and independent completeness review']})
p['status']='ALL33_INVESTIGATIONS_REVIEWED_FINAL_GATES_PENDING';write(O/'progress.json',p)
print({k:cov[k]for k in ['selected','new_deep','deep_total','remaining','fully_static_verified','new_contract_status_counts']})
