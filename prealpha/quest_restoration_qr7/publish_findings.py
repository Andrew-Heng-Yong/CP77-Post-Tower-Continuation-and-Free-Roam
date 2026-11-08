"""Reconcile exactly the original 21 QR7 targets, retaining original findings.

An updated status is explicitly scoped to the prospective successor. Historical
admission, absent contacts, pending clocks and save transitions are not passed.
"""
from pathlib import Path
import sys,copy,collections,datetime,csv,shutil,json
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
def csvwrite(path,rows):
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with Path(path).open('w',encoding='utf-8',newline='')as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False)if isinstance(v,(dict,list))else v for k,v in r.items()})
if (O/'targeted_dispositions.json').exists():
 assert sys.argv[1:]==['--recover-csv']and not(O/'contract_status_matrix.json').exists()
 failed=O/'publication_failed_01';assert not failed.exists();failed.mkdir()
 for name in ['targeted_dispositions.json','targeted_dispositions.csv','queue.json']:shutil.copyfile(O/name,failed/name)
 write(failed/'failure.json',{'reason':'CSV serializer assumed homogeneous dictionaries; union-column writer substituted. JSON target and queue data were complete; CSV only partial. No resource/package/game writes.'})
ep=O/'source_epoch_04.json';e=read(ep);a=read(O/'approved_changes_03.json');q=read(O/'queue.json');prior=read(W/'prealpha/quest_restoration_qr6/queue.json')
targets=read(O/'target_contracts_00.json')['targets'];targetkeys={(t['quest_id'],t['stage'])for t in targets};original={(t['quest_id'],t['stage']):t for t in targets};byq={x['id']:x for x in q['quests']};pbyq={x['id']:x for x in prior['quests']}
files=[O/'worker_c/results_01/contract_updates.json',O/'worker_b/reviews/CVI02/contract_updates_01/contract_updates.json',O/'worker_b/findings_01/contract_dispositions.json'];updates=[]
peerC=O/'worker_a/reviews/unknowns_final_01/review.json';peerB=O/'worker_c/reviews/ronald_01/verification_02/review.json'
common_evidence=[O/'candidate_01/package_manifest.json',O/'candidate_01/rebuild_01.json',O/'compile_reuse_01.json',ep]
for fp in files:
 for row in read(fp):
  r=copy.deepcopy(row);key=(r['quest_id'],r['stage']);assert key in targetkeys
  r['original_QR6_status']=original[key]['original_status'];r['superseded_QR6_finding']=original[key]['original_contract'];r['worker_finding']={'path':str(fp),'sha256':sha(fp),'original_record':copy.deepcopy(row)}
  r.update(effective_source_epoch='QR7:04',source_epoch_manifest=str(ep),source_epoch_sha256=sha(ep),coordinator_disposition_scope='Current staged successor only. No deployment or gameplay success; prior source finding is preserved separately.')
  r['evidence']=list(r.get('evidence',[]))+[{'path':str(p),'sha256':sha(p)}for p in common_evidence]
  if r['quest_id'].startswith('sts_ep1_'):
   r['status']='CONDITIONAL';r['disposition']='IMPLEMENTED_FUTURE_ARMED_EXISTING_SUBSCRIBER_ONLY_STATIC_REPAIR_WITH_EXPLICIT_BLOCKED_HISTORIES'
   r.pop('proposed_disposition_if_accepted',None)
   r['proven']=[s.replace('Private serialized04 proposes an actual new future-event writer','Current QR7:04 contains the independently approved serialized04 future-event writer').replace('the proposal deliberately preserves','the integrated successor preserves')for s in r['proven']]
   r['proven'].append('Coordinator promoted the exact seven peer-reviewed serialized payloads, freshly read back their complete models/packed bytes, appended one phase registration19913 and one two-trigger block, and rebuilt/read back every final archive member. Original Ronald/B0 scene and main gig bodies remain unchanged.')
   r['approved_differences']=['Private prospective owner replaces the retired news11/12 for four selected jobs only; original fluff branches are excluded and its terminal AND has four inputs. Real new Armed signals gate fresh events. Exact native selected payloads, timers, outcomes, SMS journal identities and notification flags remain.','Only two original native triggers/shapes/transforms are rehomed under one private descriptor/global hierarchy. No whole-bar owner or contact/enrollment bootstrap is cloned.']
   r['remaining']=['STATIC_BLOCKED_HISTORY: already-entered jobs without QR7 Armed, native done1/sent1 or ambiguous pending clocks are deliberately skipped; no native counter, sent flag or elapsed timer is reset. Old native saved-owner retirement beyond observable gates is not proved.','STATIC_BLOCKED_ENROLLMENT: a genuine preexisting q302_ronald_messages_enabled and active native Ronald contact are required. B0 enrollment1755 remains unreachable; first contact/new subscription is not repaired. Exact complete dialogue/contact/owner lifecycle evidence and safe saved-state transition are required before extending scope.','LIVE_ONLY: private two-trigger streaming/lease acquisition/release, occupancy, concurrent scheduling, two-game-day persistence, actual SMS rendering/delivery, interruption and cold reload remain untested.','BOUNDED_NAMESPACE: all current archive depot keys and all installed target-root XL IDs were checked. A whole native/external world-global collision census was not performed. Preserved sourcePrefabHash metadata is not itself proof of runtime lease behavior.']
   r['independent_review']=str(peerB);r['independent_review_sha256']=sha(peerB)
   r['evidence'] += [{'path':str(p),'sha256':sha(p)}for p in [peerB,O/'worker_a/reviews/ronald_namespace_03/evidence.json',O/'worker_b/findings_addendum_01/addendum.json',O/'worker_b/future_check_04/evidence.json',O/'candidate_01/repair_ronald_01/verification.json']]
  elif r['quest_id']=='sts_pac_cvi_02':
   r['remaining']=[s for s in r['remaining']if not s.startswith('Coordinator final archive/ZIP/provider')]
   r['proven'].append('Exact approved CVI04 raw bytes were promoted to QR7:04; coordinator fresh typed model matches approved model. All final archive payloads were read back; current native donor and always-loaded marker/community providers are independently pinned. No physical FO1 support clone is needed for this exact marker.')
  else:
   r['independent_review']=str(peerC);r['independent_review_sha256']=sha(peerC)
   r['remaining']=[s for s in r['remaining']if not s.startswith('Worker C does not certify')]
   r['evidence'].append({'path':str(peerC),'sha256':sha(peerC)})
  r['final_gate_boundary']='Independent final package and completeness reviews are separate evidence pinned by completion.json; this matrix does not infer their outcome.'
  updates.append(r)
