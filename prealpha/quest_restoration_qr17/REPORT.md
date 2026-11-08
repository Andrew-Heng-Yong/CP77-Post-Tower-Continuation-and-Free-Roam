# Portable Brendan stage-start fallback

QR17 implements the stage-start policy for the handoff from **Spray Paint** to **Coin Operated Boy**. Eligibility comes from the current player's settled in-game facts and journal. The code has no saved file path, save name, body hash, player identifier or requirement for a pre-ending Brendan snapshot. Two consistent samples and the existing common post-Tower, startup, support and player-safety checks govern the new admission.

## Scope

- The original Dumpster quest and its required objectives must have succeeded. Spray Paint and its required objectives must also have succeeded. Coin Operated Boy and its recorded objectives must still be Inactive. Current actor/story facts exclude prior clerk decisions, finished history and an active final scene.
- The fallback takes the beginning of the already-earned handoff as the resume point. It starts the full six-game-hour delay, so elapsed time on a lost prior timer is intentionally discarded. It then waits for the native outside-area condition.
- The fallback runs the original post-Spray hooligan deactivation and POI cleanup, then enters the unmodified native body through `brendan_gone`. That input reaches `root:28.In1`, the same Coin Operated Boy phase entry as normal Spray Paint completion. This avoids rerunning Dumpster or Spray Paint and leaves the original Coin Operated Boy dialogue, choices, rewards and cleanup in control.
- Fresh Dumpster stays excluded. Active or completed Coin Operated Boy and previously claimed PTFR owners are excluded from this new branch. QR13's exact earned peaceful final-Theo branch keeps its earlier certificate and native safety predicates. This candidate adds one portable fallback, with earlier partial encounters and other outcomes still outside its coverage.

## Implementation

The two stable-file replacements are the consolidated archive and `PTFR_SideJobsS23.reds`. There are no new depot paths or ArchiveXL registrations. The only replaced archive resource is the existing private MQ037 wrapper. The vanilla resource remains the resolved body.

Root nodes `1002/1004` each gain an OR alternative. The two old branches match their exact predecessor predicates after normalization. A new guarded route out of `1100.False` selects either the existing refusal or the new handoff. A private pending marker records selection of the one-shot support-holder output. Both QR13 and QR17 use holder `1110` and the same native support references. The fallback copies exact native delay, trigger, spawn cleanup and POI payloads from original `root/25:38/39/40/36`.

The gate rechecks earned status and common Tower safety after the wait. A failed recheck clears the private pending marker and releases the holder. A successful recheck writes the existing private Issued receipt before dispatch, writes Entered before entering the body, and leaves the existing holder release and Finished paths to handle native completion. The fallback writes no native facts and grants no direct reward. Reload behavior of the pending timer, actual prefab availability and live actor or journal delivery remain untested.

## Verification

- The original gate rejected the earned post-Spray witness. The serialized successor accepted it. Fifteen negative cases rejected missing earned history, failed Spray, active or completed Coin, active objectives, prior private ownership, outstanding support, missing Tower cleanup and conflicting native state. The original final-Theo branch, root entry and support-holder subgraphs were compared against the exact QR13 readback.
- The isolated SCC compile used all 148 currently registered sources. The compiler output and installed cache/input pins are recorded in [compile evidence](compile_01/result.json).
- The complete staged archive was reopened and all 1,577 payloads extracted and hashed. The verified ZIP has 51 paths, with 49 exact predecessor package files, 1,576 unchanged archive members and unchanged XL. All 77 pinned installed paths and six protected save files matched after staging. [Typed verification](verification.json) and [package manifest](candidate_01/package_manifest.json)

## Runtime qualification

No eligible save is currently proven. The earlier AutoSave-8 evidence has neither verified earned Dumpster/Spray Paint completion nor a qualifying unclaimed wrapper. It stays outside this fallback. On a genuine eligible post-Tower fixture, the useful test would check one six-game-hour wait, approach to Theo, activation of Coin Operated Boy, and persistence through one save/reload during the wait. The staged candidate requires separate authorization for any installation.
