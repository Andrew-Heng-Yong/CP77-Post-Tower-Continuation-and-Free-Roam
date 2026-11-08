import sys,datetime
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1];sys.path.insert(0,str(W/'prealpha/phone_support_ph1'))
from model import *
C=H/'candidate_01';D=W/'diagnostics/phone_expansion_ph3_20261029_01';m=read(C/'install_manifest_01.json');g=Path(m['game_root'])
assert read(C/'preservation_after_01.json')['status']=='PASS_SAVE_EXTERNAL_AND_MANAGED_PRESERVATION'
assert read(C/'deployment_tests_01.json')['status']=='PASS_DEPLOYMENT_FIXTURES'
assert read(W/'recovery/phone_studios_ph3_01/receipt.json')['status']=='INSTALLED_VERIFIED'
assert all(sha(g/r['path'])==r['after'] for r in m['package_files'])
census=read(D/'ownership_census_01.json');assert census['phase_resources']==997 and census['prefab_bindings']==747 and not census['studio_owners'] and not census['numeric_refs']
assessment={'status':'SHARED_NATIVE_PHONE_STUDIO_SUPPORT_GAP_CONFIRMED','user_report':'Ana Friedman call missing after Russian boss; user requests fixes for similar calls.','log_evidence':{'mark_start_ack':'17:47:52','mark_balanced_later_call':'17:55:12 start_count2->3;17:55:20 end_count2->3','boss_hologram_cleanup':'17:55:10','next_call_internal_name':'janet','janet_start_count_and_start':'17:55:51 0->1','global_setup_active':'17:55:51 0->1','janet_start_acknowledgement_recorded':False},'source_evidence':{'native_initializer_owns':['#holocalls_studio_ep1','#holocalls_studio'],'current_private_phase_census':997,'current_prefab_bindings':747,'current_studio_owners':0,'shared_native_base_variants':138,'shared_native_ep1_variants':36},'limitations':['Missing support is source-confirmed; exact live actor binding/scene node not directly captured.','End of captured events is not a measured wait duration.','WolvenKit 9.1 cannot fully decode the original studio sectors; no placement-level or rendered-geometry proof.'],'raw_log_hashes':{p.name:sha(p) for p in D.glob('*.log')}}
(D/'assessment_01.json').write_text(json.dumps(assessment,indent=2)+'\n')
out={'status':'PH3_SHARED_PHONE_STUDIOS_INSTALLED_VERIFIED_LIVE_PENDING','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'One native studio prefab owner shared by restored phone calls; no blanket quest/controller restart.','native_prefabs':read(C/'build_01.json')['prefabs'],'old_archive_members_preserved':1573,'candidate_members':1574,'archive_sha256':m['source_archive_sha256'],'xl_sha256':m['source_xl_sha256'],'new_root_id':22195,'root_registrations_checked':825,'serialized_checks':25,'admission_cases':30,'deployment_fixtures':4,'interruption_rollbacks':3,'archive_provider_scan':134,'preservation':read(C/'preservation_after_01.json'),'zip':read(C/'zip_proof_01.json'),'script_changes':0,'game_launches':0,'save_writes':0,'direct_native_fact_writes':0,'beta_distribution_changed':False,'live_call_result':'UNVERIFIED','rollback':'Ready; PH3 FIRST before PH2/PH1/LR2. File rollback is not save undo.'}
(C/'installed_assessment_01.json').write_text(json.dumps(out,indent=2)+'\n')
proofs=['build_01.json','semantic_verification_01.json','state_cases_01.json','verification_01.json','deployment_tests_01.json','preservation_before_01.json','preservation_after_01.json','install_manifest_01.json','zip_proof_01.json','installed_assessment_01.json']
(C/'evidence_hashes_01.json').write_text(json.dumps({p:sha(C/p) for p in proofs},indent=2)+'\n')
section='''Latest 2026-10-29 ANA CALL REPORT; PH3 SHARED PHONE STUDIOS INSTALLED:
User requests Ana Friedman post-Ribakov call fix and all similar phone bugs.
Latest logs show PH2 Mark ack17:47:52 and balanced calls afterboss;17:55:51
next native janet call start/count0->1 and setupactive1, no recorded startack.
Exact liveactor/node notcaptured; event cutoff is not measuredwaitduration.
Confirmed PH1 omitted native EP1 initializer ROOT PhasePrefabs (distinct from
initializer-node PhaseInstancePrefabs): #holocalls_studio_ep1 and #holocalls_studio.
Full997privatequestphase census/747root+nestedprefab bindings has0studioowners,
0numericrefs. PH3 owns exact two native prefabs at fullNodeRefs in one nested
persistent owner,19fact+Towerjournal guards,oneclaim; only ownClaimed/Entered/Ready
writes. No phoneidle/interruption guard, so pending activecalls can gain support.
Restores common studio support for restored base+EP1 calls, not unused story
controllers or arbitrary quest replay. Native descriptors:138base+36EP1variants,
Janet actor/workspot/camera/setup refs in EP1sector; fresh134archive8sources.
Original studiosectors WK9.1 DynamicBaseClass/worldNode decode limitation: no
sector edit/filter or fullplacement claim. Native exact prefabs referenced only.
825root injection IDs unique inclnew22195; all1573PH2resources byte-identical,
newstudioowner only=1574total. Same51paths; archive+XL only.25serializedchecks,
30admissioncases,fullreadback/134newdepot scan/51pathZIP and4deploymentfixtures
incl3interruptions PASS. Actual gameclosed Validate/Install/Verify/ValidateRollback
PASS;51managedhashes verified,307saves and49LizziesBDs files unchanged arounddeploy.
No REDS changes/newcompile claim, game launch/save/directnativefact edits,Gitpush,
publication or beta distchange. Actual Ana/video rendering/call/reload LIVEPENDING.
Rollback PH3 FIRST beforePH2 via prealpha/phone_studios_ph3/deploy_01.ps1 -Action
ValidateRollback then Rollback gameclosed; recovery/phone_studios_ph3_01.
Fileundo NOTsaveundo. Evidence candidate_01/installed_assessment_01.json,
diagnostics/phone_expansion_ph3_20261029_01 and docs/phone_studios_ph3_20261029.md.

'''
p=W/'AGENTS.md';t=p.read_text(encoding='utf-8-sig');at=t.find('\n\n');assert 'PH3 SHARED PHONE STUDIOS INSTALLED' not in t;p.write_text(t[:at+2]+section+t[at+2:],encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k in ('status','archive_sha256','xl_sha256','new_root_id')}))
