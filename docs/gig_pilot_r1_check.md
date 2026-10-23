# Many Ways to Skin a Cat — first gig pilot

This is a **single started-gig continuation exception**, not a fresh start and
not a global less-strict mode. The default fresh-selected-only policy stays in
place for other jobs. Cold launch is required after installation.

Installed 2026-10-09: four additions, no replacements; installed hashes and
rollback preflight passed. The user subsequently reports the complete path
worked. Native journal success and reward/counter acknowledgements are logged;
independent reload, owner release and failure-branch evidence remains limited.

Use a **disposable copy of a completed-Tower save** matching the observed
`inside`/pre-computer stage. Keep a separate pre-test save. File rollback cannot
reverse saved quest, device, loot, counter or reward effects.

## Activate

After loading, wait about ten seconds. Run this CET command once:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.GigPilotR1.GigPilotR1"):Restore())
```

Close CET and other menus, holster weapons, leave combat, vehicles and workspots.
The command queues admission; it does not reset the gig or unlock any other job.
Journal preparation is four individually acknowledged writes. Interrupted or
changed preparation refuses replay; use the pre-test save rather than forcing
facts. Do not save during stage 1 preparation.

Read-only status/diagnostics:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.GigPilotR1.GigPilotR1"):Inspect())
```

Stage 3 and `started=1` mean the native owner acknowledged entry, **not proof
that every actor/device/reward works**. If admission refuses, send its output;
do not set native tier, start, finish, failure, Tower or request facts manually.

## First live test

1. Verify only Many Ways returns to the journal; track it manually. The other
   five visible started gigs must remain unavailable. Character profile stays
   implant-focused HP150/Body3/Relic closed; accepted R11 world work is unchanged.
2. Go to Revere Courier Services. Check location geometry, existing actor/death
   state and computer interaction. Do not expect previously dead guards to be
   resurrected or the already-injected worker shard to be duplicated.
3. Enter the facility; verify `inside` succeeds and authorization appears. Use
   the computer's **Personal Link**, not a cyberdeck/quickhack. Check the progress
   bar, disconnect, and van objective/mount interaction.
4. Deliver the van, dismount and finish the native cleanup. Expect the authored
   **text debrief fallback**, not a restored global fixer holocall system.
   Record payment/XP before and after. Native reward remains the sole payout.
5. On a separate disposable branch, test save/reload during stage 3 before
   delivery. Verify progress continues without another briefing, shard grant,
   start increment or payout. After success, save/reload and rerun `Restore()`;
   it must report the existing state and never restart/reward again.
6. If needed, use another pre-test disposable branch to test native van failure.
   Preserve that outcome; do not restart the failed gig. Do not intentionally
   destroy a vehicle on the successful test branch.

The logger records every two seconds, read-only, under the installed CET mod:
`bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigPilotR1/gig_pilot_r1_*.jsonl`.
It includes journal states, foreign `cvi02/get_to_the_van` control, counters,
pilot acknowledgements and player position. A log read/open error is not proof
of a successful native operation.

## Deliberate limits

- Exact observed local start/combat/counters/tiers and journal stage required.
  Completed, genuinely failed, advanced-stage, fresh, unknown or changed states
  are not reset to this stage.
- Existing owner location-prefab binding and native communities are kept behind
  opt-in. Native `Activate` entries are retained; no blanket `Reactivate`, actor
  cloning, forced PS reset, loot restoration or invulnerability is added.
- Computer, delivery, chase, failure and reward remain native. One authored
  cross-gig journal side effect is replaced with a transparent control relay;
  the unrelated Pacifica entry must remain unchanged.
- The killed global fixer loop is not restarted. Only this success can bridge
  the audited Watson counter from 3 to 4, once; no tier threshold is crossed.
  No final fixer reward or other completion is recounted.
- Offline compilation, graph comparison, mock models and installer fixture are
  evidence of those checks only. The observed path is now user-confirmed with
  logged native success. Exact cash/XP, native failure, owner release and an
  independent cold-reload trace remain unproven.

