# Afterlife mirror: redscript proximity-driver candidate

Date: 2026-09-23 local / 2026-09-24 UTC. This is a **single-site test candidate**, not a rollout to all ordinary mirrors.

The previously validated v5 archive and ArchiveXL registration are unchanged. The questphase still owns the Afterlife scene, prompt, leave transition and one-second rearm. `redscript/PTFR_B0_Afterlife_Mirror/AfterlifeMirrorDriver.reds` now polls the observed mirror position every 0.5 seconds using the same 5.5 m enter / 7 m exit hysteresis as the successful CET development probe. It reads the existing opt-in and Tower facts and writes **only** the mod-owned `PTFRB0ALM_Near` fact when its value changes. The first poll waits one second after script-system attach so save facts and the player entity can settle. An epoch guard prevents old delayed callbacks from starting a duplicate loop after detach/reload.

The installed CET `PTFR_B0_Afterlife_Mirror/init.lua` was replaced with the read-only v6 observer; it cannot write `Enabled` or `Near`. The original v5 source remains in `diagnostics/PTFR_B0_Afterlife_Mirror/init.lua` and matched the installed helper hash before replacement. No vanilla fact, H10 file, save, or mirror archive was changed.

Offline checks: `redscript-cli.exe lint` succeeded against both `final.redscripts` and `final.redscripts.modded`. An incremental compile against the modded bundle also produced a test bundle in `build/B0_Afterlife_Redscript/` without error; this is not yet a game-startup test. The game was closed at installation. Source and installed SHA-256 matched:

- redscript driver: `0F8F2ADB277DC0D59F70951D7A84DF41DDA9D0B44CEDE0F212B5CBA046BB3BB2`
- read-only CET observer: `3E9C8C5A0EFA1CF5F336A1B20EA5634E1759288C3BE3320359802A65517BA35F`
- unchanged v5 native archive: `2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003`

First live test: game startup log listed `PTFR_B0_Afterlife_Mirror/AfterlifeMirrorDriver.reds` and reported compilation complete. The tester's three read-only observations, in top-to-bottom chronological order, showed `Near=1, Active=1` at the mirror, `Near=1, Active=1` in the mirror menu, then **`Near=0, Active=0`** after travelling far away to Claire's location. `Enabled=1`, `Completed=1`, `Interrupted=0`, `Tower=1`, and `TowerDone=1` remained stable. Because the CET observer has no fact writer, this is evidence that redscript changed the mod-owned Near fact. The tester described the mirror as working well. This is a successful same-session proximity/scene test; a cold reload with the redscript driver is still pending.

Correction/rollback: I initially misread the third screenshot as `Near=1`, incorrectly called the driver test failed, and installed an explicit PlayerPuppet bootstrap revision while the game was closed. The tester corrected the reading to `Near=0`. Before the game was reopened, I restored the exact previously tested driver source and installed SHA-256 `0F8F2ADB277DC0D59F70951D7A84DF41DDA9D0B44CEDE0F212B5CBA046BB3BB2`. The untested bootstrap revision was removed; archive and read-only observer stayed unchanged. The tester quit without saving this test session, so no save was modified by that revision.

Next test: load the disposable save that already has `PTFRB0ALM_Enabled=1`, not Manual Save 13, without running `Enable()`. At the mirror, test Look/Stop and Change facial expression, leave and re-enter, then report `GetMod("PTFR_B0_Afterlife_Mirror").Observe("redscript-after-reload")` at and away from the mirror. Do not overwrite the pre-migration test save.
