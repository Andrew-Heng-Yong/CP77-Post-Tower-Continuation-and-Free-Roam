"""Record actual deployment, then update current policy/entry coverage notes."""
from common import *
import subprocess
H=ROOT/'prealpha/sidejobs_s29';C=H/'candidate_01';PS=Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
deployment={}
for action in ['Verify','ValidateRollback']:
    r=subprocess.run([str(PS),'-NoProfile','-File',str(H/'deploy_01.ps1'),'-Action',action],capture_output=True,text=True,timeout=90)
    assert r.returncode==0,r.stdout+r.stderr
    log=C/(action.lower()+'_01.log');assert not log.exists();log.write_text(r.stdout+r.stderr);deployment[action]=json.loads(r.stdout)
m=read(C/'install_manifest_01.json');receipt=Path(m['backup_root'])/'receipt.json';assert read(receipt)['status']=='S29_INSTALLED_LIVE_PENDING'
checks=read(H/'build/native_04/tests_01.json');comp=read(C/'compiled_check_02.json');fixtures=read(C/'deployment_tests_01.json');p=read(H/'prepared_04/prepared.json')
assessment=dict(status='S29_INSTALLED_VERIFIED_LIVE_PENDING',selected_entry_coverage={'gigs':80,'side_jobs':78,'total':158,'new_journals':18,'new_native_job_owners':16,'new_phone_boots':7},files=m['files'],native_resources=194,native_offline_checks=checks['checks'],compiled_preservation=comp,full_scc_sources=93,compiled_sha256=m['compiled_sha256'],installer_actions=fixtures['count'],deployment=deployment,protected_files=len(m['protected']),save_files_unchanged=sum(x['kind']=='save' for x in m['protected']),manifest_sha256=sha(C/'install_manifest_01.json'),receipt_sha256=sha(receipt),source_pins=p['source_pins'],game_launches=0,save_edits=0,manual_fact_edits=0,framework_edits=0,public_release_changes=0,scope='Original native beginnings, native follow-ups, scoped Venus/Delamain/Corrosion branches, native phone handlers, Nix/Pepe service handoffs and Johnny voice-only presentation.',limitations=['Actual quest trees, calls, escrow, completion, rewards and reload remain live pending.','Existing active or finished baseline entries are not restarted. Unsupported unfinished progress is preserved and deferred.','HS1 retains 140 detailed/18 root-only snapshot rows; its catalogue fingerprint and saved fields are unchanged. Current detailed freshness checks are additive S29 admission, not invented pre-ending history.'],rollback='Run prealpha/sidejobs_s29/deploy_01.ps1 -Action ValidateRollback then -Action Rollback with game closed; S29 first before HS2/HS1 or prior phone cleanup packages. File rollback is not saved-game rollback. Retain the pre-S29 test save.')
out=C/'assessment_01.json';assert not out.exists();out.write_text(json.dumps(assessment,indent=2)+'\n')
doc='''# S29: remaining 18 side-job entry points

Installed on 25 October 2026. All 18 remaining selected journal entries now have
native entry adapters: 16 quest owners, because the three Sinnerman jobs share
one native quest tree. Entry coverage is now 80/80 gigs and 78/78 side jobs.
This is implementation coverage; quest-tree gameplay verification is pending.

The combined 93-source SCC compile includes EquipmentEX and the installed CF1,
H6/HS2, H5 and FS1 fixes. Native readback checks passed (17,664 checks), as did
archive packing/load order and 14 real installer fixture actions. The package
adds one archive, its XL and one runtime script, and adds a read-only method to
the existing snapshot script. Existing saved fields and snapshot catalogue
fingerprint are unchanged. No game launch, save edit or manual quest-fact edit
was performed. Evidence: [assessment](../prealpha/sidejobs_s29/candidate_01/assessment_01.json).

## Test from the retained post-Tower save

Cold-start the game and load the working save from before S29 installation.
Let normal setup finish. There is no need to replay the ending. Complete the
parent job normally, wait its original time, and check the call/message and
next journal entry. Use a new manual slot at a checkpoint, reload it, and check
that progress continues without a duplicate call, reward, item transfer or owner.

Already completed/failed jobs remain preserved. Jobs active in the accepted
history baseline are not restarted. Unsupported unfinished states defer. A
missing entry can therefore mean an unmet native prerequisite or protected
existing progress; it is not automatically a broken follow-up.

| Entries | Native route to exercise |
| --- | --- |
| Venus in Furs | Earned Meredith outcome → original invitation and No-Tell encounter; no replay of The Pickup rewards. |
| These Boots Are Made for Walkin’ | Nomad route → original car messages, encounter and outcome. |
| Freedom | Original story/race gates, messages, vehicle investigation and resolution. |
| Sweet Dreams | Stefan encounter → original payment, inventory escrow and recovery; check exact belongings after recovery and reload. |
| Nitro (Youth Energy) | Original world trigger/prerequisite → robot sequence, control return and reward. |
| Where Eagles Dare | Original race/vehicle gates → Claire messages and CrystalCoat route. |
| Raymond Chandler Evening | Heroes prerequisite → Pepe encounter, investigation and return; confirm bar service returns. |
| Every Breath You Take | Earned Us Cracks outcome → native delay, Blue Moon call and encounter. |
| Small Man, Big Mouth | Streetkid/Heroes route → Kirk call, meeting and encounter. |
| KOLD MIRAGE | Original freezer encounter → Nix handoff and recovery outcome; check his service returns. |
| Killing In The Name | Original concert/alternate native branches → messages and investigation. |
| Sinnerman → There Is A Light That Never Goes Out → They Won’t Go When I Go | Follow the original choices, delays and Rachel calls through one native owner. Native refusal/failure branches still apply. |
| Don’t Lose Your Mind | Completed Epistrophy → original messages and Delamain sequel; no replay of cab retrieval or Epistrophy payout. |
| This Corrosion | Earned component/recipe breadcrumb → original Yoko route; no forced Canto equipment. |
| One Way or Another | Roads to Redemption outcome → original Nele follow-up. |
| Corpo of the Month | Treating Symptoms outcome → original follow-up reward/pickup branch. |

Johnny's existing voice-only policy is retained. Check for visible independent
props as well as dialogue, objectives, calls and completion. Native actors and
actor IDs remain present for dialogue and scene logic.

Read-only CET status:

```lua
print(Game.GetScriptableSystemsContainer():Get(CName.new("PTFR.SideJobsS29.SideJobsS29")):Status())
print(Game.GetScriptableSystemsContainer():Get(CName.new("PTFR.SideJobsS29.SideJobsS29")):Inspect("sq025b_delamain_insurgence"))
```

`Issued` means the owner was claimed, not that its quest completed. `Entered=0`
after issuance can mean the original parent gate/timer is still waiting. The
fresh-admission diagnostic becomes false after an owner is issued by design.
For a missing follow-up, record the parent/last objective, chosen outcome,
elapsed in-game time, save/reload point and the relevant Inspect output. Keep
the CET gamelog before the next launch.

## Recovery

With the game closed, run `prealpha/sidejobs_s29/deploy_01.ps1 -Action
ValidateRollback`, then `-Action Rollback`. Backup: `recovery/sidejobs_s29_01`.
Roll back S29 before HS2/HS1 or older phone-support packages. File rollback does
not undo quest progress saved during testing; retain the pre-S29 save.

Final native build: `build/native_04`; runtime: `runtime_06`; compile:
`candidate_01/compile_04`. Earlier workspace candidates were corrected before
installation (serialization references, compiler annotation/imports, Delamain
idle names, one injection-ID collision and load-order comparison). No failed
candidate was installed. Final inputs/proofs are pinned; use successors.
'''
path=ROOT/'docs/sidejobs_s29_playtest.md';assert not path.exists();path.write_text(doc,encoding='utf-8')
pointer=ROOT/'research/gig_restoration/lore_whitelist_current.json';d=read(pointer)
d['status']='ALL_SELECTED_ENTRY_POINTS_INSTALLED_S29_QUEST_TREE_LIVE_PENDING'
d['entry_coverage_s29']={'status':assessment['status'],'gigs':80,'side_jobs':78,'total':158,'evidence':out.relative_to(ROOT).as_posix(),'generic_resume_implemented':False,'live_quest_tree_verified':False}
pointer.write_text(json.dumps(d,indent=2)+'\n')
note='''Latest2026-10-25 S29 REMAINING18 SIDEJOB ENTRY POINTS INSTALLED; LIVE PENDING:
USER requests remaining18 then tests follow-up quest trees. Added16native job
owners/18journals (3Sinnerman oneowner),7phoneboots,194resources. Coverage80/80
gigs+78/78sidejobs=158/158ENTRYIMPLEMENTATIONS, NOTgameplay/resumeproof. Full
native delays/AND-OR gates/choices/rewards/escrow retained. ScopedVenus excludes
Pickup money/corpse/cat branches; Delamain starts afterEpistrophy with original
sequel; Corrosion breadcrumb excludes equippedCanto reactions. Corpo actual
wst_ep1_02; OneWay parentSTS_EP1_07. Nix/Pepe wait actual service release;
6newphonecontacts+sharedS22Delamain claim, currentS27cleanup extended. Private
Johnny presentation retains actors/IDs/voice, strips own visualevents/props,
mutes ownworkspots and splits sharedbinding; no official-resource overrides.
Fresh-only2observations+native recheck; existingIssuedneverreset. BaselineActive/
Succeeded/Failed denied; unsupportedunfinishedDEFER, no restart. HS1catalogue
140detailed/18rootonly andfingerprint/savedfieldsunchanged; one readonlyFreshS29
method added. 4files:3add(archive/XL/REDS),1replaceSnapshotStateHS1. Combined93
sourceSCCinclEquipmentEX PASS;17664nativechecks/14installeractionsPASS.
13836othercompiledclasses andall13838existingsavedclassschemasunchanged.
Validate/Install/Verify/ValidateRollbackPASS;703protectedincl283savesunchanged.
No assistantlaunch/manualfacts/save/framework/publicreleasewrites. CF1,H6/HS2,
H5,FS1 preserved. Buildnative_04/runtime_06/compile_04 andproofsPINNED;successors.
Earlierfailedworkspacecandidates correctedbeforeinstall. Manifest
973B6786717643457B45206456FB4D84D462159394A7672B7129C6C9932D901A.
Assessmentprealpha/sidejobs_s29/candidate_01/assessment_01.json; docs/sidejobs_s29_playtest.md.
RollbackS29 FIRSTbeforeHS2/HS1/olderphonecleanup:prealpha/sidejobs_s29/deploy_01.ps1
-ActionValidateRollback/Rollback;recovery/sidejobs_s29_01. FileundoNOTsaveundo.
NEXTcoldloadpreS29postTowerfixture; normalprerequisites/calls/delays/followups,
nativechoices/rewards/inventoryescrow, newmanualslot/reload.LIVEPENDING.

'''
agents=ROOT/'AGENTS.md';s=agents.read_text(encoding='utf-8-sig');title='# AGENTS.md — Post Tower Free Roam (PTFR)\n\n';assert s.startswith(title);agents.write_text(title+note+s[len(title):],encoding='utf-8')
road=ROOT/'ROADMAP.md';s=road.read_text(encoding='utf-8-sig');i=s.index('\n')+1;road.write_text(s[:i]+'\n**25 October — S29 remaining 18 side-job entry points installed.**\nEntry coverage is now 80/80 gigs and 78/78 side jobs (158/158 selected entries).\nNative follow-up trees, rewards and save/reload are ready for user testing;\nimplementation coverage is not a live pass or generic unfinished-stage resume.\nSee [S29 test notes](docs/sidejobs_s29_playtest.md).\n'+s[i:],encoding='utf-8')
readme=ROOT/'README.md';s=readme.read_text(encoding='utf-8-sig');marker='[S28 side-job checklist](docs/sidejobs_s28_playtest.md).';assert marker in s;s=s.replace(marker,marker+'\nThe remaining 18 selected side-job entries are now installed in the local S29 test stack;\nfollow-up quest-tree testing is pending. See [S29 test notes](docs/sidejobs_s29_playtest.md).',1);readme.write_text(s,encoding='utf-8')
print(json.dumps(dict(status=assessment['status'],assessment=str(out),assessment_sha256=sha(out),deployment=deployment)))
