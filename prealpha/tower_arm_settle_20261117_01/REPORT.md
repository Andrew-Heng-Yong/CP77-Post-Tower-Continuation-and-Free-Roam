# Longer wait for the Tower arm refresh

The user reported missing arms again on 17 November. The 3:57 p.m. local CET run logged the return to the gameplay camera and setup release at the same engine timestamp, `150510.515625`. The installed loading script hash matched the earlier arm resume and Photo Mode test. The automatic stock arm reapply was still in the staged loading polish candidate. [Installed manifest](../archivexl_arm_state_20261117_01/installed_manifest.json) · [Staged predecessor](../tower_loading_polish_20261117_01/REPORT.md)

The updated candidate waits for three continuous seconds of normal gameplay camera ownership after Photo Mode closes, then reapplies the stock arm customization once. The existing readiness checks restart this interval if camera ownership or player readiness changes. The original camera return deadline gets one three-second extension when a ready camera is first observed. The cover holds for one more second after the reapply request. The loading screen debug log records `gameplay-camera-settling` and the arm reapply result. [Source](source/PTFR_LoadingCoverLC1.reds)

All 149 registered REDscript sources compiled offline. Compiled readback verified the wait and deadline ordering, existing stock arm guards, and the single changed path across all 51 Core files. [Staged package](candidate_01/core_manifest.json) · [Compilation](candidate_01/compile_01/assessment.json) · [Readback](candidate_01/verification.json)

Installed on 17 November with Cyberpunk and REDlauncher closed. The transaction replaced the loading controller and verified all 51 Core files, 93 protected dependency and preference files, and all 511 save files. The AutoSave-16 save data matches the preserved Misty's alley checkpoint. Three isolated fixtures verified exact rollback, recovery after interruption and refusal to overwrite unrelated drift. The predecessor script is backed up and verified. Live arm visibility and the compact loading screen await a Tower retest. [Installed manifest](installed_manifest.json) · [Install receipt](deployment_01/recovery/installed.json) · [Recovery fixtures](deployment_01/fixture_results.json)

## 10:42 p.m. Tower retest

The user reported that the arm refresh and loading-screen changes worked. CET records 3.047 seconds from the camera settling event to `reapply-requested`, then 1.031 seconds until setup release. This is one successful Tower transition. The user's observation establishes the visible result.