assert len(updates)==len(targetkeys)and {(r['quest_id'],r['stage'])for r in updates}==targetkeys
for r in updates:
 body={k:v for k,v in r.items()if k not in ['quest_id','title','stage']};byq[r['quest_id']]['contracts'][r['stage']]=body
 write(O/'quests'/r['quest_id']/'targeted_contracts.json',[x for x in updates if x['quest_id']==r['quest_id']])
# All ten contracts of changed entry resources receive an exact applicability
# addendum; statuses outside the original21 are not promoted.
impacts=[]
for quest,depot in [('mq060_nitro','towercontinued\\sidejobs_s29\\entries\\mq060_nitro.questphase'),('sts_pac_cvi_02','towercontinued\\native_gigs_u9\\sts_pac_cvi_02_entry.questphase')]+[(qid,'towercontinued\\native_gigs_u9\\'+qid+'_entry.questphase')for qid in ['sts_ep1_01','sts_ep1_03','sts_ep1_08','sts_ep1_12']]:
 change=next(x for x in a['resources']if x['depot']==depot)
 scope=('Existing nodes, predicates, saved graph IDs and native bodies unchanged; only root/50:65002.Out→65003.In is now65002.Out→65007.In→65003.In, writing the new private Armed receipt before existing ParentEntered.'if quest.startswith('sts_ep1_')else change['scope'])
 for stage,c in byq[quest]['contracts'].items():
  c['QR7_source_applicability']={'epoch':'QR7:04','resource':depot,'before':change['before'],'after':change['after'],'scope':scope,'status_promoted':(quest,stage)in targetkeys,'evidence':str(O/'approved_changes_03.json'),'review':change.get('source_review')}
  if (quest,stage)not in targetkeys:assert c['status']==pbyq[quest]['contracts'][stage]['status']
 impacts.append({'quest_id':quest,'resource':depot,'before':change['before'],'after':change['after'],'scope':scope,'contracts_applicability_checked':list(byq[quest]['contracts']),'status_changes_only_original_targets':True})
