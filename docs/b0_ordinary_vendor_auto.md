# Automatic ordinary vendors — current instructions

The 25-shop batch now activates automatically on eligible post-Tower saves. The user waived the structured opt-in test and will check shops informally. **No Start or Arm command is required.** The previous 15 regional owners, Wilson, H10 and mirrors are unchanged; this update does not automatically enable those separate packages.

Cold-launch the game, load a disposable post-Tower save, close any active dialogue/menu and allow about 10 seconds of normal gameplay. Visit the shops normally. Vanilla unavailable/locked shops remain gated. Original scenes and dialogue conditions remain intact; consumed or ineligible choices are not forcibly reset. If a script compilation error appears, stop and report it.

If you want shortcuts, these optional commands remain available. Run only one at a time, close CET and approach the counter. Close every interaction normally before teleporting:

```lua
GetMod("PTFR_B0_OrdinaryVendors").Go("clothing")
GetMod("PTFR_B0_OrdinaryVendors").Go("junk")
GetMod("PTFR_B0_OrdinaryVendors").Go("guns")
GetMod("PTFR_B0_OrdinaryVendors").Go("food")
GetMod("PTFR_B0_OrdinaryVendors").Go("melee")
```

These are Northside clothing, Kabuki junk, Arroyo guns, Coastview food and Japantown melee. Arroyo/Coastview also have nearby medical counters. Between teleports, after leaving the menu:

```lua
GetMod("PTFR_B0_OrdinaryVendors").Outside()
```

Close CET and wait a few seconds for native departure. Go refuses if a new owner still reports Near. Positions are original scene anchors, so move clear of a counter/actor if necessary. Do not teleport during Trade or dialogue.

If a shop fails or duplicates its seller, note the site and optionally capture:

```lua
GetMod("PTFR_B0_OrdinaryVendors").Observe("automatic-check")
```

The durable log appends automatically; no logging Start is required. Actual menu operation and actor count remain visual checks, not things the trace proves.

## Optional stop / resume

After leaving all batch shops (Outside and a short wait):

```lua
GetMod("PTFR_B0_OrdinaryVendors").Stop()
```

Stop also suspends automatic activation. If this state is saved, the suspension persists. To permit automatic activation again:

```lua
GetMod("PTFR_B0_OrdinaryVendors").Resume()
```

Wait up to 10 seconds outside interaction/combat. Neither command changes story facts or other vendor packages. Site-specific exclusions from `Skip(key)` remain excluded. Keep original/master saves; if you save this build, use a separate disposable slot. There is no mandatory new manual test or ending replay.

Status: compiled and statically checked, installed with opt-in rollback backups; **new automatic batch runtime behavior remains unverified** until the user's checks. This is 25 reviewed additional owners, not every world vendor.
