# Cyberpsycho P1 — installed; live test pending

Installed 14 October 2026. Offline graph, LuaJIT, resource and installer checks
passed. This is not a claim that all 17 encounters or the reward have been
playtested. Existing working restorations and saves were left unchanged.

## Normal behavior

- Restore the 17 stock-connected cyberpsycho encounter owners only when their
  local start/finish facts are untouched, their quest journal root is Inactive,
  and the total completion count is below 17. Preserve native district gates,
  encounter graphs, phone scenes, outcomes and rewards.
- Preserve completed/started sightings. No automatic reset of the player's
  completion count, kill count, reporting history, inventory or collected reward.
- Resume stock Psycho Killer reporting without replaying the journal increment
  for an already-earned milestone. Restore Regina's native reward-container
  lock/unlock and journal-completion handlers. An already-claimed chest is not
  refilled in normal play.
- Existing Johnny visual-only suppression remains installed; no dialogue/audio
  or encounter scene resources are replaced by P1. No periodic CET output.

## Exact starting save for this development test

Load **AutoSave-1, level 48, 17:56:55 on 14.10.2026**. Its metadata tracks the
Dogtown hotel objective (`sts_ep1_08_start`). Read-only examination found
post-Tower restoration/handoff flags, `ow_psychos_done=17`,
`ow_psychos_killed=6`, `mq043_done=1`, `ow_psychos_reward_collected=1` and
Lt. Mower's completed facts. Missing serialized fault fields are not claimed
to be measured live zeros; the command checks live admission.

Save SHA256: `1305016A84A5887B2F073ADBA703910DDF565D681A2E6CDC278E83800DC74649`.
All three files were backed up byte-for-byte under
`research/cyberpsycho_p1/checkpoint_before_install/AutoSave-1`.

1. Cold-launch the game and load that save. No ending replay is needed.
2. Make a **new manual save before running any test command**. Keep it untouched
   as your return point. Stand somewhere safe, away from Lt. Mower's encounter.
3. Open CET and run:

   ```lua
   print(GetMod("PTFR_CyberpsychoP1").Test("DISPOSABLE_SAVE"))
   ```

4. If it refuses, stop and send the refusal plus the status below. Do not
   override the guard facts. If accepted, close CET/menus, wait about ten seconds,
   then check:

   ```lua
   print(GetMod("PTFR_CyberpsychoP1").Status())
   ```

   Expected: `PTFRP1_TestResetDone=1`, `PTFRP1_TestPreparing=0`,
   `ow_psychos_done=16`, `ow_psychos_killed=0` and eventually
   `PTFRP1_ma_wat_kab_08_Entered=1`. `TestCrateReady` may remain 0 until Regina's
   reward container streams in. Issued/Entered are not proof of a visible NPC.

## Test A — one complete encounter

Enable **Cyberpsycho Sighting** in the map's custom filter. Go to **Cyberpsycho
Sighting: Lt. Mower**, in Kabuki, Watson. Check the approach marker, Regina's
briefing, an actual live enemy, combat and objectives. Defeat her non-lethally,
read the clues/shard and send the report to Regina through messages.

Expected: Lt. Mower completes, its marker clears, the native reward is delivered
once, and `ow_psychos_done` changes from 16 to 17 exactly once. This fixture
explicitly treats the other 16 as non-lethal for the final reward test.

Stop and report if the site is empty, the NPC is already defeated, the objectives
skip the fight, the report choice is missing or progress stalls. Repeating the
test command is intentionally refused. Native Reactivate/Respawn and
ResetKillCount have been serialized and checked, but their handling of this
previously completed NPC/device state is still unverified in the live game.
Old shard ownership and device history are not a pristine fresh-save simulation.

## Test B — the all-sightings reward

1. After the 17th report, allow the **stock 12 in-game-hour delay** and keep the
   phone free. Time skipping can advance the game-time delay. Verify Regina's
   final call and the **Psycho Killer / Talk to Regina** objective.
2. Visit Regina's office, allow it to stream in, and check
   `PTFRP1_TestCrateReady=1`. Speak to her about finishing the cyberpsycho work.
3. Confirm the reward container unlocks and contains loot. Take it. Verify the
   take-reward objective and Psycho Killer complete.
4. Optionally save this **test branch separately**, reload it, and revisit:
   no new encounter, repeated reward refill or extra completion increment.
5. **Discard the test branch and load the untouched manual save from step 2.**
   Do not keep the development fixture as your main character's progress.

The test command is deliberately more than a raw fact reset: it consumes a
one-use test owner, resets only Lt. Mower's local quest/message entries and two
local community sets, sets reports to 16 and killed to 0, reopens Psycho Killer,
and once reinitializes only Regina's named reward container using the stock
retrofix's container payloads. It does not grant items directly to V or alter
the game's historical retrofix flags. No automatic saving/loading is performed.

## Remaining alpha coverage

- A genuinely unstarted sighting carried through the full pre-Tower ending path.
- Both lethal and non-lethal reports; the correct native reward for each history.
- Additional districts and special encounters, especially Bloody Ritual's gates.
- Johnny voice without his rendered body where those encounters use him.
- Save/reload during an active encounter and before/after Regina's reward.
- No reopening or extra credit for the player's other completed sightings.

## Recovery and immutable evidence

Current build: `prealpha/cyberpsycho_p1/build/p1_07`.
Build SHA256: `105F80B28823891695D315B5322ABC98AD7E982780B20DEBF826CB9B3BE616E8`.
Sources, build, tests, deployment tools and install receipts are now pinned.
Do not rerun old builders or overwrite their evidence. A repair needs a new revision.

With the game closed, recovery starts with
`prealpha/cyberpsycho_p1/deploy.ps1 -Mode ValidateRollback`, then `-Mode Rollback`,
using the exact absolute recovery directory `recovery/cyberpsycho_p1_01`.
This moves only P1's four added files into recovery; the empty helper directory
may remain. Then, only if needed, use the prior D1 → N22 → N21 → C1 → N2 → N1 →
FO1 → PA6/older recovery order. Rollback does not undo test changes to a save:
return to the untouched pre-command save instead.
