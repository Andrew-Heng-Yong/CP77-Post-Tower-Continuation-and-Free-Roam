# WO2 fresh-load street cleanup — 16 November 2026

**INSTALLED_VERIFIED; AutoSave-16 gameplay retest pending.** The user found the same raised road and sidewalk meshes immediately after loading the completed-ending AutoSave-16, without travelling away. WO2 makes the existing WO1 native variant cleanup eligible near the street on a qualified free-roam load. No save, archive, ArchiveXL registration or vanilla resource was edited. [Exact installed manifest](installed_manifest_01.json) · [Offline assessment](candidate_01/assessment.json) · [Live test](TEST_CARD.md)

## Cause in the reported save

The original WO1 driver required the player to be more than 500 metres from (-1475, 1080). AutoSave-16 is 106.5 metres from that point. Its serialized facts include genuine Tower completion, `PTFRMV_Applied=1` and `PTFRWO1_CleanupRegistered=1`; `PTFRWO1_CleanupDone` has no saved entry. The saved quest stores retain WO1 child path `[1,42351]`, child node 2 and EP1 parent node 42351 in EventManager. The registered child node is WO1's pause condition. This is positive evidence that the original phase was waiting in the saved body; a fact alone would not establish that.

Those saved facts and handlers explain why the old distance guard could leave the duplicate variant present after an immediate load. They do not prove the exact live value of every defaulted fact or that the new action has run. [Read-only saved facts](candidate_01/saved_facts_01.json) · [Read-only phase membership](candidate_01/saved_phase_02.json) · [Original phase](../world_overlap_20261116_01/work/graph_01/readback.json)

## Change

WO2 changes only `r6/scripts/PTFR_Consolidated/PTFR_MistyViktorAuto.reds`. The street cleanup permit now uses a dedicated on-foot, attached-player safety check without the clinic's separate distance restriction or WO1's 500-metre restriction. It still requires genuine post-Tower completion, applied world restoration, the registered WO1 owner, no prior WO1 dispatch, and no combat, scene, workspot, vehicle, content-activation or save lock. `OnAttach` tries the permit promptly when the player and systems are ready; the existing poll remains the fallback. The clinic's original `Safe` method, poll cadence, story facts and saved class fields are unchanged.

The existing WO1 phase still dispatches the exact authored pair on the exact compiled decoration owner: `q307_final_scene=false` and `q307_final_scene_hide=true`. That pair removes the final-scene translated street and restores the ordinary street variant. It includes the original collision and scene decoration lifecycle. The existing WO1 one-time `Done` receipt is preserved, and completed ManualSave-33 remains excluded from a repeat dispatch. [Staged script](candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_MistyViktorAuto.reds) · [WO1 source review](../world_overlap_20261116_01/REPORT.md)

## Verification and limits

- All 149 currently registered REDscript sources compiled offline with the single script overlay.
- Twenty-six source, save, handler, native-phase and predecessor checks passed. AutoSave-16 is the positive saved fixture; ManualSave-33's already-done state and EndGameSave-106's pre-restoration state are negative controls.
- Three isolated transaction fixtures passed exact replacement and rollback, interrupted replacement recovery, and unknown-drift refusal.
- Guarded installation changed one of 51 Core paths. Independent readback verified all 51, 47 protected dependencies, 14 updated IFP files, four preferences and 469 unchanged save files. The game and launcher were closed; no game was launched or save written. An exact old-script backup and rollback action are ready. [Installation plan](install_plan_01.json) · [Receipt](installed_01.json) · [Fixture results](fixture_results_01.json)

The user will test AutoSave-16 later. Successful compilation, saved handler membership and installed hashes do not prove the street is visually or physically clear after load. The precise timing of `OnAttach` versus world streaming is unobserved, so a short initial appearance remains possible. Removing the final-scene variant close to V may briefly settle V onto the ordinary collision surface. A separate fresh-load test of a save with `PTFRWO1_CleanupDone=1` is still needed before claiming general reload persistence. The frozen v0.2.1-beta release copy predates WO2.
