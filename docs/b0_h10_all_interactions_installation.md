# B0 H10 all-interactions experimental installation

2026-09-23. Installed at the user's request with Cyberpunk 2077 closed. All three exact targets were absent before installation. The installer refuses overwrites and verified every installed SHA-256 against its workspace source.

| Destination relative to Cyberpunk 2077 | SHA-256 |
|---|---|
| `archive\pc\mod\TowerContinued_B0_H10_Interactions.archive` | `1F4C2FE700E9F77C18FB113180E329A3426494630FD4BC3D751C23B0E46D4F5F` |
| `archive\pc\mod\TowerContinued_B0_H10_Interactions.archive.xl` | `5605B9EC410A3237C48AC2C20C655FFED10C5DCEADC93E18672EF56A2921469F` |
| `bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_H10_Interactions\init.lua` | `2EFAB3089F4BA386EDB2495CE464E9AAAD974C8E3374F704439DC7A6BDE7A72D` |

After runtime run 1, the experimental archive alone was replaced with corrected scene input-socket stamps, including the outside exit and shower/sleep action branches. The game was closed; the installed prior archive matched its recorded hash, and a verified copy is retained at `build\B0_H10_AllInteractions\TowerContinued_B0_H10_Interactions_run1.archive`. The installed archive now hashes `1F4C2FE700E9F77C18FB113180E329A3426494630FD4BC3D751C23B0E46D4F5F`. The XL and CET files above were unchanged. See [run 1](../research/b0_h10_all_interactions/run1.md) and [run 2](../research/b0_h10_all_interactions/run2.md): the corrected wardrobe exit worked in game; other scene paths still need tests.

No prior Tower archive, ArchiveXL registration, CET addon, non-Tower mod, game binary, or save was overwritten, moved, or deleted. The older V-only mirror package remains installed and its three previously recorded hashes still match; it uses a distinct request fact. No interaction auto-activates on game load. The new archive only adds five guarded native gates and five derivative scenes. Use the [disposable test protocol](b0_h10_all_interactions_probe.md) before assuming any action works.

Recovery if the bundle itself fails to load: with the game closed, remove **only the three exact paths listed above**; the earlier H10 packages can stay. If an action traps V or loses controls, quit without saving and reload the untouched disposable fixture. Do not use a master save for these experiments.
