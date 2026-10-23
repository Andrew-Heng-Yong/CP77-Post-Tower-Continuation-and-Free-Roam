# Japantown netrunner 01 — one disposable two-visit check

Use a disposable post-Tower save, not the master. This package is installed **idle**. Do not change story or local vendor facts. Do not save after enabling it. The target is the Japantown netrunner 01 service near vanilla marker `(-354.645905, 1366.60144, 42.1621017)`; Japantown netrunner 02 is not this test.

1. Reach that netrunner counter with CET closed. First check whether a seller and working service menu are already present. If so, **stop: do not enable the probe or create a duplicate**. If absent, run the read-only baseline line at the counter:

   ```lua
   local q=Game.GetQuestsSystem(); local p=Game.GetPlayer():GetWorldPosition(); print("jpn-net1 baseline",p.x,p.y,p.z,"default_on",q:GetFactStr("wbr_jpn_netrun_01_default_on"),"Tower",q:GetFactStr("q307_done"))
   ```

2. Walk or travel more than 70 m from the counter, outside combat/scene/workspot. Run these separate CET lines:

   ```lua
   GetMod("PTFR_B0_JpnNetrunner01").Inspect()
   GetMod("PTFR_B0_JpnNetrunner01").Enable()
   ```

   `Inspect()` must say READY, then `Enable()` must confirm. If it refuses, **do not force any fact**; report the refusal.

3. Visit the counter. Confirm exactly one intended seller, open the actual netrunner service menu, close it, and run:

   ```lua
   GetMod("PTFR_B0_JpnNetrunner01").Observe("first-menu")
   ```

4. Go more than 60 m away, wait a few seconds, and run:

   ```lua
   GetMod("PTFR_B0_JpnNetrunner01").Observe("outside-first")
   ```

5. Return to the same counter, reopen the actual menu, and run:

   ```lua
   GetMod("PTFR_B0_JpnNetrunner01").Observe("second-menu")
   ```

6. Leave more than 60 m again, wait a few seconds, then run:

   ```lua
   GetMod("PTFR_B0_JpnNetrunner01").Observe("outside-second")
   GetMod("PTFR_B0_JpnNetrunner01").Disable()
   ```

Quit without saving and report whether both menus worked and one seller appeared. The durable file `bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_B0_JpnNetrunner01\jpn_netrunner01_trace.jsonl` should show two native Near entries/exits and two Far cycles. Prompt alone does not count as menu success. No other vendor should be enabled by this one-site package.