Recovery is only `tools/deploy_gig_pilot_r1.ps1 -Mode ValidateRollback`, then
`-Mode Rollback` with the game closed. It moves the four exact pilot files into
a recoverable audit folder, preserving logs and all other installed files.
Use the pre-test save to recover gameplay state; do not remove the archive while
continuing the modified test save.

## Broader 71-gig rollout: next capture

Completed on2026-10-09. Both native captures are stable with no errors/drift;
see `research/gig_restoration/rollout_r2/live_pair_summary_20261009.json`.
Do not repeat these capture instructions unless investigating a new state.

The user selected the broader whitelist. **Only a read-only audit collector is
newly installed**, not 71 restoration adapters. It reads 970 journal entries
and 1,447 facts from the native 71-gig catalogue. No quest, perk, inventory,
story fact or save is changed by this command. Completed/rewarded and genuinely
failed jobs must remain untouched; started jobs need a supported saved-stage
adapter rather than replaying normal initialization.

Cold launch the game to load `PTFR_GigAuditR2`. Load the matching pre-ending
baseline used for the earlier comparison. After loading settles, stand still,
open CET and run:

```lua
GetMod("PTFR_GigAuditR2").Capture()
```

Keep CET open and wait for **`[PTFR 71-GIG AUDIT] COMPLETE stable`** before
loading another save. Then load the current completed-Tower save and run the
same command once. Either world order is valid; native Tower markers identify
the world automatically. No manual label edits or saves are needed. If the
capture reports INVALID, pending journal changes or an abort, wait for loading
and changes to settle and retry that world.

Optional read-only progress:

```lua
print(GetMod("PTFR_GigAuditR2").Status())
```

After both complete captures, the game can be closed. Tell the agent they are
done; the logs are already on disk under the installed mod directory as
`gigs71_*.jsonl`. The analyzer classifies history only and admits zero gigs.
Source eligibility, casts, initialization hazards, stage preservation, native
rewards and exactly-once counters still require per-gig review before adapters
are installed. Do not manually change facts to make a classification pass.

R2 installation receipt: `research/gig_restoration/rollout_r2/audit_install_receipt.json`.
Two additions, zero replacements; 1,582 protected files unchanged and actual
installed hashes/rollback preflight PASS. R2 file recovery uses only
`tools/deploy_gig_audit_r2.ps1 -Mode ValidateRollback`, then `-Mode Rollback`
with the game closed. Recovery moves those two files into a recoverable audit
folder and leaves logs, G1 and all other installed files intact.

## Activity history and override foundation (R3)

Installed2026-10-09: three additions, zero replacements; 1,759 protected files
unchanged and three installed hashes/rollback preflight passed. This is a
**partial foundation, not full gig/side-job restoration or alpha readiness**.

Runtime observes both selected lists:71 gigs and57 side/minor jobs. It keeps
save-local journal states, optional/tracked flags, objective counters and native
facts, double-checks ordinary-world captures, then freezes the last clean recent
sample at the native point-of-no-return boundary. Old post-ending saves without
frozen history remain unknown. No post-cleanup snapshot is called pre-ending
history. Cutoff timing, actual save serialization, reload and performance are
live-unverified.

Read-only status/inspection after a cold launch:

```lua
print(GetMod("PTFR_ActivityStateR3").Status())
print(GetMod("PTFR_ActivityStateR3").Inspect("sts_wat_nid_02"))
```

Optional explicit pre-ending observation, changing only mod-owned history:

```lua
print(GetMod("PTFR_ActivityStateR3").CaptureBeforeEnding())
```

The runtime also observes ordinary pre-ending play automatically. A save made
after observation stores history with that save; no external Lua/JSON file is
gameplay authority. Mismatched catalogue or malformed history refuses.

The original R3 foundation accepted `fresh`, `resume`, `replay` and an explicit
`DISPOSABLE_SAVE` acknowledgement, but implemented only G1 exact-stage resume.
S1 below extends this with one fresh side-job adapter:

