"""QR7 targeted baseline and preservation capture; no census/build/runtime writes."""
from pathlib import Path
import sys,datetime,shutil,copy,subprocess,hashlib,concurrent.futures
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;P=W/'prealpha/quest_restoration_qr6'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,tree_metadata
assert not(O/'sentinel.json').exists(),'Fresh QR7 only; preserve prior start evidence'
c=read(P/'completion.json');assert sha(P/'completion.json')=='5F6452694DB80D9FF0FDC956C7D9D00357016D950166F21B587222F67892CACC'
assert c['status']=='QR6_COMPLETE_WITH_EXPLICIT_STATIC_LIMITS'
assert all(sha(r['path'])==r['sha256']for r in c['artifacts'].values())
ep=P/'source_epoch_00.json';e=read(ep);C=Path(e['candidate']);m=read(C/'package_manifest.json')
assert sha(ep)==c['canonical_epoch']['sha256']=='A532E6F1CD46B898259F78FD4D303E31C7BDC14EC1774FA2EA3875CFF1B23BC2'
assert all(sha(C/'archive_source'/d)==h for d,h in e['source_resources'].items())
assert all(sha(C/'package'/r['path'])==r['sha256']for r in e['package_files'])
assert sha(C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive')==e['archive_sha256']==m['archive_sha256']
assert sha(m['zip'])==m['zip_sha256']==e['zip_sha256']
assert all(sha(C/'archive_source'/r['depot'])==r['after']for r in e['inherited_repair_resources'])
q=read(P/'queue.json');targets=[{'quest_id':x['id'],'title':x['title'],'stage':s,'original_status':v['status'],'original_contract':copy.deepcopy(v)}for x in q['quests']for s,v in x['contracts'].items()if v['status']in ['FAIL','UNKNOWN']]
assert len(targets)==21 and sum(r['original_status']=='FAIL'for r in targets)==13 and sum(r['original_status']=='UNKNOWN'for r in targets)==8
write(O/'sentinel.json',{'status':'PASS_EXACT_QR6_COMPLETION_AND_QR5_CANDIDATE','QR6_completion':str(P/'completion.json'),'QR6_completion_sha256':sha(P/'completion.json'),'canonical_predecessor_epoch':str(ep),'canonical_predecessor_epoch_sha256':sha(ep),'verified_resources':len(e['source_resources']),'verified_package_paths':len(e['package_files']),'prior_repairs_preserved':8,'prior_repair_resources_preserved':len(e['inherited_repair_resources']),'target_FAILs':13,'target_UNKNOWNs':8,'archive_sha256':e['archive_sha256'],'zip_sha256':e['zip_sha256'],'installed':'PH3 separate, to be verified against receipt'})
e7=copy.deepcopy(e);e7.update(epoch=0,epoch_key='QR7:00',predecessor_epoch_path=str(ep),predecessor_epoch_sha256=sha(ep),changes=[],scope='QR7 targeted baseline is exact QR6:00=QR5:08candidate03; all eight staged repairs across nine resources preserved. No copied or rebuilt package yet.')
write(O/'source_epoch_00.json',e7);write(O/'target_contracts_00.json',{'source_queue':str(P/'queue.json'),'source_queue_sha256':sha(P/'queue.json'),'targets':targets,'scope':'Only13FAILs and8UNKNOWNs initially. Propagate shared evidence to other exact applicable contracts only through explicit reviewed changes.'})
q.update(predecessor_queue=str(P/'queue.json'),predecessor_queue_sha256=sha(P/'queue.json'),source_epoch_namespace='QR7',source_epoch=0,source_epoch_manifest=str(O/'source_epoch_00.json'),QR7_targeted_contracts=21,QR7_changes=[]);write(O/'queue.json',q)
write(O/'assignments.json',{'worker_a':{'role':'CVI02 controller','status':'ACTIVE','targets':[{k:r[k]for k in ['quest_id','stage','original_status']}for r in targets if r['quest_id']=='sts_pac_cvi_02']},'worker_b':{'role':'Ronald selected post-gig news','status':'ACTIVE','targets':[{k:r[k]for k in ['quest_id','stage','original_status']}for r in targets if r['original_status']=='FAIL'and r['quest_id']!='sts_pac_cvi_02']},'worker_c':{'role':'All eight UNKNOWNs','status':'ACTIVE','targets':[{k:r[k]for k in ['quest_id','stage','original_status']}for r in targets if r['original_status']=='UNKNOWN']},'cross_review':'Rotate A reviews C, B reviews A, C reviews B; coordinator alone integrates runtime changes.'})
reg=read(P/'shared_evidence_registry.json');reg.update(predecessor=str(P/'shared_evidence_registry.json'),predecessor_sha256=sha(P/'shared_evidence_registry.json'));write(O/'shared_evidence_registry.json',reg)
write(O/'approved_changes_00.json',{'status':'NO_QR7_RUNTIME_CHANGE_YET','relative_to':'QR6:00','resources':[],'inherited_repair_resources':e['inherited_repair_resources']})
shutil.copyfile(Path(r'C:\Users\Ayong\.codex\attachments\6d74eafc-4dec-460f-960b-8f81e70f2734\Pasted text.txt'),O/'REQUEST.md')
git=['git','-c','safe.directory='+str(W).replace('\\','/')];write(O/'workspace_before.json',{'cwd':str(W),'branch':subprocess.check_output(git+['branch','--show-current'],text=True).strip(),'head':subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(git+['status','--short'],text=True),'tracked_diff_sha256':hashlib.sha256(subprocess.check_output(git+['diff','--binary'])).hexdigest().upper()})
old=read(P/'protection_before.json');game=Path(read(P/'prepared.json')['game']);save=Path(old['save_root']);files=sorted(set([Path(p)for p in old['files']]+[f for f in P.rglob('*')if f.is_file()]))
def pin(f):
 if not f.is_file()or f.is_symlink():return str(f),None
 st=f.stat();return str(f),{'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'sha256':sha(f)}
pins={}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
 for name,v in pool.map(pin,files):
  if v:pins[name]=v
drift=[{'path':name,'QR6_start':v,'QR7_start':pins.get(name)}for name,v in old['files'].items()if name not in pins or pins[name]['sha256']!=v['sha256']]
assert all(Path(x['path']).is_relative_to(game)or Path(x['path']).is_relative_to(save)for x in drift),'Immutable predecessor/workspace drift'
write(O/'external_drift_since_QR6.json',{'status':'CURRENT_EXTERNAL_STATE_PINNED','changes':drift,'scope':'Changes already present between sessions are preserved, never undone to match an old snapshot.'})
write(O/'protection_before.json',{'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':pins,'game_metadata':tree_metadata(game),'save_root':str(save),'save_metadata':tree_metadata(save)})
write(O/'prepared.json',{'game':str(game),'save_root':str(save),'candidate':str(C),'scope':'13FAIL+8UNKNOWN targeted resolution and justified staged repairs; no deployment/game/save/fact/release/Git publication'})
write(O/'WORKING_CHECKPOINT.json',{'state':'QR7_ACTIVE_THREE_TARGETED_WORKERS','candidate':str(C),'canonical_epoch':str(O/'source_epoch_00.json'),'targets':21,'installed':'PH3 separate unchanged','next_action':'Resolve exact marker/owner and native authority gaps; cross-review concrete findings before coordinator-only repair integration','new_runtime_changes':0})
print({'status':'PASS_QR7_TARGETED_START','targets':len(targets),'protected_hashes':len(pins),'preexisting_external_changes':len(drift),'source_resources':len(e['source_resources'])})
