# JB2 Batch 3 implementation

9 November 2026. The verified successor is `candidate_02` on installed JB1. [Core51 ZIP](JB2_Core51_02.zip) · [Package manifest](candidate_02/package_manifest.json) · [Gameplay test card](TEST_CARD.md)

The build removes 46 Johnny and 24 V speech events from seven quests. Sixteen of V’s events belong to the approved whole-exchange cuts in Space Oddity, Happy Together and Violence. The two explicit Sacrum Profanum option cuts are scoped to their own scenes. The epilogue removes the entire branch induced by “What’s your take, Johnny?” [Reviewed selections](../johnny_video_review_20261108_02/review_01/selection_02.json) · [Exact resource edit plan](input_02/plan.json)

| Quest | JB2 change |
| --- | --- |
| Space Oddity | After the actual package pickup, V reacts to the painting and the scene signals native completion and cleanup. The Johnny conversation choices are bypassed. The corpse scene’s silent actor binding and combat callers to the original pod scene are scoped to the private cleanup. |
| Happy Together | V interacts with Andrew’s plaque using the two original situational captions. V’s observations follow either selection. The authentic plaque focus and walk-away paths share one discovery reward latch. The scene uses the plaque for distance and keeps the original completion ports. |
| Spellbound | Open and Take keep their original world and item actions. V’s stash reaction and the genuine pickup feed the native handoff to Nix. The deleted exchange’s Nix-knowledge fact write is bypassed. |
| Violence | The existing security/Liam route advances past the Johnny exchange and Talk to Johnny objective. Two separate inner-dialogue dispatches that target Johnny are disconnected. Camera, footage and Lizzy callbacks keep their native conditions. |
| Bullets | Johnny’s spawn actions, visuals, waits and selected speech are removed. Surviving events keep their authored timing. The native Zane, MaxTac and customer cleanup sequence is preserved. |
| Sacrum Profanum / Losing My Religion | Johnny’s hook, rescue and epilogue exchanges are cut, including the middle-finger option and the epilogue option with its entire reply branch. The monk conversations, outcomes, reward and player control callbacks remain. |
| I’m in Love with My Car | The existing approach trigger emits the investigation callback and closes the Johnny scene after 50 ms. The investigation and vehicle unlock retain their authored conditions. |
| The Prophet’s Song | R6.3 excludes both new PTFR admission routes. Existing issued owners and earned history are preserved. |

The private scenes disable Johnny actor acquisition and remove actor-targeted events and workspot, spawn, camera and scanner actions from the edited paths. This targets the digital spawn effect, title, scan result, cigarette and smoke at their actor source. The earlier `candidate_01` is preserved as an offline draft. The selected successor adds the Space Oddity combat caller and Violence’s two separate dispatch cuts. [R6.3 policy](../../docs/whitelist_prophets_song_20261109.md)

The archive contains 1,603 resources. Eleven existing private resources change and 22 private aliases are added. All 1,570 other JB1 payloads match their original hashes. The build verifies 71 source-provider pins and 22 new keys across 134 installed archives. ArchiveXL registration bytes are identical and there are zero new injected node IDs. The consolidated archive and two existing REDscript files are the only package replacements. All 148 registered scripts compile with the two overlays, and every Core51 ZIP member passed hash verification. [Readback and providers](archive_readback_02.json) · [Cooked and bounded flow verification](verification_02.json) · [Compile result](compile_01/result.json)

Thirteen bounded scene fixtures and 22 isolated deployment actions pass, including exact-package install and rollback and interruption after two replacements. The read-only preflight verified the JB1 installation, 26 dependency files, 313 save files and a fresh recovery path with the game and launcher closed. [Deployment fixtures](fixture_results.json) · [Readiness](readiness.json) · [Preflight](preflight_02.json)

JB2 is staged for separate closed-game installation authorization. Live presentation, the quest routes and saves already executing native child phases or scenes await gameplay qualification. The offline fixtures model authored signals and exact files, with game-engine behavior reserved for live testing.
