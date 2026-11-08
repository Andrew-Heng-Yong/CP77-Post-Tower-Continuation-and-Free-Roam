from model import *
import datetime
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_03'
m=read(C/'install_manifest_01.json');g=Path(m['game_root'])
assert read(C/'preservation_after_01.json')['status']=='PASS_SAVE_EXTERNAL_AND_MANAGED_PRESERVATION'
assert read(C/'deployment_tests_01.json')['status']=='PASS_DEPLOYMENT_FIXTURES'
assert read(W/'recovery/phone_support_ph1_01/receipt.json')['status']=='INSTALLED_VERIFIED'
assert all(sha(g/r['path'])==r['after'] for r in m['package_files'])
out={'status':'PH1_INSTALLED_VERIFIED_LIVE_PENDING','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':'candidate_03','contacts':['mark_bana','janet','karl_ginsky','pedro_aimar','nix','victor'],'managed_paths':51,'replaced_files':2,'baseline_archive_members':1566,'candidate_archive_members':1572,'old_members_byte_preserved':1562,'old_resources_changed':4,'new_resources':6,'semantic_checks':read(C/'semantic_verification_01.json')['checks'],'admission_cases':read(C/'state_tests_01.json')['checks'],'deployment_fixture_cases':4,'interruption_rollbacks':3,'archives_scanned':134,'archive_sha256':m['source_archive_sha256'],'xl_sha256':m['source_xl_sha256'],'zip':read(C/'zip_proof_01.json'),'preservation':read(C/'preservation_after_01.json'),'rollback':'Verified ready; run PH1 rollback FIRST, before LR2. File rollback is not save undo.','runtime_limitations':['No game launched or gameplay pass claimed.','Original native retirement ancestry verified; no public live phase-liveness query used.','Repair preserves queued requests and allows the native controller to acknowledge them; exact already-stalled scene resumption remains live-unverified.','MQ018/MQ028 source-only suspects remain unchanged.'],'script_changes':0,'compilation':'No REDS change; no new compilation claimed. Current managed script bytes preserved.','game_launches':0,'save_writes':0,'direct_native_fact_writes':0,'public_release':False}
(C/'installed_assessment_01.json').write_text(json.dumps(out,indent=2)+'\n')
proofs=['build_01.json','semantic_verification_01.json','state_tests_01.json','verification_01.json','ancestry_proof_01.json','cr1_controls_01.json','deployment_tests_01.json','preservation_before_01.json','preservation_after_01.json','install_manifest_01.json','zip_proof_01.json','installed_assessment_01.json']
(C/'evidence_hashes_01.json').write_text(json.dumps({p:sha(C/p) for p in proofs},indent=2)+'\n')
agents=W/'AGENTS.md';old=agents.read_text(encoding='utf-8-sig')
section='''Latest 2026-10-29 PH1 SIX PHONE CONTROLLERS INSTALLED; LIVE PENDING:
User explicitly authorized implementation+installation, superseding LATER hold.
Selected prealpha/phone_support_ph1/candidate_03: Mark+Janet (Spy), Karl (Nasty
Hangover), Pedro (Desperate Measures), conditional Nix/Viktor service calls.
Six persistent native initializer copies, owned Ready/Issued, scoped U9 fresh
Permit or active receipts; service Ready/Enabled/OwnerActive/Excluded gates.
Completed Tower journal plus existing postTower/support/reset guards; no blanket
interruption gate. Native initializer retirement ancestry checked against fresh
native providers, including normal base termination, EP1 cut BEFORE killed receipt,
and alternate q307 infrastructure cut containing both initializers. No public live
owner query. Existing serialized PH1 claim prevents reissue; no native fact resets.
Matching contact cleanup joins current shared reset chain; inline EP1 loops rewired
and preserved. Three U9 entries add only listener-ready pause before native parent;
executing descendants untouched. Six new resources+four edited old,1572 total;
1562 old members byte-identical. All29 other CR1 donors exact; existing cleanup
nodes/nested graphs preserved with only terminal routing into six owned branches.
76 serialized checks,206 condition cases,134archive native/newdepot checks, full
readback and51path ZIP PASS. Four deployment fixtures incl3interruptions PASS.
Actual gameclosed Validate/Install/Verify/ValidateRollback PASS; two managed files
replaced; all51hashes verified,307save files and49LizziesBDs files unchanged.
No REDS changes/newcompile claim, game launch/save/directnativefact edit/public
release/Gitpush. MQ018/MQ028 suspects unchanged. Beta dist unchanged.
Queued-call/door/reload gameplay LIVE UNVERIFIED; no additional test request.
Rollback PH1 FIRST gameclosed via prealpha/phone_support_ph1/deploy_01.ps1 -Action
ValidateRollback then Rollback; recovery/phone_support_ph1_01. File undo NOT save undo.
Evidence candidate_03/installed_assessment_01.json; docs/phone_support_ph1_20261029.md.

'''
if 'PH1 SIX PHONE CONTROLLERS INSTALLED' not in old:
 pos=old.find('\n\n');agents.write_text(old[:pos+2]+section+old[pos+2:],encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k in ['status','archive_sha256','xl_sha256','semantic_checks','admission_cases']}))
