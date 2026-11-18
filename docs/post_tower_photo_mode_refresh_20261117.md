# Post-Tower Photo Mode refresh investigation — 17 November 2026

## Result and scope

There is a source-confirmed route for the mod to request a genuine Photo Mode round trip. The native `questOpenPhotoMode_NodeType` executes the Photo Mode system's entry request, and the active Photo Mode menu exposes its normal `OnExitConfirmed(true)` exit. A small private quest phase plus a scoped menu observer is therefore a concrete implementation candidate. No new native DLL or simulated keyboard input is required by this design.

The automatic round trip has **not** been built or tested. A smaller body-only refresh equivalent remains unproven. No installed mod, preference, game cache or save was changed, and the game was not launched. This report preserves the investigation boundary and does not reinstate BV1's removed refresh.

The accepted live observation is still the user's Photo Mode round trip clearing the remaining torso distortion after the UpperBody and two hand resumes had restored the hands. Photo Mode alone with both symptoms present remains unqualified. The earlier standalone ActivateTPPRepresentationEvent / delayed DeactivateTPPRepresentationEvent test made no visible improvement. Do not repeat that pair as a newly established solution. [Existing observations](post_tower_vehicle_console_test_20261117.md)

## Exact inputs

The inspected executable SHA256 is `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`. This matches the executable selected by the [current vanilla script manifest](../prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01/manifest.json). Fresh read-only native evidence is under [diagnostics/post_tower_photo_mode_20261117_02](../diagnostics/post_tower_photo_mode_20261117_02/).

All RVAs below belong to that executable only. Older SDK declarations were used as search leads, not current layout authority. For example, the inspected PhotoModeSystem size is 0xBF0 while the older SDK declaration is 0xBA0. The design uses serialized native quest types and reflected script methods rather than those offsets at runtime.

## Confirmed entry and exit route

- The node's native executor at `0x2C5F880` passes `forceFppMode`, `alwaysAllowTPP`, `lockExitUntilScreenshot`, `blockOutfitOption` and `factName` into the Photo Mode interface at vtable offset 0x1B0. The exact [executor disassembly](../diagnostics/post_tower_photo_mode_20261117_02/native_24/function_02c5f880.asm) agrees with the local Codeware import. The native node description explicitly describes the optional screenshot fact. [Description](../diagnostics/post_tower_photo_mode_20261117_02/native_23/function_02c5c9ac.asm)
- The PhotoModeSystem vtable maps that request to `0x225D6C0`. It checks that the system is inactive and idle, then invokes the same native entry routine at `0x2E50690`. That entry routine checks native admission and starts the Photo Mode lifecycle. [Vtable](../diagnostics/post_tower_photo_mode_20261117_02/native_14/data_036cac88.txt) · [Request](../diagnostics/post_tower_photo_mode_20261117_02/native_08/function_0225d6c0.asm) · [Entry](../diagnostics/post_tower_photo_mode_20261117_02/native_07/function_02e50690.asm)
- In the matching vanilla script, `gameuiPhotoModeMenuController.OnTryExitPhotomode` calls `OnExitConfirmed(true)` when no options were changed. The public native method is registered in the executable and invokes the controller's live exit callback. This is a call on the active menu controller, not a method on PhotoModeSystem. [Matching source](../prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01/base.script) near lines 359514 and 359587 · [Native wrapper](../diagnostics/post_tower_photo_mode_20261117_02/native_24/function_022318d0.asm)

This establishes a route through native entry and normal exit. It does not yet qualify a private phase, visibility of its UI, ordering against the setup cover or the resulting player model.

## What the full transition includes

The native entry and exit request code constructs `PhotoModeEnableEvent(true)` and `PhotoModeEnableEvent(false)` and queues each to the local controlled game object. The receiver identity is confirmed by the PlayerSystem getter wrapper using the same virtual slot. The event constructor and reflected SetEnable/GetEnable API are confirmed. The complete receiving-handler effects were not resolved. Replaying this notification by itself is **not** a proven model refresh and is not the recommended implementation. [Event constructor](../diagnostics/post_tower_photo_mode_20261117_02/native_06/function_02e481b8.asm) · [Controlled-object getter](../diagnostics/post_tower_photo_mode_20261117_02/native_12/function_00c5ba44.asm)

Photo Mode also inspects the native representation state and conditionally sends activation/deactivation events. Its later restoration code returns to the previous representation and restores a previously captured component enable state. Those changes are separate from the PhotoModeEnableEvent notifications. The exact significance of that component to the torso defect remains unknown. [Representation operation](../diagnostics/post_tower_photo_mode_20261117_02/native_16/function_02e551a0.asm) · [Restoration](../diagnostics/post_tower_photo_mode_20261117_02/native_14/function_02e50088.asm)

The full lifecycle has more dependencies than the failed standalone TPP/FPP event pair. Static code does not identify which difference repaired the user's torso. IFP's menu callbacks and the existing equipment/preview listeners remain part of the actual installed environment. They were inspected but not changed.

## Proposed implementation and qualification

1. Use a new, minimal private phase containing the native Open Photo Mode UI-manager action. Admit it once at the end of the genuine post-Tower setup, after native gameplay control returns. Preserve the existing arrival and setup receipts. Do not run on every load or every frame.
2. Keep `factName` empty and `lockExitUntilScreenshot` false. Do not take a screenshot or alter native quest facts. Keep normal native entry restrictions. Do not force a forbidden camera mode. Select any remaining node options deliberately in the candidate and read them back after serialization.
3. Keep the setup cover until the round trip finishes. Before packaging, verify actual layer ordering so Photo Mode cannot reproduce the unwanted intervening frames. Existing cover visibility alone is not proof that it covers Photo Mode.
4. Observe the menu instance created by this request and the preview initialization/loading lifecycle. Request normal exit only once the relevant initialization has finished. Do not infer completion merely from IsPhotoModeActive becoming true or from the request being queued. Work with the outfit/preview listeners already installed.
5. Use completion observation and a bounded real-time timeout that continues while Photo Mode is active. Ordinary paused gameplay timers must not be the only exit mechanism. Track ownership so cleanup cannot close Photo Mode opened independently by the player. If entry is rejected, do not force its guards or loop indefinitely.
6. Observe normal exit and the return to V's gameplay camera before releasing the cover. Record requested, opened, exit-requested and restored separately. Native acceptance, lifecycle completion and visual repair are different results.

The first live candidate should exercise the genuine ending handoff with both missing hands and torso distortion present. Compare holstered and drawn views after the automatic cycle. Preserve the earlier standalone hand recovery as separate evidence. Qualify interruption, rejected entry, cover visibility, IFP enabled/suspended behavior and the existing large-wardrobe setup path before making this a release default.

If a full round trip is too intrusive or slow, a smaller replacement needs a separate trace of which real-player restore operation is effective. This investigation has not established such a replacement, and it does not justify writing private native fields, faking Photo Mode's blackboard state or replaying preview inventory setup on gameplay V.
