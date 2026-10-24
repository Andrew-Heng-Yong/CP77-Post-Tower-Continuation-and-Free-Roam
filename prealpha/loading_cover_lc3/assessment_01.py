from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
m=read(C/'install_manifest_01.json');G=Path(m['game_root']);R=Path(m['backup_root']);receipt=read(R/'receipt.json')
assert receipt['status']=='LC3_INSTALLED_LIVE_PENDING' and receipt['manifest_sha256']==sha(C/'install_manifest_01.json')
for f in m['files']:assert sha(G/f['target'])==f['after'] and sha(R/f['target'])==f['before']
for p in m['proofs']+m['protected']:assert sha(p['path'])==p['sha256']
inputs=read(C/'diagnosis_01/inputs.json')
for path,h in inputs['saves'].items():assert sha(path)==h
t=read(C/'tests_01.json');d=read(C/'deployment_tests_01.json');comp=read(C/'compile_01/result.json');native=read(C/'native_01.json')
assert t['status']=='PASS_LC3_COMPILED_NATIVE_FEEDBACK_NOT_LIVE' and d['status']=='PASS_REAL_INSTALLER_FIXTURES' and comp['status']=='PASS_FULL_SCC_NOT_LIVE'
assert d['manifest_sha256']==sha(C/'install_manifest_01.json')
pins=[p for p in H.iterdir() if p.is_file()]+[C/'tests_01.json',C/'deployment_tests_01.json',C/'compile_01/result.json',C/'native_01.json',C/'prepared_native_01.json',C/'diagnosis_01/assessment_01.json',C/'diagnosis_01/inputs.json',C/'install_manifest_01.json',R/'receipt.json',W/'docs/loading_cover_lc3.md']
r={'created_utc':datetime.now(timezone.utc).isoformat(),'status':'LC3_INSTALLED_VERIFIED_LIVE_PENDING','files':m['files'],'protected_unchanged':len(m['protected']),'save_files_unchanged':len(inputs['saves']),'compile_sources':comp['sources'],'compiled_sha256':comp['compiled_sha256'],'offline_checks':t['count'],'installer_actions':d['count'],'unchanged_archive_resources':native['unchanged_resources'],'exit_removed':True,'release_predicates_and_stability_duration_preserved':True,'source_cause':'CanPurchase->SafeActor rejects V in scene; published readiness starts player-acquiring native purchase scenes, watcher exits when readiness clears, next1s poll restarts. Premature/remote gameplay interaction competes with cover stability.','evidence_limit':'Old combined final-control predicate did not log its exact failing term; source mechanism matches1s alternation, live retest pending.','live_progress_observed':['SC1 crash point passed; normal shutdown','Body/Relic/other refunds completed and HP150','Housing/native handoff acknowledged','Final control gate alternated45times'],'pending':['Full startup release','No exit action on Esc/controller cancel','Local apartment world choices and purchase flow','Save/reload from new manual slot'],'game_launched_by_assistant':False,'save_edits':0,'manual_fact_writes':0,'framework_changes':0,'main_archive_changes':0,'deployment_actions':['Validate PASS','Install PASS','Verify PASS','ValidateRollback PASS'],'rollback':'LC3 first before SC1 or LC2; backup recovery/loading_cover_lc3_01; file undo not save undo','public_release_updated':False,'pins':{str(p.relative_to(W)):sha(p) for p in pins}}
with (C/'assessment_01.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({'status':r['status'],'files':len(m['files']),'protected':len(m['protected']),'saves':len(inputs['saves']),'assessment_sha256':sha(C/'assessment_01.json')}))