affected={r['quest_id']for r in updates}
for x in q['quests']:
 if x['id']in affected:
  x['QR7_targeted_findings']=str(O/'quests'/x['id']/'targeted_contracts.json')
  x['fully_static_verified']=all(c['status']in ['PASS','APPROVED_DEVIATION']for c in x['contracts'].values())
  if x['id']in {y['quest_id']for y in impacts}:x['restored_candidates']=sorted(set(x['restored_candidates'])|{y['resource']for y in impacts if y['quest_id']==x['id']})
  x['QR7_source_epoch']='QR7:04'
 else:assert x==pbyq[x['id']],x['id']
rows=[{'quest_id':x['id'],'title':x['title'],'stage':stage,**v}for x in q['quests']for stage,v in x['contracts'].items()]
counts=dict(collections.Counter(r['status']for r in rows));oldcounts=dict(collections.Counter(c['status']for x in prior['quests']for c in x['contracts'].values()))
q.update(source_epoch=4,source_epoch_namespace='QR7',source_epoch_manifest=str(ep),working_candidate=e['candidate'],QR7_targeted_contracts=str(O/'targeted_dispositions.json'),QR7_changes=a['resources'],changed_resources=[r['depot']for r in a['resources']],checkpoint_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),fully_static_verified_count=sum(x['fully_static_verified']for x in q['quests']),new_confirmed_unique_defects=1,new_repaired_unique_defects=3,source_authority_conflicts=[],package_verification='ROOT_FULL_READBACK_PASS_SEPARATE_INDEPENDENT_REVIEW_REQUIRED',new_investigated_count=0)
q['QR7_scope']='21targeted contract investigations across9quests; full161deep audit not repeated. Thirteen old FAILs have prospective conditional repairs; unsupported historical/enrollment routes remain blocked. Five UNKNOWN contracts remain.'
write(O/'queue.json',q);write(O/'targeted_dispositions.json',updates);csvwrite(O/'targeted_dispositions.csv',updates)
write(O/'contract_status_matrix.json',rows);csvwrite(O/'contract_status_matrix.csv',rows);write(O/'quest_status_matrix.json',q['quests']);csvwrite(O/'quest_status_matrix.csv',q['quests']);write(O/'affected_quest_applicability.json',{'epoch':'QR7:04','rows':impacts,'scope':'Only six entry resources changed; no old shared controller or native quest body changed. New Ronald owner subscribes only four scoped native producers and exact native SMS dependencies. Unaffected payloads remain pinned. Extra marker/provider discoveries are not projected onto other opaque contracts without exact closure.'})
coverage={'status':'TARGETED_21_DISPOSITIONS_COMPLETE_SOURCE_AND_PACKAGE_BOUNDARIES_EXPLICIT','selected':len(q['quests']),'retained_deep':len(q['quests']),'new_whitelist_deep_audits':0,'contracts':len(rows),'original_target_contracts':len(updates),'original_FAIL':sum(t['original_status']=='FAIL'for t in targets),'original_UNKNOWN':sum(t['original_status']=='UNKNOWN'for t in targets),'targeted_quests':len(affected),'before_status_counts':oldcounts,'after_status_counts':counts,'target_status_counts':dict(collections.Counter(r['status']for r in updates)),'fully_static_verified':sum(x['fully_static_verified']for x in q['quests']),'static_PASS_or_approved':sum(counts.get(k,0)for k in ['PASS','APPROVED_DEVIATION']),'remaining_UNKNOWN':[{'quest_id':r['quest_id'],'stage':r['stage']}for r in rows if r['status']=='UNKNOWN'],'source_epoch':'QR7:04','source_epoch_manifest':str(ep),'source_epoch_sha256':sha(ep),'queue_sha256':sha(O/'queue.json'),'scope':'No gameplay-success percentage. CONDITIONAL prospective scopes do not repair absent enrollment, old entered/queued histories or prove saved-owner retirement.'}
write(O/'coverage.json',coverage)
print({'status':'PUBLISHED21TARGETS_AND1610MATRIX','targeted':len(updates),'all_contracts':len(rows),'counts':counts,'fully_static_verified':coverage['fully_static_verified']})
