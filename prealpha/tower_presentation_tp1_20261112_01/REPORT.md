# TP1: arms handback candidate and fast-travel investigation

TP1 candidate 02 is now installed over RD1 following explicit user approval. See the [installation report](deployment_01/REPORT.md) for the exact manifest and preservation verification. It adds one native first-person representation handback during the existing fresh Tower treatment and bounded presentation diagnostics. The arms repair is **not verified in gameplay**; the fast-travel blackout has **no confirmed cause or repair yet**.

## Reported session

The user reports Machine Gun works. The 12 November 17:42–17:54 Toronto session records `mq007_done` changing from 0 to 1 at 17:52:04. Accept that specific fixture; do not repeat it or infer other stages, reward counts, reload behavior or Moving Heat success.

The user reports missing arms immediately after the ending. R1 logged the stock attachment refresh at 17:47:33 and attachment confirmation at 17:47:34. That confirms a logical slot, not a visible mesh. The user subsequently confirmed that reloading, or entering a car, switching to third person and exiting, restores the arms. This makes representation/visibility handback a stronger hypothesis than missing owned equipment; it does not establish the precise native state.

At 17:53:24 fast travel started from Watson Kabuki dataterm 07 toward the stadium. At 17:53:29 V's position had changed from `-1202.147461/1615.879028/22.903206` to `-1375.833618/-2122.794678/70.031357`. Both samples reported cover visible/released/popup as `false/true/false`; no `native-finished` callback was logged. The user says everything, including menus, was black. Simulation fact changes continued and shutdown was normal. The tracked setup popup is not supported as the cause of this occurrence.

Native `PerformFastTravel` teleports before `SetFastTravelStarted`, which calls native `UISystem.NotifyFastTravelStart`. The latter is not a script write of the three logged blackboard flags. Therefore the position change and false flags alone cannot identify the failed loading/fade stage. No loading flags or completion callbacks are forced by TP1.

Evidence: [pinned inputs](evidence_02/inputs.json), [session excerpt](evidence_03/session_excerpt.json), [user workaround](evidence_03/user_workaround.json). Evidence 01 is a preserved partial capture: it refused ArchiveXL's log symlink. Evidence 02 uses the exact dated regular log and completes the capture. All 51 installed Core hashes and 26 required dependencies match the RD1 manifest, SHA-256 `DCC4C8958756DDBA54C1F98404B96F2EBDF16E48F8CE3DEC6BB98A0DA6B30864`.

## Candidate 02

Only `PTFR_RestrictionsR1.reds` and `PTFR_LoadingCoverLC1.reds` change. The other 49 Core files, combined archive, XL registrations, RD1 quest entries and global-latest snapshot loader retain their exact bytes.

R1 queues `DeactivateTPPRepresentationEvent` once, only during its already-existing first-treatment hand refresh, after `PTFRPA2_Finished`, normal controlled V, settled customization and `CyberwarePolicy.Safe`. That guard excludes menus, combat, scenes/dialogue, workspots, mounted vehicles, time dilation, pending equipment and drawn weapons. The native event has a separate queued turn before the existing attachment check continues. It does not activate TPP, switch a vehicle camera or change the equipment/conservation implementation. Existing treatment receipts and persistent fields remain unchanged; completed-save loads do not rearm the first-treatment repair.

Matching vanilla `TakeOverControlSystem.EnablePlayerTPPRepresenation(false)` uses this event when returning the player from camera takeover, excluding an active vehicle TPP view. The matched engine registers its native handler through RVA `0x12a174c`, targeting `0x2aa7794`, with native state gating and representation teardown. This establishes an appropriate native handback mechanism, not proof that it resolves the reported failure. No engine patches, raw memory access or writes to native offsets are introduced. Source cache SHA-256 is `B78043064AE90FB80861B0D885D1C8DBCD22070F1DB71F20664D19F2D83C4AAC`; executable SHA-256 is `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`. Static exploration is retained under `native_01`–`native_12`; unlabelled native calls remain uncertain and are not a complete engine audit.

The observer records arm/player mesh enable flags, appearance, masks and render planes, plus roots and bounded child widgets for loading, menu, notification and HUD layers. It runs once three seconds after Ready and around up to three fast travels, with a hard ten-capture session cap. Each capture limits mesh and UI rows and nesting. Native callbacks, fade control, equipment, UI visibility and gameplay writes in LC1 remain unchanged. These field readbacks still do not prove final rendered pixels.

## Validation and remaining work

All **148 registered REDscript sources compile** in [compile 02](compile_02/result.json). The [bounded assessment](assessment_02.json) verifies the exact two-script delta, persistent field preservation, unchanged item-handling implementation, native handback guards and read-only observer calls. Candidate 01 and compile 01 preserve the earlier diagnostic-only proposal; its source pins are retained under `evidence_03/source_01` and it is superseded.

Deployment is prepared separately with exact baseline/compile pins, 51-file ZIP readback and private rollback storage. All **18 fresh deployment/recovery fixture actions passed**, including actual payload rollback, interruption recovery and game-running refusal. The real read-only [preflight](deployment_01/preflight_01.json) returned `PREFLIGHT_READY` with the game/launcher closed and exact baseline/source inputs. See [readiness](readiness.json) and [checkpoint](checkpoint.json). Preparation made no real game/save writes. The subsequent authorized installation replaced only the two reviewed scripts, preserved all 361 save files and verified rollback readiness; no game was launched. File rollback is not save rollback.

The next live check is one fresh genuine Tower handoff and one fast travel, described in the [test card](TEST_CARD.md). Full-screen blackout cause, arms visual correctness and runtime observer behavior remain unverified. Moving Heat and broad quest-restoration qualification are separate outstanding work.
