# Phase 2B-P0 — Direct-return retained-session probe

Build date: 2026-09-21. Game: locally inspected Cyberpunk 2077 2.31 / Phantom Liberty.

**Experimental: first watched-credit run produced partial success.** Credits returned to a rendered world; map/inventory/journal worked, but movement failed. All teardown markers were recorded and the six final-board restrictions cleared; player HighLevel remained SceneTier2. The user's subsequent save/reload retained completion facts and menus but left V trapped inside Viktor's clinic; loading briefly reached HighLevel 1 before returning to 2. See `docs/phase2b_p0_run1.md` for evidence and limitations. No recovery fix or skipped-credit run has been performed.

User approved a companion **read-only CET logger** alongside one gameplay archive. Removing the archive rolls back the resource patch on a fresh game start; remove the logger directory too for full uninstall. Neither removal reverses state already written into a save. Use only the disposable pre-ending fixture; do not save over it.

## Deliverables and installation

- Archive: `build/Phase2B_P0/TowerContinued_Phase2B_P0_DirectReturn.archive`.
- Logger folder: `build/Phase2B_P0/PTFR_Phase2B_P0` (`init.lua`, `events.json`). Source: `diagnostics/PTFR_Phase2B_P0`.
- Recorder readiness check: `tools/Check_Phase2B_P0_Logger.cmd`.
- Runtime analyzer: `tools/analyze_phase2b_p0.py`.
- Validation evidence: `research/phase2b_p0/validation/build_manifest.json`, `preflight.json`, original/patched JSON and **synthetic** test trace. Synthetic output is not a game test.

With the game closed, remove/move out the prior Tower Continued proof/diagnostic archives. Read-only inventory at build time found:

`C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod\TowerContinued_Phase2A_DIAG.archive`

Install the new archive in `Cyberpunk 2077\archive\pc\mod`. Copy the entire `PTFR_Phase2B_P0` logger folder into `Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods`. Do not install the workspace's raw resource directories, analysis tooling, or synthetic logs. No `.reds` or `.archive.xl` companion is needed.

## Exact resource changes

### `ep1\quest\main_quests\q307\phases\q307_ending_board.questphase`

All 25 original root nodes and their non-connection properties remain unchanged. Add nodes 100–105 (31 total):

| Node | Action / wiring |
|---|---|
| 100 | `PTFRP0_DR03=1`, parallel from original input 0.Out; all original startup edges remain. |
| 101 | Q307 guard after CreditsRolling pause 13.Out. Reads `q307_active==0`, `q307_done>=1`, `q307_finished>=1`, `q307_2079>=1`, and `PostTowerFreeRoamActive==0`. |
| 102 | True branch: `PTFRP0_DR01=1`. |
| 103 | `questFinalBoardsLoadPonRSave_NodeType.loadPointOfNoReturnSave=false`. |
| 104 | `PTFRP0_DR02=1` after routing action returns; fans out to original 5.In1 and 21.In. |
| 105 | False branch: `PTFRP0_GUARD_FAILED=1`; also preserves both original fanouts. No stall or recovery. |

**Copied precedent:** q305 `ep1\quest\main_quests\q305\phases\q305_08_border_crossing.questphase`, inline graph `Data.RootChunk.graph.Data.nodes.12.Data.phaseGraph.Data`, node **46**. Node type/properties copied unchanged; only ID/connections differ. q306 uses the same node/property at inline graph `.nodes.10...`, node 46.

The destination override occurs after rolling is established and before the original reward/delay/skip-enable chain runs. It neither loads a PONR save nor terminates the board. Tower scenario, media, rewards and skip-enable operations are unchanged. Core q307 cleanup already precedes entry to this resource.

### `base\quest\main_quests\epilogue\final_boards.questphase`

All 30 original root nodes and their non-connection properties remain unchanged. Add nodes 100–130 (61 total):

- Q307-only `53.Out1 -> 100 (DR04) -> 27.In`. DR04 is the closest editable graph point before node 27, not an injected native-node callback.
- **Keep original `27.Out -> 28.In` unchanged and immediate.** Node 27 remains the vanilla videos-finished notification, not a wait.
- Parallel `27.Out -> 101` guard, requiring the same completion predicates plus this probe's `PTFRP0_DR02==1` arm.
- `101.True -> 102 (DR05) -> 103 (DR06) -> 104`.
- 104 evaluates the exact `questUICondition / questCreditsRolling_ConditionType` copied from Q307 board node 13. True -> real-time 100 ms delay 105 -> recheck 104. False -> 100 ms delay 106 -> recheck 107. If 107 is true, return to polling. If false, recheck guard 108; only its True output reaches 109 (DR07).
- False guards end this added branch without changing the vanilla fade. There is no timeout that forces restoration, no force-stop-credits write, and no terminating output that cancels other graph branches.

