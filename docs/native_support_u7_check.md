# U7 — Jeopardy native support and completion test

## Latest result: Life's Work completion and credit survived reload

The user reports identical results before and after reload: `root=3`,
`creditDone=1`, `Heywood=2`, `fault=0`. Completion and fixer-credit persistence
passed; `entrySafe=false` is expected for an already completed gig. The output
does not separately confirm voice calls or money payout.

`finished=0` is still pending, not by itself a bug: the original openworld
graph `root/2` waits **one in-game day** at node32 after its debrief join, then
requires the player outside the initial gig area at node33, performs native
cleanup, and checks departure from the debrief scene at node43 before output.

Continue from the **completed-Life's-Work save you just reloaded**, not the
pre-U8 ManualSave-21. Leave the gig area, skip 24 in-game hours normally, close
menus and allow a few seconds, then repeat:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeHeywoodU8"):Inspect("sts_hey_gle_06"))
```

Expected: `finished=1`, with `creditDone=1` and `Heywood=2` unchanged if no other
gig was completed. If still 0, report it rather than forcing facts or replaying.
No restart, repeated StartAll, or new installation is needed. If pausing, keep
the completed save and close normally; preserve ManualSave-21 as the baseline.

## Latest result: startup and visible markers passed

The user reports the reinstated U8 test loaded without a crash and supplies a
map screenshot with visible gig icons. Installed files still match. Individual
gig states, completion and save persistence are not yet verified.

Continue the current session: **no restart and no repeat StartAll needed**.
Test **Life's Work** if available. Check the normal Padre briefing, journal
objectives, completion, payout and debrief. If the briefing or objectives fail,
report that before proceeding. After completion, run:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeHeywoodU8"):Inspect("sts_hey_gle_06"))
```

Leave the encounter to allow native cleanup. Preserve ManualSave-21 and use a
separate new manual save for a later reload check. If pausing now, you may save
to a new slot and close; do not overwrite the pre-U8 baseline.

## Current: U8 restored at your request

2026-10-12, 18:14 Toronto time: the exact same U8 build is installed again.
The user attributed the earlier crashes to PC memory exhaustion and explicitly
requested reinstatement. No gameplay, graphics, save or cache changes were made.
File verification passed; new-gig gameplay and the memory diagnosis remain
unverified by a new live test.

Launch the game normally (it was closed during installation), load
**ManualSave-21, level 49, 16:47:20 on 12.10.2026**, and resume the U8 procedure
under "Current result and next test" below. StartAll once, close menus for
15 seconds, then InspectAll. Do not restart U7/U4/U6 or use B7 OverrideAll.
If loading fails again, stop and report before further attempts.

Current file recovery: `tools/reinstall_native_heywood_u8.ps1 -Mode Rollback`.
Original installation and withdrawal receipts are preserved as history.

## Historical withdrawal and isolation instructions — superseded by user request

2026-10-12: U8 was rolled back after two exits while loading ManualSave-21.
Both crash reports say `D3D12MA: Out of memory`. That identifies a graphics
allocation failure, but does not establish that U8 caused it. Scripts compiled
successfully. The save hash is unchanged; no graphics or unrelated mods changed.

1. Cold-launch the game and load **ManualSave-21, level 49, 16:47:20 on 12.10.2026**.
2. Keep the same graphics settings. **Do not run any commands or create a save.**
3. If it loads, stay in gameplay for about 30 seconds, close the game and report.
   If it exits again, stop and report; no repeated crashes are needed.

The three new U8 files are retained outside the game and the previous B7
dispatcher is restored. U7, Jeopardy, HP150 and Johnny presentation remain intact.
This is an isolation test, not a confirmed underlying fix. **All U8 StartAll and
gig-test instructions below are suspended. Do not reinstall withdrawn U8 unchanged.**

## Current result and next test: U8 Heywood expansion

U7 Jeopardy completion, native credit, departure cleanup and the follow-up
save/load check passed on the user's tested route. ManualSave-21 corroborates
`CreditDone=1`, `OwnerFinished=1`, `hey_sts_counter=1`, and Padre call counters
`3/3`. HP150 checkpoint reload was also confirmed fixed by the user.
Do not repeat the historical U7/U4 startup instructions below for this test.

U8 is installed, with offline checks passed and new-gig gameplay still pending.
It adds original-graph entries for Life's Work, Fifth Column, On a Tight Leash,
Old Friends, Eye for an Eye, The Lord Giveth and Taketh Away, and Hot Merchandise.
Jeopardy and the already-running U7 phone support remain unchanged.

1. Cold-launch and load **ManualSave-21, level 49, 16:47:20 on 12.10.2026**.
   This is the completed-Jeopardy/U7-cleanup save, not ManualSave-20 and not an
   old B7 batch save. Keep ManualSave-21 untouched as the pre-U8 test baseline.
2. In CET, run once:

   ```lua
   print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeHeywoodU8"):StartAll("DISPOSABLE_SAVE"))
   ```

3. Close CET and menus, holster, leave combat/vehicle/workspot and allow 15 seconds.
   Then inspect:

   ```lua
   print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeHeywoodU8"):InspectAll())
   print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeHeywoodU8"):TierStatus())
   ```

   Accepted entries have `request=1`, `fault=0`; `entered` is ownership of the
   original parent/prelude, not proof that the encounter or briefing has fired.
   `nativeTier=false` can legitimately wait. Completed/outcome/previously owned
   gigs are preserved. If deferred for legacy ownership or unsupported progress,
   send the output: do not reset facts or force tiers.
