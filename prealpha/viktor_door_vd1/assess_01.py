"""Record the verified installation without claiming a live door test."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_02'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
m=read(C/'install_manifest_01.json');r=read(Path(m['backup_root'])/'receipt.json')
assert r['status']=='VD1_INSTALLED_LIVE_PENDING'
assert r['manifest_sha256']==sha(C/'install_manifest_01.json')
fixture=read(C/'deployment_tests_01.json');assert fixture['status']=='PASS' and fixture['cases']==6 and fixture['interrupted']==5
for stage in ('before','after'):
    v=read(C/f'save_comparison_{stage}_01.json')
    assert v['status']=='PASS_SAVE_NAMES_AND_BYTES_UNCHANGED' and v['files']==307 and v['managed_files_verified']==52
game=Path(m['game_root'])
for row in m['package_files']+m['compatibility_files']:assert sha(game/row['path'])==row['after']
verification=read(C/'verification_01.json');assert all(x['pass'] for x in verification['checks'])
zipproof=read(C/'zip_proof_01.json');assert sha(Path(zipproof['path']))==zipproof['sha256']
pins=[C/'build_01.json',C/'verification_01.json',C/'compile_inputs_01.json',C/'deployment_tests_01.json',C/'install_manifest_01.json',C/'zip_proof_01.json',C/'save_comparison_before_01.json',C/'save_comparison_after_01.json',H/'native_review_03/providers.json',H/'deploy_01.ps1',Path(m['backup_root'])/'receipt.json']
assessment={'status':'VD1_INSTALLED_VERIFIED_LIVE_PENDING','date':'2026-10-29','scope':'Exact downstairs Viktor clinic door after Tower completion and setup','full_package_files':51,'managed_paths_verified':52,'changed_production_paths':[x['path'] for x in m['package_files'] if x['before']!=x['after']],'archive_members':1564,'unchanged_prior_members':1563,'serialized_checks':len(verification['checks']),'guard_combinations':verification['guard_combinations'],'compile_sources':112,'compile_mode':'Reuse after exact current/compiled source and compiled-cache hash comparisons','deployment_cases':6,'interrupted_rollback_cases':5,'deployment_fixture_actions':sum(len(x['actions']) for x in fixture['results']),'actual_validate':'PASS','actual_install':'PASS','actual_verify':'PASS','actual_validate_rollback':'PASS','save_files_unchanged':307,'archive_sha256':sha(game/'archive/pc/mod/zzzz_PTFR_Combined.archive'),'xl_sha256':sha(game/'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'),'zip_sha256':zipproof['sha256'],'rollback':m['backup_root'],'runtime_live_result':'UNVERIFIED','open_beta':'ON_HOLD','game_launched':False,'save_writes':0,'native_fact_writes_by_tools':0,'public_release':False,'pins':[{'path':str(p.relative_to(W)),'sha256':sha(p)} for p in pins]}
path=C/'assessment_01.json';assert not path.exists()
path.write_text(json.dumps(assessment,indent=2)+'\n')
(C/'assessment_01.json.sha256').write_text(sha(path)+'\n')
print(json.dumps({k:assessment[k] for k in ('status','archive_sha256','xl_sha256','zip_sha256','save_files_unchanged','deployment_fixture_actions')}))
