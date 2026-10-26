from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_02'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
m=read(C/'install_manifest_01.json');r=read(W/'recovery/fred_scene_fs1_01/receipt.json');t=read(C/'tests_01.json');d=read(C/'deployment_tests_01.json')
assert r['status']=='FS1_INSTALLED_LIVE_PENDING' and t['status']=='PASS_FS1_OFFLINE_LIVE_PENDING' and d['status']=='PASS_REAL_INSTALLER_FIXTURES'
for x in m['files']:
 assert sha(Path(m['game_root'])/x['target'])==x['after']
 assert sha(Path(m['backup_root'])/x['target'])==x['before']
for x in m['protected']+m['proofs']:assert sha(x['path'])==x['sha256']
assert sha(H/'deploy_01.ps1')==d['deployer_sha256'] and sha(C/'install_manifest_01.json')==d['manifest_sha256']
before=read(W/'diagnostics/scene_membership_20261025_01/inputs_01/receipt.json')
G=Path(m['game_root']);S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
assert {str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()}==before['save_hashes']
changed=[x['path'] for x in before['installed'] if sha(G/x['path'])!=x['actual_sha256']]
assert changed==[m['files'][0]['target']]
out={'status':'FS1_INSTALLED_LIVE_PENDING','summary':'Private Fred service scene acquires within 8m and releases beyond 12m; NPC remains spawned to original departure. Original fresh boxing branch retains its 50m/100m conditions. Existing saved node IDs/types retained; old wait5 routes into the scoped release.','files':m['files'],'protected_files_unchanged':len(m['protected']),'saved_files_unchanged':len(before['save_hashes']),'other_installed_ptfr_files_unchanged':116,'offline_checks':t['checks'],'installer_fixture_actions':d['count'],'rollback':'Run prealpha/fred_scene_fs1/deploy_01.ps1 -Action ValidateRollback then Rollback before older S25 deployments. File undo is not save undo; use a pre-FS1 save if rolling back after saving at new nodes.','limitations':['Cold-load of saved active Fred scene and engine actor release remain untested.','Fred is strongly implicated, not proven by a direct engine call stack.','Trade, dialogue, leave/return, save/reload and fresh boxing branch need live checks.','No game launch, save edit, manual fact write, framework change or public release.'],'pins':{str(p.relative_to(W)):sha(p) for p in list(H.glob('*.*'))+[C/'build_01.json',C/'tests_01.json',C/'deployment_tests_01.json',C/'install_manifest_01.json',W/'recovery/fred_scene_fs1_01/receipt.json']}}
p=C/'assessment_01.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'protected':out['protected_files_unchanged'],'saves':out['saved_files_unchanged'],'assessment_sha256':sha(p)}))
