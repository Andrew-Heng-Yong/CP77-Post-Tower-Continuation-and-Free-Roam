# El Capitán vehicle contract restoration playtest

**17 October checkpoint follow-up:** a later contract reached Dogtown's closed
militarized gate. The native gate controller was missing after EP1 teardown;
DT1 restores that controller separately, retaining stock vehicle scanning and
combat lockdown. Use the current working post-Tower save for the new crossing
test, not the historical AutoSave-8 below. See the
[DT1 checklist](alpha_playtest_tasks.md#dogtown-checkpoint-regression--dt1-17-october-2026).
No courier restart, reset or forced completion is involved. Live crossing and
delivery after the repair remain pending.

Installed 14 October 2026. **User-reported functional pass:** the user found a
vehicle opportunity and reports the car-stealing job works. Exact call/text/reward
coverage, second cycle, new-save/reload and fresh-ending integration remain
unspecified. N2.2 scanners also have a user-reported visibility/functionality pass.
The steps below remain for deferred coverage; no repeat basic startup test needed.

The patch starts the original courier-only sandbox branch after a completed
Tower handoff. Stock district selection, vehicle spawning, calls, delivery
objectives, challenges, rewards, vehicle-unlock counters and cleanup remain in
their original resources. It also retains eligible one-time onboarding and the
later Muamar mission, rather than replaying completed ones. Officer Daniels's
original phone controller and cleanup are included for that later mission.

Existing Muamar/fixer/NCPD phone services are not restarted. Johnny's existing
body-hidden, voice-retained policy remains; the courier scene's Johnny actor uses
the `Character.Silverhand` record handled by that policy. No general side-job,
race, airdrop or cyberpsycho restoration is added here.

## Short test when ready

1. Cold launch and load **AutoSave-8, level 48, 12:10:04 on 14.10.2026**.
   Match its timestamp, not merely the slot name. This is the existing post-Tower
   scanner-test save; its metadata says `ma_wat_lch_01_start`. Its saved courier
   introduction is already complete, with one recorded successful delivery.
   No ending replay, `StartAll`, fact override or forced teleport is needed.
2. Close CET and menus, then travel around normally. Look for a native vehicle
   contract opportunity. The stock controller chooses opportunities by location
   and cooldown: this is not a citywide set of permanently visible new markers.
   An empty journal before accepting a contract is not itself a failure.
3. Approach the marked vehicle and begin the contract. Check that the vehicle is
   usable, the delivery objective appears, and Muamar's native call/text route
   runs. A marker alone does not count as a working contract.
4. If convenient, deliver it normally. Check the payout once, objective cleanup,
   and whether another opportunity becomes available later. Do not force timer,
   completion, reward or vehicle-unlock facts to manufacture a pass.
5. Make a **new save**, reload it, and check that the controller continues without
   replaying onboarding or duplicating rewards. Preserve the original fixture.

The fixture's original three files are already backed up byte-for-byte under
`recovery/ncpd_n2_fixture_20261014/AutoSave-8`; they were not edited.
`sav.dat` SHA256: `A7A55B53FAE56E8EB70485711A9B9BBE8DE3159DCC34E9C7F62ABDCABC59A12B`.

## Read-only diagnostics if no opportunity appears

Paste only the command, not its printed output:

```lua
local q=Game.GetQuestsSystem(); for _,f in ipairs({"PTFRC1_Ready","PTFRC1_Issued","PTFRC1_Support_Ready","PTFRC1_Support_Issued","PTFRPA2_Finished","PTFRU9_Support_Issued","PTFRU9_Support_Fault","ep1_active","ep1_side_content","sa_ep1_courier_ready_to_start","sa_ep1_couriers_active","sa_ep1_courier_force_despawn_and_block","sa_ep1_courier_quest_silencer","sa_ep1_courier_quest_silencer_active","sa_ep1_courier_loop_blocked_by_outro","sa_ep1_courier_introduction_quest_started","sa_ep1_courier_introduction_quest_finished","sa_ep1_courier_outro_available","sa_ep1_courier_outro_active","sa_ep1_courier_outro_finished","sa_ep1_courier_outro_failed","sa_ep1_courier_succesfull_deliveries","sa_ep1_courier_jobs_succesfull","holo_setup_active","holo_setup_started"}) do print(f.."="..q:GetFactStr(f)) end
```

`PTFRC1_Issued=1` means the native branch was issued once, **not proof of a
spawned vehicle or working call**. If it stays zero, send the output and your
location. Do not clear the issued flag; that could duplicate its owner.

## Later coverage

- [ ] At least two different regions produce usable contracts.
- [ ] Ordinary theft and hacking opportunities, where natively eligible.
- [ ] Chase, timed and vehicle-damage variants; success and legitimate failure.
- [ ] Native payout, delivery totals and vehicle unlocks advance once, not twice.
- [ ] Next opportunity after completion and after abandoning/failing a contract.
- [ ] New save/reload before accepting, during delivery and after completion.
- [ ] Death/checkpoint reload retains the contract and existing nerf profile.
- [ ] An ordinary gig call and NCPD dispatch still work after courier calls;
  interruption and call cleanup do not leave the phone occupied.
- [ ] On a separate genuinely unstarted eligible fixture, onboarding works once.
- [ ] At the native delivery threshold, the later Muamar mission starts once;
  Daniels calls work, Johnny has voice but no body, and courier contracts resume
  afterward. Completed or failed story outcomes must not replay.
- [ ] Fresh pre-ending-to-post-ending integration, when the full alpha is ready.

## Admission limits

This restores the controller from an idle courier state. It does not reconstruct
an unfinished pre-Tower delivery or partially completed courier story. Such
states wait without being reset. Completed onboarding is accepted; already
completed/failed later-story outcomes remain protected by the stock gate.

Original startup sets `sa_ep1_courier_ready_to_start=1`. Subsequent cooldowns are
native, but the exact remaining pre-Tower cooldown is not reconstructed. Lifetime
delivery totals and rewards are not cleared. Do not interpret the generic
`sa_ep1_courier` entry in finished-quest metadata as completion of the repeatable
system.

## Recovery

Current chain: recover **D1, then N22 and N21 before C1**. Close the game.
For C1 itself, recover **C1 before N2 or N1** using
`prealpha/courier_c1/deploy.ps1`: first `ValidateRollback`, then `Rollback`, with
the exact directory `recovery/courier_c1_01`. Only C1's two added files are moved
recoverably; the previous NCPD/fixer cleanup resource becomes effective again.
Then, if needed, recover N2, N1, FO1, PA6 and older transactions in order.
File rollback cannot undo gameplay already written into a later save.

Evidence: `research/courier_c1/assessment.json` and
`prealpha/courier_c1/build/c1_02/`. The installed build, sources, test tools and
receipts are pinned; use a new revision for any repair.
