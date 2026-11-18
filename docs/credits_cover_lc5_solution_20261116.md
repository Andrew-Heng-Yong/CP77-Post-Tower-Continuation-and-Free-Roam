# LC5 proposal: continuous cover across credits closure

Status: **source-qualified integration point; proposed rendering host awaits runtime qualification.** This is a continuation of the [recorded flash investigation](credits_flash_review_20261116.md). No runtime implementation, compilation, installation, launch, save edit or fact write was performed.

## Additional findings

The existing mod starts its setup UI after credits are closed, then queues a popup attachment. LC4's world fade and the eventual popup do not provide independent, continuous UI coverage over that interval. The supplied video exposes Afterlife for approximately 0.522 seconds. Which native fade writer exposed it remains unproven without a synchronized live trace.

The optional `TryEndingLoadingCleanup()` in the current loading-cover script cannot directly explain this opening gap: its caller runs only after the setup readiness checks pass, whereas the video first shows setup at 2 / 12 checks. Moving or removing that later cleanup is therefore not the proposed fix.

The current vanilla cache matches the preserved decompilation exactly: cache SHA-256 `B78043064AE90FB80861B0D885D1C8DBCD22070F1DB71F20664D19F2D83C4AAC`, decompiled source SHA-256 `5DED85C18A0FECFC055CB36E6636F55B6D909865D1393935FC6343DC23111E38`. The inspected executable is `D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4`; older executable addresses were not reused.

Current native code has two callers converging on the credits terminal routine at RVA `0x2E0ACFC`: the confirmation/forced-stop path at `0x2E0C1F8` and the scrolling-update path at `0x2E0C3C0`. The terminal routine has a branch that resolves `OnCloseFinalBoardsRequest` at `0x2E0AE6D` and queues the event at `0x2E0AE91`. Its alternate branch still performs a native destination request. This does not authorize intercepting other endings or changing that branch.

The matching current script handler `MenuScenario_FinalBoards.OnCloseFinalBoardsRequest()` calls `GotoIdleState()`. Idle closes all menus, hides menus and queues removal of an in-game notification. Thus a wrapper **before the original close handler** is a concrete integration point on the retained Tower route. A rectangle parented to the credits menu itself would not survive that menu teardown.

The current script API provides `inkLayerWrapper.GetVirtualWindow()`, widget `Reparent`, `RemoveChild`, visibility and opacity queries. The installed Codeware popup manager, by contrast, uses `DelayCallback` to attach a popup. Codeware's inspected local widget-building source attaches newly reparented widget trees without that popup queue. These establish candidate APIs, not proof of final compositor visibility or that every available layer is active during loading.

Evidence: [current script identity and extracted classes](../diagnostics/credits_flash_20261116_02/current_script_proof.json), [current terminal routine](../diagnostics/credits_flash_20261116_02/native_03/function_02e0acfc.asm), [forced-stop path](../diagnostics/credits_flash_20261116_02/native_05/function_02e0c1f8.asm), [scrolling-update path](../diagnostics/credits_flash_20261116_02/native_05/function_02e0c3c0.asm), and [current symbol/call references](../diagnostics/credits_flash_20261116_02/native_04/strings_xrefs.json). Native function names above describe observed structure; their RVAs are evidence for this executable, not proposed runtime hooks.

## Recommended implementation

Limit the proposed production change to the existing `r6/scripts/PTFR_Consolidated/PTFR_LoadingCoverLC1.reds`. Retain the current archive and all saved node, field and receipt identities.

1. Add a transient bridge owned by the current `StartupCoverLC1` session. Register its owner with a service so the menu-scenario callback can reach the existing game-bound owner without inventing a global `GameInstance` accessor.
2. Wrap `MenuScenario_FinalBoards.OnCloseFinalBoardsRequest`. Before calling the original handler, arm the bridge only for the actual close event, genuine completed Tower facts, the existing retained-session receipt `PTFRP0_DR02=1`, and an unfinished continuation with `PostTowerFreeRoamActive=0` and `PTFRPA2_Finished=0`. Do not use an old receipt alone, intercept Back/skip confirmation, start setup early, or write admission facts.
3. Attach an opaque full-screen canvas directly to a separate UI layer, outside the credits menu and the deferred popup queue. `inkSystemNotificationsLayer` is the candidate host to qualify, not an assumed working host. Preserve existing system notifications above the owned canvas and do not change the layer's visibility, fade policy, child order, input policy or native controllers. If a suitable live parent cannot be obtained, delegate the original close handler and record bridge unavailability rather than blocking the ending.
4. Keep this same canvas through the loading transition and setup. Mirror the current setup title, detail and progress into it using a shared view builder, so it remains a useful setup page rather than hiding the normal popup behind a blank screen. Keep the existing popup's blocking behavior and readiness pipeline. Avoid another early bridge-to-popup removal step; that would introduce a second visibility race.
5. Remove only the owned canvas when normal setup release succeeds. Existing `CoverReady -> native fade release -> camera/control readiness -> final checks` ordering remains intact. The bridge must not retain the native world fade until all checks pass.
6. Remove the owned canvas and invalidate callbacks on detach, restore/save switch and cancellation. Make repeated close events idempotent. Bind callbacks to the current owner/session epoch, not saved UI fields. Keep recovery from missing/replaced layer roots explicit; never remove or reparent unrelated widgets.

This changes presentation only. It neither speeds up wardrobe/profile processing nor unlocks or completes quests. It does not require a guessed delay, a changed q307 fact, replayed cleanup or a new native-address hook.

## Checks before implementation can be called a fix

The read-only CET layer check requested in chat establishes only root availability, visibility and opacity in that session. It cannot establish active drawing through a credits/loading transition. The layer's lifetime, draw order and behavior during loading are still open; a missing or hidden host requires revising the host choice before deployment.

Instrument bridge arm/attach/removal, setup popup show/ack, UI-state changes and the existing fade/handoff receipts with engine timestamps. Observe a recorded genuine Tower transition; distinguish the logical UI callbacks from visible pixels. Do not log every frame permanently.

Required fixtures: close during Rogue's call as in the supplied recording; confirmed close during another call; watched completion; slow loading and delayed popup attachment; duplicate close event; ordinary continuation-save reload; cancellation/save switch; unavailable host; preservation of system notifications; complete setup with normal camera/control; and a non-Tower close with the wrapper taking no action. The runtime success criterion is continuous coverage through the last pre-setup frame and correct final release, not merely an animation callback or a successful compile.

The proposed implementation is not yet built or installed. Source/native verification establishes the intervention point and the conservative lifecycle design; the outstanding rendering-host check and gameplay fixtures remain necessary.
