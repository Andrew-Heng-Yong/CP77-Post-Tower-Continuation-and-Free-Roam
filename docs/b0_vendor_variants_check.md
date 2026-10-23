# Six deferred ordinary vendors — one combined check

Installed automatic candidate. Load a disposable post-Tower save that already
works with the current mod. No Start/Enable command is required. Wait a few
seconds in normal gameplay after loading so the bootstrap can run.

The six sites and log keys are:

| Site | Log key |
|---|---|
| Badlands gun shop 02, Inland Avenue SE1 | `badlands_gun` |
| Badlands food shop 01, Inland Avenue SE5 | `badlands_food` |
| West Wind Estate melee shop | `westwind_melee` |
| Rancho Coronado clothing shop | `rancho_clothes` |
| Rancho Coronado medical shop | `rancho_meds` |
| Japantown medical shop 01 | `japantown_meds` |

Use the map/normal travel to reach these shops. Scene-anchor coordinates have
been extracted for runtime departure checks, but **not verified as safe player
landing points**. There is deliberately no Go helper or guessed teleport in
this package, following the earlier Chang landing problem.

## One session, two rounds

1. Visit all six in any convenient route. Check for one seller; open the actual
   Trade inventory and try any available ordinary dialogue. Close it normally.
2. Leave each shop by at least 120m before the next. Do not teleport while in a
   dialogue, Trade menu, or workspot. The departure counter must advance before
   returning; seeing the same seller continuously is not a respawn proof.
3. Repeat the same route once. Confirm Trade reopens and no duplicate actor or
   stuck player. No separate enable/stop commands between vendors.
4. After the last shop, move at least 120m away, wait five seconds, then run:

```lua
GetMod("PTFR_B0_VendorVariants").Observe("six-vendors-finished")
```

5. Quit without saving. Tell me which shops worked or failed. Logging starts
   automatically; no recording command required. These are disposable checks,
   not permission to modify the master save. No ending replay is needed.

Expected evidence: entry/exit increases by at least 2/2 per visited shop, idle
Near=0 after leaving, and user-confirmed usable Trade on both visits. Extra
boundary crossings can legitimately yield larger counters. Counters alone do
not prove menus or dialogue; a locked vanilla gate is not forced open.

## Optional diagnostics/recovery

`Observe("label")` is read-only. Durable files are inside CET's
`PTFR_B0_VendorVariants` folder, named `vendor_variants_YYYYMMDDTHHMMSS.jsonl`.
Samples flush every two seconds and on manual marks/shutdown.

Only if this new batch causes a problem: close Trade, leave all six areas,
wait for native departure, then `GetMod("PTFR_B0_VendorVariants").Stop()`.
This suspends only the six new owners and refuses if one is still Near.
`Resume()` removes only this batch's suspension. `Finish()` stops logging,
not restoration. No story/default/dialogue facts are changed by these helpers.
