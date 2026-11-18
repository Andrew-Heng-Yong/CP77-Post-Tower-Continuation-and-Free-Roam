# First-person body view after The Tower

The [follow-up camera investigation](post_tower_camera_investigation_20261116.md) records the native completion checks, a confirmed Immersive First Person compatibility problem, and the agreed paired CET capture. The observations below remain the original evidence; the root cause is not yet confirmed.

On 16 November the user reported that V’s torso and clothing fill the view when looking down after finishing The Tower. The first two screenshots show clipping with hands empty and with the Fang knife drawn. The last two show a normal body view in both states after entering and exiting a vehicle. The vehicle was set to third-person view by default. The user saw a short loading screen while getting in. [Screenshot hashes and local log excerpts](../diagnostics/post_tower_body_view_20261116_01/observation.json)

The installed credits cover reached Ready before the report. The stock hands attachment had been confirmed and the setup controller had queued its temporary third-person representation and then its first-person return. In both recent runs, the active camera was about 1.3 metres lower in the sample during the temporary representation than it was at the first-person arrival. The log has no camera transform sample after the return event or after vehicle exit. That leaves the camera position during the clipped view unmeasured. The current control check compares the active camera with V’s first-person camera component, so a shared offset can pass the alignment check. [Setup controller](../prealpha/credits_cover_lc5_20261116_01/PTFR_LoadingCoverLC1.reds) · [Observed samples and event order](../diagnostics/post_tower_body_view_20261116_01/observation.json)

In the later run, Immersive First Person recorded vehicle entry at 15:49:03 and on-foot camera ownership becoming available again at 15:49:13 Toronto time. The game recorded entering `inkFastTravelLoadingState` at 15:49:06 and returning to `inkGameState` at 15:49:10. The mod’s fast-travel start wrapper logged no request in that interval. The camera add-on also yielded to the weapon camera while the knife was drawn. Both the native vehicle transition and the add-on’s suspension and return are relevant to the recovery. [Local timeline](../diagnostics/post_tower_body_view_20261116_01/observation.json) · [Immersive First Person author documentation](https://github.com/cp2077/ImmersiveFirstPerson)

The exact current vanilla script cache shows that vehicle exit restores defaults for `CameraBodyOffset` and `CameraGameplay`. Player attachment also initializes both features. The mod’s existing appearance refresh queues representation events. A possible correction is to restore the same native on-foot camera defaults once the fresh Tower handoff has returned to the same attached player, provided a before-and-after comparison supports that change. It needs to respect scene, workspot, and external camera ownership. First check the settled camera after the existing return and after the vehicle workaround. The current evidence cannot separate the camera animation reset from the other operations during the vehicle round trip.

During the next reported occurrence, sample while on foot at the same location and downward angle before entering and after leaving the vehicle. Use the same weapon state for both snapshots. The command reads the current camera diagnostics and the installed add-on’s mode. It prints to CET and requires a loaded game.

```lua
do
  local a = Game.GetScriptableSystemsContainer():Get(CName.new("PTFR.ActivityStateR3.PreAlphaArrivalPA1"))
  if IsDefined(a) then print(a:Status()) end
  local m = GetMod("ImmersiveFirstPerson")
  if m and m.api and m.api.GetCameraState then
    local s = m.api.GetCameraState()
    print("IFP mode=" .. tostring(s.mode) .. " ownsCamera=" .. tostring(s.ownsCamera)
      .. " pitch=" .. tostring(s.nativePitch) .. " bodyBlend=" .. tostring(s.bodyBlend))
  end
end
```