The delays use the existing `questRealtimeDelay_ConditionType` structure from Q307 board node 11, shortened to 100 ms for polling/rechecking. They are scheduling intervals, **not** presumed credit durations or timer-based dismissal.

## Exact teardown, in requested order

| Nodes | Operation | Diagnostic |
|---|---|---|
| 110 -> 111 | Request `Tier1_FullGameplay`, copied from q305 cleanup node 21 | DR08 before; DR09 confirms node returned |
| 112 -> 113 | Show player, copied from q305 cleanup node 15 (`isPlayer=true`, `show=true`) | DR09 before; DR10 confirms return |
| 114 -> 115/117/119/121/123/125 | Six individual `RemoveRestriction` operations, source `finalboards` | DR10 start; DR11_1…DR11_6 after each action returns |
| 127 -> 128 | `questContentTokenManager_NodeType / questBlockTokenActivation_NodeSubType`, `action=Unblock`, `source=finalboards` | DR12 before; downstream DR13 confirms return |
| 129 -> 130 | Set exact `PostTowerFreeRoamActive=1` | DR13 after write |

Six identifiers, checked against **both** the Q307 setup and q305 explicit-removal precedent:

1. `GameplayRestriction.NoMovement`
2. `GameplayRestriction.BlockDeviceInteractions`
3. `GameplayRestriction.NoPhotoMode`
4. `GameplayRestriction.NoRadialMenus`
5. `GameplayRestriction.NoTimeSkip`
6. `GameplayRestriction.NoWorldInteractions`

q305 cleanup node 19 supplies `RemoveRestriction`; its source is changed from `EP1_credits` to the exact Q307 setup source `finalboards`. Each copy contains only one of the six IDs. No `RemoveAllRestrictions` operation is added.

Content release clones Q307 setup node 19 and changes **only** `Block` to `Unblock` (besides node ID/connections), preserving source and `resetTokenSpawnTimer=true`. That property is retained from the paired Q307 operation, not an extra token activation or timer-based restoration. No `UnblockAll` operation is added.

All added fact writes are `PTFRP0_*` diagnostics or `PostTowerFreeRoamActive`. No new writes to q307, TV/radio, air traffic, relationships, root state, quests, cyberware or despawn state. No teleport, root restart, PONR load, vendor restoration or fast-travel restoration.

## Wait and source-scoping evidence

**CONFIRMED static, not a runtime success claim:**

- Existing native CreditsRolling evaluator `0x26DCDF0` reads `UI_CreditsScreen.CredditsScrolling`; credits teardown `0x2879B94` clears it. Graph requires prior rolling via board node 13, false twice, and a valid Q307 arm/guard. A missing game/board can also produce false; the completion guard and runtime continuity observations are therefore essential. No claim that a false alone proves a live session or rendered UI disappearance.
- Enum registration `0x9A0888` distinguishes `Block=0`, `Unblock=1`, `UnblockAll=2`. Native node description `0x26E38AC` uses the supplied source for `Unblock '%hs'`; the all-source action has a separate description and branch. Vanilla SQ025 bugfix resources use named-source `Unblock`. Together these establish the source-specific operation contract used here; this is not the q306 all-source action.
- Native restriction validation `0x26E50CC` requires a source and valid IDs for Add/Remove operations, unlike the all-removal mode. Q305 supplies the working explicit-removal precedent.
- `IsTokensActivationBlockedBySource` is a native getter. Its registered thunk `0x1D0B2B0` dispatches to content-system slot `+0x1D8`; concrete getter `0x2706254` checks the supplied CName against the source collection using `0x2A66A0`. Logger records both the exact finalboards source and aggregate blocking. Other owners are not enumerated, and preservation of all unknown owners is not claimed as a completed runtime test.

These RVAs belong only to the executable hash recorded in `research/finalboards_dismissal_lifecycle.md`. No binary patch, detour, memory write or executable replacement is included.

