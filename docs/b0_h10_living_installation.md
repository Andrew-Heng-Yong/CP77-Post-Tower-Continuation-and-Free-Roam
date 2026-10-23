# H10 living-only probe installation

2026-09-22. Installed with the game process closed, using the previously authorized Tower-only mod-management scope. The three destination paths did not exist before installation. Installed-file hashes equal the validated workspace artifacts:

| Destination relative to Cyberpunk 2077 | SHA256 |
|---|---|
| `archive\pc\mod\TowerContinued_B0_H10_Living.archive` | `E69C2996904EFD751F7168888BB9DE16C6FF08270A9D384F7CE5F9EDAEBA464E` |
| `archive\pc\mod\TowerContinued_B0_H10_Living.archive.xl` | `E83181DFC39B5DC4AA651566C3FC9F823422662C106FA51210A76C8DFBAEB77F` |
| `bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_H10_Living\init.lua` | `906BAA936B800C3CDF27BEA54B0730330ABE41A8770110F739D5EF945C42BAC7` |

Existing Tower components were left in place. Post-install inventory still shows P0 archive SHA256 `DF9B68C7B8E06ACF081043592CB56620BC3F09804235F619A2C17CEA319AEF54` and floor archive SHA256 `A6848C597E48E7F499D30788850F924A1BAE8DD1707448271F8884454837DC66`. No non-Tower mod was moved or modified. The new probe is inert until the user loads a post-floor-success experimental save and explicitly runs its one-shot `Restore()` command. No game-runtime result has been claimed.