4. Enable **Gigs** on the map. At Heywood count 1, the initial native group is
   Life's Work, Fifth Column and On a Tight Leash, subject to actual saved state.
   The named journal entry normally appears on approach/native briefing; an
   empty journal before approach does not by itself mean failure.
5. For the first gameplay check, approach **Life's Work** if accepted and marked.
   Answer Padre normally. Confirm the call, written brief and journal objective.
   Complete just that gig normally, report any missing interaction, reward or
   call, then inspect it:

   ```lua
   print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeHeywoodU8"):Inspect("sts_hey_gle_06"))
   ```

   Its native credit should occur once; starting from count 1 and completing
   only this gig should yield count 2. Native departure cleanup may finish later
   than the journal/payout. Other gigs have their own original outcome rules.
6. Once complete and out of the encounter, create a **separate new manual save**,
   reload it, and repeat that Inspect plus U7 Inspect. Credit must not repeat.
   Do not call U4/U6/U7 Start, B7 OverrideAll, or attempt a completed-gig replay.

You do not need to complete all seven in one session. If you are only checking
startup, capture InspectAll/TierStatus and you may close the game without making
a new save; resume from ManualSave-21 next time. No additional restart is needed
after this installation's initial cold launch unless a later fix says so.

Later native thresholds are 4, 7, 10 and 11, with the original story gate for
the last tier. The whitelist may leave insufficient gigs to reach later tiers;
U8 does not invent credit for excluded gigs. Final fixer reward and production
pre-Tower eligibility integration remain pending. Recovery uses only
`tools/deploy_native_heywood_u8.ps1`, then reloads the pre-U8 ManualSave-21.

## Historical U7 procedure — already passed, do not repeat for U8

Installed 2026-10-12; offline compilation, graph and recovery checks passed.

U7 restores the original Padre phone/interrupt/cleanup phases through a scoped
copy of the stock parent reset loop. It also restores Jeopardy's exact original
completion watcher and fixer-credit node. The gig's original gameplay, dialogue
and rewards are unchanged. Other contacts, fixer tiers and final fixer rewards
are not restored by this step. In-game acceptance remains to be tested.

## Load this save

After installation, cold-launch the game and load **the original ManualSave-20,
level49, 16:32:18 on 11.10.2026**. This is the post-Tower snapshot from before any
U6 Padre or U4 Jeopardy request, not a save from the successful call test.
Keep that original snapshot unchanged. Do not run U6 Start or any batch override.

1. Close menus and allow15 seconds in the world. Open CET and run:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeSupportU7"):Start("DISPOSABLE_SAVE"))
```

2. Close CET/menus, holster and stay out of combat for5 seconds. Then inspect:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeSupportU7"):Inspect())
```

Expect `ready/request/issued=1/1/1`, `fault=0`, `creditDone/base/current=0/0/0`
on this original snapshot. If refused/not issued, send the output and stop;
do not force facts or try to migrate the prior U6-running save.

3. Start the original gig, once:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.ActivityStateR3.NativeJeopardyU4"):Start("DISPOSABLE_SAVE"))
```

Close CET/menus and approach the same **Gig: Jeopardy** location. Answer Padre's
briefing normally. U4's old status text still describes its original call-only
trial; use the U7 instructions/status for this combined test.

4. **This time, complete Jeopardy normally**, including the final delivery,
Padre's debrief and reward. Note whether the briefing/debrief voice, objectives
and payout work. Ordinary combat during the gig is fine. Do not force a phone
reset, set completion facts, replay the gig or run a restoration batch.

5. Leave the encounter, let calls finish and leave combat, then run U7 Inspect
again. Expected completion evidence:

- `creditDone/base/current=1/0/1` if no other Heywood gig was completed.
- Jeopardy root `3` (Succeeded), native `done=1`.
- Phone start/end counts balanced, `setupActive/Started=0/0` and `interrupt=0`.
- `ownerFinished=1` after native departure cleanup. It can lag reward/credit;
  if it remains0, send the output rather than restarting anything.

If these pass, create a **separate new manual test save**, reload it and inspect
again: the credit must remain1, not increase again, and no call/reward should
replay. Send the completion and reload output. You may then close the game.
If a call/objective hangs or any output is unexpected, stop and report it; no
new save is required in that case, and you may close the game.

## Optional trace if a call misbehaves

The existing read-only U5 logger remains available. Arm it before approaching
an upcoming call, not after it has already failed:

```lua
print(GetMod("PTFR_PadrePhoneU5").Arm())
```

Stop after that call/test segment:

```lua
print(GetMod("PTFR_PadrePhoneU5").Stop())
```

It has a five-minute limit and is not a full-gig recording. Do not replay a call
in-place just to obtain a trace. U7 supports the original interruption/recovery
wiring, but this normal completion test does not prove every rejection/reset
route. Forced-fact tests are not requested.

## Recovery and scope

Recovery uses only `tools/deploy_native_support_u7.ps1 -Mode Rollback`, with the
game closed: three additions are moved recoverably and the prior U6 script is
restored from its hash-checked backup. Reload the original pre-U6/U4 snapshot
after file recovery. File changes cannot rewind native owners, rewards or credit
in later saves. Do not run the predecessor U6 aggregate recovery while its script
is replaced by U7. No installed builder/test main should be rerun.

This is one development pilot, not all-gig restoration, production pre-ending
history support, or proof of complete stock phone/fixer parity.
