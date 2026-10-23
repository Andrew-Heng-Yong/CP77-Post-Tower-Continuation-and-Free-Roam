# Plan B0 H10 floor probe — installation record

2026-09-22. The user explicitly authorized installing the B0 probe and managing previous Tower mods while leaving other mods unchanged. The game process was closed. This is a file installation and hash verification, **not a runtime restoration result**. No Git operations or save changes.

## Active Tower files

| Purpose | Installed path | SHA256 |
|---|---|---|
| Retained-session P0 mod, kept unchanged | `C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod\TowerContinued_Phase2B_P0_DirectReturn.archive` | `DF9B68C7B8E06ACF081043592CB56620BC3F09804235F619A2C17CEA319AEF54` |
| B0 floor archive | `C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod\TowerContinued_B0_H10_Floor.archive` | `A6848C597E48E7F499D30788850F924A1BAE8DD1707448271F8884454837DC66` |
| B0 ArchiveXL metadata | `C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod\TowerContinued_B0_H10_Floor.archive.xl` | `60DCB71D504BF5C5504237BC28C37D478301941B345B5709869F57F570EDC5CF` |
| B0 manual CET probe | `C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_H10_Floor\init.lua` | `87A82458333C8D3F75D35CFE77B7E2500E872180170B19D73DE0A75AB908030E` |

Installed hashes match the statically validated workspace sources. ArchiveXL and Codeware were already present; they were not altered. There are exactly two Tower archive files active, the prior P0 and the new B0, plus the B0 `.archive.xl`; one Tower CET addon is active. The P0 archive hash still matches its workspace build. No non-Tower mod was moved or changed.

## Retired Tower addon

The former `PTFR_Phase2B_P3_ShopExitProbe` CET folder was moved intact from the game `mods` directory to:

`C:\Users\Ayong\Documents\cp77 modding\tower ws\build\B0_H10_Floor\previous_tower_mod_backup\PTFR_Phase2B_P3_ShopExitProbe`

Its `init.lua`, `ptfr_p3_shop_exit.jsonl`, `.log`, and `db.sqlite3` remain in that backup. The folder was **moved, not deleted**. The old door-opening probe is no longer active. This change is recoverable by moving that specific folder back after a future test; do not enable it alongside B0 for this isolated experiment.

## Next manual action

Restart the game after this installation. Load a disposable post-Tower fixture, go to H10, and run:

```lua
GetMod("PTFR_B0_H10_Floor").Inspect("baseline")
```

Only if it reports `READY`, continue with the once-only `Restore()` procedure in [the probe guide](b0_h10_floor_probe.md#minimal-manual-test--when-ready-to-installtest). Keep the original baseline save unchanged. No floor request was made by the agent during installation; no game process was launched.
