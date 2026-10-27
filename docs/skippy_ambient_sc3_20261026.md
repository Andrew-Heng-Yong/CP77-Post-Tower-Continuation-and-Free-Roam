# Skippy equip/unequip lifecycle repair SC3

**SC3 candidate_02 is installed; gameplay remains unverified.** The user confirmed that “still not working” refers to Skippy's combat lines and hologram after SC2, not the earlier fast-travel blackout. No further in-game test commands were requested.

## Cause and repair

The 22:52:10 SC2 log records `Claimed=1`, `Entered=1`, `Stopped=1`, `Stop=0`. Read-only decoding of `ManualSave-23` found the same state saved at 22:48:59, before the 22:49:36 SC2 installation. SC2 required all these receipt/control facts to be zero before requesting an ambient owner, so its wider startup guards could not recover this save.

SC1 interpreted native MQ007's `TurnOff` output incorrectly. That output normally means Skippy is no longer equipped. Vanilla terminates that particular ambient activation, waits for the exact Skippy item to be equipped again, and restarts its ambient branch. SC1 instead wrote a permanent `Stopped` receipt and terminated the entire private owner. This is a source-confirmed defect matching the saved state and runtime log; it does not prove every possible cause of missing Skippy audio or rendering.

SC3 restores the native equip → ambient → unequip → equip loop inside a new private phase. The native expression reset, gameplay comments, reaction scenes, hologram prefab, prop attach/detach operations and combat counters are retained. The existing stopped receipt is preserved. A still-active old controller must finish its existing stop/cut path; an unclaimed old controller has its request cancelled and stop guard latched. The new controller cannot enter until the old controller is retired or blocked from entering. The old resource stays in the archive for saved-owner compatibility.

The new loop contains both the equipped-item wait and active ambient phase. When the one-time Skippy quest takes priority, one cut retires both, and only then is the new `Stopped` receipt written. Both one-time S23 owners wait for that acknowledgement. Normal unequipping never permanently stops the new owner. No native quest fact, kill counter, mode, journal, reward or item reset is added by the repair.

The copied native comment phase also contains a separate `SkippyTestIn` input with item/ammo grant operations. That input is unreachable from normal `In1`, which is the only comment input used here. Native return-scene references are guarded reaction one-liners, not a request to restart the Regina story owner. Native timing and expression behavior remain unchanged.

## Validation and packaging

- Freshly decoded selected resources preserve all six native graphs: **68 nodes and 73 connections**, plus the exact equipped-Skippy wait.
- **74 native payload and guard checks** passed, including the migration truth table and adversarial root guards. A separate **88-assertion review**, with 17 guard cases and three negative controls, evaluates the actual script predicates against the captured save and exercises repeated equip/unequip and takeover.
- The revised script passed the complete **64-source compile** with public Codeware 1.21.1. Existing persistent class fields and one-time quest identities remain unchanged.
- The archive has **1,185 members**, with all **1,184 existing resources unchanged** and every member read back exactly. The new resource has no collision in 68 installed mod archives. Neither native comment phase nor either reaction scene has an installed mod override.
- The complete package retains **51 game paths**. It replaces the combined archive, its ArchiveXL file and existing `PTFR_SideJobsS23.reds`. Coaster Johnny VO removal, W3 workspots and all prior package content are retained.
- **20 recorded deployment fixture actions** passed, including five interrupted installations and their rollbacks. Actual closed-game `Validate`, `Install`, `Verify` and `ValidateRollback` passed. All 51 installed files match the manifest, the three previous files are backed up and no staging files remain. All **301 save files and their names are unchanged** from the closed-game baseline.

Native and parent candidate_01 are rejected workspace artifacts. WolvenKit `DeepCopy` duplicated shared socket references within the native subtree. The selected candidate_02 retains the directly loaded native object and passes independent edge/payload checks. No rejected candidate was installed. The unchanged script compilation from candidate_01 is reused by hash in candidate_02; the failed resource copy did not affect that script.

## Recovery and limits

The selected installer is `prealpha/skippy_ambient_sc3/deploy_02.ps1`; package and evidence are under `prealpha/skippy_ambient_sc3/candidate_02`. Its verified recovery directory is `recovery/skippy_ambient_sc3_01`. If rollback is needed, roll back **SC3 first**, with the game closed, using `-Action ValidateRollback` then `-Action Rollback`; only then consider SC2 or older layers. File rollback does not undo saved progress. The actual installation remains SC3; rollback was exercised in fixtures and its readiness checked against the installed files.

The full local, unreleased 51-file ZIP is `candidate_02/dist/Post-Tower-Continuation-and-Free-Roam-SC3-unreleased.zip` under that directory, SHA-256 `0644159D08F51568A3F15AFC9A360348B3838B9CF9686E6B826C8CCC78D35547`. The install manifest SHA-256 is `AF2B50683688B8D15425F6DE90067539B7D5842B52E940A36974BD16E6BB5DAD`. The new combined archive SHA-256 is `D58806A8BB7AD91E447D6565C4A58E4D638FDDC5CDFFD7DEBB28713B609A43E9`.

Audible lines, visible hologram and the one-time Skippy quest remain unverified in gameplay. The repair addresses the demonstrated lifecycle failure; offline validation is not a live success claim. No assistant game launch, manual native fact change, saved-game edit, Git push or public release is part of this work.
