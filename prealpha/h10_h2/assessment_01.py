from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
m=read(C/'install_manifest_01.json');g=Path(m['game_root']);receipt=read(W/'recovery/h10_h2_01/receipt.json')
assert receipt['status']=='H2_INSTALLED_LIVE_PENDING'
for f in m['files']:assert sha(g/f['target'])==sha(C/'package'/f['target'])==f['after']
for p in m['protected']+m['proofs']:assert sha(p['path'])==p['sha256']
for p,h in read(C/'diagnosis_01/inputs.json')['saves'].items():assert sha(p)==h
for p,v in read(W/'recovery/h10_h2_diagnosis_01/receipt.json').items():assert sha(p)==sha(v['backup'])==v['sha256']
log=(C/'diagnosis_01/logs/gamelog.log').read_text(encoding='utf-8-sig');assert '17:49:09' in log and 'All required setup checks passed' in log
t=read(C/'tests_02.json');d=read(C/'deployment_tests_01.json');assert d['status']=='PASS_REAL_INSTALLER_FIXTURES'
out={'status':'H2_INSTALLED_LIVE_PENDING','user_scope':'H10 purchase at entrance, unpaid private-entry lock, no unpaid home services; investigate missing Wilson.',
 'prior_lc3_live':'17:49:09 Ready, 42.5 simulation seconds; normal shutdown17:53:46. This passes the previous loading loop, not H2 live behavior.',
 'findings':{'h10':'Existing H1 intentionally preserved physical door access; unpaid record correctly denies services. Custom action lacked declared choice metadata, now uses native Pay metadata and proximity confirmation independent of automatic-door action exposure.',
 'wilson':'Both retained saves have QuestOwns1/Released1/Near0 and no serialized Issued/Entered. S23 reserved Wilson before native parent waits. Exact active native wait not decoded; live repair checks all flags and does not assume absent serialized facts are runtime zero.'},
 'changes':m['files'],'native_changes':{'private_resource':'towercontinued/sidejobs_s23/base_b/mq011.questphase','preserved_resources':33,'existing_node_ids_preserved':True,'existing_guard_native_child_reward_payloads_preserved':True,'saved_preparent_wait_preserved':True},
 'counts':{'offline_checks':t['count'],'installer_fixture_actions':d['count'],'protected_files':len(m['protected']),'unchanged_save_files':sum(x['kind']=='save' for x in m['protected'])},
 'full_compile':read(C/'compile_04/result.json')['compiled_sha256'],
 'native_archive':read(C/'native_02.json')['after'],'manifest_sha256':sha(C/'install_manifest_01.json'),
 'rollback':'prealpha/h10_h2/deploy_01.ps1 -Action ValidateRollback / Rollback; recovery/h10_h2_01 FIRST before LC3 or S23. File rollback does not undo saved door/quest/housing state.',
 'limits':['User cold-load/front-door cancel/payment/egress/save-reload and Wilson trade test pending.','Default unpaid approach opens the confirmation once; cancel rearms after leaving5m and returning.','Inside-side orientation uses native door forward and live/current-source-bound bed anchor; unknown geometry defers rather than trapping a player.'],
 'assistant_game_launch':False,'save_edits':0,'native_story_fact_writes':0,'public_release_changes':0,
 'final_proof_pins':{str(p):sha(p) for p in [C/'tests_02.json',C/'deployment_tests_01.json',C/'native_02.json',C/'anchor_01.json',C/'compile_04/result.json',W/'recovery/h10_h2_01/receipt.json',Path(__file__)]}}
p=C/'assessment_01.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'assessment_sha256':sha(p),'counts':out['counts']}))
