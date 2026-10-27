"""Verify installed SC3 and pin the final local evidence."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_02'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
manifest=C/'install_manifest_01.json';m=read(manifest)
assert sha(manifest)==Path(str(manifest)+'.sha256').read_text().strip()
g=Path(m['game_root']);backup=Path(m['backup_root'])
for r in m['package_files']:
 assert sha(g/r['path'])==r['after'] and sha(C/'package'/r['path'])==r['after'],r['path']
 if r['before']!=r['after']:
  assert sha(backup/'old'/r['path'])==r['before']
  assert not (g/(r['path']+'.PTFRSC3_STAGE')).exists()
for p in m['proofs']:assert sha(Path(p['path']))==p['sha256'],p['path']
runtime=read(H/'runtime_review/verification_01.json')
for p in runtime['pins']:assert sha(W/p['path'])==p['sha256']
native=read(H/'native_review/assessment_01.json')
for p in native['pins']:assert sha(H/'native_review'/p['path'])==p['sha256']
receipt=read(backup/'receipt.json')
assert receipt['status']=='SC3_51_PATH_INSTALLED_LIVE_PENDING' and receipt['manifest_sha256']==sha(manifest)
saves=read(C/'save_comparison_01.json');assert saves['status']=='PASS_ALL_SAVES_BYTE_IDENTICAL'
tests=read(C/'deployment_tests_01.json');assert tests['status']=='PASS' and tests['interruption_points']==5
zipproof=read(C/'zip_proof_01.json');assert sha(Path(zipproof['path']))==zipproof['sha256']
actions={}
for name,status in [('validate','READY'),('install','SC3_51_PATH_INSTALLED_LIVE_PENDING'),('verify','VERIFIED'),('validate_rollback','ROLLBACK_READY')]:
 actions[name]=read(C/('actual_'+name+'_01.json'));assert actions[name]['status']==status
paths=[manifest,C/'package_proof_01.json',C/'dependency_winners_01.json',C/'compile_01/result.json',C/'deployment_tests_01.json',
 C/'save_baseline_01.json',C/'save_comparison_01.json',C/'zip_proof_01.json',backup/'receipt.json',
 H/'native_review/assessment_01.json',H/'runtime_review/verification_01.json',W/'docs/skippy_ambient_sc3_20261026.md']
paths+=sorted(H.glob('*.py'))+sorted(H.glob('*.ps1'))
paths+=[C/('actual_'+n+'_01.json') for n in actions]
result={'status':'SC3_INSTALLED_VERIFIED_GAMEPLAY_PENDING','created_utc':datetime.now(timezone.utc).isoformat(),
 'cause':'SC1 treated ordinary native TurnOff as permanent owner termination; SC2 cannot admit the already-stopped save.',
 'selected_candidate':'candidate_02','rejected_candidate':'candidate_01 (native socket DeepCopy error; never installed)',
 'package':{'paths':51,'replacements':3,'archive_members':1185,'unchanged_archive_members':1184,
            'new_resource':'towercontinued/skippy_ambient_sc3/skippy_ambient_owner.questphase',
            'unchanged_other_files':48,'zip_sha256':zipproof['sha256']},
 'checks':{'native_payload_guards':74,'native_graphs':6,'native_nodes':68,'native_edges':73,
           'independent_lifecycle':runtime['checks'],'negative_controls':3,'compile_sources':64,
           'recorded_fixture_actions':tests['fixture_actions'],'interruption_points':5,'installed_hashes':51,
           'save_files_unchanged':saves['files'],'actual_actions':actions},
 'recovery':{'path':str(backup.relative_to(W)),'installer':'prealpha/skippy_ambient_sc3/deploy_02.ps1','order':'SC3 before SC2','save_undo':False},
 'limits':['Gameplay speech and hologram rendering remain unverified.','One-time Skippy story quest remains untested.','No user in-game test commands requested.'],
 'game_launches':0,'save_writes':0,'manual_fact_writes':0,'github_push':False,'public_release':False,
 'pins':[{'path':str(p.relative_to(W)),'sha256':sha(p)} for p in paths]}
out=C/'assessment_01.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
Path(str(out)+'.sha256').write_text(sha(out)+'\n')
print(json.dumps({'status':result['status'],'pins':len(paths),'save_files':saves['files'],'sha256':sha(out)}))
