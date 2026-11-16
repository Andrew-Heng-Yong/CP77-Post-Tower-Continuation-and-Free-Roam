# PE1 markers appeared after a delay — 8 November 2026

The user initially reported that KOLD MIRAGE's marker and new undiscovered markers had not appeared. During the investigation, the user then reported “wait its restored” and “look like it need some time before makers will pop out”. Accept marker restoration as **USER_REPORTED_PASS for this attempt**, with delayed appearance. No fixed wait duration was measured and no further repair was applied.

The initial live CET check reported `postTowerReady=true`, KOLD `ready/permit/issued/finished=1/1/1/0`, `fault=0`, `entered=0`, `baselineFresh=false`, `currentMatch=true`, `safe=true`. Its native fact prerequisites all passed: `q001_done=1`, `q005_done=1`, `q101_enable_side_content=1`, `q103_rogue_done=1`, `mq015_active=0`. Later read-only content queries returned aggregate blocking false and `finalboards` blocking false. Do not reinterpret the initial `entered=0` receipt as the later restored-marker state.

All 51 installed Core files and 26 dependencies matched PE1 during the read-only investigation. Captured runtime logs show successful REDscript compilation and the KOLD entry's ArchiveXL merges. These establish loading/merge evidence, not exact executing-owner identity. The marker delay is consistent with native setup/admission scheduling; the exact token/scheduling cause remains uninstrumented. No token was forced, condition removed, owner reissued, quest fact reset or game/save file changed by this investigation.

Freezer Open, cyberdeck pickup, JP1 dialogue/menu behavior, quest completion, rewards and save/reload remain separate, unreported results. The successful pre-ending comparison needs no repetition. Allow startup and native setup to settle before assessing missing markers; this observation supplies no universal timeout or all-quest qualification.

[Initial observation and file pins](observation.json), [later user result and fresh logs](restored_01/result.json), [installed PE1 manifest](../../deployment_01/installed_manifest_01.json) and [pilot test card](../../TEST_CARD.md).
