# Phase 2A — Minimal post-Tower hook proof of concept

## Scope and status

This build implements only a diagnostic handoff after genuine Q307 final-board completion. It does not restore gameplay, player visibility/control, gameplay tier, content tokens, TV/radio, quest roots, Dogtown, air traffic, cyberware, quests, PONR state, or One More Gig behavior. It does not write any q307 fact.

The cooked resources and archive pass structural validation. Runtime validation is still pending because the archive has not been installed in the Cyberpunk 2077 directory.

## Pristine source

- Vanilla depot path: `base\quest\main_quests\epilogue\final_boards.questphase`
- Untouched workspace copy: `research\phase2a\pristine\base\quest\main_quests\epilogue\final_boards.questphase`
- Original SHA-256: `AB38062475447BADFDADB9B294522B4A5407C89DEF118026D3009A3256D47738`
- Original size: 327,443 bytes
- Source archive extraction remains separately available under `research\q307_extracted\raw`.

## Vanilla resource patch

Patched depot path:

```text
base\quest\main_quests\epilogue\final_boards.questphase
```

Only the top-level edge from node 27 to node 28 is spliced. All 30 original top-level nodes remain present. A semantic comparison confirmed that every original node is unchanged after excluding top-level socket connection arrays.

Existing socket changes:

| Existing node | Socket | Before | After |
|---|---|---|---|
| 27 `questUIManagerNodeDefinition` / `questFinalBoardsVideosFinished_NodeType` | `Out` | node 28 `In` | new node 56 `In` |
| 28 `questRenderFxManagerNodeDefinition` | `In` | node 27 `Out` | new node 58 `Out1` |

Added nodes:

| Node | Type | Purpose |
|---|---|---|
| 56 | `questConditionNodeDefinition` | Logical-AND Q307 completion guard |
| 57 | `questPhaseNodeDefinition` | Starts `towercontinued\quest\post_tower_hook.questphase` through `In1`; returns through `Out1` |
| 58 | `questLogicalXorNodeDefinition` | Two-input join back into the original node-28 fade |

Added edges:

```text
27.Out    -> 56.In
56.True   -> 57.In1
56.False  -> 58.In1
57.Out1   -> 58.In2
58.Out1   -> 28.In
```

Q307 guard:

```text
q307_active == 0
AND q307_done >= 1
AND q307_finished >= 1
AND q307_2079 >= 1
```

The guard reads q307 state only. It does not set or clear those facts. A non-Q307 ending falls through node 56's false socket directly to the join and the original fade.

### Before

```text
node 27: questFinalBoardsVideosFinished
                  |
                  v
node 28: original zero-duration fade
```

### After

```text
node 27: questFinalBoardsVideosFinished
                  |
                  v
node 56: completed-Q307 guard
           /                 \
        true                 false
          |                    |
          v                    |
node 57: mod phase             |
          |                    |
          +--------+-----------+
                   v
            node 58: XOR join
                   |
                   v
node 28: original zero-duration fade
```

## Mod-owned resource

Resource:

```text
towercontinued\quest\post_tower_hook.questphase
```

It contains six nodes:

| Node | Type | Behavior |
|---|---|---|
| 0 | `questInputNodeDefinition` | External input `In1` |
| 1 | `questConditionNodeDefinition` | Reads `PostTowerFreeRoamHookSeen == 0` |
| 2 | `questUIManagerNodeDefinition` / `questWarningMessage_NodeType` | Shows `Tower Continued hook reached.` for five seconds |
| 3 | `questFactsDBManagerNodeDefinition` / `questSetVar_NodeType` | Sets exact `PostTowerFreeRoamHookSeen = 1` |
| 4 | `questLogicalXorNodeDefinition` | Joins first-run and already-seen paths |
| 5 | terminating `questOutputNodeDefinition` | External output `Out1` |

One-shot flow:

```text
0.Out -> 1.In

1.True -> 2.In -> 3.In -> 4.In1
1.False -----------------> 4.In2

4.Out1 -> 5.In
```

`PostTowerFreeRoamHookSeen` is the only new persistent fact. On its first execution the phase shows the diagnostic and sets the fact to exactly 1. When the fact is already 1, the phase skips both the message and writer and immediately returns to vanilla node 28.

## Build

Run from the workspace root:

```powershell
& .\tools\build_phase2a.ps1
```

The script:

1. reads only the pristine resource as its patch source;
2. verifies the original node-27-to-node-28 edge shape;
3. constructs the guard, phase call, join, and mod-owned phase from WolvenKit RED4 types;
4. cooks both resources as CR2W v195;
5. decodes them again and verifies every required condition, fact, edge, and phase reference;
6. verifies all 30 original nodes apart from their top-level connection arrays;
7. packs the two resources;
8. reopens the archive and requires exactly the intended depot paths.

Output:

```text
build\TowerContinued_Phase2A.archive
```

Validation artifacts:

```text
research\phase2a\validation\build_manifest.json
research\phase2a\validation\final_boards.graph_diff.txt
research\phase2a\validation\final_boards.original.json
research\phase2a\validation\final_boards.patched.json
research\phase2a\validation\post_tower_hook.json
```

