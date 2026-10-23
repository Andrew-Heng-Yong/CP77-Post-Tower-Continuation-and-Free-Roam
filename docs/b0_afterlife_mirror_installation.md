# Afterlife representative mirror installation

Date: 2026-09-23. Cyberpunk 2077 process was closed. All three exact targets were absent before installation. The additive package was installed with `tools/install_b0_afterlife_mirror.ps1`; source and installed hashes matched. No existing file, H10 package, game resource, or save was replaced.

| Installed target under game root | SHA-256 |
|---|---|
| `archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive` | `FF013D15E9255EF78769A108C193194F8BB958B8453E5A7B734BCFBF68BE87A8` |
| `archive\pc\mod\TowerContinued_B0_Afterlife_Mirror.archive.xl` | `CFADB0472E2F5EFE48BCF681BF589FC9FFE6A9A04EC3D192887F448D34058614` |
| `bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_Afterlife_Mirror\init.lua` | `5E947591DEDDD522C9FEF99294EDCE8CABE9797CFA0D90178B6687A002064D46` |

The native phase remains inert until an explicit `GetMod("PTFR_B0_Afterlife_Mirror").Enable()` on a disposable completed-Tower save, after `Inspect()` reports ready. The test must verify the physical Look prompt, one clean use/Stop looking, prompt rearm, exit/re-entry, and cold save/reload. This installation is not evidence of in-game success.

The separate Little China clothing-vendor candidate remains **uninstalled** pending this mirror test and its own opt-in protocol.

## Plane-distance v2

The first live test reported no physical prompt after `Inspect()` returned READY and `Enable()` succeeded. The trace showed `Ready=1`, `Enabled=1`, all required Tower facts at expected values, combat/scene/workspot false, but `Active=0` throughout the observed interval. Thus the scene never started; the failed gate is not yet uniquely identified. The local `#mirror_tr_afterlife` trigger is a leading hypothesis, not a confirmed missing asset. The tester quit without saving the opt-in change.

With Cyberpunk closed and the exact v1 archive hash verified, v1 was backed up to `build\B0_Afterlife_Mirror_V2\backup\TowerContinued_B0_Afterlife_Mirror_v1.archive` (same SHA-256 as the original archive). Only the archive was replaced. Current installed archive SHA-256: `BAE339F2D61806DE691A78CC083FA6BE1BCB3660B60C374C69A7F57ABEE34090`. XL and CET addon are unchanged.

v2 uses a vanilla-derived quest distance condition to gate entry within 4 m of the physically present `#mirror_plane_afterlife`. Its mod-owned copy of the Afterlife scene changes only the leave condition from `IsOutside #mirror_tr_afterlife` to greater than 4 m from that plane. It does not replace the vanilla scene or modify a vanilla fact. `tools/test_b0_afterlife_mirror_v2.py` passes static checks. Live entry, prompt, action, rearm and cold reload remain unproven.

The v2 live attempt also produced no physical prompt. Its trace showed `Enabled=1` while `Active=0`, `Completed=0`, and `Interrupted=0`; V was close to the mirror and observable Tower/idle state remained correct. A single-use v3 diagnostic has been built and statically checked but is **not installed**. It will separate native spatial-gate failure from a shared guard/phase issue after the tester exits without saving. v3 is not a persistent mirror solution.

## Single-use v3 diagnostic

Cyberpunk was closed and the exact installed v2 hash verified. The v2 archive was backed up to `build\B0_Afterlife_Mirror_V3\backup\TowerContinued_B0_Afterlife_Mirror_v2.archive` (SHA-256 `BAE339F2D61806DE691A78CC083FA6BE1BCB3660B60C374C69A7F57ABEE34090`). Only the archive was replaced. Current installed SHA-256: `7646FC8C1499A1BA8F279553D0743F3EB4CA4CD25F812A7A9D562C5742C8C926`. XL, CET addon and H10 package remain unchanged. The separate clothing-vendor package is still uninstalled.

v3 has no native spatial entry gate. CET `Inspect()` still guards a nearby, idle, completed-Tower player before the mod-owned opt-in write. The native owner then attempts one scene only; it does not rearm. The mod-owned scene replaces the area-exit check with a 30-second safety exit. This diagnostic is not a durable restoration and must be tested without saving. Whether it actually enters the scene is not yet known.

The tester reported that the v3 mirror worked. The trace confirms scene entry (`Active=1`, player `in_scene=true`) and timed completion about 31 seconds later (`Active=0`, `Completed=1`, `Interrupted=0`, player `in_scene=false`). This proves the shared Tower/fact guard and scene can run, but not a durable local owner, natural mirror exit, rearm, or cold reload. Do not present v3 as restoration of all mirrors.

