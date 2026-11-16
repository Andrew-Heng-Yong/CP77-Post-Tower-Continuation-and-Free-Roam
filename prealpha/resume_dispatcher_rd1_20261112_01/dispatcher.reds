// RD1 does not issue quests or change gameplay history. Native adapters retain
// their own durable receipts and authored progression. New native preservation
// is unavailable until it has a qualified suspension/ownership contract.
public enum ResumeDecisionRD1 {
  Defer = 0,
  PreserveHistory = 1,
  KeepPrivateOwner = 2,
  KeepOriginalOwner = 3,
  FreshEntry = 4,
  EarnedStage = 5
}

public abstract class ResumeDispatcherRD1 {
  public static func Decide(history: Int32,live: Int32,privateReceipt: Int32,
    originalOwnerProven: Bool,retirementQualified: Bool,freshMatch: Bool,stageMatch: Bool) -> ResumeDecisionRD1 {
    // An existing receipt is never cleared to make a second controller eligible.
    if privateReceipt>0 { return ResumeDecisionRD1.KeepPrivateOwner; }
    if privateReceipt<0 { return ResumeDecisionRD1.Defer; }
    if originalOwnerProven { return ResumeDecisionRD1.KeepOriginalOwner; }
    if history==3 || history==4 || live==3 { return ResumeDecisionRD1.PreserveHistory; }
    if history!=1 && history!=2 { return ResumeDecisionRD1.Defer; }
    if !retirementQualified { return ResumeDecisionRD1.Defer; }
    if history==1 && live==1 && freshMatch { return ResumeDecisionRD1.FreshEntry; }
    if history==2 && (live==1 || live==2 || live==4) && stageMatch { return ResumeDecisionRD1.EarnedStage; }
    return ResumeDecisionRD1.Defer;
  }

  // Existing adapters retain their narrower stage, live-state, ownership and
  // one-time checks. This shared history filter does not grant an entry alone.
  public static func HistoryAdmits(history: Int32) -> Bool {
    return history==1 || history==2;
  }

  public static func Fact(game: GameInstance,name: String) -> Int32 {
    let qs=GameInstance.GetQuestsSystem(game);
    return IsDefined(qs)?qs.GetFactStr(name):-2147483647;
  }

  public static func Journal(game: GameInstance,path: String,type: String) -> Int32 {
    let jm=GameInstance.GetJournalManager(game);
    if !IsDefined(jm) || jm.HasAnyDelayedStateChanges() { return -1; }
    let entry=jm.GetEntryByString(path,type);
    return IsDefined(entry)?EnumInt(jm.GetEntryState(entry)):-1;
  }

  public static func Receipt(game: GameInstance,names: array<String>) -> Int32 {
    let i=0;let value=0;
    while i<ArraySize(names) {
      value=ResumeDispatcherRD1.Fact(game,names[i]);
      if value<0 { return -1; }
      if value>0 { return 1; }
      i+=1;
    }
    return 0;
  }

  public static func Same(a: ref<ResumeObservationRD1>,b: ref<ResumeObservationRD1>) -> Bool {
    if !IsDefined(a) || !IsDefined(b) || !a.valid || !b.valid || ArraySize(a.values)!=ArraySize(b.values) { return false; }
    let i=0;
    while i<ArraySize(a.values) {
      if a.values[i]!=b.values[i] { return false; }
      i+=1;
    }
    return true;
  }
}

public class ResumeObservationRD1 extends IScriptable {
  public let valid: Bool;
  public let values: array<Int32>;
  public let reason: String;
}
