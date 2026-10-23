# S4 combined check — Nix, Yoko, Mateo, Fingers, Viktor, Karim, Ronald, Bill

Use a disposable copy/slot of your working post-Tower save with the existing
automatic restoration. Cold-launch after installation. **No Enable/Arm/Start
commands are needed.** Wait briefly while standing normally, outside dialogue,
workspots, combat and vehicles, so the safe automatic startup can run.

Do one combined route, checking whichever sites your saved quest outcomes make
eligible. At each, open the actual Trade/ripperdoc/bar menu, try one available
ordinary dialogue option, close the menu and stand up normally. Leave the shop
area (200 m is sufficient for the copied distance-based departure boundaries),
return and reopen the menu. Walking between all eight then doing a return route
is also fine. Never teleport while a dialogue/menu/workspot is active.

Check:

- One intended seller; Bill's sleeping companion and Yoko's native ambient
  community are not automatically duplicates.
- No Johnny, Evelyn/Judy quest staging, unexpected quest/objective/reward, or
  stuck player state. At Viktor also check clinic access, his appearance and
  that there is no second cinematic Viktor.
- Fingers' original anger/refusal or death outcome stays intact. Do not attack
  him merely to test this batch.
- Shops blocked by their original/earned prerequisites remain blocked. Karim
  requires the completed Ballad service unlock; Bill requires his earned
  post-Dodger hot-dog service; Ronald requires his post-quest tree state.
  Viktor's unpaid-debt service is not forcibly unlocked. Report unavailable
  sites; do not change facts to make them work.

Logging starts automatically. Optional **one** CET command after the route:

```lua
GetMod("PTFR_B0_StoryEight").Observe("combined-route-done")
```

Then quit **without saving** this first smoke run. Tell me which sellers/menus
worked on first and return visits, which were absent/refused, and any stuck or
duplicate actor. I will read `story_eight_*.tsv` inside the installed CET module
and distinguish missing gates from failed scene requests. There is no need to
run a Stop command that changes vendor state; this diagnostic is read-only.

Cold reload persistence is a later result only if actually tested from a
disposable save made with S4 active; passing this route does not prove it.
