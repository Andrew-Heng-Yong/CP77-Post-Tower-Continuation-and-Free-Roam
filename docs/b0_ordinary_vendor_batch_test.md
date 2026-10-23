# Ordinary vendor batch: one combined test

**Superseded:** the user waived this opt-in test and approved automatic activation. Follow [current automatic instructions](b0_ordinary_vendor_auto.md); no Start/Arm is needed. The old sequence below is retained as an optional historical test plan, not a required test or a recorded pass.

Installed 2026-09-25, **idle until Start**. Covers 25 new shops only; existing vendor and mirror packages are unchanged. No ending replay. Unique dialogue already passed previous tests; no repeated dialogue checklist is required.

Use a **disposable post-Tower save**, preferably your known-working later save with mirrors. Keep the original and master saves untouched. Close every Trade/wardrobe/dialogue menu normally before moving or teleporting. Never teleport while interacting.

## 1. Launch and stage outside

Cold-launch Cyberpunk, load the disposable save, then run:

```lua
GetMod("PTFR_B0_OrdinaryVendors").Outside()
```

Close CET and wait about 3 seconds. This goes to the existing outside staging point, not a shop. Durable logging starts automatically with the module and flushes each record.

If `GetMod` is nil, stop and report the error; do not try fact-setting commands. If a scene/workspot guard refuses Start, finish the current interaction normally. Do not force scene flags or reload all mods to bypass it.

## 2. Baseline and enable once

For any sample shop whose absence you have not checked, use its `Go` command from the route below **before Start**, look for the seller/menu, then return with `Outside()`. If it already works, while outside exclude it using its alias, for example:

```lua
GetMod("PTFR_B0_OrdinaryVendors").Skip("clothing")
```

Do not duplicate an already-working owner. `List()` prints all 25 exact site IDs; `Skip` also accepts an exact ID or list index. This baseline does not require inspecting every shop in the world, and unvisited shops remain unverified.

Outside all shops, run these as separate lines:

```lua
GetMod("PTFR_B0_OrdinaryVendors").Inspect()
GetMod("PTFR_B0_OrdinaryVendors").Start()
```

Close CET briefly, wait about 3 seconds, and check for **ARMED**. A smaller eligible count is normal if original availability gates are 0 or sites were skipped. Do not change those gates. Start does not arm the older packages or mirrors.

## 3. First route — five stops

Run **one Go command at a time**, close CET, approach the counter and open the actual Trade inventory. Check for one visible seller/no overlapping model. Close the menu normally. After each stop, use the Outside command below and close CET for at least 3 seconds before the next Go. If Go says an owner is still near, wait and Observe; do not bypass it.

Northside clothing:

```lua
GetMod("PTFR_B0_OrdinaryVendors").Go("clothing")
```

Kabuki junk:

```lua
GetMod("PTFR_B0_OrdinaryVendors").Go("junk")
```

Arroyo guns (also check the nearby medical counter if accessible):

```lua
GetMod("PTFR_B0_OrdinaryVendors").Go("guns")
```

Coastview food (also check the adjacent medical counter, covering the sixth retail type without another teleport):

```lua
GetMod("PTFR_B0_OrdinaryVendors").Go("food")
```

Japantown melee:

```lua
GetMod("PTFR_B0_OrdinaryVendors").Go("melee")
```

**Between every stop, after closing the menu:**

```lua
GetMod("PTFR_B0_OrdinaryVendors").Outside()
```

These teleport coordinates come from vanilla scene markers. Move clear of the counter/actor if the destination is tight; these are new-route test positions, not a guarantee of collision-free standing at every marker.

## 4. Return and save — same run

Repeat **clothing and guns** using the same Go/Outside sequence. Confirm the actual menus reopen and no duplicate seller appears. The other types' first/return mechanism already has prior representative evidence; this checks coexistence without asking for 25 repeated tests.

After the last Outside and a short wait, run:

```lua
GetMod("PTFR_B0_OrdinaryVendors").Observe("before-save")
GetMod("PTFR_B0_OrdinaryVendors").Checkpoint()
```

Proceed only when Checkpoint says **Outside/idle**. Create a **new disposable manual save**, note its slot, then fully quit. **Do not run Stop before this save or before quitting**: this part deliberately checks persistence of the armed idle state. Checkpoint does not create the save for you. Do not overwrite the save you loaded or the master fixture.

If there is any failure, duplicate or stuck interaction, skip saving; leave the shop if possible, Stop, quit without saving and report the site. Do not force the owner through it.

## 5. Cold reload — finish the same combined test

Relaunch and load the **new save from step 4**. Do not run Start or any Arm command. Visit clothing and guns again using the same Go/Outside sequence and confirm their menus work. A skipped sample should be replaced with another enabled sample using its same Go alias.

Finally, outside and after a short wait:

```lua
GetMod("PTFR_B0_OrdinaryVendors").Observe("after-cold-reload")
GetMod("PTFR_B0_OrdinaryVendors").Stop()
```

Fully quit **without saving again**. Tell me which menus worked, whether any duplicate appeared, and the new disposable save slot. I will inspect native Entries/Exits, departure/rearm, reload state, runtime counters and errors from the durable trace. Native counts prove owner transitions, not that you opened the inventory; your menu confirmation supplies that evidence.

Log: `Cyberpunk 2077/bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_B0_OrdinaryVendors/ordinary_vendors_trace.jsonl`. It appends across launches and records shutdown. Stop disables only this new 25-site batch; it does not disable older vendor or mirror packages.
