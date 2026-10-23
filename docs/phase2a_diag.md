# Phase 2A-DIAG — watched-credit hook instrumentation

## Purpose

This diagnostic build determines how far the Q307 final-board graph executes. It adds only five mod-owned diagnostic facts and five warning messages. It does not restore gameplay state, write vanilla facts, change q307 state, alter restrictions/tokens, change tier or visibility, change TV/radio, restart quest roots, or call PONR logic.

Do not use this build for skipped-credit testing.

## Archive

```text
build\TowerContinued_Phase2A_DIAG.archive
```

Build SHA-256:

```text
39B8B9F95F8133B1C4137237BB52E68BD66D76C45B52E186013CB769FCCAFADB
```

The archive contains exactly:

```text
base\quest\main_quests\epilogue\final_boards.questphase
towercontinued\quest\post_tower_hook.questphase
```

Do not install it at the same time as `TowerContinued_Phase2A.archive`; both archives own the same two depot paths.

## Instrumentation points

| Point | Exact/closest location | Fact written exactly to 1 | Visible message |
|---|---|---|---|
| A | Node 55 `q307_ending_board.questphase` `Out1`, before Q307 rejoins node 53 | `PostTowerDiag_EndingBoardReturned` | `[PTFR DIAG A] Q307 ending board returned` |
| B | Between node 53 `Out1` and node 27 `In` | `PostTowerDiag_Node27Entered` | `[PTFR DIAG B] Node 27 input reached` |
| C | Node 27 `Out`, before the Q307 guard | `PostTowerDiag_Node27Out` | `[PTFR DIAG C] Node 27 Out reached` |
| D | Q307 guard node 56 `True`, before phase node 57 `In1` | `PostTowerDiag_GuardTrue` | `[PTFR DIAG D] Q307 guard true` |
| E | Mod-owned phase input node 0 `Out`, before its one-shot condition | `PostTowerDiag_ModPhaseEntered` | `[PTFR DIAG E] Mod phase entered` |

Point B is the closest valid graph-level instrumentation for “node 27 entered.” The native node has an `In` socket, its native action, and an `Out` socket; there is no separate editable node-body entry location. Therefore B is placed immediately before `27.In`. B=1 proves that execution reached the incoming edge and was handed to node 27 after the B warning node completed.

Each point executes its exact fact writer before its visible message, so the fact can prove execution even if final-board UI suppresses the warning.

## Resource and node changes

### Patched `final_boards.questphase`

The validated Phase 2A nodes remain:

- 56: completed-Q307 guard;
- 57: mod-owned phase call;
- 58: join returning to vanilla node 28.

Diagnostic nodes added:

| Point | Fact node | Message node | Replaced edge |
|---|---:|---:|---|
| A | 59 | 60 | `55.Out1 -> 53.In1` |
| B | 61 | 62 | `53.Out1 -> 27.In` |
| C | 63 | 64 | `27.Out -> 56.In` |
| D | 65 | 66 | `56.True -> 57.In1` |

The false guard branch and final join remain:

```text
56.False -> 58.In1
57.Out1  -> 58.In2
58.Out1  -> 28.In
```

Thus both guard outcomes still return to the original vanilla node-28 fade.

### Mod-owned `post_tower_hook.questphase`

Point E adds:

- node 6: exact writer `PostTowerDiag_ModPhaseEntered = 1`;
- node 7: `[PTFR DIAG E] Mod phase entered` warning.

It replaces:

```text
0.Out -> 1.In
```

with:

```text
0.Out -> 6.In -> 7.In -> 1.In
```

The existing one-shot check, original `Tower Continued hook reached.` warning, `PostTowerFreeRoamHookSeen = 1` writer, and phase output are unchanged.

## Expected execution

```text
q307 ending-board phase node 55 returns
        ↓
A fact + message
        ↓
shared hub node 53
        ↓
B fact + message
        ↓
node 27 questFinalBoardsVideosFinished
        ↓
C fact + message
        ↓
completed-Q307 guard
        ├─ false → join → vanilla node 28
        └─ true
             ↓
          D fact + message
             ↓
          mod phase
             ↓
          E fact + message
             ↓
          existing one-shot diagnostic
             ↓
          join → vanilla node 28
```

## Interpretation

| Facts after the run | Interpretation |
|---|---|
| A=0, B=0, C=0, D=0, E=0 | The instrumented Q307 return edge was not reached. The likely fork is “patched resource was not active” versus “node 55 never returned through `Out1`.” |
| A=1, B=0 | The q307 ending-board phase returned, but execution did not reach the edge immediately before node 27. Inspect the A message node and shared hub path. |
| A=1, B=1, C=0 | Execution was handed to node 27, but node 27 did not return through its `Out` socket. This would confirm the native final-board action/menu transition as the blocking boundary. |
| A=1, B=1, C=1, D=0 | Node 27 returned, but the Q307 guard true branch was not reached. Compare the four read-only Q307 facts at that moment. |
| A=1, B=1, C=1, D=1, E=0 | The guard passed, but the mod-owned phase input did not execute. Investigate phase resource loading/reference/socket lifetime. |
| A=B=C=D=E=1 | The full hook path executes. Missing visible messages would then be a separate final-board UI presentation problem. |

