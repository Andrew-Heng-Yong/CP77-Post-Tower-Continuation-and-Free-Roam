# Christine + deferred Japantown netrunner

Use a disposable post-Tower save. Cold-launch after installation and allow about 10 seconds outside combat/interactions. **No Start or Arm command.** Existing vendor/mirror packages are untouched. This pair is a new candidate, not yet a live pass.

One combined route: Christine → outside → netrunner → outside → repeat both once. Open the actual Trade menu each visit, then close it normally before teleporting. Confirm the expected seller is present without duplicate models. Keep any original dialogue; there is no need to exhaust or reset it.

Christine:

```lua
GetMod("PTFR_B0_DeferredVendors").Go("christine")
```

Between shops, after closing Trade, run this and close CET for about 3 seconds:

```lua
GetMod("PTFR_B0_DeferredVendors").Outside()
```

Chang-Hoon Nam (Japantown netrunner 02, not the previously tested 01):

```lua
GetMod("PTFR_B0_DeferredVendors").Go("netrunner02")
```

Close CET, step clear of the scene-marker landing point if necessary, and approach. His shop remains unavailable unless this save has legitimately completed his rescue and already initialized the shop/market. If he does not appear, **do not force a gate**. Run:

```lua
GetMod("PTFR_B0_DeferredVendors").Observe("at-shop")
```

After the route, outside both shops:

```lua
GetMod("PTFR_B0_DeferredVendors").Observe("finished")
```

Quit without saving this first check. Report the two menu results; the trace logs automatically. No separate logging or rearming sequence. A locked netrunner is not by itself an installation failure; his output lists rescue/default/market facts for diagnosis.

Optional stop, only outside both shops: `GetMod("PTFR_B0_DeferredVendors").Stop()`. This suspends only this pair. `Resume()` permits automatic activation again; it does not change vanilla gates. Save in a new disposable slot only if deliberately testing persistence later, never over the master.

Log: `Cyberpunk 2077/bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_B0_DeferredVendors/deferred_vendors_trace.jsonl`. Entries/exits prove native owner transitions; SceneRequests proves reaching the scene input, not opening a menu. Your visual/menu confirmation remains necessary.
