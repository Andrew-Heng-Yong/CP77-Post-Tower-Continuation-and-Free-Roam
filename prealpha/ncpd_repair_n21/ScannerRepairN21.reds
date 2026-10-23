module PTFR.NCPDRepairN21

// Native journal entry activation only, after an N2 owner has been issued.
// No synthetic mappins, native fact resets, reward/credit repair or log polling.
public class ScannerRepairN21 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let attempts: array<Int32>;
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1; }
  public func Restored() -> Void {
    this.epoch+=1;this.warmup=5;
    ArrayClear(this.attempts);ArrayResize(this.attempts,ScannerDataN21.Count());
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(ScannerTickN21.Create(this,this.epoch),2.0,false);
  }
  private func Fact(name: String) -> Int32 {
    return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(StringToName(name));
  }
  private func SetOwned(id: String,suffix: String) -> Void {
    GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFactStr("PTFRN21_"+id+suffix,1);
  }
  private func Tower() -> Bool {
    return this.Fact("PostTowerFreeRoamActive")==1 && this.Fact("PTFRP0_DR13")==1
      && this.Fact("PTFRPA2_Finished")==1 && this.Fact("PTFRPA2_Fault")==0
      && this.Fact("q307_done")==1 && this.Fact("q307_finished")==1 && this.Fact("q307_2079")==1
      && this.Fact("q307_main_game_killed")==1 && this.Fact("q307_ep1_killed")==1
      && this.Fact("q307_active")==0 && this.Fact("q307_debug_reset")==0
      && this.Fact("q115_point_of_no_return")==0 && this.Fact("q305_johnny_scene_active")==0
      && this.Fact("PTFRU9_Support_Issued")==1 && this.Fact("PTFRU9_Support_Fault")==0
      && this.Fact("PTFRN1_Support_Issued")==1;
  }
  private func Terminal(i: Int32) -> Bool {
    let names=ScannerDataN21.Finish(i);let k=0;
    while k<ArraySize(names) { if this.Fact(names[k])!=0 { return true; };k+=1; }
    return false;
  }
  private func State(id: String) -> Int32 {
    let jm=GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(jm) || jm.HasAnyDelayedStateChanges() { return -1; }
    let entry=jm.GetEntryByString("points_of_interest/minor_activities/"+id,"gameJournalPointOfInterestMappin");
    return IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;
  }
  private func Phase(id: String) -> Int32 {
    let jm=GameInstance.GetJournalManager(this.GetGameInstance());let ms=GameInstance.GetMappinSystem(this.GetGameInstance());
    let phase: Uint16;let variant: Uint16;let active: Bool;
    if !IsDefined(jm) || !IsDefined(ms) || jm.HasAnyDelayedStateChanges() { return -1; }
    let entry=jm.GetEntryByString("points_of_interest/minor_activities/"+id,"gameJournalPointOfInterestMappin");
    if !IsDefined(entry) { return -1; }
    if !ms.GetPointOfInterestMappinSavedState(Cast<Uint32>(jm.GetEntryHash(entry)),phase,variant,active) { return -1; }
    return Cast<Int32>(phase);
  }
  public static func EligiblePOI(state: Int32,phase: Int32) -> Bool {
    return (state==1 || state==2) && (phase==1 || phase==2 || phase==3);
  }
  private func Permit(i: Int32) -> Void {
    let id=ScannerDataN21.ID(i);let mode=ScannerDataN21.Mode(i);let tag="PTFRN21_"+id;
    if mode==0 || this.Fact(tag+"_Request")!=1 || this.Fact(tag+"_Permit")!=0
      || this.Fact(tag+"_Denied")!=0 || this.Fact("PTFRN2_"+id+"_Issued")!=0 { return; }
    if this.Terminal(i) { this.SetOwned(id,"_Denied");return; }
    let state=this.State(id);let phase=this.Phase(id);
    if state<0 || phase<0 { return; }
    if !ScannerRepairN21.EligiblePOI(state,phase) { this.SetOwned(id,"_Denied");return; }
    if mode==1 {
      // These four stock start flags are written on initial owner entry,
      // before any player trigger. Exactly one old initialization is eligible.
      if this.Fact(ScannerDataN21.InitFact(i))!=1 { return; }
    } else {
      // The old N2 path accepts only phases 1/3. This supplementary path
      // accepts only 2 and cannot race an outstanding old permission.
      if phase!=2 || this.Fact("PTFRN2_"+id+"_Permit")!=0 { return; }
    }
    this.SetOwned(id,"_Permit");
  }
  private func Activate(i: Int32) -> Void {
    let id=ScannerDataN21.ID(i);let tag="PTFRN21_"+id;
    if this.Fact("PTFRN2_"+id+"_Issued")!=1 || this.Fact(tag+"_MapAck")==1 || this.Terminal(i) { return; }
    let state=this.State(id);let phase=this.Phase(id);
    if !ScannerRepairN21.EligiblePOI(state,phase) { return; }
    if state==2 { this.SetOwned(id,"_MapAck");return; }
    if this.attempts[i]>=3 { return; }
    this.attempts[i]+=1;
    // Preserve the native saved marker phase, variant and encounter progress.
    // Confirm Active on a later poll before persisting an acknowledgement.
    GameInstance.GetJournalManager(this.GetGameInstance()).ChangeEntryState(
      "points_of_interest/minor_activities/"+id,"gameJournalPointOfInterestMappin",
      gameJournalEntryState.Active,JournalNotifyOption.DoNotNotify);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; }
    this.Schedule();if this.warmup>0 { this.warmup-=1;return; }
    if !IsDefined(GetPlayer(this.GetGameInstance())) || !this.Tower() { return; }
    let i=0;
    while i<ScannerDataN21.Count() { this.Permit(i);this.Activate(i);i+=1; }
  }
  public func Inspect(id: String) -> String {
    let i=0;
    while i<ScannerDataN21.Count() {
      if Equals(id,ScannerDataN21.ID(i)) {
        let p="PTFRN21_"+id;
        return "Scanner N2.1 "+id+": issued="+ToString(this.Fact("PTFRN2_"+id+"_Issued"))
          +" mapAck="+ToString(this.Fact(p+"_MapAck"))+" journal/phase="+ToString(this.State(id))+"/"+ToString(this.Phase(id))
          +" terminal="+ToString(this.Terminal(i))+" supplementalMode="+ToString(ScannerDataN21.Mode(i))
          +" request/permit/denied="+ToString(this.Fact(p+"_Request"))+"/"+ToString(this.Fact(p+"_Permit"))+"/"+ToString(this.Fact(p+"_Denied"))
          +" | Read-only; acknowledgements are not rendered-icon or gameplay proof.";
      };i+=1;
    }
    return "Unknown N2 scanner ID; no changes.";
  }
}
public class ScannerTickN21 extends DelayCallback {
  private let owner: wref<ScannerRepairN21>;private let epoch: Int32;
  public static func Create(owner: ref<ScannerRepairN21>,epoch: Int32) -> ref<ScannerTickN21> {
    let tick=new ScannerTickN21();tick.owner=owner;tick.epoch=epoch;return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let owner=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.NCPDRepairN21.ScannerRepairN21") as ScannerRepairN21;
  if IsDefined(owner) { owner.Restored(); }
}
