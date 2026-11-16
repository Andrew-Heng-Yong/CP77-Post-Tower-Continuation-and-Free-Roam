  // Native arrival, job and control checks have passed before this is called.
  // A presentation repair can wait briefly for stock hands, then yield to gameplay.
  private func FinishPresentationTP2() -> Bool {
    if this.continuation || this.presentationRepairState >= 4 { return true; }
    let now = this.EngineNow();
    if this.presentationRepairState == 3 {
      if now < this.presentationRepairAt { return false; }
      this.presentationRepairState = 4;
      this.TracePresentation(n"handoff-presentation-return");
      return true;
    }
    if this.presentationRepairState == 2 { return false; }
    if this.presentationRepairState == 0 {
      this.presentationRepairState = 1;
      this.presentationRepairAt = now + 4.0;
      this.SetStage("Restoring player appearance", "Finishing the transition back to gameplay.");
    }
    let game = this.GetGameInstance();
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerControlledGameObject() as PlayerPuppet;
    let chrome = CyberwarePolicy.Get(game);
    if !this.Accepts(this.epoch) || !this.visible || !this.rendered || !IsDefined(this.popup) ||
       !IsDefined(player) || !player.IsAttached() || !IsDefined(chrome) || !chrome.PTFRTP2HandsSettled() ||
       (NotEquals(this.presentationUIState, n"") && NotEquals(this.presentationUIState, n"inkGameState")) {
      if now < this.presentationRepairAt { return false; }
      this.presentationRepairState = 4;
      ModLog(n"PTFR_PresentationTP2", "Appearance refresh skipped after waiting for stock hands or safe presentation.");
      return true;
    }

    this.TryEndingLoadingCleanup();
    this.presentationRepairActor = player;
    this.presentationRepairState = 2;
    this.presentationRepairAt = now + 1.0;
    player.QueueEvent(new ActivateTPPRepresentationEvent());
    ModLog(n"PTFR_PresentationTP2", "Body refresh: native representation activation queued under setup cover.");
    return false;
  }

  // These flags and controllers guard only the optional loading cleanup.
  private func TryEndingLoadingCleanup() -> Void {
    let game = this.GetGameInstance();
    let defs = GetAllBlackboardDefs().FastTRavelSystem;
    let travel = GameInstance.GetBlackboardSystem(game).Get(defs);
    if !IsDefined(travel) {
      ModLog(n"PTFR_PresentationTP2", "Ending loading cleanup skipped: travel blackboard unavailable.");
      return;
    }
    let started = travel.GetBool(defs.FastTravelStarted);
    let loading = travel.GetBool(defs.FastTravelLoadingScreenStarted);
    if started || loading {
      ModLog(n"PTFR_PresentationTP2", "Ending loading cleanup skipped: travel started/loading=" + ToString(started) + "/" + ToString(loading));
      return;
    }
    let ink = GameInstance.GetInkSystem();
    let controllerCount = -1;
    if IsDefined(ink) {
      let layer = ink.GetLayer(n"inkLoadingLayer");
      if IsDefined(layer) { controllerCount = ArraySize(layer.GetGameControllers()); }
    }
    if controllerCount != 0 {
      ModLog(n"PTFR_PresentationTP2", "Ending loading cleanup skipped: loading controller count=" + ToString(controllerCount));
      return;
    }
    this.popup.QueueBroadcastEvent(new inkHideLoadingScreenDelayedEvent());
    GameInstance.GetUISystem(game).RestorePreviousVisualState(n"inkEndGameLoadingState");
    ModLog(n"PTFR_PresentationTP2", "Ending loading cleanup requested.");
  }

  // Return the same actor before polling setup checks again. A new scene,
  // vehicle or possession can take over representation while the event settles.
  private func FinishBodyReturnTP3() -> Void {
    let now = this.EngineNow();
    if this.presentationRepairState != 2 || now < this.presentationRepairAt { return; }
    this.presentationRepairState = 3;
    this.presentationRepairAt = now + 1.0;
    let game = this.GetGameInstance();
    let player = this.presentationRepairActor;
    let players = GameInstance.GetPlayerSystem(game);
    if !this.Required() || !IsDefined(player) || !player.IsAttached() || player.IsDead() || player.IsReplacer() ||
       players.GetLocalPlayerMainGameObject() != player || players.GetLocalPlayerControlledGameObject() != player || players.IsInFreeCamera() {
      ModLog(n"PTFR_PresentationTP2", "Body refresh return skipped: original player is no longer in normal control.");
      return;
    }
    let scene = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let mount = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(player);
    if !IsDefined(scene) || scene.IsEntityInScene(player.GetEntityID()) || EntityID.IsDefined(mount.parentId) ||
       GameInstance.GetWorkspotSystem(game).IsActorInWorkspot(player) {
      ModLog(n"PTFR_PresentationTP2", "Body refresh return yielded to a scene, vehicle or workspot.");
      return;
    }
    player.QueueEvent(new DeactivateTPPRepresentationEvent());
    ModLog(n"PTFR_PresentationTP2", "Body refresh: native first-person return queued under setup cover.");
  }
