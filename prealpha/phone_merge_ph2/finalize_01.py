import sys,datetime
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1];sys.path.insert(0,str(W/'prealpha/phone_support_ph1'))
from model import *
C=H/'candidate_01';m=read(C/'install_manifest_01.json');g=Path(m['game_root'])
assert read(C/'deployment_tests_01.json')['status']=='PASS_DEPLOYMENT_FIXTURES'
assert read(C/'preservation_after_01.json')['status']=='PASS_SAVE_EXTERNAL_AND_MANAGED_PRESERVATION'
assert read(W/'recovery/phone_merge_ph2_01/receipt.json')['status']=='INSTALLED_VERIFIED'
assert all(sha(g/r['path'])==r['after'] for r in m['package_files'])
logs=W/'diagnostics/organitopia_ph1_failure_20261029_01'
evidence={'status':'PH1_MARK_REGISTRATION_FAILURE_CONFIRMED','archiveXL_failures_local':['2026-10-29 17:20:50','2026-10-29 17:23:20'],'call_requests_local':['2026-10-29 17:22:21','2026-10-29 17:25:54'],'mark_acknowledgements_recorded_after_request':False,'cause':'Generated node ID 40560 collides with existing Watson map1 registration; ArchiveXL skips Mark listener.','files':{f.name:sha(f) for f in logs.iterdir() if f.is_file()}}
(logs/'assessment_01.json').write_text(json.dumps(evidence,indent=2)+'\n')
out={'status':'PH2_INSTALLED_VERIFIED_LIVE_PENDING','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'change':'Byte-identical Mark listener alias and one XL path substitution','old_id':40560,'new_id':61197,'root_registrations_checked':824,'old_archive_members_preserved':1572,'candidate_members':1573,'archive_sha256':m['source_archive_sha256'],'xl_sha256':m['source_xl_sha256'],'package_paths':51,'replaced_paths':m['changed_paths'],'deployment_fixtures':4,'interrupted_rollbacks':3,'preservation':read(C/'preservation_after_01.json'),'zip':read(C/'zip_proof_01.json'),'rollback':'READY; PH2 first before PH1. File rollback is not save undo.','game_launches':0,'save_writes':0,'direct_native_fact_writes':0,'script_changes':0,'live_call_and_door_result':'UNVERIFIED','beta_distribution_changed':False}
(C/'installed_assessment_01.json').write_text(json.dumps(out,indent=2)+'\n')
files=['verification_01.json','semantic_verification_01.json','registration_regression_01.json','deployment_tests_01.json','preservation_before_01.json','preservation_after_01.json','install_manifest_01.json','zip_proof_01.json','installed_assessment_01.json']
(C/'evidence_hashes_01.json').write_text(json.dumps({f:sha(C/f) for f in files},indent=2)+'\n')
section='''Latest 2026-10-29 PH1 LIVE FAILURE; PH2 MARK REGISTRATION CORRECTION INSTALLED:
User retried Organitopia, no Mark call/door. Latest ArchiveXL logs17:20:50 and
17:23:20 reject Mark PH1 phase: generated ID40560 collides with existing U9
sts_wat_kab_101_map1. Five other PH1 listeners merged. Requests17:22:21/17:25:54
remain without logged Mark ack. Prior validation missed generated registration
IDs despite depot collision scan. PH2 adds byte-identical alias at
towercontinued/phone_merge_ph2/mark_bana_listener.questphase, generated ID61197;
one XL path substitution only. Old Mark resource retained unregistered; all1572
PH1 payloads preserved,1573 total. Six phone registration IDs unique across824
current EP1 root additions+5native IDs; independent CRCs reproduce oldcollision.
Fresh134archive aliasdepot/fullreadback+51pathZIP PASS. No nativecontroller,
cleanup, receipt/admission, quest or REDS logic changes; no newcompile claim.
Four deployment fixtures incl3interruptions PASS. Actual gameclosed Validate/
Install/Verify/ValidateRollback PASS;51managedhashes verified,307savefiles and49
LizziesBDs files unchanged around PH2 deployment. No game launch/save/nativefact
edit/publicrelease/Gitpush; beta dist unchanged. Call/door LIVEUNVERIFIED.
Rollback PH2 FIRST beforePH1 via prealpha/phone_merge_ph2/deploy_01.ps1 -Action
ValidateRollback then Rollback gameclosed; recovery/phone_merge_ph2_01.
Fileundo NOTsaveundo. Evidence candidate_01/installed_assessment_01.json,
diagnostics/organitopia_ph1_failure_20261029_01 and docs/phone_merge_ph2_20261029.md.

'''
p=W/'AGENTS.md';t=p.read_text(encoding='utf-8-sig');at=t.find('\n\n')
assert 'PH2 MARK REGISTRATION CORRECTION INSTALLED' not in t
p.write_text(t[:at+2]+section+t[at+2:],encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k in ('status','archive_sha256','xl_sha256','old_id','new_id')}))
