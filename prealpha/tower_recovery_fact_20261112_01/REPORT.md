# Recovery day quest fact

`PTFRRecovery_Day` drives the existing Health and Stamina recovery curve. It starts at zero on a new recovery and advances at 11:55 a.m. in-game. The saved checkpoint identifies the last 11:55 processed. A forward time skip credits each crossed checkpoint up to day 30. Reloads and backward time changes retain that checkpoint. Day 30 sets the maximums to 125 Health and 75 Stamina. The curve still uses floating-point values.

At the first eligible update, an older save imports its saved recovery day or its elapsed recovery since the recorded start, whichever is higher, up to 30. The new schedule starts from the next checkpoint. The existing saved fields keep their identities. The new fields store whether the schedule has been initialized and the last credited checkpoint. The saved day mirrors credited progress and can restore the fact if a publication is missed.

Run this in the CET console to complete recovery in the current save. The next eligible update applies the day-30 caps. The existing day-14 bruise trigger also becomes eligible and waits for safe gameplay.

```lua
Game.GetQuestsSystem():SetFactStr("PTFRRecovery_Day", 30)
```

## Verification

Source checks and the clock model cover the exact threshold, midnight, forward time skips, rewinds, duplicate credit after reload, missed fact publication, the day-30 cap and override, and import of old save progress. The REDscript compiler accepted all 148 registered sources. [Source patch](candidate_01/source.patch) · [Source and clock checks](candidate_01/verification.json) · [Compile result](compile_01/result.json)

A read-only `AutoSave-4` sample stored the previous recovery clock start at game second `7430400` with vitals enabled. Its SHA256 is `16CE5E08F7A6D511556D646ED4D28D07DC6A4FB75611320490C48F7A4FED8140`. The model covers legacy saves with nonzero day counts and the completed cap.

Nine installer fixture actions passed. The closed-game installation and independent readback verified all 51 Core paths and 26 dependencies. All 343 save files matched their pre-install names and hashes. File rollback is ready. Live checkpoint timing, time skips, and the CET override remain to be confirmed in-game. [Installed manifest](deployment_01/installed_manifest_01.json) · [Transaction fixtures](fixture_results.json) · [Rollback readiness](deployment_01/rollback_readiness.json)
