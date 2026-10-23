# Afterlife A2: native scene lifecycle test

2026-09-24. Single-site opt-in candidate installed after the A1 shadow probe passed native Inside=2/Exits=2. The existing v5 Afterlife archive, v6 redscript driver and read-only observer remain installed with their original SHA-256 hashes. No other mirror was enabled. A2 is three additive mod-owned resources under `towercontinued\afterlife_native_scene_a2`: outer gate, one owner with exactly the vanilla `#mirror_scene_afterlife` prefab, and a copy of the authored Afterlife scene whose exit uses the full native `IsOutside` trigger. No vanilla resource is replaced.

The old v5 scene owner stays installed as rollback. A2's controller arms only from outside the bathroom with no combat, scene or workspot. It temporarily sets `PTFRB0ALM_Enabled=0` and `PTFRALMA2_Requested=1`. Both are mod-owned facts. Redscript stays installed and will write Near=0 while the old owner is disabled. **Do not save this session; reloading the original disposable save restores the old Enabled fact and working driver.** No story fact is set.

## First manual run

Use the disposable post-Tower save that already has the working Afterlife v5/v6 restoration. Start near Claire, outside the bathroom. Run **each CET line separately**:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Start("native-scene-a2-first")
GetMod("PTFR_Afterlife_NativeScene_A2").Arm()
```

If Arm refuses, stop there and send its printed reason; do not force facts. If it returns true, close CET briefly, then record:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Mark("outside-armed")
```

Walk to the Afterlife mirror. Confirm the **physical Look prompt**. Use Look, one facial expression and Stop, then record:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Mark("first-at-mirror")
```

Leave the bathroom and go back near Claire. Wait at least one real-time second for the authored rearm and record:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Mark("first-outside")
```

Return to the mirror. Again use Look, one facial expression and Stop; record:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Mark("second-at-mirror")
```

Leave to Claire, wait one real-time second, record and close the log:

```lua
GetMod("PTFR_Afterlife_NativeScene_A2").Mark("second-outside")
GetMod("PTFR_Afterlife_NativeScene_A2").Stop()
```

Quit without saving and report which physical actions worked. If the prompt fails, V is stuck, or Arm refuses, stop at that point, mark the failure if possible, close the log and quit without saving. There is no need to attempt the second cycle after an initial failure.

The CET module writes a unique, flushed `afterlife_native_scene_a2_*.jsonl` in its installed mod folder. It records explicit snapshots; it does not claim frame-accurate fact callbacks. I will read the log directly after you say the game is closed.

## Pass criteria and limits

### First live run (2026-09-24, inconclusive for native path)

Durable log `afterlife_native_scene_a2_20260924T130447Z_0001.jsonl` records a valid baseline and `ARMED` at 13:04:47Z: `PTFRALMA2_Requested=1` and old `PTFRB0ALM_Enabled=0`. By the next mark at 13:06:11Z, those values had reverted to `Requested=0` and `Enabled=1`; the A2 Guard/Ready/scene counters stayed zero. Both mirror visits therefore used the old v5/v6 owner (`Near=1`, `Active=1` at the mirror), not A2. The source of the reversion is not established. The only installed Lua/redscript writers found for these two facts are the A2 Arm controller; a save reload between marks is one possibility, not a confirmed cause. Do not count the working physical actions as native success or expand mirror scope. Ask whether a load/restart occurred after Arm, then verify that the armed state persists at the first outside mark before another two-visit run.

### Second live run (2026-09-24, native lifecycle reached with one extra cycle)

The repeat log `afterlife_native_scene_a2_20260924T131435Z_0001.jsonl` shows fresh baseline, successful Arm, then Guard=1 and Ready=1 at the outside mark. `PTFRALMA2_Requested` stayed 1, while old `PTFRB0ALM_Enabled`, Near, and Active stayed 0 through Stop. Native counters were 2/1/1 and Active=1 at first mirror mark, 2/2/2 and Active=0 at first outside mark, 3/2/2 and Active=1 at second mirror mark, and 3/3/3 and Active=0 at second outside and Stop. Interrupted stayed 0; sampled Tower/story guards did not change. The player confirmed Look, one facial expression, and Stop worked on both visits and that they crossed the trigger boundary twice on the first visit. Thus the three native entry/exit/rearm cycles match the three reported crossings; the fixed 2/2/2 expectation was too rigid for that route. A2's native scene path is live-validated for this opt-in, no-save session, with v5/v6 scene owner disabled throughout. Keep v5/v6 as rollback: automatic startup and saved-load persistence are untested, so do not broadly expand or replace the driver yet.

The first run passes only if:

- the fresh Boot/Guard/Ready markers establish that A2 started;
- the old owner stays disabled (`PTFRB0ALM_Enabled=0`, old Near/Active=0);
- physical Look, facial expression and Stop work on both visits;
- `PTFRALMA2_SceneRequests=2`, `SceneReturns=2`, `Rearms=2`, `Active=0`, `Interrupted=0` after the second departure;
- sampled Tower/story guard facts remain at their expected values.

These counters bracket the native-triggered scene node and its native scene output, unlike A1's independent trigger witness. The second live run began after a cold game relaunch from the disposable baseline, but A2 still required manual Arm. Automatic startup and save/load persistence are separate, untested gates before production replacement. The current no-save instruction prevents claiming persistence of A2 state across a saved reload. No second mirror or 36-mirror rollout follows automatically from this test.

## Native versus redscript decision after the repeat

For this one Afterlife mirror, the native path now has direct evidence of functional scene entry, exit, one-second rearm, and usable Look/expression/Stop while the old owner is disabled. The redscript fallback remains the better *installed* implementation until native startup and persistence are validated: A2 currently depends on a manual CET Arm and has not been tested across a save made while A2 is active. The redscript poll is once per 0.5 seconds; its distance arithmetic is cheap, but it also reads several quest facts and reschedules an engine callback. Native trigger delivery avoids that repeated script-side work, though no measured performance difference has been established. The smallest safe next step is a one-site automatic bootstrap design that keeps the v5/v6 rollback available; do not extrapolate this Afterlife prefab result to all graph-shaped mirror leaves.

## Offline checks and rollback

`tools/build_afterlife_native_scene_a2.ps1` built the three-resource archive; static graph/scene and LuaJIT controller mock checks passed via `tools/test_afterlife_native_scene_a2.py`. Source/binary round-trip and installed hashes matched. The archive SHA-256 is `9025E676069478FFFCD6DCED71850383126BF09C1C0C4842B4A56A2AA9BBBDFC`; the installed CET controller SHA-256 is `F0830CCACDAE51DEB15F7CA43CF849616A73E70D7C6BF448276C441FDF886AE0`. A2's ArchiveXL registration ID is 52297 and did not collide with the inspected installed phase registrations or vanilla EP1 node IDs.

The working rollback remains: v5 archive `2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003`, v6 driver `0F8F2ADB277DC0D59F70951D7A84DF41DDA9D0B44CEDE0F212B5CBA046BB3BB2`, and read-only observer `3E9C8C5A0EFA1CF5F336A1B20EA5634E1759288C3BE3320359802A65517BA35F`. A2 is inert until Arm succeeds. After quitting without saving, loading the original disposable save restores the previous mod-owned Enabled state. The A2 package can remain installed inert while its result is reviewed; a final production switch has not been made.