## Absolute-reference v4

The tester closed Cyberpunk. The exact installed v3 hash was verified and backed up to `build\B0_Afterlife_Mirror_V4\backup\TowerContinued_B0_Afterlife_Mirror_v3.archive` (SHA-256 `7646FC8C1499A1BA8F279553D0743F3EB4CA4CD25F812A7A9D562C5742C8C926`). Only the archive was replaced. Current installed SHA-256: `07A6A90D036D3E6061EF093C137D7388FFDBACB7DF0A127ABE6439AC20E05407`; XL, CET addon, H10 package, and vendor candidate remain unchanged/uninstalled as applicable.

v4 restores the repeatable one-second native owner loop of v2 but uses the full world reference to the physical Afterlife mirror plane for entry and exit. The full reference is independently present in the extracted Night City streaming sector. `tools/test_b0_afterlife_mirror_v4.py` shows the only phase/scene difference from v2 is that reference expansion. This is an unproven hypothesis about relative NodeRef resolution. Test prompt, Look/Stop, rearm, exit/re-entry, and cold reload on a disposable save before using the pattern elsewhere.

The v4 live attempt again had `Inspect()` READY and `Enable()` accepted, but no physical prompt; trace `Enabled=1`, `Active=0`, `Completed=0`, and V within a few metres of the mirror. The full NodeRef did not open the native spatial gate on this save. This narrows the problem to native spatial-condition evaluation or target availability, not CET command syntax or the scene resource. The tester quit without saving.

## Mod-owned proximity v5, development-only driver

With Cyberpunk closed, v4 archive and old CET helper hashes were verified and backed up under `build\B0_Afterlife_Mirror_V5\backup`. Only those two files were replaced. Installed archive SHA-256: `2643F18D8946FB9C96FB479FD91418D3446E4792CE21562A11CBEC371D534003`; installed helper SHA-256: `C56FE010E8549B9DF3ECDC97A4A573469523CEFEFD4B41E0A0DFCEEB194795B4`. XL, H10, and vendor files are unchanged.

v5 uses CET **only as a development proximity writer** for mod-owned `PTFRB0ALM_Near`, based on bounded player distance to the observed mirror position with entry/exit hysteresis. The native phase waits for Near=1, starts the mirror scene, and loops through the vanilla one-second rearm; the mod-owned scene uses Near=0 for its leave condition. The helper writes only mod-owned Enabled/Near facts and logs transitions. This may establish durable behavior, but it is **not a release implementation** until the proximity writer is migrated to redscript or an equally reliable non-CET runtime and tested on load, leave/return, and interruption. No other mirror is activated.

`tools/test_b0_afterlife_mirror_v5.py` passed static checks plus an in-memory Lua mock that observed exactly three writes: mod-owned Enabled=1, Near=1 on approach, and Near=0 after moving away. No vanilla fact writer was found in this helper. In-game v5 behavior remains untested.

The tester reports Look/Stop worked twice, the bathroom was left and re-entered, and the prompt remained. The trace independently records three `Active=1` scene entries and three clean `Active=0` completions, with mod-owned Near toggling 1/0 at arrival/departure and `Interrupted=0`. This establishes repeatable same-session Afterlife behavior for the development driver. The tester initially described the choices as "Only Look/Stop," then clarified that **Change facial expression is present**. Cold save/reload was not yet reported at this checkpoint. Do not generalize to all 44 leaves or call CET the final runtime.

Cold-reload checkpoint (2026-09-24 UTC): the tester supplied `Observe("pre-save")` with `Enabled=1, Active=0, Completed=1, Near=0, Interrupted=0, scene=false, workspot=false`. After a full quit and reload, `Observe("after-cold-reload")` reported the same values. The trace confirms a new CET initialization/attach and this observation, with no `Near=1` or new scene entry yet in the reloaded session. Thus the opt-in marker and clean completion persisted, but physical prompt/action reactivation after the cold reload is **not yet confirmed**; test at the mirror before calling this persistence validated.

Cold-reload action result: the tester returned to the physical Afterlife mirror and confirmed Look/Stop worked after the reload without another `Enable()` call. The trace recorded a fresh `Near=1` at 2026-09-24 02:18:18 UTC, `Active=1` at 02:18:19, then `Near=0` at 02:18:40 and a clean `Active=0, Completed=1, Interrupted=0` at 02:18:41. This validates cold-reload reactivation and clean exit for the **single Afterlife mirror** under the development CET proximity driver. The tester clarified that Change facial expression is present. The extracted ordinary Afterlife scene has no apparent Change appearance option, unlike H10's separate mirror scene.
