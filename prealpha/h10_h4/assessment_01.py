from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
m=read(C/'install_manifest_01.json');r=read(W/'recovery/h10_h4_01/receipt.json')
assert r['status']=='H4_INSTALLED_LIVE_PENDING'
for x in m['protected']+m['proofs']:assert sha(Path(x['path']))==x['sha256']
for x in m['files']:assert sha(Path(m['game_root'])/x['target'])==sha(C/'package'/x['target'])==x['after']
o={'status':'H4_INSTALLED_LIVE_PENDING','manifest_sha256':sha(C/'install_manifest_01.json'),'files':m['files'],'protected':len(m['protected']),'save_files':sum(x['kind']=='save' for x in m['protected']),'compiled_sha256':sha(C/'compile_01/cache/compiled.redscripts'),'offline_checks':read(C/'tests_01.json')['count'],'actual_installer_fixture_actions':read(C/'deployment_tests_01.json')['count'],'actual_deployment':['Validate PASS','Install PASS','Verify PASS','ValidateRollback PASS'],'live_evidence':'H3 icon appeared. Log repeatedly showed door=true entrance=true released=true nativeUI=true popup=false and high=1 tier=1 scene=true dialogue=false combat=false. No H10 confirmation request. SafeActor scene-membership term blocks CanPurchase. Other latent guard failures cannot be excluded until live retest.','change':'CanPurchase and its read-only status use PurchaseSafeActor, a copy of SafeActor with only IsEntityInScene removed. MigrationContext retains original SafeActor. The original Purchase, single-debit, receipt, access and saved-schema code is unchanged.','unchanged':['H3 purchase dialog and map pin','H2 private door/inside egress/Wilson lease','frameworks','world/quest archives','all save files'],'recovery':'FIRST prealpha/h10_h4/deploy_01.ps1 ValidateRollback/Rollback with recovery/h10_h4_01, THEN H3/H2/older overlapping housing packages. File rollback does not undo saves.','live_test':'pending new cold load; expect PurchaseBlockH3 eligible and H10 native Yes/No at apartment door. No automatic payment.','game_launched_by_assistant':False,'save_edits':0,'manual_runtime_fact_writes':0,'public_release_changed':False}
p=C/'assessment_01.json';assert not p.exists();p.write_text(json.dumps(o,indent=2)+'\n')
print(json.dumps({'assessment_sha256':sha(p),'manifest_sha256':o['manifest_sha256'],'protected':o['protected']}))
