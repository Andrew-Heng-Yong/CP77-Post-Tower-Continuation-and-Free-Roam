from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
m=read(C/'install_manifest_01.json');r=read(W/'recovery/h10_h5_01/receipt.json');t=read(C/'tests_01.json');d=read(C/'deployment_tests_01.json')
assert r['status']=='H5_INSTALLED_LIVE_PENDING' and t['status']=='PASS_H5_OFFLINE_LIVE_PENDING' and d['status']=='PASS_REAL_INSTALLER_FIXTURES'
for f in m['files']:
 assert sha(Path(m['game_root'])/f['target'])==f['after']
 if f['before']:assert sha(Path(m['backup_root'])/f['target'])==f['before']
for f in m['protected']+m['proofs']:assert sha(f['path'])==f['sha256']
assert sha(H/'deploy_01.ps1')==d['deployer_sha256'] and sha(C/'install_manifest_01.json')==d['manifest_sha256']
out={'status':'H5_INSTALLED_LIVE_PENDING','summary':'Actor-free native H10 dialogue choices replace automatic confirmation. Explicit priced selection consumes one request before unchanged payment operation; cancel, stale reload request and old popup/device callbacks cannot debit.','files':m['files'],'protected_files':len(m['protected']),'save_files':sum(p['kind']=='save' for p in m['protected']),'full_script_sources':91,'compiled_sha256':t['compiled_sha256'],'offline_checks':t['count'],'installer_fixture_actions':d['count'],'preserved':['HousingState entire compiled class','H10 lock, inside egress, map and entitlement','DLC purchase popup and website guard','Fred FS1 and all existing archives','Frameworks and saved files'],'limitations':t['limits'],'rollback':'H5 before H3/H2/LC3 overlapping purchase scripts. ValidateRollback/Rollback via deploy_01.ps1, backup recovery/h10_h5_01. File undo is not save/payment undo.','public_release_changed':False,'game_launched':False,'manual_fact_writes':0,'pins':{str(p.relative_to(W)):sha(p) for p in list(H.glob('*.*'))+[C/'tests_01.json',C/'native_01.json',C/'install_manifest_01.json',C/'deployment_tests_01.json',W/'recovery/h10_h5_01/receipt.json']}}
p=C/'assessment_01.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'protected':out['protected_files'],'saves':out['save_files'],'assessment_sha256':sha(p)}))