Current cooked-resource hashes:

- patched `final_boards.questphase`: `26775342D6B29D9414E6195FA7C0D8CAD3821AC3438DA924E6392ED52F2CBDB1`
- mod-owned hook phase: `84AA5419BD4D3425094F1346AB512B2077A95ECCD778433A1F3DB00B62F67C7E`

The archive container hash can change between builds because archive metadata is regenerated; use `build_manifest.json` for the latest value.

## Install procedure

The archive has not been installed by this task. For a runtime test, close the game and copy only:

```text
build\TowerContinued_Phase2A.archive
```

to:

```text
C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod\TowerContinued_Phase2A.archive
```

No loose vanilla resource should be copied or overwritten. A read-only collision scan found no currently installed mod archive that contains `base\quest\main_quests\epilogue\final_boards.questphase`.

## Runtime test protocol

Use distinct disposable pre-ending saves for watched and skipped credits so no q307 fact or mod marker needs to be reset manually.

For each Q307 path, record:

1. whether credits complete through the ordinary watched/skip action;
2. whether `Tower Continued hook reached.` appears exactly once;
3. whether Fact Finder or a read-only CET query reports `PostTowerFreeRoamHookSeen == 1`;
4. whether the original final fade still executes;
5. whether the ordinary ending/menu behavior remains intact;
6. any game, CET, redscript, RED4ext, ArchiveXL, or WolvenKit error.

Reload the resulting disposable save if the game permits a post-ending save to be produced. The message must not appear again when the marker is already 1.

For non-Q307 isolation, use a separate disposable save from another ending. The diagnostic must not appear and `PostTowerFreeRoamHookSeen` must remain 0. If a complete alternate-ending run is impractical, this remains structurally validated but not runtime-confirmed.

## Rollback

Close the game and remove exactly:

```text
C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod\TowerContinued_Phase2A.archive
```

No vanilla file restoration is needed because the package shadows the resource through the normal mod archive path and does not overwrite a vanilla archive. Test saves in which `PostTowerFreeRoamHookSeen` was set retain that inert mod-owned fact; use the untouched disposable-save source for clean retesting.

## Current evidence

- **CONFIRMED structurally:** both resources decode successfully as CR2W v195; the Q307 guard and mod phase reference round-trip; the one-shot condition, message, exact marker write, return path, and original fade edge round-trip; the archive contains only the two intended resources.
- **CONFIRMED structurally:** non-Q307 paths take the guard's false branch and still reach node 28 without executing the mod phase.
- **RUNTIME FAILED — watched credits, game 2.31:** using disposable Manual Save 10 from before entering Viktor's clinic, Viktor, the thug encounter, Misty, the final scene, credits, and final-board videos all completed normally. The diagnostic did not appear, and the game returned to the main menu normally.
- **CONFIRMED from the Fact Finder/CET game log:** during that run, `q307_done` and `q307_finished` changed from 0 to 1 at 22:22:29, `q307_active` changed from 1 to 0 four seconds later, and `q307_2079` had already changed from 0 to 1. No `PostTowerFreeRoamHookSeen` change exists in the log.
- **CONFIRMED installation:** the installed archive SHA-256 matched the build (`C98411E64CF8B9C2F6096058C39BAE70C764E08E178C616B8EB8B0BCE0F0584F`), and a scan of all installed mod archives found no competing override of `final_boards.questphase` or the custom hook path.
- **INFERRED:** the four Q307 guard values were valid before final-board completion, so an ordinary false evaluation of the fact guard is unlikely to explain the missing diagnostic.
- **UNKNOWN:** whether the running quest used the patched `final_boards.questphase`, whether node 27's native final-board action ever traversed its `Out` socket before the menu transition, and whether the mod-owned phase reference was requested. These must be separated with a targeted diagnostic build before changing architecture.
- **NOT RUNTIME-TESTED:** skipped credits, marker persistence/reload, and non-Q307 isolation. The original node-28 fade is structurally preserved, but its execution through the added path was not demonstrated because the hook path did not run.

### Phase 2A-DIAG resolution

The instrumented watched-credit rerun resolved the unknown execution fork: all points A–E and `PostTowerFreeRoamHookSeen` were 1. Therefore the patched resource was active, node 27 traversed `Out`, the Q307 guard passed, and the mod-owned phase launched successfully. **OBSERVED**

The warnings remained invisible, and this full graph path executed during the credit roll. UI suppression/occlusion is an **INFERRED** explanation, not a confirmed mechanism. The later `PRESS [Space] TO CONTINUE` screenshot may be the pregame engagement screen; its active scenario was not logged. Node 27 is not a sufficiently late user-visible activation boundary. Phase 2A.5 recovered it as a notification rather than a wait and found an automatic native credits-termination path. See `research/finalboards_dismissal_lifecycle.md` for the corrected closure/destination analysis.

The original Phase 2A archive is structurally sound as a quest execution proof, but its warning is not a viable post-credit presentation mechanism at that location. Skipped credits, reload persistence, and non-Q307 runtime isolation remain untested.