Because every fact writer precedes its matching message, a fact can be 1 even if execution stalls or transitions away while processing that point's warning message.

## Build validation

The build script verified:

- both cooked resources decode as CR2W v195;
- all five unique fact writers set exact value 1;
- all five message strings are unique and visible-warning nodes;
- every instrumented edge round-trips;
- the original node-28 fade join remains connected;
- the archive reopens with exactly the two intended resource paths.

Validation output:

```text
research\phase2a_diag\validation\build_manifest.json
research\phase2a_diag\validation\final_boards.diag.json
research\phase2a_diag\validation\post_tower_hook.diag.json
```

Rebuild command:

```powershell
& .\tools\build_phase2a_diag.ps1
```

## Exact manual test procedure

1. Close Cyberpunk 2077.
2. Remove `TowerContinued_Phase2A.archive` from `archive\pc\mod` or move it outside the game directory. Do not leave both versions installed.
3. Copy `build\TowerContinued_Phase2A_DIAG.archive` to:

   ```text
   C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod\TowerContinued_Phase2A_DIAG.archive
   ```

4. Confirm that only `TowerContinued_Phase2A_DIAG.archive` is installed for Tower Continued.
5. Start the game and load the same disposable pre-Viktor save. Do not use the master save.
6. Play Viktor, the thug encounter, Misty, and the final sequence normally.
7. Watch the credits/final-board videos normally. Do not use the skip action.
8. Write down every `[PTFR DIAG X]` message observed and its order. Do not treat missing UI as proof that its fact remained 0.
9. If CET remains accessible before the main-menu transition, run this read-only command:

   ```lua
   local q=Game.GetQuestsSystem(); print("A="..tostring(q:GetFactStr("PostTowerDiag_EndingBoardReturned")).." B="..tostring(q:GetFactStr("PostTowerDiag_Node27Entered")).." C="..tostring(q:GetFactStr("PostTowerDiag_Node27Out")).." D="..tostring(q:GetFactStr("PostTowerDiag_GuardTrue")).." E="..tostring(q:GetFactStr("PostTowerDiag_ModPhaseEntered")).." HookSeen="..tostring(q:GetFactStr("PostTowerFreeRoamHookSeen")))
   ```

10. Allow the ending to continue without attempting to restore control. Record whether the normal final fade and main-menu transition occur.
11. Exit the game normally. Even if CET could not be opened in time, Fact Finder's `gamelog.log` should record every diagnostic fact transition that occurred.
12. Report the five fact values, visible messages, fade/menu result, and any error. Do not run the skipped-credit test yet.

Use this response sheet:

```text
PHASE 2A-DIAG WATCHED-CREDIT RESULT

Visible messages in order:
A visible: YES / NO
B visible: YES / NO
C visible: YES / NO
D visible: YES / NO
E visible: YES / NO
Original “Tower Continued hook reached.” visible: YES / NO

Facts:
PostTowerDiag_EndingBoardReturned =
PostTowerDiag_Node27Entered =
PostTowerDiag_Node27Out =
PostTowerDiag_GuardTrue =
PostTowerDiag_ModPhaseEntered =
PostTowerFreeRoamHookSeen =

Normal final fade occurred: YES / NO
Reached main menu normally: YES / NO
Freeze, black screen, or abnormal delay:
Errors shown or logged:
```

## Runtime result — watched credits

The instrumented watched-credit run on game 2.31 reached all five points. A read-only CET query made while the credits lifecycle was still active returned:

```text
A=1 B=1 C=1 D=1 E=1 HookSeen=1
```

No diagnostic warning—including the original `Tower Continued hook reached.` warning—was visible. After the credit roll, the tester supplied a Cyberpunk logo / `PRESS [Space] TO CONTINUE` screenshot and reported a normal final fade/main-menu transition, with no freeze, abnormal delay, or displayed/logged error. The screenshot's active scenario was not recorded. Phase 2A.5 found a separate pregame engagement screen consistent with that image; the previous identification as a still-active final-credits screen was unsupported.

Interpretation:

- **OBSERVED:** node 55 returned, node 27 was entered, node 27 traversed `Out`, the Q307 guard selected true, the mod-owned phase entered, and its original one-shot writer executed.
- **OBSERVED:** those graph operations completed during the credit roll. Whether the later Space prompt belonged to the ending session or the pregame engagement screen was not instrumented.
- **INFERRED:** `questWarningMessage_NodeType` presentation is suppressed or hidden behind `MenuScenario_FinalBoards` during this lifetime. The five fact writers prove that missing warnings were not missing graph execution.
- **CORRECTION:** node 27 is a reliable quest-graph execution point, but it is not a genuinely post-credit, user-visible activation boundary. Phase 2A.5 recovered it as a videos-finished notification; natural credits can terminate automatically. A future handoff must establish in-session UI closure without assuming a final key press. See `research/finalboards_dismissal_lifecycle.md`.

Phase 2A-DIAG stops here. Skipped credits remain untested, and no Phase 2B behavior is implemented.
