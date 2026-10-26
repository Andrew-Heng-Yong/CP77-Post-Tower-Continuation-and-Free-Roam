from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
m=read(C/'install_manifest_01.json');r=read(W/'recovery/judy_dennis_jd1_01/receipt.json')
assert r['status']=='JD1_INSTALLED_LIVE_PENDING'
for row in m['files']:assert sha(Path(m['game_root'])/row['target'])==row['after']
for row in m['protected']:assert sha(Path(row['path']))==row['sha256']
a={'status':'JD1_INSTALLED_VERIFIED_LIVE_PENDING','files':m['files'],'compiled_sha256':m['compiled_sha256'],'native_component_sha256':sha(H/'native_02/component.json'),'native_tests':read(H/'native_02/tests_02.json')['count'],'installer_tests':read(C/'deployment_tests_01.json')['count'],'protected_unchanged':len(m['protected']),'saves_unchanged':sum(x['kind']=='save' for x in m['protected']),'manifest_sha256':sha(C/'install_manifest_01.json'),'game_launched':False,'save_edits':0,'manual_fact_writes':0,'live_tests':'pending','user_approved_install':True,'lipsync_installed':False}
p=C/'assessment_01.json';assert not p.exists();p.write_text(json.dumps(a,indent=2)+'\n',encoding='utf-8')
entry='''Latest2026-10-25 JD1 JUDY DOOR / DENNIS PHONE INSTALLED; LIVE PENDING:
USER reports upstairsJudydoorunlocked; Dennisnoincomingcall,proceededbytalking.
Explicitapproval installtwofixes. HousinghadnostrictJudyprivateentrancelock.
JD1 exactupstairsdooronly; outsideclose/lock, ownlockreleaseforinsideegress;
nativeinterioranchor+pathboundtocurrentworld; unknowndefer,thresholdmargin.
Visualopen suppression synchronizesPSfirsttoavoidrecursiveUpdateDeviceState.
MQ038 originalcallsretainedbutDenniscontroller/cleanupmissing. Log19:49:20
start_activate1withoutstart. Newonce-onlynative106handler; freshMQ038wait1003
requiresreceipt. ExistingPTFR-ownedunfinishedresume permitsqueuedrequest,
noquestrestart/factclear. NativeMQ038holdsmanualinterruptuntilcall_out: existing
listenerbootstrapmustnotwaitonthatflag; setup/resetguardsretained. Original
cleanup439/303 appendedbehindownreceipt; old69nodepayloads unchanged.
Fourfiles: HousingPurchaseoneTickline replacement; addJudyDoorJD1+archive+XL.
Threearchiveresources:1newphoneboot,2PTFRoverrides; noofficialoverrides.
Full94sourceSCCinclEquipmentEXPASS; 27803offlinechecks+14installeractionsPASS.
Install/Verify/ValidateRollbackPASS;721protectedincl289savesunchanged.
Noassistantlaunch/manualfacts/framework/lipsync/publicreleasewrites.
Finalnative_02/tests_02,compile_04; sources/proofsPINNED,usesuccessors.
ManifestB9B0A332D3177FD80E40AF684AE369F43412CD24AF4330302AFD62B5D286D3C6.
Assessmentprealpha/judy_dennis_jd1/candidate_01/assessment_01.json SHA
ASSESSMENT_SHA.
RollbackJD1FIRSTbeforeS29/S23/H5:prealpha/judy_dennis_jd1/deploy_01.ps1
-ActionValidateRollback/Rollback;recovery/judy_dennis_jd1_01.
FileundoNOTsaveundo; retainpreJD1saveforremovingnewphoneowner.
NEXTcoldloadprivateJudylock/insideexit/reload; Dennisnextnativecall/end/interrupt,
earlierfixtureforalready-passedcalls. AllLIVEPENDING. docs/judy_dennis_jd1.md.
USER nowrequests anotherbroadmissingdependency auditofrestoredsidejobs/quests.

'''.replace('ASSESSMENT_SHA',sha(p))
agents=W/'AGENTS.md';s=agents.read_text(encoding='utf-8-sig');title='# AGENTS.md — Post Tower Free Roam (PTFR)\n\n';assert s.startswith(title);agents.write_text(title+entry+s[len(title):],encoding='utf-8')
print(json.dumps({'status':a['status'],'assessment_sha256':sha(p)}))
