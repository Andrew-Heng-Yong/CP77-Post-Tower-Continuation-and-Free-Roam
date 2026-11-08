"""QR5 coordinator: verify exact QR4 successor and initialize bounded groups."""
from pathlib import Path
import sys,datetime,shutil,collections
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;P=W/'prealpha/quest_restoration_qr4'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,snapshot,tree_metadata
assert not (O/'progress.json').exists(),'Fresh QR5 workspace required'
q=read(P/'queue.json');cp=read(P/'checkpoint.json');e=read(P/'source_epoch_03.json');m=read(P/'candidate_01/package_manifest.json');C=Path(e['candidate'])
assert q['selected_count']==len(q['quests'])==161 and q['deep_reviewed_count']==64 and q['static_verified_count']==0
assert q['source_epoch']==cp['source_epoch']==e['epoch']==3 and sha(P/'queue.json')==cp['queue_sha256']
assert sha(C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive')==e['archive_sha256']==m['archive_sha256']
assert sha(m['zip'])==m['zip_sha256']
assert all(sha(C/'archive_source'/d)==h for d,h in e['source_resources'].items())
assert all(sha(C/'package'/r['path'])==r['sha256'] for r in e['package_files'])
prior_repairs=read(W/'prealpha/quest_restoration_qr3/approved_changes_02.json')['resources']+read(P/'approved_changes_01.json')['resources']
assert all(sha(C/'archive_source'/r['depot'])==r['after'] for r in prior_repairs)
write(O/'sentinel.json',{'status':'PASS_EXACT_QR4_HANDOFF_SENTINEL','canonical_predecessor_epoch':str(P/'source_epoch_03.json'),'canonical_predecessor_epoch_sha256':sha(P/'source_epoch_03.json'),'selected':len(q['quests']),'deep':q['deep_reviewed_count'],'static':0,'payload_hashes_verified':len(e['source_resources']),'package_paths_verified':len(e['package_files']),'zip_sha256':m['zip_sha256'],'archive_sha256':m['archive_sha256'],'preserved_prior_repair_resources':prior_repairs})
write(O/'source_epoch_00.json',{'epoch':0,'candidate':str(C),'source_resources':e['source_resources'],'package_files':e['package_files'],'archive_sha256':m['archive_sha256'],'xl_sha256':m['xl_sha256'],'predecessor_epoch_path':str(P/'source_epoch_03.json'),'predecessor_epoch_sha256':sha(P/'source_epoch_03.json'),'prior_repairs':prior_repairs,'scope':'Frozen QR5 investigation baseline is QR4 candidate, not installedPH3; no candidate copied or rebuilt yet'})
primary=[x for x in q['quests'] if x['batch'] in ['Q05','Q06','Q07']];stretch=[x for x in q['quests'] if x['batch']=='Q08'];groups={}
families=[('padre',[x for x in primary if x['id'].startswith('sts_hey_')],4),('pacific',[x for x in primary if x['id'].startswith('sts_pac_')],3),('muamar_arroyo',[x for x in primary if x['id'].startswith('sts_std_arr_')],3),('muamar_rancho',[x for x in primary if x['id'].startswith('sts_std_rcr_')],4),('regina_kabuki',[x for x in primary if x['id'].startswith('sts_wat_kab_')],4),('regina_littlechina',[x for x in primary if x['id'].startswith('sts_wat_lch_')],4),('regina_northside',[x for x in primary if x['id'].startswith('sts_wat_nid_')],4),('wakako',[x for x in primary if x['id'].startswith('sts_wbr_')],3),('hands_followup',[x for x in primary if x['id'].startswith('sts_ep1_')],3)]
for family,items,size in families:
 for start in range(0,len(items),size):
  chunk=items[start:start+size];gid=f'G{len(groups)+1:02}';groups[gid]={'ids':[x['id'] for x in chunk],'titles':[x['title'] for x in chunk],'family':family,'batches':sorted({x['batch'] for x in chunk}),'scope':'PRIMARY','status':'UNCLAIMED','worker':None,'epoch':0,'output':str(O/'groups'/gid),'review':None}
assert {x['id'] for x in primary}=={i for g in groups.values() for i in g['ids']} and len(primary)==48
for family,items in [('ep1_world',[x for x in stretch if x['id'].startswith('wst_')]),('ep1_minor',[x for x in stretch if x['id'].startswith('mq')]),('ep1_q304',[x for x in stretch if x['id'].startswith('q304_')]),('ep1_gigs',[x for x in stretch if x['id'].startswith('sts_')])]:
 for start in range(0,len(items),3):
  chunk=items[start:start+3];gid=f'G{len(groups)+1:02}';groups[gid]={'ids':[x['id'] for x in chunk],'titles':[x['title'] for x in chunk],'family':family,'batches':['Q08'],'scope':'STRETCH','status':'UNCLAIMED','worker':None,'epoch':0,'output':str(O/'groups'/gid),'review':None}
assert len({i for g in groups.values() for i in g['ids']})==64
initial={'G01':'qr4_worker_a','G04':'qr4_worker_b','G07':'qr4_worker_c'}
for g,w in initial.items():groups[g]['status']='CLAIMED';groups[g]['worker']=w
write(O/'progress.json',{'status':'IN_PROGRESS','primary_target':48,'stretch_target':64,'predecessor_deep':64,'worker_capacity':3,'capacity_basis':'4concurrency slots including coordinator; three reusedworkers','groups':groups,'completed_quests':[],'new_defects':[],'repair_epochs':[str(O/'source_epoch_00.json')],'events':[{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':'START_QR5_THREE_WORKER_POOL'}]})
q['predecessor_queue']=str(P/'queue.json');q['predecessor_queue_sha256']=sha(P/'queue.json');q['new_investigated_count']=0;q['pending_review_ids']=[];q['source_epoch']=0;q['source_epoch_manifest']=str(O/'source_epoch_00.json')
write(O/'queue.json',q);shutil.copyfile(P/'contract_status_matrix.json',O/'contract_status_matrix.json')
shutil.copyfile(Path(r'C:\Users\Ayong\.codex\attachments\e675c7db-8b53-49f9-aa0e-6b37cf82f867\Pasted text.txt'),O/'REQUEST.md')
write(O/'shared_evidence_registry.json',{'status':'PINNED_SHARED_EVIDENCE_WITH_APPLICABILITY_REVIEW_REQUIRED','predecessor':str(P/'group_evidence_index.json'),'predecessor_sha256':sha(P/'group_evidence_index.json'),'items':[{'id':'QR4-U9-DAKOTA','path':str(P/'groups/G09/shared_core.json'),'sha256':sha(P/'groups/G09/shared_core.json'),'applies_to':'U9 common mechanics only; each fixer/quest must prove exact applicability'},{'id':'QR4-PADRE','path':str(P/'groups/G12/results.json'),'sha256':sha(P/'groups/G12/results.json'),'applies_to':'Padre exact controller/entry/credit shared evidence; gig-specific paths not inherited'}],'unresolved_shared_domains':['TweakDB target definitions','DynamicBaseClass/worldNode decoded placement','saved-owner and engine scheduling','localization and voice presentation']})
write(O/'WORKING_CHECKPOINT.json',{'state':'SENTINEL_PASSED_WORKERS_STARTING','working_candidate':str(C),'installed':'PH3 unchanged','epoch':0,'next_action':'Keep dynamic primary groups occupied, integrate independent reviews, centralize only justified source repairs','restrictions':'No install/game/save/fact/release/Git publication changes'})
print({'status':'PASS_SENTINEL_AND_DYNAMIC_QUEUE','primary':len(primary),'stretch':len(stretch),'groups':len(groups),'initial':initial})