## Logging and interpretation

Every `[PTFR]` JSON line includes a per-run monotonic sequence, run ID, UTC timestamp, accumulated update time, event/resource/node, and state snapshot. Each line is flushed to the logger's own `ptfr_runtime.jsonl`; the file is append-only across launches. Parser selects the latest run and checks sequence completeness. Do not relaunch before analysis, because that would make a new latest run.

Graph stage definitions are machine-readable in `events.json` and the build manifest. DR00 is logger startup. DR03 is naturally earlier than DR01/DR02; numeric labels are **not** chronological sorting keys. DR05 is after the guarded node-27 output branch; DR06 starts the wait. Native quest-node entry bodies themselves are not intercepted.

The logger registers read-only quest fact listeners through CET `NewProxy` and blackboard Bool listeners, with polling backup. It observes FinalBoards enter/leave/back/close, credits uninitialization, Idle entry, player attach/detach, engagement entry and exposed main-menu/save/checkpoint requests. No `Override` or gameplay setter is used. It retains no strong player/world/system object handles to manufacture continuity.

Snapshots record Q307 facts, `q307_2079`, `q307_main_game_killed`, gameplay HighLevel/tier, visibility-component state, player existence/entity ID/position, six effective status effects, finalboards/aggregate token blocking, attempted credits fields including LoadPonRSave (**UNKNOWN when this native board is not script-exposed**), saving-lock read where available, vehicle-system existence, phone-call state, map/hub facts and lifecycle counters. DR14 samples continuity; DR15 samples position/movement after activation.

Unavailable APIs/values are explicitly `UNKNOWN` with read errors. Menu availability, phone usability, vehicle usability, world AI activity, EP1 root state and Dogtown availability are not inferred from merely obtaining a system handle. Map/inventory need a brief human usability check. Actual rendered visibility and camera/control response need human observation too.

**Limits that must remain visible in analysis:**

- Listener timestamps are callback-delivery times, not guaranteed underlying native-write times. Polling can recover permanent markers but cannot reconstruct sub-sample write order. Parser labels this rather than inventing precise timestamps.
- DR11 means the corresponding quest action returned, not that its effective restriction vanished. Compare state reads.
- Native destination slot `+0x218` is not intercepted. No exposed load/menu call observed is **not proof** that no native call occurred. DR16 distinguishes front-end entry from an exposed request; DR17 is a save/checkpoint request with PONR attribution unknown.
- Matching player identity, no attach/detach, unchanged Tower state, false routing and the close/Idle path together support **INFERRED retained session**. No exact native session GUID or quest-system instance identity is available. A conclusive identity claim is not fabricated.
- Global content blocking may remain true while `finalboards` becomes false. That can be correct ownership-preserving behavior; do not clear other sources.

