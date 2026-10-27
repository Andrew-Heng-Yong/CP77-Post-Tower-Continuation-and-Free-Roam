"""Verify installed CC1 files, save preservation, and recovery receipt."""
from pathlib import Path
from hashlib import sha256
import json

H=Path(__file__).resolve().parent
W=H.parents[1]
C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
sha=lambda p:sha256(p.read_bytes()).hexdigest().upper()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
manifest=read(C/'install_manifest_01.json')
assert manifest['status']=='CC1_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED'
assert len(manifest['package_files'])==51 and manifest['changed_paths']==2
assert all(sha(G/r['path'])==r['after'] for r in manifest['package_files'])
old={r['path']:r['sha256'] for r in read(C/'save_baseline_01.json')['files']}
new={str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()}
assert old==new
receipt=read(W/'recovery/coaster_cutoff_cc1_01/receipt.json')
assert receipt['status']=='CC1_51_PATH_INSTALLED_LIVE_PENDING'
assert receipt['manifest_sha256']==sha(C/'install_manifest_01.json')
assert read(C/'verification_01.json')['status']=='PASS_TWO_CUTOFF_GUARDS_ONLY'
assert read(C/'compile_01/result.json')['status']=='PASS'
assert read(C/'winner_scan_01.json')['status']=='PASS_SINGLE_EXPECTED_PTFR_WINNER'
assert read(C/'deployment_tests_01.json')['status']=='PASS'
zip_proof=read(C/'zip_proof_01.json')
assert zip_proof['members']==51 and sha(Path(zip_proof['path']))==zip_proof['sha256']
result={'status':'CC1_INSTALLED_VERIFIED_LIVE_PENDING','installed_paths':51,'changed_paths':2,'archive_members':1185,'semantic_cutoff_guards':2,'compiled_redscript_sources':64,'deployment_fixture_actions':20,'interruption_rollbacks':5,'save_files_preserved':len(old),'manifest_sha256':sha(C/'install_manifest_01.json'),'unreleased_zip_sha256':zip_proof['sha256'],'rollback_receipt':str(W/'recovery/coaster_cutoff_cc1_01/receipt.json'),'rollback_ready':True,'game_launched_by_assistant':False,'save_writes':0,'public_release':False,'scope':'New post-q105 one-time Jean entry blocked; existing owner progress and repeatable ride unchanged. Live behavior pending.'}
out=C/'assessment_01.json'
assert not out.exists()
out.write_text(json.dumps(result,indent=2)+'\n')
Path(str(out)+'.sha256').write_text(sha(out)+'\n')
print(json.dumps(result))
