"""Fresh QR8 baseline, exact QR7 seal/package and protected-state capture.

Read-only with respect to QR7, the game, saves and all existing artifacts.
"""
from pathlib import Path
import sys,shutil,copy,datetime,hashlib,zipfile,subprocess,concurrent.futures
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;P=W/'prealpha/quest_restoration_qr7'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,tree_metadata
assert not(O/'sentinel.json').exists(),'Fresh QR8 output only'
c=read(P/'completion.json');assert sha(P/'completion.json')=='8C41857D4F9FCB87C5DE3E456EC00C2C70E7F84EB722B46F21280413682E41C6'
assert c['status']=='QR7_COMPLETE_TARGETED_STATIC_WORK_WITH_PARTIAL_REPAIR_AND_UNKNOWN_LIMITS'
assert all(sha(r['path'])==r['sha256']for r in c['artifacts'].values())
ep=P/'source_epoch_04.json';e=read(ep);C=Path(e['candidate']);m=read(C/'package_manifest.json')
assert sha(ep)==c['canonical_epoch']['sha256']
actual={str(p.relative_to(C/'archive_source')):sha(p)for p in(C/'archive_source').rglob('*')if p.is_file()}
assert actual==e['source_resources']
assert all(sha(C/'package'/r['path'])==r['sha256']for r in e['package_files'])
assert {str(p.relative_to(C/'package')).replace('\\','/')for p in(C/'package').rglob('*')if p.is_file()}=={r['path'].replace('\\','/')for r in e['package_files']}
assert sha(C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive')==e['archive_sha256']==c['archive_sha256']
assert sha(C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl')==e['xl_sha256']==c['xl_sha256']
assert sha(m['zip'])==m['zip_sha256']==c['zip_sha256']
with zipfile.ZipFile(m['zip'])as z:
 assert z.testzip()is None and len(z.infolist())==len(e['package_files'])and len(z.namelist())==len(set(z.namelist()))
 for r in e['package_files']:assert hashlib.sha256(z.read(r['path'].replace('\\','/'))).hexdigest().upper()==r['sha256']
im=W/'prealpha/phone_studios_ph3/candidate_01/install_manifest_01.json';installed=read(im);game=Path(installed['game_root'])
assert all(sha(game/r['path'])==r['after']for r in installed['package_files'])
atelier=game/'r6/scripts/virtual-atelier-full/SetupNewTab.reds';assert sha(atelier)=='5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8'
old=read(P/'protection_before.json');save=Path(old['save_root']);files=sorted(set([Path(p)for p in old['files']]+[p for p in P.rglob('*')if p.is_file()]))
def pin(p):
 if not p.is_file()or p.is_symlink():return str(p),None
 s=p.stat();return str(p),{'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':sha(p)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:pins={p:v for p,v in pool.map(pin,files)if v}
drift=[{'path':p,'QR7_start':v,'QR8_start':pins.get(p)}for p,v in old['files'].items()if p not in pins or pins[p]['sha256']!=v['sha256']]
assert all(Path(x['path']).is_relative_to(game)or Path(x['path']).is_relative_to(save)for x in drift),'Pinned non-external predecessor drift'
write(O/'external_drift_since_QR7.json',{'status':'CURRENT_EXTERNAL_STATE_PINNED_NOT_REVERTED','changes':drift})
write(O/'protection_before.json',{'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':pins,'game_metadata':tree_metadata(game),'save_root':str(save),'save_metadata':tree_metadata(save)})
git=['git','-c','safe.directory='+str(W).replace('\\','/')]
write(O/'workspace_before.json',{'cwd':str(W),'branch':subprocess.check_output(git+['branch','--show-current'],cwd=W,text=True).strip(),'head':subprocess.check_output(git+['rev-parse','HEAD'],cwd=W,text=True).strip(),'status':subprocess.check_output(git+['status','--short'],cwd=W,text=True),'tracked_diff_sha256':hashlib.sha256(subprocess.check_output(git+['diff','--binary'],cwd=W)).hexdigest().upper()})
e8=copy.deepcopy(e);e8.update(epoch=0,epoch_key='QR8:00',predecessor_epoch_path=str(ep),predecessor_epoch_sha256=sha(ep),changes=[],scope='Exact QR7:04 source/package reused. No new source/package/ZIP; all current QR7 corrections retained by exact identity. Final QR8 integration/reviews pending.',package_state='EXACT_QR7_PACKAGE_REUSED_NOT_REBUILT')
e8['zip']=m['zip'];e8['zip_sha256']=m['zip_sha256'];write(O/'source_epoch_00.json',e8)
q=read(P/'queue.json');q.update(predecessor_queue=str(P/'queue.json'),predecessor_queue_sha256=sha(P/'queue.json'),source_epoch=0,source_epoch_namespace='QR8',source_epoch_manifest=str(O/'source_epoch_00.json'),QR8_scope='Targeted engine/communication/fiveUNKNOWN resolution and controlled-test readiness; no repeated whitelist/deep audit.',QR8_status='ACTIVE_TARGETED_INVESTIGATIONS');write(O/'queue.json',q)
write(O/'approved_changes_00.json',{'status':'NO_QR8_RUNTIME_OR_PACKAGE_CHANGE','relative_to':'QR7:04','resources':[],'prior_repair_preservation_basis':str(ep),'prior_repair_preservation_basis_sha256':sha(ep)})
shutil.copyfile(Path(r'C:\Users\Ayong\.codex\attachments\2dc6a6d5-8159-475e-a66b-bbd5a362dc1d\Pasted text.txt'),O/'REQUEST.md')
write(O/'prepared.json',{'game':str(game),'save_root':str(save),'candidate':str(C),'scope':'QR8 final integration/blocker resolution/test readiness only. No launch/deploy/save/fact/release/Git publication.'})
write(O/'sentinel.json',{'status':'PASS_EXACT_QR7_SEAL_SOURCE_PACKAGE_ZIP_AND_INSTALLED_PH3','QR7_completion':str(P/'completion.json'),'QR7_completion_sha256':sha(P/'completion.json'),'source_epoch':str(ep),'source_epoch_sha256':sha(ep),'source_payloads':len(actual),'package_paths':len(e['package_files']),'archive_sha256':e['archive_sha256'],'xl_sha256':e['xl_sha256'],'zip_sha256':m['zip_sha256'],'installed_manifest':str(im),'installed_manifest_sha256':sha(im),'installed_paths':len(installed['package_files']),'atelier_sha256':sha(atelier),'protected_hashes':len(pins),'preexisting_external_changes':len(drift),'archive_member_readback':'PENDING_SEPARATE_FRESH_READ_ONLY_GATE','game_writes':0,'save_writes':0})
write(O/'checkpoint.json',{'state':'QR8_ACTIVE_THREE_TARGETED_WORKERS','canonical_epoch':str(O/'source_epoch_00.json'),'candidate':str(C),'new_runtime_changes':0,'new_ZIPs':0,'next_action':'Fresh archive readback, installed DLL/communication/UNKNOWN investigations, crossreviews and controlled acceptance-test preparation.','installed':'PH3 unchanged'})
print({'status':'PASS_EXACT_QR7_START','source_payloads':len(actual),'package_paths':len(e['package_files']),'protected_hashes':len(pins),'preexisting_external_changes':len(drift)})
