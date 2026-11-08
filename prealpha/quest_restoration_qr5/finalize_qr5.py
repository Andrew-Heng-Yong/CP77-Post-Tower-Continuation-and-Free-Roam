"""Freeze reconciled queue/matrices and coverage after all claimed reviews finish."""
from pathlib import Path
import sys,argparse,copy,collections,datetime
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,csvwrite
STAGES={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'}
STATUSES={'PASS','APPROVED_DEVIATION','FAIL','CONDITIONAL','OPAQUE','UNKNOWN','LIVE_ONLY'}
ap=argparse.ArgumentParser();ap.add_argument('--expected-new',type=int,required=True);args=ap.parse_args()
assert not (O/'checkpoint.json').exists(),'Preserve final checkpoint; use explicit successor for later amendments'
p=read(O/'progress.json');q=read(O/'queue.json');prior=read(W/'prealpha/quest_restoration_qr4/queue.json');ep=Path(q['source_epoch_manifest']);e=read(ep);defs=read(O/'defects_and_repairs.json');epoch=e['epoch']
manifest=read(Path(q['working_candidate'])/'package_manifest.json')
assert q['package_verification'].startswith('PASS_INDEPENDENT_FULL_CANDIDATE03'), 'Final candidate independent package gate incomplete'
assert defs['new_repaired_unique_defects']==len(manifest['changed_resources'])==len(e['changes'])
assert defs['new_confirmed_unique_defects']==defs['new_repaired_unique_defects']+defs['new_blocked_unique_defects']
assert manifest['archive_sha256']==e['archive_sha256']and e['package_manifest_sha256']==sha(Path(q['working_candidate'])/'package_manifest.json')
assert sha(q['independent_package_review']['path'])==q['independent_package_review']['sha256']
groups={k:g for k,g in p['groups'].items()if g['status']=='REVIEWED_WITH_LIMITS'}
assert not any(g['status']in ['CLAIMED','INVESTIGATED_AWAITING_REVIEW']for g in p['groups'].values()),'Outstanding investigation/review'
new=[i for g in groups.values()for i in g['ids']];old=set(prior['deep_reviewed_ids']);assert len(new)==len(set(new))==args.expected_new and not old&set(new)
assert set(new)<=set(p['completed_quests']);assert set(q['deep_reviewed_ids'])==old|set(new)
assert len(q['quests'])==q['derived_selected_count']==len(prior['quests']);assert {x['id']for x in q['quests']}=={x['id']for x in prior['quests']}
index=[];pins={};resolutions=[]
for gid,g in groups.items():
 rp=Path(g['review']['path']);assert sha(rp)==g['review']['sha256'];res=O/'groups'/gid/'results.json';d=read(res);pins[str(res)]=sha(res);pins[str(rp)]=sha(rp)
 assert d.get('quest_ids',d.get('quests',g['ids'])) # Actual exact per-quest hashes below are the identity check.
 for f in g['findings']:
  fp=Path(f['contracts']);assert sha(fp)==f['sha256'],str(fp)
  orig=read(fp);assert orig['quest_id']==f['id']and set(orig['contracts'])==STAGES
  pins[str(fp)]=sha(fp)
  item=next(x for x in q['quests']if x['id']==f['id']);assert set(item['contracts'])==STAGES
  for k,v in item['contracts'].items():
   assert v['status']in STATUSES and v.get('proven')and v.get('evidence'),(item['id'],k)
   v['original_findings_source']=str(fp);v['original_findings_source_sha256']=sha(fp)
   if v.get('source_correction'):
    cp=read(v['source_correction']['path']);assert v['findings_source']==cp['corrected']and v['findings_source_sha256']==cp['corrected_sha256']==sha(cp['corrected'])
   elif item.get('explicit_staged_contracts'):
    ss=item['explicit_staged_contracts'];assert sha(ss['path'])==ss['sha256'];v.update(findings_source=ss['path'],findings_source_sha256=ss['sha256'])
   else:v.setdefault('findings_source',str(fp));v.setdefault('findings_source_sha256',sha(fp))
   v.update(source_epoch_investigated='QR5:'+str(g['epoch']).zfill(2),effective_source_epoch='QR5:'+str(epoch).zfill(2),independent_review=str(rp),independent_review_sha256=sha(rp))
  item.update(status='DEEP_REVIEWED_WITH_STATIC_LIMITS',finding_source_epoch=g['epoch'],effective_source_epoch=epoch,review=str(rp),review_sha256=sha(rp),fully_static_verified=all(v['status']in ['PASS','APPROVED_DEVIATION']for v in item['contracts'].values()))
 index.append({'group':gid,'quest_ids':g['ids'],'findings':g['findings'],'results':str(res),'results_sha256':sha(res),'review':g['review'],'review_addendum':g.get('review_addendum'),'reported_check_events':d.get('checks',d.get('total_checks',d.get('tests'))),'reported_mutation_events':d.get('mutations'),'limits':'Counts may reuse shared controls; not unique semantic or gameplay coverage.'})
for fp in [O/'adjudications/G03_01.json',O/'adjudications/G03_02_crosswriter.json',O/'adjudications/repairs_01.json',O/'groups/G13/corrections/G02_SPR01/verification_02/correction.json',O/'reviews/worker_b/G03.json',O/'metadata_corrections.json',O/'groups/G16/timer_arithmetic_correction_01.json',O/'adjudications/moving_heat_01.json',O/'metadata_corrections_02.json',O/'groups/G18/moving_heat_prefab_03/proposal_scope_addendum_01.json',O/'shared/tier3_condition_readback_01/disjunction_tests.json']:
 assert fp.is_file();pins[str(fp)]=sha(fp);resolutions.append({'path':str(fp),'sha256':sha(fp)})
for fp in [O/'adjudications/ronald_01.json',O/'shared/ronald_family_inventory_01.json',O/'groups/G21/reviews/RONALD/verification_05/review.json']:
 assert fp.is_file();pins[str(fp)]=sha(fp);resolutions.append({'path':str(fp),'sha256':sha(fp)})
for x in q['quests']:
 x['remaining']=[{'contract':k,'status':v['status'],'item':u}for k,v in x['contracts'].items()for u in v.get('remaining',[])]
q.update(deep_reviewed_count=len(old|set(new)),deep_reviewed_ids=[x['id']for x in q['quests']if x['id']in old|set(new)],pending_review_ids=[],new_investigated_count=len(new),static_verified_count=sum(bool(x.get('fully_static_verified'))for x in q['quests']),source_epoch=epoch,source_epoch_manifest=str(ep),checkpoint_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
q['completed_count']=q['static_verified_count'];rows=[]
for x in q['quests']:
 for stage,v in x['contracts'].items():
  rows.append({'quest_id':x['id'],'title':x['title'],'stage':stage,**copy.deepcopy(v),'review_state':x['status']})
assert len(rows)==10*len(q['quests'])and len({(r['quest_id'],r['stage'])for r in rows})==len(rows)
write(O/'queue.json',q);write(O/'quest_status_matrix.json',q['quests']);write(O/'contract_status_matrix.json',rows)
for name,data in [('quest_status_matrix.csv',q['quests']),('contract_status_matrix.csv',rows)]:
 fields=list(dict.fromkeys(k for r in data for k in r));csvwrite(O/name,[{k:r.get(k)for k in fields}for r in data])
write(O/'group_evidence_index.json',{'scope':'Source-specific investigations plus independent actual-resource reviews; assertion counts are not gameplay coverage.','groups':index,'supersessions':resolutions,'input_pins':pins})
# Authoritative prior exceptions are retained, then source-specific new evidence.
diffs=read(W/'prealpha/quest_restoration_qr4/intentional_differences.json')['differences']
for x in q['quests']:
 if x['id']not in new:continue
 for stage,v in x['contracts'].items():
  for text in v.get('approved_differences',[]):diffs.append({'quest_id':x['id'],'contract':stage,'difference':text,'evidence':v['evidence'],'findings_source_sha256':v['findings_source_sha256'],'effective_epoch':'QR5:'+str(epoch).zfill(2),'new_repair':v.get('repair')})
write(O/'intentional_differences.json',{'source_epoch':epoch,'differences':diffs,'approval_boundary':'Evidence-backed existing adaptations and exactly allowlisted repairs. Neither a status nor prose approves another runtime change.'})
pending=[x for x in q['quests']if x['id']not in q['deep_reviewed_ids']];nextbatch=pending[0]['batch']if pending else None
counts=lambda ids:dict(collections.Counter(v['status']for x in q['quests']if x['id']in ids for v in x['contracts'].values()))
coverage={'status':'RECONCILED_SOURCE_AND_REVIEW_COVERAGE_WITH_EXPLICIT_LIMITS','selected':len(q['quests']),'prior_deep':len(old),'new_deep':len(new),'deep_total':q['deep_reviewed_count'],'remaining':len(pending),'primary':{'required':sum(len(g['ids'])for g in p['groups'].values()if g['scope']=='PRIMARY'),'reviewed':sum(len(g['ids'])for g in groups.values()if g['scope']=='PRIMARY')},'stretch':{'required':sum(len(g['ids'])for g in p['groups'].values()if g['scope']=='STRETCH'),'reviewed':sum(len(g['ids'])for g in groups.values()if g['scope']=='STRETCH')},'new_contract_status_counts':counts(set(new)),'deep_contract_status_counts':counts(set(q['deep_reviewed_ids'])),'fully_static_verified':q['static_verified_count'],'contracts':len(rows),'new_confirmed_defects':5,'new_repaired_defects':4,'new_blocked_defects':1,'new_affected_quests':5,'cumulative_staged_repairs':7,'batch_counts':{b:{'total':sum(x['batch']==b for x in q['quests']),'deep':sum(x['batch']==b and x['id']in q['deep_reviewed_ids']for x in q['quests'])}for b in sorted({x['batch']for x in q['quests']})},'limits':['Deep reviewed means ten source-specific dispositions plus independent actual-resource review, not ten PASSes.','No gameplay, save-transition, opaque placement, runtime merged TDB or call/reward/reload success certification.','Pending/unknown/opaque and confirmed blocked CVI02 branch remain visible.'],'source_epoch':5,'queue_sha256':sha(O/'queue.json')}
coverage.update(new_confirmed_defects=defs['new_confirmed_unique_defects'],new_repaired_defects=defs['new_repaired_unique_defects'],new_blocked_defects=defs['new_blocked_unique_defects'],new_affected_quests=defs['new_affected_quest_count'],cumulative_staged_repairs=defs['cumulative_staged_repairs'],source_epoch=epoch)
write(O/'coverage.json',coverage)
write(O/'checkpoint.json',{**coverage,'state':'QR5_DEEP_INVESTIGATIONS_REVIEWED_REPAIRS_PACKAGED_BLOCKERS_EXPLICIT','working_candidate':q['working_candidate'],'source_epoch_manifest':str(ep),'source_epoch_sha256':sha(ep),'installed':'PH3 unchanged','next_batch':nextbatch,'next_batch_quests':[{'id':x['id'],'title':x['title']}for x in pending if x['batch']==nextbatch],'next_all_unreviewed':[{'id':x['id'],'title':x['title'],'batch':x['batch']}for x in pending],'remaining_final_gates':'Final preservation read-only verification and concise report/handoff'} )
p['status']='ALL_CLAIMED_INVESTIGATIONS_REVIEWED_FINAL_PRESERVATION_REPORT_PENDING';write(O/'progress.json',p)
print({k:coverage[k]for k in ['selected','new_deep','deep_total','remaining','fully_static_verified','new_contract_status_counts']})
