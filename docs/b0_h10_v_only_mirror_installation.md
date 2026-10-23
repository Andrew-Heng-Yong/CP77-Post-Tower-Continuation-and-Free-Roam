# B0 H10 V-only mirror experimental installation

2026-09-23. Installed at the user's explicit request with Cyberpunk 2077 closed. All three destinations were absent before installation. This is a disposable-save experiment; the candidate remains unsafe under scene interruption and is not a release build.

| Destination relative to Cyberpunk 2077 | SHA-256 |
|---|---|
| `archive\pc\mod\TowerContinued_B0_H10_VOnlyMirror.archive` | `1A5E09FD044BB1CFA8A7B0FA5A5B245AE50FE614B25060B2A7CA53574ACD7994` |
| `archive\pc\mod\TowerContinued_B0_H10_VOnlyMirror.archive.xl` | `0C4E63018D27F7D8F47BE42B13B296AF0E435D8AC9925253D0668366450B340B` |
| `bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_H10_VOnlyMirror\init.lua` | `49C0B30BAFFF98A4158E0207E2C6860E6F3B0EBECF28D194438201910E160CEB` |

No pre-existing destination was overwritten. No other mod, game file, save, or quest fact was changed during installation. See `b0_h10_v_only_mirror_probe.md` for the reviewed path, limitations, and stop conditions.

Runtime correction: the first trace showed the player at the H10 mirror with `HighLevel=2`, `SceneTier=2`, `content_blocked=false`, `saving_locked=false`, and no active scene/workspot. The wrapper's initial Tier-1-only check was stricter than the vanilla entry and made this test impossible. With the game closed, only the installed CET wrapper was updated to accept stable Tier 1 or Tier 2 while retaining the combat, scene, workspot, mount, content and saving guards. The archive and ArchiveXL registration were unchanged.