```lua
print(GetMod("PTFR_ActivityStateR3").Override("sts_wat_nid_02", "resume", "DISPOSABLE_SAVE"))
```

This skips missing historical baseline, not G1 native-stage/outcome/Tower guards.
It cannot replay completed Many Ways. Unsupported activities/modes refuse without
quest mutation. The original `RestoreSelected()` dispatched only G1; S1 adds
Only Pain when its additional pre-ending evidence qualifies. Observing128
activities is not128 implemented adapters.

The user intends the first combined ending alpha after gig AND side-job
restoration is ready. **Do not start that alpha yet.** No additional live
capture is needed now. Remaining work: fresh/continuation adapters, representative
side-job restoration, supported completed-content replay with reward/counter
handling, then the ending/save/reload test. Default automation still preserves
completed/rewarded/genuinely failed content; explicit supported replay is a
separate exception, never a global story/relationship/profile reset.

Evidence under `research/activity_state_r3/`:definition, compile result, tests,
deployment fixture and install receipt. The original three-file installer is
historical for the ActivityState file replaced by S1; use the scoped S1 installer
below for that revision. File rollback cannot undo saved history or native
quest effects. Native fact-source bindings for10 side jobs remain incomplete,
so their journal alone cannot declare freshness or safe restart.

## Only Pain side-job pilot (S1)

Installed2026-10-09T19:20:25Z with game closed: four additions and one backed-up
R3 dispatcher replacement;1,777 protected files unchanged. Actual five hashes
and recovery preflight pass. Both compilers/full EquipmentEx readback, exact
native graph deltas,26 guard mutants/47,270 abstract admission cases, getter-only
logger checks and mixed deployment/recovery fixture pass. These are offline
checks, not proof of actor spawn, dialogue, payment, cleanup or reload behavior.

Cold launch and load a **disposable post-Tower save**. Inspect first:

```lua
print(GetMod("PTFR_ActivityStateR3").Inspect("mq005_alley"))
```

Start its supported fresh encounter:

```lua
print(GetMod("PTFR_ActivityStateR3").Override("mq005_alley", "fresh", "DISPOSABLE_SAVE"))
```

Close CET/menus, holster and leave combat/vehicles/workspots. Reopen CET briefly
to inspect if necessary. `stage=3 started=1` acknowledges the native owner;
the quest journal itself may remain Inactive until approaching the encounter.
Follow its restored map marker in Vista del Rey. Check the three officers and
corpo, native dialogue/combat route, journal objectives and completed outcome.
Leave the alley after completion: native cleanup waits for distance/out-of-camera
gates; `ownerFinished=0` while standing nearby is not alone a failure. Use a
separate test save, then reload and inspect for preserved stage/outcomes and no
second owner/reward. Keep the original pre-test save intact.

If admission refuses, send `Inspect()` output. Six journal entries must all be
Inactive and seven native encounter/scene facts zero, alongside the original
q001/q005/q101 side-content unlocks and completed Tower markers. Terminal,
halfway, unavailable/unknown and old mod-owned outcomes are not reset. Do not
force facts. `resume` and `replay` remain unsupported for this side job.

The S1 logger writes getter-only snapshots every two seconds after its boot
gate is ready in a Tower world, including seven journal states, thirty facts,
position, errors, native completion/reward acknowledgements and owner release.
Logs are under the installed `PTFR_SideJobPilotS1` CET folder. It never activates
or changes quests; disk failure reports without changing gameplay.

Automatic restoration additionally requires certified frozen history AND a
pre-ending available POI/source-audited pristine encounter sample. S1 adds a
save-local boolean defaulting false in old saves; no schema/catalogue/fingerprint
change or invented retroactive freshness. Ending timing, serialization and
automatic dispatch remain live-unverified. This pilot is not full whitelist
restoration or readiness for the combined ending alpha.

Evidence: `research/side_job_pilot_s1/assessment.json`, `tests.json`,
`compile_result.json`, `deployment_tests.json`, `install_receipt.json`.
Use ONLY `tools/deploy_side_pilot_s1.ps1` for its five-file recovery. It restores
the backed-up R3 source and recoverably removes S1 additions, but cannot reverse
saved actor, quest, reward or history effects. Do not rerun old R3 predecessor
tests/installers or regenerate S1 over pinned installed evidence.

