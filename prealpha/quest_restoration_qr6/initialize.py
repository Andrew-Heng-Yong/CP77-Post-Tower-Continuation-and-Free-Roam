"""One-shot QR6 sentinel/assignment/protection capture; no runtime writes/builds."""
from pathlib import Path
import sys, shutil, datetime, subprocess, copy
W=Path(__file__).resolve().parents[2]; O=Path(__file__).resolve().parent; P=W/'prealpha/quest_restoration_qr5'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,snapshot,tree_metadata
assert not (O/'sentinel.json').exists(), 'Fresh QR6 initialization only'
q=read(P/'queue.json'); cp=read(P/'checkpoint.json'); ep=P/'source_epoch_08.json'; e=read(ep); C=Path(e['candidate']); m=read(C/'package_manifest.json')
assert sha(ep)=='B8BC8D6630F51E07125789FAB5A54D188EB45CE7044F35E2E6F09DE460B91D83'
assert sha(P/'queue.json')==cp['queue_sha256']
assert q['source_epoch']==e['epoch']==8 and q['deep_reviewed_count']==128 and len(q['quests'])==161
assert sha(C/'package_manifest.json')==e['package_manifest_sha256']
assert sha(C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive')==m['archive_sha256']==e['archive_sha256']
assert sha(m['zip'])==m['zip_sha256']
assert all(sha(C/'archive_source'/d)==h for d,h in e['source_resources'].items())
assert all(sha(C/'package'/r['path'])==r['sha256'] for r in e['package_files'])
repairs=e['prior_repairs']+e['changes']; assert len(repairs)==9
assert all(sha(C/'archive_source'/r['depot'])==r['after'] for r in repairs)
assert sha(P/'approved_changes_04.json')==e['approved_changes_sha256']
link=read(P/'completion_linkage_01/addendum.json')
write(O/'sentinel.json',{'status':'PASS_EXACT_QR5_CANONICAL08','canonical_predecessor_epoch':str(ep),'canonical_predecessor_epoch_sha256':sha(ep),'selected':len(q['quests']),'deep':128,'remaining':33,'payloads_verified':len(e['source_resources']),'package_paths_verified':len(e['package_files']),'archive_sha256':m['archive_sha256'],'zip_sha256':m['zip_sha256'],'all_nine_prior_repaired_resources':repairs,'completion_linkage':str(P/'completion_linkage_01/addendum.json'),'completion_linkage_sha256':sha(P/'completion_linkage_01/addendum.json'),'scope':'Static baseline sentinel; PH3 installed and no gameplay success implied'})
write(O/'source_epoch_00.json',{'epoch':0,'epoch_key':'QR6:00','candidate':str(C),'source_resources':e['source_resources'],'package_files':e['package_files'],'archive_sha256':e['archive_sha256'],'xl_sha256':e['xl_sha256'],'package_manifest_path':str(C/'package_manifest.json'),'package_manifest_sha256':sha(C/'package_manifest.json'),'zip':m['zip'],'zip_sha256':m['zip_sha256'],'predecessor_epoch_path':str(ep),'predecessor_epoch_sha256':sha(ep),'inherited_repair_resources':repairs,'changes':[],'scope':'QR6 frozen investigation baseline is QR5candidate03canonical08. No copied/rebuilt candidate; all eight cumulative repairs across nine resources retained.'})
specs={'A01':('qr6_a',['mq040_biosculpt','mq028_stalker','mq018_writer']), 'A02':('qr6_a',['mq016_bartmoss','mq006_rollercoaster','mq029_tourist']), 'A03':('qr6_a',['mq017_streetkid','q003_stout','mq036_overload']), 'B01':('qr6_b',['mq050_ken_block_tribute','mq042_nomad','mq059_freedom','mq060_nitro','mq058_semimaru_crystalcoat']), 'B02':('qr6_b',['mws_wat_08_trauma_drama','mws_se5_07','mq022_ezekiel','mq003_orbitals']), 'B03':('qr6_b',['sq023_real_passion','sq023_hit_order','sq023_bd_passion','sq025b_delamain_insurgence']), 'C01':('qr6_c',['sts_hey_gle_03','sts_hey_gle_05','sts_hey_rey_01','sts_hey_rey_02']), 'C02':('qr6_c',['sts_std_arr_03','sts_wat_nid_07','sts_wbr_hil_06','sts_wbr_jpn_12']), 'C03':('qr6_c',['q305_postcontent','wst_ep1_09','sts_ep1_12_pickup'])}
pending=[x for x in q['quests'] if x['id'] not in q['deep_reviewed_ids']]; assigned=[i for _,ids in specs.values() for i in ids]
assert len(assigned)==len(set(assigned))==len(pending)==33 and set(assigned)=={x['id'] for x in pending}
groups={g:{'worker':worker,'ids':ids,'titles':[next(x['title'] for x in pending if x['id']==i) for i in ids],'batches':sorted({x['batch'] for x in pending if x['id'] in ids}),'status':'CLAIMED','epoch':'QR6:00','findings':[],'review':None,'output':str(O/'groups'/g)} for g,(worker,ids) in specs.items()}
write(O/'progress.json',{'status':'IN_PROGRESS','prior_deep':128,'target_new':33,'worker_capacity':3,'groups':groups,'events':[{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':'ALL_THREE_WORKERS_DISPATCHED_ALL33_ASSIGNED'}]})
q.update(predecessor_queue=str(P/'queue.json'),predecessor_queue_sha256=sha(P/'queue.json'),source_epoch_namespace='QR6',source_epoch=0,source_epoch_manifest=str(O/'source_epoch_00.json'),new_investigated_count=0,pending_review_ids=[],retained_QR5_deep_reviewed_ids=q['deep_reviewed_ids'].copy())
write(O/'queue.json',q)
shutil.copyfile(Path(r'C:\Users\Ayong\.codex\attachments\7cb72174-f1fd-45ff-a6d2-a1de5c53e8a6\Pasted text.txt'),O/'REQUEST.md')
reg=read(P/'shared_evidence_registry.json'); reg.update(predecessor=str(P/'shared_evidence_registry.json'),predecessor_sha256=sha(P/'shared_evidence_registry.json'));write(O/'shared_evidence_registry.json',reg)
write(O/'approved_changes_00.json',{'relative_to':'QR5:08','resources':[],'status':'NO_QR6_RUNTIME_CHANGES','inherited_allowlist':str(P/'approved_changes_04.json'),'inherited_allowlist_sha256':sha(P/'approved_changes_04.json'),'inherited_prior_repairs':repairs})
write(O/'WORKING_CHECKPOINT.json',{'state':'QR6_ACTIVE_ALL33_ASSIGNED','candidate':str(C),'canonical_epoch':str(O/'source_epoch_00.json'),'installed':'PH3 unchanged','next_action':'Complete nine source-specific groups, rotate independent cross-reviews, investigate repair blockers and integrate only proven fixes','restrictions':'No game/deploy/save/fact/release/Git publication writes'})
git=['git','-c','safe.directory='+str(W).replace('\\','/')]
write(O/'workspace_before.json',{'cwd':str(W),'branch':subprocess.check_output(git+['branch','--show-current'],cwd=W,text=True).strip(),'head':subprocess.check_output(git+['rev-parse','HEAD'],cwd=W,text=True).strip(),'status':subprocess.check_output(git+['status','--short'],cwd=W,text=True),'tracked_diff_sha256':__import__('hashlib').sha256(subprocess.check_output(git+['diff','--binary'],cwd=W)).hexdigest().upper()})
old=read(P/'protection_before.json'); game=read(P/'prepared.json')['game']; files=[Path(p) for p in old['files']]+[p for p in P.rglob('*') if p.is_file()]
pins=snapshot(files); drift=[p for p,v in old['files'].items() if p not in pins or pins[p]['sha256']!=v['sha256']]
assert not drift, 'Previous protected input bytes changed: '+str(drift[:10])
write(O/'prepared.json',{'game':game,'save_root':old['save_root'],'candidate':str(C),'scope':'33 remaining deep quests and source-confirmed safe repairs only; no deploy'})
write(O/'protection_before.json',{'files':pins,'game_metadata':tree_metadata(game),'save_root':old['save_root'],'save_metadata':tree_metadata(old['save_root'])})
write(O/'protection_start.json',{'status':'PASS_PINNED_QR5_AND_PROTECTED_INPUTS','protected_hashes':len(pins),'old_hash_drift':len(drift),'game_and_save_writes':0})
print({'status':'PASS_QR6_INITIALIZATION','assigned':len(assigned),'groups':len(groups),'protected_hashes':len(pins)})
