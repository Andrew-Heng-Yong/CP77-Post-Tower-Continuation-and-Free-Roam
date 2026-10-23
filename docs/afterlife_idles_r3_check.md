# Afterlife idle routines R3 — focused live check

R3 installed with receipt on 2026-10-05 at 15:25Z; live checks pending. Do not
paste commands to force quest facts or reset crowds. R2 density and earlier
hologram/Rogue/Nix/Zetatech passes are preserved, not tests to repeat.

1. Cold-launch a disposable
   completed-Tower save. Do not save during this first test.
2. Visit the booth with the four mercenaries. Wait about 15 seconds without
   entering combat or a dialogue. Expected source routine: **three sitting,
   one standing with an ambient idle**, not four standing motionless.
3. Walk through the bar, entrance and rear rooms. Pause about 30 seconds near
   any suspicious stationary NPC so the audit can distinguish a transition
   from a persistent candidate. Working standing idles are valid. No NPC needs
   to be attacked or reset.
4. Mark an observed problem while looking at that actor:

   ```lua
   print(GetMod("PTFR_Afterlife_Behavior_Audit").Observe("still-frozen"))
   ```

5. Send the resulting `afterlife_behavior_*.jsonl` filename and whether the
   booth actors sit/animate. Quit without saving. The separate diagnostic lives
   in `bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_Afterlife_Behavior_Audit`.

If nothing changes, this read-only counter check helps separate registration,
streaming and command delivery:

```lua
local q=Game.GetQuestsSystem(); for _,n in ipairs({"PTFRAL2_LocalActive","PTFRAL3_Registered","PTFRAL3_WorldApplied","PTFRAL3_Merc01Ready","PTFRAL3_Merc02Ready","PTFRAL3_Merc03Ready","PTFRAL3_Merc04Ready","PTFRAL3_Requests","PTFRAL3_Failures","PTFRAL3_Timeouts"}) do print(n,q:GetFactStr(n)) end
```

Counters show dispatch, not successful animation. Empty native actor bindings
remain unknown, not a reason to spawn replacements. Broader census completeness,
return/reload and combat cancellation require separate evidence.

Rollback, only with the game closed: `tools/rollback_afterlife_idles_r3.ps1`
defaults to a read-only preflight; `-Restore` moves only the four R3 additions
recoverably into the workspace. It does not roll back R2 or Nix. Leave any new
diagnostic logs in place for analysis.