Update2026-10-09: USER screenshots and getter logs show the encounter, dialogue,
journal progression and completion; USER save/reload preserves done1,
rewardClaim/Ack1/1 and Succeeded quest/phase/talk. Exact cash/XP and alternate
routes were not independently checked. Nearby ownerFinished0 is not a failure:
native cleanup requires departing the encounter. Move several hundred metres
away next session and inspect; no fact resets or repeat override needed.

### Empty-page journal label (J1)

Installed2026-10-09T19:49:48Z with game closed. One new UI-only script corrects
the stock widget's sample "For Whom the Bell Tolls" title to localized "Journal"
when no quest is selected in completed post-Tower free roam. Native quest states,
tracking and selected titles are untouched. Both compilers with all installed
dependencies and scoped deployment/recovery checks pass; visual check pending.

Cold-launch once, open the empty active-jobs page and confirm "Journal" above
"[No job selected]". Select completed Only Pain and confirm its own title, then
close/reopen the journal. No CET command, quest reset or save migration required.
Use ONLY `tools/deploy_journal_label_j1.ps1` for recoverable file removal.
Evidence: `research/journal_label_j1/tests.json`, `compile_result.json`,
`deployment_tests.json`, `install_receipt.json`.

### Only Pain departure repair (S1.1)

LIVE update2026-10-10: USER Inspect and getter log confirm `stage=4`,
`ownerFinished=1`, waits1/1, deactivated1/1, joined1 and reward still1/1.
The cold-loaded existing waits adopted the repair. `entered=0` is normal here:
the saved cleanup phase began before that acknowledgement was added. No further
immediate test is required; save to a separate test slot before closing if
desired. Post-repair stage4 save/reload, visual actor absence, exact cash/XP and
alternate routes remain separate unverified checks. See
`research/side_job_cleanup_s1_1/live_result_20261010.json`.

Installed2026-10-10T14:51:31Z, game closed: three backed-up replacements of the
S1 archive, pilot script and getter logger;1,827 protected files unchanged.
J1 empty-page label now has USER-pass. Native release remained0 after departure
up to757m, so the earlier nearby-only explanation was insufficient.

S1.1 retains native distance/camera conditions and adds a guarded alternative
only for the tested completed, reward-acknowledged police-left route. Five
consecutive safe samples at least500 horizontal metres from the encounter arm
an owned departure flag. The native outside-trigger gate still applies; existing
deactivation actions and joined terminal path—not a forced status—must release
the owner. Rewards, quest objectives, spawn/combat and original save fields stay
unchanged. Additional getter fields expose the cleanup branches.

Cold-launch and load your **completed test save**, not the earlier untouched
one. Stay at least500m from the alley, close CET/menus, holster and stay out of
combat/vehicles/workspots for about10 seconds. Then run:

```lua
print(GetMod("PTFR_ActivityStateR3").Inspect("mq005_alley"))
```

Expected: `stage=4`, `ownerFinished=1`, reward1/1 unchanged. Native cleanup
acknowledgements should complete too. `entered=0` alone on an old active save
does not prove cleanup never started: the new entry instrumentation was absent
when that saved phase began. If still stage3, send the complete output including
`cleanupS1.1 departure`, `waits`, `deactivated` and `joined`. Active saved waits
adopting changed definitions is still live-unproven. **Do not rerun fresh override,
replay, or force any facts.** Keep the pre-fix completed save intact.

Evidence/recovery: `research/side_job_cleanup_s1_1/assessment.json`, tests,
compile/manifest/fixture/installation receipts. Use ONLY
`tools/deploy_side_cleanup_s1_1.ps1` for these three paths. Original S1 five-file
recovery is now historical for the replaced files. File rollback does not undo
saved native cleanup or owned acknowledgements; do not overwrite pinned old
S1 evidence by rerunning its build/compile/test main.
