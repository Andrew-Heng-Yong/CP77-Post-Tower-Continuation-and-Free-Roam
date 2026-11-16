  private persistent let executionCheckpointId: CName;
  private persistent let executionCheckpointState: array<Uint64>;
  private persistent let executionCheckpointTicket: Int32;
  private persistent let executionCheckpointRoute: Int32;
  private persistent let executionCheckpointCatalogue: CName;
  private persistent let executionCheckpointJournals: array<CaptureJournalHS3>;
  private persistent let executionCheckpointFacts: array<CaptureValueHS3>;
  private persistent let executionCheckpointItems: array<CaptureValueHS3>;
  private let executionCheckpointAttempts: Int32;

  private func ReadExecution(ticket: Int32, route: Int32, historyRevision: Int32,
                             presentation: array<Uint64>) -> array<Uint64> {
    let game = this.GetGameInstance();
    return ReadExecutionCheckpoint(GameInstance.GetQuestsSystem(game), GameInstance.GetDelaySystem(game),
                                   GameInstance.GetTimeSystem(game), ticket, route, historyRevision, presentation);
  }

  private func PrimeExecutionCheckpoint(ticket: Int32, route: Int32) -> Void {
    let unobserved: array<Uint64>;
    this.ReadExecution(ticket, route, 0, unobserved);
  }

  private func ReadExecutionPresentation(player: ref<PlayerPuppet>) -> array<Uint64> {
    let game = this.GetGameInstance();
    let entity = player.GetEntityID();
    let result: array<Uint64>;
    ArrayResize(result, 15);
    result[0] = EntityID.ToHash(entity);
    result[1] = Cast<Uint64>(PlayerPuppet.GetSceneTier(player));

    let scene = GameInstance.GetSceneSystem(game);
    if IsDefined(scene) {
      let access = scene.GetScriptInterface();
      if IsDefined(access) {
        result[2] = 1u;
        result[3] = Cast<Uint64>(access.IsEntityInScene(entity) ? 1 : 0);
        result[4] = Cast<Uint64>(access.IsEntityInDialogue(entity) ? 1 : 0);
        result[5] = Cast<Uint64>(access.GetSceneSystemCameraControlEnabled() ? 1 : 0);
      }
    }

    let manager = GameInstance.GetPhoneManager(game);
    if IsDefined(manager) {
      result[6] = 1u;
      result[7] = Cast<Uint64>(manager.IsPhoneCallActive() ? 1 : 0);
    }
    let board = GameInstance.GetBlackboardSystem(game);
    if !IsDefined(board) { return result; }
    let comDevice = board.Get(GetAllBlackboardDefs().UI_ComDevice);
    if !IsDefined(comDevice) { return result; }
    let variant = comDevice.GetVariant(GetAllBlackboardDefs().UI_ComDevice.PhoneCallInformation);
    if !IsDefined(variant) { return result; }
    let info = FromVariant<PhoneCallInformation>(variant);
    result[8] = 1u;
    result[9] = NameToHash(info.contactName);
    result[10] = Cast<Uint64>(EnumInt(info.callPhase));
    result[11] = Cast<Uint64>(EnumInt(info.callMode));
    result[12] = Cast<Uint64>((info.isAudioCall ? 1 : 0) + (info.isPlayerCalling ? 2 : 0) +
      (info.isPlayerTriggered ? 4 : 0) + (info.isRejectable ? 8 : 0) + (info.showAvatar ? 16 : 0));
    result[13] = Cast<Uint64>(EnumInt(info.visuals));
    let phone = GameInstance.GetScriptableSystemsContainer(game).Get(n"PhoneSystem") as PhoneSystem;
    if IsDefined(phone) && IsNameValid(info.contactName) {
      let fact = info.isPlayerCalling ? phone.GetPhoneCallFactName(n"player", info.contactName) :
        phone.GetPhoneCallFactName(info.contactName, n"player");
      result[14] = Cast<Uint64>(this.Fact(StringToName(fact)) + 1);
    }
    return result;
  }

  private func StoreExecutionCheckpoint(ticket: Int32, route: Int32, capture: array<Uint64>) -> Void {
    this.executionCheckpointId = n"";
    ArrayClear(this.executionCheckpointState);
    this.executionCheckpointTicket = 0;
    this.executionCheckpointRoute = 0;
    this.executionCheckpointCatalogue = n"";
    ArrayClear(this.executionCheckpointJournals);
    ArrayClear(this.executionCheckpointFacts);
    ArrayClear(this.executionCheckpointItems);
    if ArraySize(capture) == 0 || !this.GateOpen(ticket, route) {
      ModLog(n"PTFR_HistorySnapshot", "Execution checkpoint unavailable for the current cutoff.");
      return;
    }
    let encoded = DecodeExecutionCheckpoint(capture);
    if UTF8StrLen(encoded) <= 32 || !this.GateOpen(ticket, route) { return; }
    this.executionCheckpointState = capture;
    this.executionCheckpointTicket = ticket;
    this.executionCheckpointRoute = route;
    this.executionCheckpointCatalogue = SnapshotDataHS3.Fingerprint();
    // The global-latest import owns the legacy cache. This snapshot belongs
    // to the ending session that committed both samples in this request.
    this.executionCheckpointJournals = this.journals;
    this.executionCheckpointFacts = this.facts;
    this.executionCheckpointItems = this.items;
    this.executionCheckpointId = StringToName(UTF8StrMid(encoded, 0, 32));
    ModLog(n"PTFR_HistorySnapshot", "Save-local execution checkpoint committed before native cleanup.");
  }

  private func HasExecutionCheckpoint() -> Bool {
    return this.running && NotEquals(this.executionCheckpointId, n"") && ArraySize(this.executionCheckpointState) > 0 &&
      Equals(this.executionCheckpointCatalogue, SnapshotDataHS3.Fingerprint()) &&
      this.executionCheckpointTicket > 0 && this.executionCheckpointTicket == this.Fact(n"PTFRHS3_GateTicket") &&
      (this.executionCheckpointRoute == 1 || this.executionCheckpointRoute == 2) &&
      this.executionCheckpointRoute == this.Fact(n"PTFRHS3_GateRoute") &&
      ArraySize(this.executionCheckpointJournals) == SnapshotDataHS3.JournalCount() &&
      ArraySize(this.executionCheckpointFacts) == SnapshotDataHS3.FactCount() &&
      ArraySize(this.executionCheckpointItems) == SnapshotDataHS3.ItemCount();
  }

  public func ExecutionCheckpointId() -> String {
    return this.HasExecutionCheckpoint() ? NameToString(this.executionCheckpointId) : "";
  }

  public func ExecutionCheckpointJSON() -> String {
    if !this.HasExecutionCheckpoint() { return ""; }
    let encoded = DecodeExecutionCheckpoint(this.executionCheckpointState);
    let length = UTF8StrLen(encoded);
    if length <= 32 || NotEquals(StringToName(UTF8StrMid(encoded, 0, 32)), this.executionCheckpointId) { return ""; }
    return UTF8StrMid(encoded, 32, length - 32);
  }

  public func MatchesExecutionCheckpoint(id: String, data: String) -> Bool {
    return NotEquals(data, "") && Equals(id, this.ExecutionCheckpointId()) &&
      Equals(data, this.ExecutionCheckpointJSON());
  }

  public func ExecutionCheckpointJournal(index: Int32) -> CaptureJournalHS3 {
    let missing: CaptureJournalHS3;
    if !this.HasExecutionCheckpoint() || index < 0 || index >= ArraySize(this.executionCheckpointJournals) {
      missing.state = -1;
      missing.counter = -1;
      missing.optional = -1;
      missing.tracked = -1;
      return missing;
    }
    return this.executionCheckpointJournals[index];
  }

  public func ExecutionCheckpointFact(index: Int32) -> CaptureValueHS3 {
    let missing: CaptureValueHS3;
    if !this.HasExecutionCheckpoint() || index < 0 || index >= ArraySize(this.executionCheckpointFacts) { return missing; }
    return this.executionCheckpointFacts[index];
  }

  public func ExecutionCheckpointItem(index: Int32) -> CaptureValueHS3 {
    let missing: CaptureValueHS3;
    if !this.HasExecutionCheckpoint() || index < 0 || index >= ArraySize(this.executionCheckpointItems) { return missing; }
    return this.executionCheckpointItems[index];
  }

