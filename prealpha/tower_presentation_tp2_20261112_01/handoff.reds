// TP2: finish presentation teardown in the retained, genuinely completed
// Tower session. This is an input-covered, one-shot sequence, never a travel
// watchdog. It does not claim that queued events prove rendered pixels.
@addMethod(StartupCoverLC1)
private func FinishPresentationTP2() -> Bool {
  if this.continuation || this.presentationRepairState >= 4 { return true; }
  let game=this.GetGameInstance();
  let player=GameInstance.GetPlayerSystem(game).GetLocalPlayerControlledGameObject() as PlayerPuppet;
  if !IsDefined(player) || !player.IsAttached() || player.IsReplacer() { return false; }
  if IsDefined(this.presentationRepairActor) && this.presentationRepairActor != player {
    // The old component's native detach owns cleanup. Never send its delayed
    // return event to a replacement player or resume the old sequence.
    this.presentationRepairState=4;
    ModLog(n"PTFR_PresentationTP2", "Presentation refresh abandoned after player replacement; no event sent to replacement.");
    return true;
  }
  if !this.Accepts(this.epoch) || !this.visible || !this.rendered ||
    !CyberwarePolicy.Safe(player) ||
    GameInstance.GetSceneSystem(game).GetScriptInterface().IsEntityInScene(player.GetEntityID()) ||
    GameInstance.GetPhoneManager(game).IsPhoneCallActive() ||
    GameInstance.GetPlayerSystem(game).IsInFreeCamera() { return false; }
  let chrome=CyberwarePolicy.Get(game);
  if !IsDefined(chrome) || !chrome.PTFRTP2HandsSettled() { return false; }
  let travel=GameInstance.GetBlackboardSystem(game).Get(GetAllBlackboardDefs().FastTRavelSystem);
  if !IsDefined(travel) || travel.GetBool(GetAllBlackboardDefs().FastTRavelSystem.FastTravelStarted) ||
    travel.GetBool(GetAllBlackboardDefs().FastTRavelSystem.FastTravelLoadingScreenStarted) { return false; }
  let ink=GameInstance.GetInkSystem();
  if !IsDefined(ink) { return false; }
  let layer=ink.GetLayer(n"inkLoadingLayer");
  if !IsDefined(layer) || ArraySize(layer.GetGameControllers()) != 0 { return false; }
  if this.presentationRepairState==0 {
    this.presentationRepairActor=player;
    this.presentationRepairState=1;
    this.presentationRepairAt=this.EngineNow()+0.25;
    // Native HideLoading clears the finished layer's presentation phase and
    // current loading-screen type. Pop only the named ending visual state.
    // The actual loading controller must already be absent; never manufacture
    // FastTravelLoadingScreenFinished or interrupt a real loading screen.
    this.popup.QueueBroadcastEvent(new inkHideLoadingScreenDelayedEvent());
    GameInstance.GetUISystem(game).RestorePreviousVisualState(n"inkEndGameLoadingState");
    ModLog(n"PTFR_PresentationTP2", "Completed Tower: residual loading presentation cleanup requested; no active loading controller.");
    this.SetStage("Restoring player appearance", "Finishing the transition back to gameplay.");
    return false;
  }
  if this.EngineNow()<this.presentationRepairAt { return false; }
  if this.presentationRepairState==1 {
    this.presentationRepairState=2;
    this.presentationRepairAt=this.EngineNow()+1.0;
    // A lone Deactivate can be a native no-op in the already-FPP state.
    // Rebuild through the native pair used by camera takeover/vehicle return.
    // No camera is activated and no inventory/equipment item is changed.
    player.QueueEvent(new ActivateTPPRepresentationEvent());
    ModLog(n"PTFR_PresentationTP2", "Body refresh: native representation activation queued under setup cover.");
    return false;
  }
  if this.presentationRepairState==2 {
    this.presentationRepairState=3;
    this.presentationRepairAt=this.EngineNow()+1.0;
    // The native handler also handles activation still awaiting appearances;
    // native finalization events remain engine-owned.
    player.QueueEvent(new DeactivateTPPRepresentationEvent());
    ModLog(n"PTFR_PresentationTP2", "Body refresh: native first-person return queued under setup cover.");
    return false;
  }
  this.presentationRepairState=4;
  this.TracePresentation(n"handoff-presentation-return");
  ModLog(n"PTFR_PresentationTP2", "Presentation handoff pair queued and settling interval elapsed; rendered arms and fast travel require gameplay verification.");
  return true;
}

// Observe the real ink state transitions; keep the existing quick-load
// cancellation callback and all native loading behavior intact.
@wrapMethod(gameuiInGameMenuGameController)
protected cb func OnUiStateChangedSuccessfully(previousStateName: CName, currentStateName: CName) -> Bool {
  let result=wrappedMethod(previousStateName,currentStateName);
  let player=this.GetPlayerControlledObject();
  if IsDefined(player) {
    let cover=StartupCoverLC1.Get(player.GetGame());
    if IsDefined(cover) { cover.TraceUIStateTP2(previousStateName,currentStateName); }
  }
  return result;
}

@addMethod(StartupCoverLC1)
public func TraceUIStateTP2(previous: CName, current: CName) -> Void {
  if !this.running || !this.Required() || this.presentationStateCaptures>=24 { return; }
  this.presentationStateCaptures+=1;
  ModLog(n"PTFR_PresentationTP2", "ink state="+NameToString(previous)+" -> "+NameToString(current)+
    " fresh="+ToString(!this.continuation)+" repair="+ToString(this.presentationRepairState));
}
