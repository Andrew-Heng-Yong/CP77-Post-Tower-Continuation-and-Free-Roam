# Cyberware restrictions test and rollback

Test on a disposable copy of a supported post-Tower save. Keep the original save untouched. The script policy activates automatically; no ripperdoc visit is needed. Close menus, holster weapons and stand out of combat for about 40 seconds so a heavily equipped loadout can finish its one-item-per-second removal queue.

## Commands

Read status in CET:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR1.CyberwarePolicy"):GetStatus())
```

Expected after safe removal: `active=true pending=0 fault=false`. Pending lists exact records; a safety message means close menus/holster/leave the scene and wait. “Locked/unresolved” means an attempted removal did not finish; do not force-remove a quest lock.

Existing-save activation or a deliberate retry, outside menus:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR1.CyberwarePolicy"):Enable())
```

This checks genuine completed-Tower free-roam markers. It does not alter story facts or turn a pre-Tower save into a completed one. Automatic mode already covers supported existing post-Tower saves.

Removal audit for this load:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR1.CyberwarePolicy"):GetAudit())
```

`result=1` means the exact slot emptied and item/part conservation readback passed; `0` means not removed; `-1` means a conservation mismatch. Stop testing on a fault and reload the untouched pre-test save. Do not repeatedly force retries.

No Nerf, outside menus:

```lua
print(Game.GetScriptableSystemsContainer():Get("PTFR.RestrictionsR1.CyberwarePolicy"):NoNerf())
```

This changes only the save-local preference. It does not restore an old loadout; re-equip owned items normally. `Enable()` returns to Cyberware Only. No Nerf cannot undo a lost item or a corrupted save.

## First live checks

1. Confirm prohibited equipped implants disappear from equipment, including the Faceplate. Confirm Basic Kiroshi and Johnny's Special remain. Check ordinary fists, weapons, healing consumables, phone, scanner and Personal Link. The Faceplate ability should no longer work; normal unequip must not reset police history.
2. Check retained inventory counts and attached quickhacks/parts. Do not treat a Faceplate missing from the ordinary backpack as proof of deletion: it is normally hidden there. Use the ripperdoc's owned items or exact inventory data. Check removal of cyberware effects, hotkeys, arm attachments and the cyberdeck quickhack list; empty slots alone do not prove those are clean.
3. Open each of the ten ripperdoc categories. Restricted slots should show locks while categories and vendor inventory still open. Face/Hands stay mixed categories for approved items; native perk locks remain.
4. Buy one cheap restricted implant. The confirmation must explicitly say inventory-only. Check the expected money deduction, one acquired item, no installation, unchanged other equipment and no new cyberware hotkey. Cancel another purchase and verify no charge. Test buyback separately.
5. Try installing a restricted owned item with an empty slot, then with a slot already occupied. Neither may remove the old item or charge money/materials. Restricted upgrades must remain unavailable. Test an owned Basic Kiroshi and Johnny tattoo; ordinary requirements still apply. Test an affordable Basic Kiroshi upgrade without switching to another optic family.

After the first checks pass, use only disposable saves to test cold load, quickload, death reload, a saved equipped-Faceplate case, active-cyberware deferral and repeated Enable calls. Separately verify an ordinary pre-Tower save is untouched and two saves retain different No Nerf/Cyberware Only preferences. Do not overwrite the original baseline during this testing.

## Rollback

Close the game. From the workspace in PowerShell:

```powershell
& .\tools\deploy_restrictions_r1.ps1 -Mode ValidateRollback
& .\tools\deploy_restrictions_r1.ps1 -Mode Rollback
```

Run only this restriction rollback, not any Afterlife rollback. It recoverably moves the three added scripts to a timestamped workspace directory and leaves the accepted restoration files untouched. It does not re-equip implants in an already saved altered loadout; load the untouched pre-test save or re-equip manually after disabling/uninstalling the policy.
