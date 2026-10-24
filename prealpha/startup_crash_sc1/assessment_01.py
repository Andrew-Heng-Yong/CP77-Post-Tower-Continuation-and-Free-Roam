from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
m=read(C/'install_manifest_01.json');G=Path(m['game_root']);R=Path(m['backup_root']);receipt=read(R/'receipt.json')
assert receipt['status']=='SC1_INSTALLED_LIVE_PENDING' and receipt['manifest_sha256']==sha(C/'install_manifest_01.json')
for f in m['files']:assert sha(G/f['target'])==f['after'] and sha(R/f['target'])==f['before']
for p in m['protected']+m['proofs']:assert sha(p['path'])==p['sha256']
inputs=read(C/'diagnosis_01/inputs.json')
for p,h in inputs['saves'].items():assert sha(p)==h
t=read(C/'tests_01.json');d=read(C/'deployment_tests_01.json');b=read(C/'build_02.json');cause=read(C/'diagnosis_01/cause_02.json')
assert t['status']=='PASS_NATIVE_INDEX_REPAIR_NOT_LIVE' and d['status']=='PASS_REAL_INSTALLER_FIXTURES'
assert d['manifest_sha256']==sha(C/'install_manifest_01.json')
pins=[p for p in H.iterdir() if p.is_file()]+[C/'tests_01.json',C/'deployment_tests_01.json',C/'build_02.json',C/'prepared_01.json',C/'install_manifest_01.json',C/'diagnosis_01/cause_02.json',C/'diagnosis_01/cause_02.asm',C/'diagnosis_01/inputs.json',C/'scene_audit_01/audit.json',R/'receipt.json',W/'docs/startup_crash_sc1.md']
r={'created_utc':datetime.now(timezone.utc).isoformat(),'status':'SC1_INSTALLED_VERIFIED_LIVE_PENDING','cause':cause,'files':m['files'],'private_scenes_repaired':9,'owner_resources_byte_exact':8,'offline_checks':t['count'],'installer_fixture_actions':d['count'],'protected_files_unchanged':len(m['protected']),'save_files_unchanged':len(inputs['saves']),'actions':['Validate PASS','Install PASS','Verify PASS','ValidateRollback PASS'],'game_launches':0,'save_edits':0,'runtime_fact_writes':0,'reds_changes':0,'framework_changes':0,'main_archive_changes':0,'live_lc2_hs1_evidence':['User screenshot shows opaque cover and progress bar','Native fade, control and camera progressed','Body/Relic refunds completed','158-row verified post_ending_fallback JSON exported'],'live_pending':['Full startup through readiness barrier','H1 purchase/service interactions','Fresh save/reload and any prior active H1 scene compatibility'],'legacy_unmodified_non_dense_scene':'towercontinued\\streetkid_seat_s1\\seat.scene','rollback':'startup_crash_sc1/deploy_01.ps1 ValidateRollback/Rollback before older H1 package; cover chain LC2 -> LC1 -> HS1 separate. File undo is not save undo.','public_release_updated':False,'pins':{str(p.relative_to(W)):sha(p) for p in pins}}
with (C/'assessment_01.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({'status':r['status'],'files':len(m['files']),'protected':len(m['protected']),'saves':len(inputs['saves']),'assessment_sha256':sha(C/'assessment_01.json')}))
