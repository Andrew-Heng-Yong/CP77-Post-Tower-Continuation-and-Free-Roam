# Phase 2B-P4 — B0 persistent-world exploration probe

2026-09-22 · development-only · version 2B-P4.1. No production transition, new archive, installation or agent runtime test. No Git operations. Use an untouched disposable **ManualSave-11 copy**, not a post-fall/P3 experimental save. No ending replay.

## Purpose and evidence

The tester has already **OBSERVED** genuine q307 completion, retained `q307_2079` and session, saving/reload, movement after reload, map/inventory/character menus, ordinary pedestrians, working weapons and police reactions. These do not need restoration or mandatory repeat tests. The q307/Zetatech exit staging is **OBSERVED broken**. This experiment asks what ordinary Night City already provides after one position change; it does not rebuild a 2077 world.

Plan B0 preserves actual Tower/2079 logical/media state, uses ordinary persistent physical streets, and adds no speculative future overlay. Plan A remains for later isolated assets; Plan C is a fallback. This is a prototype decision, not production certification.

## Destination: static review passed, runtime support still required

Three ordinary Little China arrival markers were evaluated: 05 (~22m from fixture), 04 (~182m), and **11 (~258m, selected)**. Exact supporting collision remained unresolved for 05/04; they are not available fallback commands. No Box intersection is not proof of a hole where mesh collision remains undecoded.

Selected vanilla reference:

```text
$/03_night_city/c_watson/little_china/#little_china_data_terminals/wat_lch_dataterm_11_prefabDX7GUFI/#wat_lch_dataterm_11
position: (-1658.87463, 997.365662, 23.6999989)
quaternion (i,j,k,r): (0,0,-0.99619472,0.0871557295)
```

**CONFIRMED resource membership:** the arrival marker is EP1 `always_loaded_1` node4523/data10751, unconditioned range0. Ordinary terminal node900/data981 in `exterior_-26_15_0_0`, range0, links it to `FastTravelPoints.wat_lch_dataterm_11`. Vanilla uses that marker as a player destination.

The support is in `base/worlds/03_night_city/_compiled/default/exterior_-13_7_0_1.streamingsector`: ordinary sidewalk mesh node732/data991 and collision node1494/data1792, actor20/shape0 (`Box`, `CharacterObstacle`), both range0. Descriptor10873 assigns only ranges1–3 to `morning_deco`, `var_impulse_env`, and `prolog_blockades`. The selected support and marker are **not owned by q307 variants**. Their world poses match within exported float precision. Independent geometry calculation agrees on support Z≈23.2792434 and confirms all nine ±0.3m footprint samples. Authored marker Z is deliberately retained, ~0.421m above that face.

**INFERRED:** this ordinary sidewalk is independent of the dismantled ending set. **UNKNOWN until tested:** live streaming, collision, clearance, navmesh, wider route and services. This distinction is why the probe still checks live physics before moving.

Exact evidence: [selection](../research/phase2b_p4/destination_selection.md), [independent review](../research/phase2b_p4/destination_review.md), [independent calculation](../research/phase2b_p4/destination_independent_math.json), [probe source review](../research/phase2b_p4/probe_review.md).

## Install — game closed, user only

1. Preserve the original `C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\ManualSave-11` and its backup. Use a disposable copy derived from that exact fixture. The probe cannot identify a save filename from facts; select the correct copy yourself. Do not overwrite or edit the original and do not use the post-fall state. If the copy is not prepared, stop before testing.
2. Keep the existing `archive\pc\mod\TowerContinued_Phase2B_P0_DirectReturn.archive` unchanged. **No new `.archive` is supplied.** Do not put the ZIP or Lua files in the archive folder.
3. Preserve prior logs, then move older `PTFR_...` CET recorder/probe folders completely **outside** CET's `mods` directory. A rename inside `mods` still loads `init.lua`. Leave unrelated mods untouched; do not run P2/P3 repair commands during this experiment.
4. Extract `build\Phase2B_P4_Explore\PTFR_Phase2B_P4_Explore.zip` into:

```text
C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods
```

Required installed layout (no doubled folder):

