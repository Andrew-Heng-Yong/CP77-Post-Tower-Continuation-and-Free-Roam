// Separate transient coordinator for the new delivery entry. The graph owns
// Issued/Entered/Finished; this class can write only its private Permit.
public class StageResumeRD1 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let previous: ref<ResumeObservationRD1>;
  private let lastReason: String;

  public static func Get(game: GameInstance) -> ref<StageResumeRD1> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.HistorySnapshotHS1.StageResumeRD1") as StageResumeRD1;
  }
  private func Fact(name: String) -> Int32 { return ResumeDispatcherRD1.Fact(this.GetGameInstance(),name); }
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1;this.previous=null; }
  public func Restored() -> Void {
    this.epoch+=1;this.warmup=3;this.previous=null;this.SetPermit(false);
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(StageResumeTickRD1.Create(this,this.epoch),1.0,false);
  }
  private func SetPermit(allowed: Bool) -> Void {
    let qs=GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(qs) || this.Fact("PTFRRD1_MQ007_DELIVERY_Issued")!=0 { return; }
    let value=allowed?1:0;
    if qs.GetFactStr("PTFRRD1_MQ007_DELIVERY_Permit")!=value { qs.SetFactStr("PTFRRD1_MQ007_DELIVERY_Permit",value); }
  }
  private func Common() -> Bool {
    // This source-qualified route is under the native base/EP1 retirement paths
    // reviewed in HP1; killed facts alone are not a general ownership API.
    let game=this.GetGameInstance();let profile=ProfilePolicy.Get(game);let player=GetPlayer(game);
    return this.running && this.warmup==0 && SnapshotStateHS1.StartupReady(game) &&
      this.Fact("PostTowerFreeRoamActive")==1 && this.Fact("PTFRP0_DR13")==1 &&
      this.Fact("PTFRPA2_Finished")==1 && this.Fact("PTFRPA2_Fault")==0 &&
      this.Fact("q307_done")==1 && this.Fact("q307_finished")==1 && this.Fact("q307_2079")==1 &&
      this.Fact("q307_main_game_killed")==1 && this.Fact("q307_ep1_killed")==1 &&
      this.Fact("q307_active")==0 && this.Fact("q307_debug_reset")==0 &&
      this.Fact("q115_point_of_no_return")==0 && this.Fact("q305_johnny_scene_active")==0 &&
      this.Fact("PTFRU9_Support_Issued")==1 && this.Fact("PTFRU9_Support_Fault")==0 &&
      IsDefined(profile) && profile.PTFRPAComplete() && !profile.PTFRPAFaulted() &&
      IsDefined(player) && !player.IsDead() && !player.IsReplacer() && BodyPolicy.Safe(player) &&
      StartupCoverLC1.GameplayReleased(game);
  }
  public func DeliveryWanted() -> Bool {
    if !this.Common() || this.Fact("PTFRRD1_MQ007_DELIVERY_Ready")!=1 { return false; }
    let observed=ResumeContractsRD1.Read0(this.GetGameInstance(),false);
    return observed.valid;
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; }
    this.Schedule();if this.warmup>0 { this.warmup-=1; }
    if this.Fact("PTFRRD1_MQ007_DELIVERY_Issued")!=0 { this.previous=null;return; }
    if !this.Common() || this.Fact("PTFRRD1_MQ007_DELIVERY_Ready")!=1 {
      this.SetPermit(false);this.previous=null;return;
    }
    let game=this.GetGameInstance();let history=SnapshotStateHS1.Get(game);
    let observed=ResumeContractsRD1.Read0(game,true);
    let live=ResumeDispatcherRD1.Journal(game,"quests/minor_quest/mq007_smartgun","gameJournalQuest");
    let decision=ResumeDispatcherRD1.Decide(history.HistoryRootRD1("mq007_smartgun"),live,
      this.Fact("PTFRRD1_MQ007_DELIVERY_Issued"),false,true,false,observed.valid);
    this.SetPermit(Equals(decision,ResumeDecisionRD1.EarnedStage) && ResumeDispatcherRD1.Same(this.previous,observed));
    this.previous=observed;
    if NotEquals(this.lastReason,observed.reason) {
      this.lastReason=observed.reason;ModLog(n"PTFR_ResumeRD1","Machine Gun: "+observed.reason);
    }
  }
}

public class StageResumeTickRD1 extends DelayCallback {
  private let owner: wref<StageResumeRD1>;
  private let epoch: Int32;
  public static func Create(owner: ref<StageResumeRD1>,epoch: Int32) -> ref<StageResumeTickRD1> {
    let result=new StageResumeTickRD1();result.owner=owner;result.epoch=epoch;return result;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let owner=StageResumeRD1.Get(gameInstance);if IsDefined(owner) { owner.Restored(); }
}
