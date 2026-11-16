# Sweet Dreams SD1 — Johnny presentation cleanup

SD1 is installed over KM2. The user authorized installation with the game closed on 8 November 2026. The accepted KOLD MIRAGE edit remains byte-identical.

## Implemented scope

The user reviewed Sweet Dreams and requested no gameplay sequence rewrite. SD1 retains the existing speech cuts and disables Johnny's actor acquisition in the private scavenger scene. This targets his entity/shadow, spawn/glitch effect, name/title, scanner identity, cigarette and smoke together. Thirteen Johnny animation/gaze/presentation events and his section actor behaviors are removed. The scene has no independent prop or effect instances; its cigarette workspot and the actor initialization are left unreachable.

Only dependencies on the absent actor change: scene entries bypass Johnny acquisition/workspots; a wake-up auxiliary Johnny camera/comment/attachment branch is disconnected; four Johnny-bearing scene callers disable speaker-distance interruptions. Scav chatter keeps its original interruption behavior.

The existing gameplay and cleanup exit names and IDs remain. Three former Johnny camera-focus waits now deliver their original terminating cleanup exits after a 50 ms timer, following the original nonterminating gameplay exit. This retains both inputs of the native payback AND gate. Dropping the cleanup exit would strand that gate. The elevator still waits for the player to enter its native trigger.

V's recovery/get-up animations, retained V/scav/Stefan speech and event timestamps, section durations, PC/gear choices, quest objectives, combat, equipment confiscation/retrieval, money/refunds and Stefan outcomes are preserved. There is no Talk to Johnny journal objective in the reviewed Sweet Dreams closure, so no journal replacement is needed. No scripts, XL registrations, native resources, new depot paths, saved IDs or quest receipt names change.

## Evidence and limits

- Fifteen current/native resources were captured with unique providers across 134 archive indices. [Source capture](source_01/manifest.json), [source analysis](analysis_02/summary.json).
- Both edited resources were cooked and decoded again. All 479 checks and 14 bounded signal/choice/AND fixtures passed. Every previously retained spoken event is exact; native inventory/journal/reward nodes are unchanged. [Verification](verification.json), [cooked readback](readback_01/manifest.json).
- All 1,581 archive members were extracted and hashed: two private resources changed and 1,579 remain exact. The full 51-path ZIP also passed member/hash/CRC checks. The other 50 package files are exact. [Archive readback](archive_readback.json), [package manifest](candidate_02/package_manifest.json).
- All 148 current REDS sources match the actual inputs of PE1's complete successful compile. No source changed and no new compilation ran. The normal sixteen-byte compiler timestamp refresh is recorded separately. [Compile inventory](compile_inventory.json).

These are source, serialization, package and bounded graph results. They do not prove engine spawning, scanner/render behavior, interruptions, save/reload or a live playthrough. No game launch or quest/save mutation occurred during preparation.

## Test state

The user's current screenshot reports `mq036_start=1`, `mq036_done=1`, `mq036_items_retrieved=1`, `mq036_cancel_bd=0`: completed, with equipment recovered. It does not identify the executing/saved owner. Clearing those four fields would not safely retire the controller or restore inventory ownership, so no reset command is supplied or executed. Installation preserves that completed state. [Observation](observations/current_completed_20261108_01/result.json).

The intended fresh test point is a genuine post-Tower working save before using Stefan's braindance player, with Sweet Dreams not already completed and its owner/gear state intact. No such fixture has been qualified in this task. No saved mid-scene migration is included. See the [test card](TEST_CARD.md); KOLD MIRAGE and the wider marker-count investigation need no repeat.

## Preserved preparation failures

The exploratory `analysis_01` reused a basename for native root and private wrapper normalized models; `analysis_02` corrected model names using scope and depot key. Original captures were distinct and unaffected. The first preparation removed the inline definition of a shared handle when unlinking an edge; normalization rejected it. `preparation_failure_01.json`, `input_01` and `candidate_01` are retained. Fresh `input_02`/`candidate_02` preserve the original handle map, passed cooking/readback and are selected. Neither failure touched the game or saves.

## Installed result

Closed-game preflight, installation, post-install verification and rollback readiness passed. Only the existing consolidated archive changed. All 51 Core files and 26 dependencies verified; all 313 save files and unmanaged game metadata were preserved. The exact KM2 archive recovery copy is verified. Twenty-two installer actions across eight isolated fixtures passed, including full Core51 install/rollback, interrupted replacement/receipt/rollback recovery and game-running/unknown-file refusal. No game launch, save/fact edit or real rollback occurred.

Archive SHA256: `748447DAC5B8A02EA2B79F6CF40E4250A9E9CF5406F85D6B62DE5D3078910CC2`. [Installed manifest](deployment_01/installed_manifest_01.json), [preservation](deployment_01/verification.json), [deployment report](deployment_01/REPORT.md). Live Sweet Dreams testing remains pending a supported fixture; KOLD MIRAGE remains accepted complete.