```text
mods\PTFR_Phase2B_P4_Explore\init.lua
mods\PTFR_Phase2B_P4_Explore\ptfr_p4_survey.lua
mods\PTFR_Phase2B_P4_Explore\ptfr_p4_target.lua
```

`manifest.json` stays in the workspace build directory; it is build/check evidence, not a required CET file. No other dependency or installation change is requested.

5. Double-click `tools\Check_Phase2B_P4_Installed.cmd`. It checks the three Lua hashes, unchanged required P0 archive and original ManualSave-11 hashes, and detects older PTFR probes. It only reads the game/save directories. Do not proceed on a failed check.
6. Start the game fresh (do not hot-reload mods into an already loaded save). Load the disposable ManualSave-11 copy. Wait five seconds in the unpaused game.

## One session

1. Open CET and run this **read-only** readiness check:

```lua
GetMod("PTFR_Phase2B_P4_Explore").Inspect()
```

Expect `Baseline=true target=true attempted=false`. Double-click `tools\Check_Phase2B_P4_Ready.cmd` for the trace check. A failed required check means **no move**: stop and provide the log, without replaying the ending or using guessed coordinates. An unavailable optional survey getter is UNKNOWN, not a failed logger.

2. If ready, trigger the **only deliberate probe world change**, once:

```lua
GetMod("PTFR_Phase2B_P4_Explore").RelocateToPersistentWorld()
```

The command repeats all safety checks. It appends/flushes the original pose and state before the native call, consumes the attempt before dispatch, and never automatically retries—even after an exception or reload. The call returning is not proof of arrival.

3. Close CET. Stand still for **10 seconds**; confirm visible ground and stable height. Then walk a few steps. If falling, suspended, trapped or missing terrain: **stop, do not save, quit and send the log**. No automatic rescue or alternative destination is included.
4. If stable, explore ordinary streets for several minutes. Optional checks only:

   - Observe traffic; try summoning/driving an owned vehicle.
   - Open the phone; try a nearby vendor or another ordinary interaction.
   - Check nearby fast-travel access or apartment access if convenient.
   - Go farther only while terrain remains stable. Dogtown is optional, not a required long trip.

   Pedestrians/weapons/police and hub menus already have positive observations. Normal use can reveal regressions, but no repeated crime test is required. Do not run any restoration commands or force facts. Manual gameplay actions are distinct from what the probe itself changes.
5. Optional log annotation (or simply report observations afterward):

```lua
GetMod("PTFR_Phase2B_P4_Explore").Report("ground", "WORKING", "Stable sidewalk, walked several streets")
GetMod("PTFR_Phase2B_P4_Explore").Report("vehicles", "BROKEN", "Summon attempted; no vehicle arrived")
```

Only report what actually happened; those are examples, not assumed results. Statuses: `WORKING`, `BROKEN`, `UNKNOWN`. Systems: `ground`, `movement`, `traffic`, `vehicles`, `phone`, `vendors`, `fast_travel`, `apartments`, `encounters`, `quests`, `dogtown`, `media`, `pedestrians`, `weapons`, `police`, `map`, `inventory`, `character`, `saving`, `reload`, `other`. Report writes only the diagnostic log.

6. If the world is stable, you may make a **NEW experimental save** through the normal game UI. Never overwrite original ManualSave-11 or its backup. The probe neither saves nor removes save locks. Reload is optional, not necessary to complete this exploration; a new load is logged separately and never triggers another teleport. One successful new save is not a reload/stability guarantee.
7. Quit. Preserve `mods\PTFR_Phase2B_P4_Explore\ptfr_p4_explore.jsonl` and provide observations. `tools\Analyze_Phase2B_P4.cmd` writes a compact workspace summary without altering the game log. No ending replay needed.

## Automatically read / logged

