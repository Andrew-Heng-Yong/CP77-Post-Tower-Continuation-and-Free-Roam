# Immersive First Person 2.2.0 update — 16 November 2026

The user requested an IFP update while the first-person body-view investigation was open. The prior RED4ext log rejected the installed IFP 0.2.0 native plugin for Cyberpunk 2077 2.50, although its CET Lua layer continued to run. The official [v2.2.0 release](https://github.com/cp2077/ImmersiveFirstPerson/releases/tag/v2.2.0) states 2.50 support. This is a compatibility update, not evidence that IFP caused or fixed the post-Tower body clipping.

## Exact input and change

- The official `Immersive.First.Person.zip` SHA-256 is `F576D7FA67818F87E231F8AFC4C1840D0AFC82C0C1BE26C74646EFD478C15809`, matching the release asset digest. All 14 ZIP entries passed CRC, path, and duplicate checks.
- The fresh [deployment plan](work/plan_01.json) records every before/after file hash. Nine files changed: the height archive, CET entry script and six modules (including new `HeightControl.lua`), and native RED4ext DLL. Five files were already byte-identical, including both IFP REDscript sources.
- The 149 live REDscript sources still match the successful LC5 compile inventory. No script was changed by this update, so that compilation result remains applicable. The game and launcher were closed at each write.

## Verification and limits

The replacement/addition/rollback fixture passed in a separate workspace directory. The install and independent verification both passed: 14 IFP files match the release, 51 LC5 Tower files and 47 protected dependencies are unchanged, four IFP setting/binding/log files are unchanged, and all 451 saved-game files have the same hashes and inventory. Nine exact old-file copies and the [installation journal](work/recovery_01/journal.json) are retained for rollback; the [receipt](work/installed_01.json) records the verified result. The ZIP, staged payload and backups remain local and are ignored by Git.

The game was not launched as part of installation. RED4ext accepting the new DLL, IFP behavior, the Tower transition, and the camera clipping are not yet gameplay-verified. Re-test the transition first. If the bug recurs, collect the already agreed read-only paired camera outputs before and after the vehicle workaround. The existing smaller loading-page layout request remains deferred.
