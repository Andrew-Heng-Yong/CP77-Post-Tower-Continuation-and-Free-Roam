# Red Dirt baseline before C5 installation

2026-09-26: user has not checked access yet. C5 rebuilt and remains workspace-only.
Do not enable it until the physical site and original gate are checked.

Load a disposable post-Tower save and visit Red Dirt in Arroyo normally. Confirm
the interior and mirror are accessible, and whether Look already works. No
teleport destination is validated yet; the extracted trigger center is not a
verified safe landing point.

At the mirror, while standing freely, run this read-only CET line:

```lua
local q=Game.GetQuestsSystem(); local p=Game.GetPlayer(); local v=p:GetWorldPosition(); print("RedDirt",v.x,v.y,v.z,"combat",p:IsInCombat(),"scene",Game.GetSceneSystem():GetScriptInterface():IsEntityInScene(p:GetEntityID()),"workspot",Game.GetWorkspotSystem():IsActorInWorkspot(p)); for _,f in ipairs({"PostTowerFreeRoamActive","PTFRP0_DR13","q307_active","q307_done","q307_finished","q307_2079","q307_main_game_killed","q305_johnny_scene_active","q115_point_of_no_return","mirror_interaction_disabled","sq011_mirror_off ","sq011_mirror_off","PTFRBM42_Enabled"}) do print("["..f.."]",q:GetFactStr(f)) end
```

The two sq011 names are deliberately different: the vanilla scene reads the
one with a trailing space. Never set either. Idle player state is necessary
but does not by itself prove that all sq011 ownership has ended. If the site
is inaccessible, the original gate is closed, or a quest owns the interaction,
stop and investigate rather than force the owner. If Look already works, no
additional mirror owner is justified.

Send the output and the physical prompt result, then quit without saving.
Installation requires a closed game and review of this baseline. Existing
Streetkid, ordinary mirrors and vendor packages remain unchanged.
