# WO1 street overlap cleanup — 16 November 2026

**INSTALLED_VERIFIED; gameplay pending.** WO1 adds guarded post-Tower cleanup for the displaced final-scene street set between Viktor's clinic and Afterlife. Installation completed at 16:30 UTC with the game and launcher closed. The current epoch is `WO1_STREET_OVERLAP_CLEANUP`, succeeding `KM3_KOLD_PREPARED_ENTRY`.

[Installed manifest](work/deployment_01/installed_manifest_01.json) · [Independent verification](work/deployment_01/verify.json) · [Gameplay test](TEST_CARD.md)

## Finding and scope

The user reported raised, translated duplicate roads and sidewalks with collision. Both supplied World Inspector captures match current 2.5 resources, indices and transforms:

| Example | EP1 compiled sector | Definition / instance | Position |
| --- | --- | --- | --- |
| `wlc_01_crossroad_02.mesh` | `exterior_-1_0_0_5.streamingsector` | 87 / 120 | -1407.215, 888.410, 0.357 |
| `br_1c2d1b36_rt_1x1_with_right_sidewalk_24m.mesh` | `exterior_-12_8_0_1.streamingsector` | 0 / 0 | -1480.136, 1149.382, 19.207 |

The audit found **43 matching asset/rotation/scale pairs**, with a common translation of approximately **(-0.86535, +0.96045, +0.357322) metres**, within 4 mm tolerance. Both examples match this offset. These pairs include roads, curbs, sidewalks, retaining walls, stairs and three lamp proxies. They belong to the native `q307_final_scene` decoration variant at:

`$/03_night_city/c_watson/little_china/wlc_01/wlc_01_b_env_prefab6TCITNI/#wlc_01_b_decoration`

The bounded census examined 16 current sectors, resolving 27 provider hits against 135 installed archive indices. It retained the installed R8 clinic-sector override when selecting the current provider. The affected owner has 49 variant range records covering 1,439 placements across its final-scene and ordinary-street variants. Those placements include collision, cinematic props, vehicles, lights and workspots; 43 is the matching-mesh count, not a count of all objects removed. None of the 31 inspected private world sectors references either reported mesh.

[Pinned source audit](work/audit_01.json) · [User captures and tool observation](work/observations_01/user_report.json)

The captures also provide a later, bounded observation that Red Hot Tools RC7's World Inspector displays native node details. They do not qualify every tool function or the repair's result.

## Repair and lifecycle

Native q307 cleanup already authors `q307_final_scene=false` and `q307_final_scene_hide=true` for this decoration set. WO1 dispatches that same pair at the exact compiled owner above. Native cleanup uses a different owner spelling; runtime alias equivalence and why its cleanup did not remove the reported overlap remain unknown.

The new private phase, `towercontinued\street_overlap_wo1\cleanup.questphase`, has eight nodes and no support prefabs. It waits for existing genuine post-Tower completion and world-restoration guards, then checks them again immediately before dispatch. The existing Misty/Viktor driver grants a private permit only when restoration is applied, the player is outside combat/scenes/workspots/vehicles and content/save locks, and the player is more than 500 metres from (-1475, 1080). The permit is cleared on attachment and refreshed on the existing two-second poll.

Cleanup uses the original variant lifecycle, including associated collision and cinematic props/vehicle spawners. It does not issue individual actor commands or transplant an unfiltered prefab into a new owner. The separate WLC03 FX owner, private clinic/Zetatech restoration and existing story, quest, reward and history logic remain unchanged. The new `PTFRWO1_CleanupDone` receipt records dispatch; it is not evidence of visual or collision removal. Save/reload persistence still needs a live check.

Only three installed paths changed: the combined archive, its additive ArchiveXL registration, and `PTFR_MistyViktorAuto.reds`. All 1,748 predecessor archive payloads are byte-identical, including KM3; the new phase makes 1,749. No native resource was edited. Existing registrations, merge order and saved identities remain.

## Validation and installation

| Gate | Result |
| --- | --- |
| Serialized phase, native action and guard checks | 78 checks passed |
| REDscript compilation | All 148 registered sources compiled, with one changed source |
| Archive readback | All 1,749 payloads verified; 1,748 unchanged |
| Depot/provider and phase-node collisions | Passed; new ID 42351 checked against native roots and all 831 root registrations |
| Deployment/recovery fixtures | Six cases, 18 actions passed, including interrupted writes, staging, receipt recovery and running-game rejection |
| Installed readback | All 51 Core paths verified; exactly three changed |
| Preservation | 436 save files, unmanaged mod tree and 46 dependency/preference files unchanged |
| File rollback readiness | Verified; no save rollback or game launch performed |
| Gameplay | Pending visual, collision and new-slot reload checks |

[Phase assessment](work/assessment.json) · [Compilation](work/compile_01/assessment.json) · [Archive readback](work/archive_01/readback.json) · [Registration checks](work/xl_assessment.json) · [Recovery fixtures](work/fixture_results.json) · [Rollback readiness](work/deployment_01/rollback_readiness.json)

Protected files include the existing 26 dependencies, all 18 Red Hot Tools files, the RED4ext loader and CET bindings. The current manifest retains 45 stable required files and records volatile CET bindings separately as transaction-only preservation. Historical KM3 and tool receipts remain unchanged.

The archive SHA-256 is `20957F0D58A3F10B9FD050E6F6FDEF1FCBB592EFBE49DB34324B11A993665FF7`. The transaction manifest SHA-256 is `D702386BF785130F80AE8ACEAD97DF9A92D253A5D2DBEC35098AADCA2AEC5CC1`. Recovery is retained under `work/recovery/street_overlap_01`; file rollback does not undo effects subsequently saved by the game.

## Reader and evidence limits

WolvenKit 9.1 could not decode current cooked world-node types. The audit used the official [WolvenKit 10.0.0-beta.1 release](https://github.com/WolvenKit/WolvenKit/releases/tag/10.0.0-beta.1), downloaded only into this workspace. Its ZIP SHA-256 is `292185C2F51D1CA85B95E1A7CA63A2D1BC8A3FC5EE387275E9A42EC78103155E`. The reader accepts only the explicit serialized-default-value warning after the field has been decoded, preserving that value; other parse failures are not suppressed. This follows the tagged [CR2W reader implementation](https://github.com/WolvenKit/WolvenKit/blob/10.0.0-beta.1/WolvenKit.RED4/Archive/IO/CR2WReader.cs). All 27 selected provider resources decoded; original failures and warning counts remain in evidence. Native world assets were read, not rebuilt.

Mesh transform matches are not a complete triangle/collision intersection audit or all-city coverage. The user's collision report is runtime evidence; collision-body equivalence and successful live release are not independently proved. Build, installation and recovery passes do not qualify the final scene, post-cleanup vehicle lifecycle, street traversal or save/reload behavior. Those remain bounded live checks.
