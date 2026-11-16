  private persistent let claireTicket: Int32;
  private persistent let claireRemaining: Int32;
  private persistent let claireChoices: Int32;
  private let claireProbeLogged: Bool;

  // Bit mask for the actual reply options the player could see at cutoff.
  private func ClairePendingOptions(jm: ref<JournalManager>) -> Int32 {
    let root = "quests/minor_quest/mq058_semimaru_crystalcoat";
    let thread = "contacts/marianne/mq058_02_resolution/01a_v";
    let quest = jm.GetEntryByString(root,"gameJournalQuest");
    let group = jm.GetEntryByString(thread,"gameJournalPhoneChoiceGroup");
    if !IsDefined(quest) || !IsDefined(group) ||
      !Equals(jm.GetEntryState(quest),gameJournalEntryState.Succeeded) ||
      !Equals(jm.GetEntryState(group),gameJournalEntryState.Active) { return 0; }
    let options = [thread + "/01a_ch1_1",thread + "/01a_ch2_1",thread + "/01a_ch3_1"];
    let weights = [1,2,4];
    let mask = 0;
    let i = 0;
    while i < ArraySize(options) {
      let entry = jm.GetEntryByString(options[i],"gameJournalPhoneChoiceEntry");
      if !IsDefined(entry) { return 0; }
      let state = jm.GetEntryState(entry);
      if Equals(state,gameJournalEntryState.Active) { mask += weights[i]; }
      else {
        if !Equals(state,gameJournalEntryState.Inactive) { return 0; }
      }
      i += 1;
    }
    return mask;
  }

  private func ClaireCompletedUpgrade() -> Bool {
    return this.Fact(n"mq058_done")==1 && this.Fact(n"mq058_update_applied")==1 &&
      this.Fact(n"mq058_opened_vvc")==1 && this.Fact(n"mq058_active")==0 &&
      this.Fact(n"mq058_Claire_Attitude")==0 &&
      this.Fact(n"PTFRS29_mq058_semimaru_crystalcoat_Issued")==0;
  }

  private func ClaireResolutionIdle(game: GameInstance) -> Bool {
    let phone=GameInstance.GetPhoneManager(game);
    return IsDefined(phone) && !phone.IsPhoneCallActive();
  }

  private func CaptureClaireReply(ticket: Int32, route: Int32, jm: ref<JournalManager>) -> Void {
    this.claireTicket=0; this.claireRemaining=0; this.claireChoices=0;
    if route!=1 || !this.GateOpen(ticket,route) || !this.ClaireCompletedUpgrade() ||
      !this.ClaireResolutionIdle(this.GetGameInstance()) { return; }
    let options=this.ClairePendingOptions(jm);
    if options==0 { return; }
    let quests=GameInstance.GetQuestsSystem(this.GetGameInstance());
    let seconds=ReadClaireReplyWait(quests,ticket);
    if seconds<=0 || seconds>172800 || !this.GateOpen(ticket,route) ||
      jm.HasAnyDelayedStateChanges() || this.ClairePendingOptions(jm)!=options { return; }
    if !CommitClaireReplyWait(quests,ticket,seconds) || !this.GateOpen(ticket,route) { return; }
    this.claireRemaining=seconds; this.claireChoices=options; this.claireTicket=ticket;
    ModLog(n"PTFR_HistorySnapshot","Claire reply captured for this Tower run. Remaining game seconds " + ToString(seconds));
  }

  private func PollClaireReply(jm: ref<JournalManager>) -> Void {
    // Persist source data separately from globally imported history.
    if this.claireTicket<=0 || this.claireTicket!=this.Fact(n"PTFRHS3_GateTicket") ||
      this.Fact(n"PTFRHS3_GateRoute")!=1 || this.Fact(n"PTFRHS3_GateResult")!=1 ||
      this.Fact(n"PTFRHS3_GateOpen")!=0 || this.Fact(n"q307_done")!=1 ||
      this.Fact(n"q307_finished")!=1 || this.Fact(n"q307_2079")!=1 ||
      this.Fact(n"q307_debug_reset")!=0 || this.Fact(n"q307_active")!=0 ||
      this.Fact(n"q307_main_game_killed")!=1 || this.Fact(n"q307_ep1_killed")!=1 ||
      this.Fact(n"PostTowerFreeRoamActive")!=1 ||
      this.Fact(n"PTFRPA2_Finished")!=1 || this.Fact(n"PTFRPA2_Fault")!=0 ||
      this.Fact(n"PTFRClaire_Finished")!=0 || this.Fact(n"PTFRClaire_TimerReady")!=0 { return; }
    let quests=GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !this.ClaireCompletedUpgrade() || !this.ClaireResolutionIdle(this.GetGameInstance()) ||
      jm.HasAnyDelayedStateChanges() ||
      this.ClairePendingOptions(jm)!=this.claireChoices { return; }
    if PrepareClaireReplyOwner(quests,this.claireTicket,this.claireRemaining) {
      if this.Fact(n"PTFRClaire_Issued")==1 {
        quests.SetFact(n"PTFRClaire_TimerReady",1);
      } else {
        if this.Fact(n"PTFRClaire_Permit")==0 {
          quests.SetFact(n"PTFRClaire_Permit",1);
        }
      }
    } else {
      if !this.claireProbeLogged {
        this.claireProbeLogged=true;
        ModLog(n"PTFR_HistorySnapshot","Claire reply is waiting for the original owner to retire.");
      }
    }
  }

