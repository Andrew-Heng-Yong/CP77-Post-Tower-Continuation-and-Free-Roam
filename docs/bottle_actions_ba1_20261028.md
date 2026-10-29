# BA1 bottle-shooting action controller

**28 October live follow-up:** the user reports that the prototype works and
requests broader application. This confirms their matched group 179 fixture;
speech and save/reload were not separately itemized. The later historical
installation checks below retain their original pending-live status. Broader
work is recorded in [WA2](world_actions_wa2_20261028.md).

BA1 restores the isolated native action controller for the matched Coastview bottle-shooting community, W3 group 179. It addresses the missing hold-position and shooting commands observed for spawner `8640981183263935109`, entry `goon2`, after Tower. It covers this community only. The spoken lines have not been traced to an authored dialogue controller, so this repair does not establish speech recovery.

The native phase `root/28/14/61` is retained with its 32 nodes, 43 connections, weighted 1–4-second delay, random choice between goon2 and goon3, seven-second shooting windows, security-system combat handling, and community-ready/not-ready lifecycle. Ten community references are qualified to the exact persistent spawner; the absolute bottle targets, security reference and native `#player` combat targets are preserved.

A distinct private resource gives existing saves a new action owner while leaving their already-entered W3 support owner and receipts intact. Admission requires the completed Tower gates and `PTFRWW2_179_Claimed=1`, `Entered=1`, `Hold=0`. The private claim prevents a second fresh admission. A native ready condition gates every start of the action phase. Losing any eligibility gate cuts the entire nested phase, including pending timers and ready waits; resumption goes through eligibility again. No encounter reactivation, kill-count reset, prefab spawn, reward replay or native-fact write is added.

The complete consolidated successor retains 51 install paths. It replaces the combined archive and its XL registration, adds one resource to the archive, and preserves all 1,185 prior resources byte-for-byte. All REDscript sources remain byte-identical to CC1; compilation is reused only after matching the complete 64-source compiler input set. The new phase is registered once under the existing EP1 root.

Independent verification passed 46 checks, all 32,768 boolean combinations of the 15 eligibility gates, and five negative controls. It compared fresh native and cooked graph payloads, verified the exact captured spawner hash, and checked duplicate exclusion, unloaded-community admission, and whole-loop suspension/rearm. The archive readback preserves all 1,185 prior members and adds exactly one; the new depot has zero collisions across 68 installed mod archives.

The environment review passed 28 checks. Both target entities (nodes 71/72) and the security system/area (79/81) resolve in `default/exterior_-33_-30_0_0.streamingsector`, registered as ordinary Exterior level 0 with no quest-prefab owner. Base and EP1 definitions agree for these objects; a 125-archive census found no mod override of the sector or default block. No additional environment prefab owner is needed.

**Installed on 28 October 2026.** The closed-game Validate, Install, Verify and ValidateRollback actions passed. All 51 installed paths match the manifest, all 301 save files and names are unchanged, and the 20 deployment fixture actions include five successful interrupted-install recoveries. The full unreleased ZIP SHA-256 is `6348515E7103D45AB07A0EB006507CDD52F6335419AD25C5B7EB2D1DD285DFB5`; manifest SHA-256 is `B1E381553E2D2DD062BA01ED77465E08EC61DED2C2FF890F5AD732975C70FD9F`.

Build and validation evidence is in `prealpha/bottle_actions_ba1/candidate_01`, including `installed_assessment_01.json`; source and verification tools are in `prealpha/bottle_actions_ba1`. Native gameplay, streaming and save/reload behavior require live observation; structural checks do not constitute a live pass. No game launch, save/native-fact edit, Git push or public release was performed.

Rollback, once installed: with Cyberpunk 2077 and REDprelauncher closed, run `prealpha/bottle_actions_ba1/deploy_01.ps1 -Action ValidateRollback`, followed by `-Action Rollback`. This restores the prior CC1 files from `recovery/bottle_actions_ba1_01`. File rollback does not undo state already written by the game into a save.
