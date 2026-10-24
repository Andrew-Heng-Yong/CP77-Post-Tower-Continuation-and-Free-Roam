from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_04'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
m=read(C/'install_manifest_01.json');G=Path(m['game_root']);R=Path(m['backup_root'])
receipt=read(R/'receipt.json');assert receipt['status']=='LC1_INSTALLED_LIVE_PENDING'
assert receipt['manifest_sha256']==sha(C/'install_manifest_01.json')
for f in m['files']:
 assert sha(G/f['target'])==f['after']
 if f['before']:assert sha(R/f['target'])==f['before']
for item in m['protected']+m['proofs']:assert sha(item['path'])==item['sha256']
tests=read(C/'tests_01.json');deploy=read(C/'deployment_tests_01.json');compile=read(C/'compile_02/result.json');native=read(H/'candidate_02/native_01.json')
assert tests['status']=='PASS_OFFLINE_COMPILED_NATIVE_NOT_LIVE' and deploy['status']=='PASS_REAL_INSTALLER_FIXTURES' and compile['status']=='PASS_FULL_SCC_NOT_LIVE'
assert deploy['manifest_sha256']==sha(C/'install_manifest_01.json')
pins=[p for p in H.iterdir() if p.is_file()]+[C/'tests_01.json',C/'deployment_tests_01.json',C/'compile_02/result.json',C/'install_manifest_01.json',R/'receipt.json',H/'candidate_02/native_01.json',W/'docs/loading_cover_lc1.md']
report={'schema':1,'created_utc':datetime.now(timezone.utc).isoformat(),'status':'LC1_INSTALLED_VERIFIED_LIVE_PENDING','files':m['files'],'protected_unchanged':len(m['protected']),'save_files_unchanged':sum(p['kind']=='save' for p in m['protected']),'compile_sources':compile['sources'],'compiled_sha256':compile['compiled_sha256'],'offline_checks':tests['count'],'installer_fixture_actions':deploy['count'],'unchanged_archive_resources':native['unchanged_resources'],'current_lighting_preserved':native['preserved_lighting_sha256'],'native_splice':native['added_edges'],'deployment_actions':['Validate PASS','Install PASS','Verify PASS','ValidateRollback PASS'],'game_launched_by_assistant':False,'save_edits':0,'manual_fact_writes':0,'framework_changes':0,'speed_claim':'Refund opportunity spacing 1s -> 0.25s; 27-rank scheduling estimate saves20.25s, no measured total','live_checks_pending':['Native notification blocks all gameplay input without pausing setup','No first-frame gameplay exposure at native handoff or reload','Esc returns to menu without unlock','Profile/housing/world and quest classification complete before release','Completed weapon/combat/vehicle and death/save reload does not replay transactions','Measured end-to-end duration and native callbacks'],'rollback':'loading_cover_lc1/deploy_01.ps1 ValidateRollback then Rollback, before HS1; restores main2FC245 current lighting, not obsolete crashing archive','public_release_updated':False,'pins':{str(p.relative_to(W)):sha(p) for p in pins}}
out=C/'assessment_01.json'
with out.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'status':report['status'],'files':len(m['files']),'protected':len(m['protected']),'saves':report['save_files_unchanged'],'assessment_sha256':sha(out)}))
