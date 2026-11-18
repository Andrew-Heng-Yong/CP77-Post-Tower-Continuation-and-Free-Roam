# Post-Tower first-person arm capture

The 17 November 13:04 Toronto handoff logged the stock hands attachment and a complete automatic Photo Mode cycle. At 13:05 CET printed `Exploration animation reset queued`. The user reported that the arms were still missing. [Automatic refresh retest](post_tower_arm_refresh_retest_20261117.md)

The user supplied two CET captures, before and after entering and exiting a vehicle in third person. The same console probe enumerated skinned meshes on V and on the `AttachmentSlots.RightArm` item. The timestamps and rows below match CET's local `scripting.log`.

| Runtime observation | 13:12:20, arms missing | 13:13:23, after the vehicle |
| --- | --- | --- |
| `RightArm` entity ID and current appearance | `10461275`, `default` | `10461275`, `default` |
| `a0_000_nomad_base_fists` on V | Disabled | Disabled |
| `right_arm` and `left_arm` on V | Absent from the capture | Both enabled, `02_ca_limestone`, mask `18446744073709551615` |
| `a0_001__personal_link_default_holstered` on V | Absent from the capture | Enabled, mask `0` |

The stock first-person arms appearance `base\characters\common\player_base_bodies\appearances\arms\a0_000_fpp__full.app` defines meshes with the recovered `left_arm` and `right_arm` names. The current basegame engine and appearance archives contain identical bytes for that resource, with SHA-256 `C012DA0E8029303763F3D5DD2B7A7FAD3EE53ECE6E67847BA2A22C9D0B1527B6`. The stock TweakDB maps V's base fists to `Items.HolsteredFists` and the `holstered_arms` entity factory. The runtime arm component list gives a stronger readout for this bug than the attachment slot alone.

Clean Arms, UV Framework and VanillaHD each supply a different payload for the left first-person arm mesh. UV Framework and VanillaHD also supply distinct right-arm meshes. Clean Arms' female holstered personal link appearance uses mask `0`, matching the recovered link component. This identifies an installed appearance customization to account for. The vehicle recovery occurred with these archives available. The exact live resource provider order and any contribution to the initial missing components remain unverified.

The next console test targets the existing `Items.HolsteredFists` appearance. The matching vanilla equipment code uses `TransactionSystem.ResetItemAppearance` to restore an item's default appearance. A native registration lookup on the current executable confirmed the callable method. The slot-specific `RefreshAttachment` takes an input slot declared as `out` in REDscript. CET allocates a placeholder for `out` parameters, so a REDscript caller is needed to supply that slot. Whether the stock-item appearance call alone can add V's meshes back remains unverified. [Vanilla appearance reset](../prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01/base.script#L85266) · [Native lookup](../diagnostics/post_tower_arm_components_20261117_01/lookup/strings_xrefs.json) · [CET argument handling](https://github.com/maximegmd/CyberEngineTweaks/blob/v1.38.0/src/reverse/RTTIHelper.cpp#L534-L629)

Run once when the issue recurs with V on foot and the weapon holstered. The command checks that the two captured first-person mesh names are missing in whole or in part and that the existing RightArm item is the stock record. It requests the default appearance of that item and prints a receipt in CET. Compare whether the two meshes and the visible arms return after closing CET.

```lua
do local p=Game.GetPlayer(); if not IsDefined(p) or Game.GetQuestsSystem():GetFactStr("PostTowerFreeRoamActive")~=1 or Game.GetMountingFacility():IsMountedToAnything(p:GetEntityID()) or Game.GetWorkspotSystem():IsActorInWorkspot(p) or Game.GetPhotoModeSystem():IsPhotoModeActive() then print("Run on foot in post-Tower free roam"); return end; local t=Game.GetTransactionSystem(); local a=t:GetItemInSlot(p,TweakDBID.new("AttachmentSlots.RightArm")); if not IsDefined(a) or not ItemID.IsOfTDBID(a:GetItemID(),TweakDBID.new("Items.HolsteredFists")) then print("Stock hand attachment unavailable"); return end; local l,r=false,false; for _,c in ipairs(p:GetComponents()) do local n=c:GetName().value; l=l or n=="left_arm"; r=r or n=="right_arm" end; if l and r then print("Both arm components already present"); return end; t:ResetItemAppearance(p,a:GetItemID()); print("Stock hands appearance reset requested") end
```
