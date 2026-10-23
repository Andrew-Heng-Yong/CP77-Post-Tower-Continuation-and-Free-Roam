# H10 persistent owner installation

Date: 2026-09-23. Cyberpunk 2077 was closed. All three exact targets were confirmed absent before installation; no existing archive, addon, game resource, or save was overwritten or removed. The additive native owner remains inert until a guarded `PTFR_B0_H10_Persistent.Enable()` on a disposable completed-Tower save.

| Installed target under game root | SHA-256 |
|---|---|
| `archive\pc\mod\TowerContinued_B0_H10_Persistent.archive` | `19E7158A28B32526757DE00B579C9EB309BFEBF226FCEC2164E9C6A02C5AE1A9` |
| `archive\pc\mod\TowerContinued_B0_H10_Persistent.archive.xl` | `15DEA45EFAB5F9C93DE1436D7E5FF9FE99039FB68E4EA829B4B2E6210315CFAC` |
| `bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_H10_Persistent\init.lua` | `022B21F4A428CF352230C8F98AFE50751855F20E06FEB6FF217DCA83CD5786F4` |

The game root is `C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077`. The installer validated source and target hashes. The old five-action manual bundle, previous mirror probes, H10 shell packages, time-unpause probe, and unrelated mods were left untouched. The tester subsequently confirmed that v1's basic mirror Look/Stop prompt returned on a second use and after leaving/returning to H10. See [test protocol](b0_h10_persistent_probe.md).

## Mirror-actions update (v2)

On 2026-09-23, with Cyberpunk fully closed, the exact v1 archive hash above was verified, backed up to `build\B0_H10_Persistent\backup\TowerContinued_B0_H10_Persistent_v1.archive`, then the archive alone was replaced. The installed archive now hashes to `3E060AC9AB7A284265E822FF1FDAA22FCACAE1AAB013C80AE159B41BF6644203`. The XL and CET files above remain unchanged. Static checks pass: 162 reachable scene nodes, eleven choices, full vanilla-local appearance/facial routes, and no reachable old hairdresser-history write or Johnny/q101/MQ055 facts. Expanded mirror actions are **not yet game-tested**. The v1 archive is recoverable from the workspace backup; no game save was changed by installation.

## Corrected mirror entry (v3)

The v2 live test showed that Look worked, but the new choices did not appear. The trace confirmed the opt-in owner entered the scene and mirror workspot; it did not provide individual choice visibility. A stricter graph audit then found that v2 connected 1125/1246 only through choice-attachment input stamps, not through an executable branch. Vanilla enters those choices through a longer MQ055/Johnny condition chain, which the V-only route had bypassed. v3 directly enters both the local appearance/facial chooser (1246) and the Stop looking chooser (1270) after mirror approach, without restoring the old condition chain.

Cyberpunk was closed; the exact v2 archive was backed up to `build\B0_H10_Persistent\backup\TowerContinued_B0_H10_Persistent_v2.archive`, then only the archive was replaced. Current installed SHA-256: `F8E8D001FB639F62FD5FB040F3455B834FB618C24F76F5B96BF6F69C18742DA4`. The executable-path test now reaches 1246 and 1125 without attachment-only links; old q101/MQ055/Johnny writers remain unreachable. XL and CET files were not changed. v3 is **not yet game-tested**.
