# Staged H10 architecture probe installation

2026-09-22. Installed with the game process closed under the user's Tower-only mod-management authorization. All three exact destinations were absent before installation. Installed hashes match the workspace build:

| Destination relative to Cyberpunk 2077 | SHA256 |
|---|---|
| `archive\pc\mod\TowerContinued_B0_H10_Architecture.archive` | `B3CFC4607863ED10986F6C56810B2E8AD292901A07AB7AA5AF18AFB1BB740601` |
| `archive\pc\mod\TowerContinued_B0_H10_Architecture.archive.xl` | `A38531E8FDAAF944DE96FDB14FA86595233324DF5880CB0082BDB570E9A05792` |
| `bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_H10_Architecture\init.lua` | `4BD72A886C152250E2907E604178B4B68F76D7D77322F1CCC158403367E17C9C` |

Post-install inventory confirmed unchanged P0, floor and living archive hashes (`DF9B68C7B8E06ACF081043592CB56620BC3F09804235F619A2C17CEA319AEF54`, `A6848C597E48E7F499D30788850F924A1BAE8DD1707448271F8884454837DC66`, `E69C2996904EFD751F7168888BB9DE16C6FF08270A9D384F7CE5F9EDAEBA464E`). No non-Tower mod was moved or modified. This package only registers passive manual gates at startup; there was no game-runtime test, quest fact write, or save change by the agent.
