# Post-Tower camera investigation — 16 November 2026

The cause of the reported body clipping remains unconfirmed. The strongest current lead is incomplete restoration of the on-foot camera or body animation state during the retained-session handoff. A vehicle visit changes several of those states together, so its success does not identify the individual repair. This investigation made no runtime, installation or save changes. All 51 installed Core files still match the LC5 manifest. [Input hashes, source comparison and log excerpts](../diagnostics/post_tower_body_view_20261116_02/investigation.json)

The [original observation](post_tower_body_view_20261116.md) retains the four screenshots and vehicle/loading timeline. The roughly 1.3-metre camera drop was sampled **during** setup's temporary third-person body representation, before the first-person return request. There is no settled camera transform from the visibly broken view or the repaired view. The drop therefore cannot yet be described as the camera position causing the screenshots.

## What the handoff actually verifies

The installed `FinishPresentationTP2` and `FinishBodyReturnTP3` method bodies match the earlier TP3 source exactly. LC5's credits-cover change did not alter those methods. The existing refresh queues third-person representation, waits one second, queues first-person return for the same attached player, and waits another second before marking the presentation step finished. Its later trace records mesh visibility and UI state, without measuring the camera transform. [Installed-matching source](../prealpha/credits_cover_lc5_20261116_01/PTFR_LoadingCoverLC1.reds)

The native executable confirms separate request and completion handlers. The matched deactivation handler at RVA `0x2AA7794` accepts the intermediate activation states and starts deactivation state 5. It takes an early path when already in state 1 or 5. The separate finalizer at `0x2AA7A6C` completes state 5 to state 1 and clears the puppet's native representation flag. The activation finalizer at `0x2AA79E0` completes state 3 to state 4. These are static branches in the exact installed executable, not observations of the player's live state. In particular, an early return request is not automatically ignored merely because activation has not finished. [Fresh native handler readback](../diagnostics/post_tower_body_view_20261116_02/native_handlers_01.json)

The setup controller does not observe those native completions. Its control check verifies that the active camera agrees with V's first-person camera component, allowing the component within four horizontal metres and three vertical metres of V. A shared bad offset can pass. This is a confirmed verification gap; whether it caused this occurrence is unknown. A fixed extra delay or arbitrary camera-height correction is not supported by the present evidence.

## Why the vehicle recovery is useful evidence

In the exact current vanilla script cache, `DriveEvents.OnEnter` applies vehicle camera animation parameters. `DriveEvents.OnExit` resets both `CameraBodyOffset` and `CameraGameplay` to their authored defaults and resumes paused player state machines. `ExitEvents.OnEnter` also unmounts V, resets the vehicle animation feature, and restores camera bobbing. Player attachment initializes the two camera features too. The mod's body refresh is therefore only part of what a real vehicle round trip does. [Matching vanilla source and hashes](../prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01/manifest.json)

Relevant source locations are `PlayerPuppet` initialization at lines 45112–45113, `ResetVehFppCameraParams` at 281980–281983, `DriveEvents` from 547207, and `ExitEvents` from 550915 in `base.script`. The camera-feature reset is a reasonable candidate for a later controlled test, but no such reset was run here. The recorded four-second loading state during the vehicle visit does not establish that loading itself repaired the view.

## Separate confirmed compatibility finding

The same session's RED4ext log reports game version 2.50 / runtime `3.0.88.46235` and rejects **Immersive First Person 0.2.0** as incompatible because its requested runtime is `3.0.80.51928`. Its CET Lua code remains active, and its own log reports that the native plugin is unavailable. Height is configured at zero centimetres. This is a concrete mixed installation state, rather than proof that Immersive First Person caused the Tower symptom. [Pinned loader and add-on evidence](../diagnostics/post_tower_body_view_20261116_02/investigation.json)

The Lua camera had already suspended for the weapon at 15:48:39 Toronto time, before the bugged knife screenshot's clipboard timestamp. At vehicle entry it still reported `ownsCamera=false`. Its inspected suspension path releases its stored camera transform and clears the baseline. Consequently, simply releasing and reacquiring that Lua camera is a weaker explanation for the vehicle-only recovery. The screenshots are not frame-synchronized to these logs, and the add-on's archive and earlier writes remain possible contributors. No add-on file or setting was changed.

## Next observation

The user agreed to collect the following paired read-only check. Outputs are pending. Run it once during the broken view and once after the vehicle workaround, on foot with the knife drawn and roughly the same downward angle. It reads the current player, camera and installed add-on state and prints to CET. It does not write facts, settings, transforms or saves. Method availability was checked against the installed sources; live execution of this combined command is pending.

```lua
do local a=Game.GetScriptableSystemsContainer():Get(CName.new("PTFR.ActivityStateR3.PreAlphaArrivalPA1")); if IsDefined(a) then print(a:Status()) end; local p=Game.GetPlayer():GetFPPCameraComponent():GetLocalPosition(); local v=Game.GetCameraSystem():GetActiveCameraForward(); print("FPP local="..p.x..","..p.y..","..p.z.." forward="..v.x..","..v.y..","..v.z); local m=GetMod("ImmersiveFirstPerson"); if m and m.api then local s=m.api.GetCameraState(); print("IFP="..tostring(s.mode).." owns="..tostring(s.ownsCamera)) end end
```

Compare the camera position relative to the player, the first-person component's local position, and the viewing direction. A changed relative position at a matched angle would support camera/animation offset restoration. Similar positions with different visible bodies would shift the investigation toward representation, pose or garment attachment. A different local camera offset or add-on ownership would require separating that layer. Native completion state would still need observation if the paired camera data is inconclusive. No implementation or deployment follows from this report; the smaller loading-page layout remains deferred.