| Area | Coverage and limitation |
|---|---|
| Tower/2079 | Five eligibility facts; known Johnny, PONR, cutscene, hub, air/TV/radio facts; q307 journal root/phase/objective, contacts and selected future pages/emails/shard states. Historical fact values are not live graph enumeration or a cyberware policy. |
| Player/support | Exact pose and player/load identity; scene/dialogue/workspot/mount, PSM tier/locomotion/ground, save lock; target physics/nav checks; rapid initial arrival samples and height-loss warning. No tier changes. |
| Population / traffic | Optional NPC/vehicle attach/detach observations, classifications/counts, bounded vehicle positions/displacement. Process-lifetime scope is explicit. Zero callbacks does not prove no population. |
| Police / weapons / hub | Effective prevention state/heat; equipped weapon and outfit reads; observed menu requests. No generated crime, firing, equipment or menu changes. |
| Vehicles / phone / fast travel | Owned/unlocked/active vehicle and summon gates; phone/call availability; registered base/EP1 points and enabled/resolvable state. Availability is not demonstrated successful use. |
| Interactions | Looked-at entity/device readouts and optional vendor-menu callbacks. Apartment, generic encounter and full vendor usability require human observations. |
| World/time/quests | Timestamp/pause and rain values; active journal entries; historical root facts and content blockers. Live base/EP1 root instances, complete streaming, full weather preset, and Dogtown activity usability remain explicitly UNKNOWN where no safe getter exists. |

Sampling: cheap 1Hz heartbeat; rich survey at baseline/Inspect, arrival ~2s/~10s, every ~10s and manual reports; 0.1s arrival reads through the first ~10s, then 2s. Optional errors are individually recorded, not converted to BROKEN or allowed to disable the core logger. New process/run and loaded-session IDs distinguish restart/reload from another ending execution.

Prior working observations are labeled as prior tester evidence, not fabricated current-run outcomes. The analyzer uses WORKING/BROKEN/UNKNOWN / NOT TESTED, preserves numeric fact comparisons per load and does not invent changes when a cheap snapshot omits optional facts.

## Exact safety behavior and scope

- Five facts must match the known completed fixture, with a delivered stable player attach, original pose and durable baseline, and source within 25m of the reviewed ManualSave-11 staging position. Completion authenticity comes from the fixture's recorded ending provenance plus these checks—not arbitrary matching facts.
- Target uses the **exact extracted vanilla transform**, not an arbitrary street coordinate or a runtime-resolved replacement. The full NodeRef is provenance. No second marker-resolution binding is required by this equivalent-transform implementation.
- Five live Static downward rays must hit near the reviewed support/marker height band, with finite approximately unit upward normals and consistent heights. Navmesh must be resident and a nearby human-nav point must be OK, within 1m in 3D and the reviewed height band. It never replaces the authored position.
- Static/Vehicle overlaps must confirm clear standing volume covering initial and settled height. Missing/error/malformed required results fail closed. A valid miss at a distant unloaded target does not diagnose a broken world. Dynamic actors can change after the checks; static approval does not make runtime landing risk-free.
- Only `TeleportationFacility.Teleport(player, exact_position, converted_authored_rotation)` is dispatched. No fast-travel wrapper (it clears restrictions and requests autosave), prefetch, scene exit, status removal, player show/tier operation, journal/door/prefab/world/root/fact/media/equipment mutation or automatic save exists in this probe.
- Offline mocks test control flow, not the game's native bindings or terrain. Read-only Inspect is the runtime binding/support gate. If it fails, send the log; do not lower guards or repeat a 15-minute ending.

## Removal and result

With the game closed, preserve the JSONL log, then move **only** `PTFR_Phase2B_P4_Explore` completely outside CET `mods` (or remove that folder after saving the log). Keep the pre-existing P0 archive unchanged for the retained-session fixture. No manifest installation/uninstallation or save edit is needed. Removal does not reverse a relocation saved in a NEW experimental save; return to the untouched original fixture for a clean baseline.

One session can establish local stable ordinary terrain, several actual services and whether Tower/media observations remain compatible without world restoration. Positive results support “ordinary world already present; hand off out of ending staging,” followed later by targeted residual cleanup. Missing services identify their owners for future work; a preflight miss is only an inconclusive tooling/residency result. No outcome alone proves all Night City/Dogtown, full cyberware/Johnny enforcement, or long-term save stability.
