# Post-Tower vehicle console test — 17 November 2026

CET logged `First-person return queued` for the standalone third-person representation activation and delayed first-person return. The user reported no visible improvement. The console line confirms that requests were submitted. Completion of the native transitions was not observed.

The first scripted vehicle test failed before mounting V with `Function 'IsSlotAvailable' requires 2 parameter(s).` CET supplies the `GameInstance` argument automatically. The corrected Lua call is `VehicleComponent.IsSlotAvailable(vehicle, seat)`. The same test requests regular entry with the mounting system and uses the stationary driver's exit request once third person is active. Entry, exit and the view after exiting remain pending for the console version. The manual vehicle round trip in the earlier report restored the body and arms.

[Earlier isolation](post_tower_body_view_isolation_20261116.md) · [CET argument handling](https://github.com/maximegmd/CyberEngineTweaks/blob/master/src/reverse/RTTIHelper.cpp#L545-L565) · [Vanilla seat check](../prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01/VehicleComponent.script#L863)

## On-foot follow-up

After the on-foot test queued `PSMStartStateMachine` for UpperBody and both Equipment hands, the user reported that the hands were normal and the torso was still distorted. The events were sent together, so the result does not identify which event mattered. The IFP state and separate holstered and drawn results were not reported for this test.

The proposed torso test applies the default `VehicleData` and `VehiclePassenger` features to V using `AnimationControllerComponent.ApplyFeature` while on foot. The vanilla exit state supplies those defaults through its state machine interface. The console path queues them on V and awaits a visual comparison. [VehicleData and VehiclePassenger defaults](../prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01/base.script#L281775)

## Photo Mode retest

The user reported that opening and exiting Photo Mode on foot cleared the remaining first-person torso distortion. The hands had already returned to normal after the earlier console test. This establishes a workaround for the torso in that session. Photo Mode alone with both symptoms present, the effect of the proposed animation feature resets, and the specific Photo Mode exit step that cleared the torso remain unverified.

## Automatic equivalent review

The matching `PhotoModeSystem` script interface includes `IsPhotoModeActive()` and `CanPhotoModeBeEnabled()` but exposes no entry or exit method. The live `gameuiPhotoModeMenuController` calls native `OnExitConfirmed(true)` during normal exit. It requires the active controller. The executable references `TogglePhotoMode` and `ExitPhotoMode` together in input registration. `PhotoModeEnableEvent` exposes an enable value, and its recipient and ability to drive the full transition are unverified. [System](../prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01/base.script#L58356) · [Menu exit](../prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01/base.script#L359587) · [Exact executable input references](../diagnostics/post_tower_photo_mode_20261117_01/native_02/function_00916cb0.asm)

The installed IFP observes Photo Mode show and hide and the pause menu through the same session pause and resume path. IFP's own API suspension releases its camera and shuts down runtime height, while a menu pause preserves the camera baseline and height. An API suspension cycle is therefore a different operation. The next comparison is a regular pause and resume while the torso is broken. If it remains broken, a Photo Mode round trip while IFP is suspended can test whether the torso recovers without active IFP camera correction. The existing upper body and hand resume is already callable in script. Any automatic torso repair still needs a confirmed gameplay operation and a handoff test on the genuinely completed Tower session.

Further native tracing confirmed the quest Open Photo Mode action reaches the full system entry request. The proposed automatic round trip and its remaining qualification are recorded in the [successor investigation](post_tower_photo_mode_refresh_20261117.md). No implementation or installation followed.
