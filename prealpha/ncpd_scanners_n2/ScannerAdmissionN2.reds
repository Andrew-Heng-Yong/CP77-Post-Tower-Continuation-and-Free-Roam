module PTFR.NCPDScannersN2

// Only two stock scanner owners lack an authored start fact. Read their
// saved native POI phase before allowing a new owner. Never set native facts,
// journal state, markers, inventory, rewards, or renderer settings here.
public class ScannerAdmissionN2 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1; }
  public func Restored() -> Void {
    this.epoch+=1;this.warmup=5;
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(ScannerAdmissionTickN2.Create(this,this.epoch),2.0,false);
  }
  private func Fact(name: String) -> Int32 {
    return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(StringToName(name));
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
  public static func FreshPhase(found: Bool,phase: gamedataMappinPhase) -> Bool {
    return found && (Equals(phase,gamedataMappinPhase.DefaultPhase) || Equals(phase,gamedataMappinPhase.UndiscoveredPhase));
  }
  private func Phase(id: String) -> Int32 {
    let jm=GameInstance.GetJournalManager(this.GetGameInstance());
    let ms=GameInstance.GetMappinSystem(this.GetGameInstance());
    let phase: Uint16;let variant: Uint16;let active: Bool;
    if !IsDefined(jm) || !IsDefined(ms) || jm.HasAnyDelayedStateChanges() { return -1; }
    let entry=jm.GetEntryByString("points_of_interest/minor_activities/"+id,"gameJournalPointOfInterestMappin");
    if !IsDefined(entry) { return -1; }
    if !ms.GetPointOfInterestMappinSavedState(Cast<Uint32>(jm.GetEntryHash(entry)),phase,variant,active) { return -1; }
    return Cast<Int32>(phase);
  }
  private func Check(id: String) -> Void {
    let tag="PTFRN2_"+id;
    if this.Fact(tag+"_Request")!=1 || this.Fact(tag+"_Issued")!=0
      || this.Fact(tag+"_Permit")!=0 || this.Fact(tag+"_Denied")!=0 { return; }
    let phase=this.Phase(id);
    // Missing saved state is unknown, not fresh: keep waiting without output.
    if phase<0 { return; }
    let fresh=ScannerAdmissionN2.FreshPhase(true,IntEnum<gamedataMappinPhase>(Cast<Uint32>(phase)));
    GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFactStr(tag+(fresh ? "_Permit" : "_Denied"),1);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; }
    this.Schedule();if this.warmup>0 { this.warmup-=1;return; }
    if !IsDefined(GetPlayer(this.GetGameInstance())) || !this.Tower() { return; }
    this.Check("ma_cct_cpz_16");this.Check("ma_wbr_nok_05");
  }
  public func Inspect() -> String {
    return "N2 saved POI phases: cpz16="+ToString(this.Phase("ma_cct_cpz_16"))+" nok05="+ToString(this.Phase("ma_wbr_nok_05"))+" (-1 unknown; 0 completed; 1 default; 2 discovered; 3 undiscovered). No native state changed by Inspect.";
  }
}
public class ScannerAdmissionTickN2 extends DelayCallback {
  private let owner: wref<ScannerAdmissionN2>;private let epoch: Int32;
  public static func Create(owner: ref<ScannerAdmissionN2>,epoch: Int32) -> ref<ScannerAdmissionTickN2> {
    let tick=new ScannerAdmissionTickN2();tick.owner=owner;tick.epoch=epoch;return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let owner=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.NCPDScannersN2.ScannerAdmissionN2") as ScannerAdmissionN2;
  if IsDefined(owner) { owner.Restored(); }
}