CET API implementation references: [NewProxy](https://raw.githubusercontent.com/maximegmd/CyberEngineTweaks/master/src/reverse/NativeProxy.cpp) and [observers/runtime bindings](https://raw.githubusercontent.com/maximegmd/CyberEngineTweaks/master/src/scripting/Scripting.cpp). Local vanilla scripts provide game-side listener signatures and snapshot getters. Offline LuaJIT mocks validate logger logic/API shapes, not live engine behavior.

## Pre-runtime validation

- Both resources cook/read back as CR2W v195.
- Existing root-node properties unchanged; exactly three original edges spliced across both resources; all other original edges retained, including 27 -> 28.
- New edges round-trip once; socket ownership/reciprocal connections verified.
- Guard, false routing, rolling conditions and two real-time delays inspected in cooked exports; no timeout path into restoration.
- Six identifiers checked by TweakDBID against both vanilla templates; exact source/action checked.
- Added facts/types inspected; no new Tower fact write, PONR load, root restart, media write or broad clear.
- Archive reopens with exactly the two intended paths; re-extracted packed bytes match the validated cooked files. No Phase 2A custom phase is included.
- LuaJIT 2.1 syntax/mock run passes; parser failure cases pass, including front-end, load, detach, stale markers, missing sequence, absent close observation, unknown UI state, early teardown, later user exit and a new logger run.
- `--check-ready` performs the inexpensive live recorder check after loading the fixture. It does not modify game state. This is necessary because offline mocks cannot certify the user's running CET environment.

### Recorder correction after the first live preflight

On 2026-09-21, the installed archive and CET logger were detected, but the pre-credits readiness check failed: 31/37 listeners registered. All 31 fact listeners worked. A second live preflight identified the actual issue: `GetAllBlackboardDefs().UI_CreditsScreen` is **unexposed in the user's current CET session**. The first failure did not establish that a valid credits board merely had not been created yet; that earlier explanation was incorrect. No ending test was run from either blocked state.

The corrected read-only recorder distinguishes `DEFINITION_UNEXPOSED`, `NOT_CREATED`, `AVAILABLE`, and `API_ERROR`. Six credits fields stay `UNKNOWN` when unavailable. It retries binding if the definition and board become available later and keeps bound credits listeners through player detachment. `FACT_LISTENERS_READY` documents the independent fact-listener set; `LISTENERS_READY` is emitted if credits listeners bind. Preflight accepts `DEFINITION_UNEXPOSED` only when fact listeners, archive, freshness, player reads, and registration requests for the key final-board UI observers pass. This is `READY (UI blackboard unexposed)`, **not** a claim that credits-field values or UI hook invocations were observed. Native `LoadPonRSave(false)` action return is tracked by DR02; credits dismissal is tracked by final-board close/uninitialization/Idle callbacks and user observation. The parser labels teardown from UI callbacks **INFERRED**, not directly confirmed. An API exception, incomplete fact listeners, stale markers, or missing archive still fails preflight. The logger remains observation-only; the archive is unchanged.

Autosave 18 is the selected disposable test fixture. A separate verified copy was made at `C:\Users\Ayong\Documents\Cyberpunk 2077 Save Backups\TowerContinued\AutoSave-18_20260921_190537`; it is not in the game save folder or repository. Do not edit that backup or use CET to force a mid-quest save.

On the next live preflight, CET encoded the empty `read_errors` Lua table as `[]`; the Python checker expected `{}` and raised `AttributeError`. The checker now treats **only an empty array** as an empty error map and rejects nonempty arrays. Offline tests pass, and the checker returned `READY (UI blackboard unexposed)` against the live Autosave 18 session. This change is workspace-only; it does not require a game restart or CET reload.

## Single watched-credit procedure

1. Close the game; remove the prior Tower Continued DIAG archive. Install this archive and the approved logger folder in the locations above.
2. After installing the corrected CET logger and restarting the game, load disposable **Autosave 18**. Wait a few seconds, then run `tools/Check_Phase2B_P0_Logger.cmd`. Proceed only if it begins with **READY**. `READY (UI blackboard unexposed)` is expected with this CET build; its credits fields remain unknown, and the experiment relies on quest markers plus final-board UI callbacks and the user's visible observation. If it says **NOT READY**, stop before the ending and report its specific reason; no replay is needed.
3. Play thug/Misty/final sequence normally. **Watch credits; do not skip or accelerate them.**
4. Allow automatic completion. Press a normal completion/Continue prompt only if actually offered after credits; there is no custom Continue popup. If the Cyberpunk title/engagement screen appears, do not select main-menu Continue or load a save.
5. After the result stabilizes, report only what logs cannot reliably establish: black screen versus rendered world, camera/player visibility, whether looking/walking works, whether map/inventory actually open, and any freeze. Do not use repair commands, change equipment, fast travel or save.
6. Leave the result running for about **30 seconds** to capture post-result samples, then quit normally without saving. That observation interval is not part of the quest trigger. Do not relaunch. Say **test complete** and include those brief visual/control observations. If the game is genuinely unresponsive, report that rather than attempting recovery; flushed logs remain useful.

## Automatic follow-up on “test complete”

Run `tools/analyze_phase2b_p0.py` using the configured Python runtime. It reads the installed logger output and writes `research/phase2b_p0/runtime/analysis.json` and `analysis.md` in this workspace. No existing runtime parser was present in the inspected tools directory, so this dedicated parser was added rather than pretending a static resource parser already handled runtime logs.

The agent then reads the report plus the CET/framework logs around this run, reconstructs delivery order, compares arm/post-teardown state, checks load/front-end/lifecycle evidence, identifies the last stage, and updates this document/PROJECT with **OBSERVED / INFERRED / UNKNOWN** results and the human visual observations. No new run or fix is authorized automatically. Missing instrumentation or uncertain identity stays unresolved; it must not be converted into a successful result.
