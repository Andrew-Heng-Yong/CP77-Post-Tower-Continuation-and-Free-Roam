# Afterlife v7: full native area-trigger trial

**Current audit supersedes the initial failure attribution below:** [Afterlife native trigger audit](afterlife_native_trigger_audit.md). V7 omitted the vanilla `#mirror_scene_afterlife` phase-prefab owner. This is the first concrete static chain break; live trigger registration was never established. Near is unused by v7, Completed is write-only history and cannot block it, and Active/Ready snapshots cannot prove which node ran. The working v5/v6 rollback remains installed. A fresh, separate shadow probe is built only in the workspace, not installed.

Built and installed on 2026-09-23 local / 2026-09-24 UTC while Cyberpunk 2077 was closed. This is a reversible **one-site test**, not the 36-mirror rollout.

Vanilla's Afterlife leaf uses `questTriggerCondition(IsInside, #mirror_tr_afterlife)` to enter and the scene uses `IsOutside` to leave. The v1 mod-owned leaf reused those relative references and did not activate. v2/v4 distance-reference approaches also did not activate. The extracted `always_loaded_1.streamingsector` contains the complete trigger NodeRef:

`$/03_night_city/c_watson/little_china/#loc_q103_afterlife/#loc_q103_afterlife_openworld/#mirror_scene_afterlife/#mirror_tr_afterlife`

v7 uses that **exact full trigger reference** for both native entry and scene exit. The existing completed-Tower guard, mod-owned `PTFRB0ALM_Enabled` opt-in, scene marker, native scene lifecycle, and one-second rearm remain. It reads no `PTFRB0ALM_Near` fact. Its archive contains exactly the two additive Afterlife owner/scene resources; no vanilla resource is replaced. `tools/test_b0_afterlife_mirror_v7.ps1` passed static checks.

For an attribution-clean test, the installed v6 redscript proximity driver was replaced at the same exact path with a linted no-op trial source. The CET observer remains read-only. The working v5 archive/v6 driver remain in the workspace and can be restored with `tools/switch_b0_afterlife_native_trigger_v7.ps1 -Rollback` while the game is closed.

Installed hashes:

- v7 archive: `A6D422EC36A3AB77C4E9394E8D09ED7C11C8E5B4B1F1194FB118464F7611562E`
- no-op redscript trial: `08DA5EBEBE06E7799B5DE05DB9B7BB9A98896B1F81E4BC2AA0FD60C7EAAAE17E`
- unchanged read-only observer: `3E9C8C5A0EFA1CF5F336A1B20EA5634E1759288C3BE3320359802A65517BA35F`

First live report: the physical mirror prompt did **not** appear. The game compiled redscript successfully, and ArchiveXL logged that it merged `towercontinued\b0_afterlife_mirror\afterlife_mirror_owner.questphase` from the installed XL entry. This confirms compilation and graph insertion, not live phase execution or trigger registration. Read-only `Ready`/`Enabled`/`Active`/Tower-fact/position/idle observations at the mirror were requested. The tester was told not to save this trial. Do not use v7 as the general-mirror implementation.

Read-only live observation at the physical mirror: V stood at `(-1437.6966552734, 1038.6705322266, 16.91822052002)`, combat/scene/workspot all false. `PTFRB0ALM_Ready=1`, `Enabled=1`, `Active=0`, `Interrupted=0`, `Near=0`, `Completed=1`. All listed Tower and local guard facts matched the required values: `PostTowerFreeRoamActive=1`, `PTFRP0_DR13=1`, `q307_active=0`, `q307_done=1`, `q307_finished=1`, `q307_2079=1`, `q307_main_game_killed=1`, `q305_johnny_scene_active=0`, `mirror_interaction_disabled=0`, and `q115_point_of_no_return=0`. These snapshots establish matching fact values, not that every live guard passed, that v7 reached its wait, or that the scene never briefly started/returned. Near is unused and Completed is historical. The missing prefab ownership is now the strongest static explanation, with live phase scheduling, trigger registration/NodeRef binding and containment still unmeasured. V7 failed its prompt test and was rolled back before further play.

Rollback completed after the tester quit without saving. Installed Afterlife archive SHA-256 is again `2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003` (v5), and installed redscript driver SHA-256 is again `0F8F2ADB277DC0D59F70951D7A84DF41DDA9D0B44CEDE0F212B5CBA046BB3BB2` (v6). The observer and saves were not changed. Do not enable the 36 simple-shaped leaves from this failed native-trigger result.

For the diagnostic, load only the disposable Afterlife save with `PTFRB0ALM_Enabled=1`; do not call `Enable()` or overwrite the pre-trial save. `GetMod("PTFR_B0_Afterlife_Mirror").Observe("native-v7-no-prompt")` is read-only. In this trial `Near=0` is expected even at the mirror. If the trial is rolled back, use `tools/switch_b0_afterlife_native_trigger_v7.ps1 -Rollback` with the game fully closed.

The 36 simple-shaped vanilla leaves are not a verified list of ordinary, eligible mirrors: it includes story/location-specific sites. Do not activate the set solely from graph shape. Filter sites by access and independent owner/trigger evidence, then instantiate separate guarded leaves rather than the parent controller.
