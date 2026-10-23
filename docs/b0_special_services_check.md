# Special services S1 — one combined check

Installed automatically, alongside Claire and the unchanged previous baseline.
Load the disposable post-Tower save that worked for Claire; **no Enable/Arm/Start**.
Wait 10 seconds in normal gameplay. Do not change shop/story facts.

Use one session to sample the distinct mechanisms:

1. Stadium: Michał/Marcin's shared junk shop, Sammy's bell/netrunner shop,
   Sophia's gun shop, Herold's black market, and Eron's ripperdoc service.
2. At each, check the intended actors, use an available unique dialogue, open
   and close the actual service menu. For Sammy, try the bell if offered.
   At Herold, only verify normal earned stock; no special item purchase needed.
3. Leave the Stadium shopping area far enough to unload the shops, then return
   and repeat their service menus. Multiple legitimate companion NPCs are not
   duplicates; look for overlapping copies of the same role.
4. If convenient in the same session, check Leon's guitar/Trade return and one
   clothing wardrobe. Farida/Anderson/Odell can remain closed if their original
   earned gates are absent; do not force them open.
5. Quit **without saving** and tell me which samples worked or failed. Logging
   starts and flushes automatically, so no logging command is required.

If a shop fails, an optional read-only observation captures all gates/counters:

```lua
GetMod("PTFR_B0_SpecialServices").Observe("failed-shop-name")
```

Finish every dialogue/menu before travelling. Do not teleport from a mirror,
ripperdoc, wardrobe or bar dialogue. Do not run old opt-in vendor controllers.
For a stuck scene or duplicate actor, stop the check and quit without saving.

This is a representative mechanism test, not proof that all 19 sites or cold
save/reload pass. The catalogue's remaining story-heavy vendors are not included
in this package; see [scope and blockers](../research/b0_special_services/assessment.md).
