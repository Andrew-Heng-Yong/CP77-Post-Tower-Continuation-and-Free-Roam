// Additive save-local history. Existing HS1 saved rows and indices stay intact.
public struct CaptureJournalHS3 {
  public persistent let state: Int32;
  public persistent let counter: Int32;
  public persistent let optional: Int32;
  public persistent let tracked: Int32;
  public persistent let stable: Bool;
}
public struct CaptureValueHS3 {
  public persistent let value: Int32;
  public persistent let stable: Bool;
}
public class CaptureRestoreHS3 extends ScriptableSystemRequest {}
public class CapturePollHS3 extends ScriptableSystemRequest {
  public let epoch: Int32;
}
public class CaptureArchiveHS3 extends ScriptableSystem {
  private persistent let schema: Int32;
  private persistent let catalogue: CName;
  private persistent let journals: array<CaptureJournalHS3>;
  private persistent let facts: array<CaptureValueHS3>;
  private persistent let items: array<CaptureValueHS3>;
  private persistent let previousJournals: array<CaptureJournalHS3>;
  private persistent let previousFacts: array<CaptureValueHS3>;
  private persistent let previousItems: array<CaptureValueHS3>;
  private persistent let previousRevision: Int32;
  private persistent let revision: Int32;
  private persistent let committedTicket: Int32;
  private persistent let route: Int32;
  private persistent let committed: Bool;
  private persistent let fileToken: CName;
  private let running: Bool;
  private let epoch: Int32;
  private let faulted: Bool;
  private let exported: Bool;
  private let pendingTicket: Int32;
  private let pendingRoute: Int32;
  private let pass: Int32;
  private let cursor: Int32;
  private let journalSample: array<CaptureJournalHS3>;
  private let factSample: array<CaptureValueHS3>;
  private let itemSample: array<CaptureValueHS3>;
  private let jsonRows: array<String>;
  private let jsonHeader: String;
  private let jsonCursor: Int32;
  private let jsonReady: Bool;
  private let detail: String;
  private let exportLease: CName;
  private let observedTicket: Int32;
  private let reportedMiss: Int32;

  public static func Get(game: GameInstance) -> ref<CaptureArchiveHS3> {
    return GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.HistorySnapshotHS1.CaptureArchiveHS3") as CaptureArchiveHS3;
  }
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1;this.exported=false;this.jsonReady=false; }
  public func Restored() -> Void { this.QueueRequest(new CaptureRestoreHS3()); }
  private func OnCaptureRestoreHS3(request: ref<CaptureRestoreHS3>) -> Void {
    if !this.running { return; }
    this.epoch+=1;this.exported=false;this.observedTicket=0;this.reportedMiss=0;this.ClearJSON();this.ResetCapture();
    // Never consult early quest-fact reads to erase a serialized certificate.
    this.faulted=this.schema!=0 && (this.schema!=3 || NotEquals(this.catalogue,SnapshotDataHS3.Fingerprint()));
    if this.committed && !this.Shape() { this.faulted=true; }
    this.Schedule();
  }
  private func Shape() -> Bool {
    return this.schema==3 && Equals(this.catalogue,SnapshotDataHS3.Fingerprint()) && this.revision>0 &&
      this.committedTicket>0 && (this.route==1 || this.route==2) &&
      ArraySize(this.journals)==SnapshotDataHS3.JournalCount() &&
      ArraySize(this.facts)==SnapshotDataHS3.FactCount() && ArraySize(this.items)==SnapshotDataHS3.ItemCount();
  }
  private func Fact(name: CName) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(name); }
  private func GateOpen(ticket: Int32,route: Int32) -> Bool {
    return ticket>0 && this.Fact(n"PTFRHS3_GateOpen")==1 && this.Fact(n"PTFRHS3_GateTicket")==ticket &&
      this.Fact(n"PTFRHS3_GateRoute")==route && this.Fact(n"PTFRHS3_GateResult")==0 &&
      ((route==1 && this.Fact(n"q307_point_of_no_return")>0 && this.Fact(n"q115_point_of_no_return")==0) ||
       (route==2 && this.Fact(n"q115_point_of_no_return")==0 && this.Fact(n"q307_point_of_no_return")==0)) &&
      this.Fact(n"q307_debug_reset")==0 && this.Fact(n"q307_2079")==0 &&
      this.Fact(n"q307_main_game_killed")==0 && this.Fact(n"q307_ep1_killed")==0 &&
      this.Fact(n"q307_done")==0 && this.Fact(n"q307_finished")==0;
  }
  private func ResetCapture() -> Void {
    this.pendingTicket=0;this.pendingRoute=0;this.cursor=0;this.pass=0;
    ArrayClear(this.journalSample);ArrayClear(this.factSample);ArrayClear(this.itemSample);
  }
  private func ClearJSON() -> Void { this.jsonReady=false;this.jsonCursor=0;this.jsonHeader="";this.exportLease=n"";ArrayClear(this.jsonRows); }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(CaptureTickHS3.Create(this,this.epoch),0.05,false);
  }
  public func Poll(epoch: Int32) -> Void {
    let request=new CapturePollHS3();request.epoch=epoch;this.QueueRequest(request);
  }
  private func ReadJournal(index: Int32) -> CaptureJournalHS3 {
    let row: CaptureJournalHS3;row.stable=true;
    let jm=GameInstance.GetJournalManager(this.GetGameInstance());
    let entry=jm.GetEntryByString(SnapshotDataHS3.Path(index),SnapshotDataHS3.Class(index));
    let objective=entry as JournalQuestObjective;
    row.state=IsDefined(entry)?EnumInt(jm.GetEntryState(entry)):-1;
    row.counter=IsDefined(objective)?jm.GetObjectiveCurrentCounter(objective):-1;
    row.optional=IsDefined(objective)?(jm.GetIsObjectiveOptional(objective)?1:0):-1;
    row.tracked=IsDefined(entry)?(jm.IsEntryTracked(entry)?1:0):-1;
    return row;
  }
  private func SameJournal(a: CaptureJournalHS3,b: CaptureJournalHS3) -> Bool {
    return a.state==b.state && a.counter==b.counter && a.optional==b.optional && a.tracked==b.tracked;
  }
  private func OnCapturePollHS3(request: ref<CapturePollHS3>) -> Void {
    if !this.running || request.epoch!=this.epoch { return; }
    this.Schedule();
    if this.faulted { return; }
    let player=GetPlayer(this.GetGameInstance()) as PlayerPuppet;
    let jm=GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(player) || !player.IsAttached() || player.IsReplacer() || player.IsDead() || !IsDefined(jm) { return; }
    let ticket=this.Fact(n"PTFRHS3_GateTicket");let route=this.Fact(n"PTFRHS3_GateRoute");
    if !this.GateOpen(ticket,route) {
      if ticket>0 && ticket==this.observedTicket && ticket!=this.committedTicket && ticket!=this.reportedMiss && this.Fact(n"PTFRHS3_GateOpen")==0 {
        this.reportedMiss=ticket;this.detail="Native capture gate closed without a committed history; no earlier state was fabricated.";
        ModLog(n"PTFR_HistorySnapshot",this.detail);
      }
      this.ResetCapture();this.PrepareJSON();return;
    }
    this.observedTicket=ticket;
    let legacy=SnapshotStateHS1.Get(this.GetGameInstance());
    if !IsDefined(legacy) || legacy.Faulted() { return; }
    if this.committed && this.committedTicket==ticket && this.route==route && this.Shape() && legacy.NativeTicketHS3()==ticket {
      GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(n"PTFRHS3_GateResult",1);return;
    }
    if jm.HasAnyDelayedStateChanges() { this.ResetCapture();return; }
    if this.pendingTicket!=ticket || this.pendingRoute!=route || this.pass==0 {
      this.ResetCapture();this.pendingTicket=ticket;this.pendingRoute=route;this.pass=1;
      this.detail="Capturing before native journal cleanup.";
    }
    let budget=0;let jr: CaptureJournalHS3;let vr: CaptureValueHS3;let actual: Int32;let index: Int32;
    let journalCount=SnapshotDataHS3.JournalCount();let factCount=SnapshotDataHS3.FactCount();
    let tx=GameInstance.GetTransactionSystem(this.GetGameInstance());
    if !IsDefined(tx) { return; }
    while budget<512 && this.cursor<SnapshotDataHS3.Count() {
      if this.cursor<journalCount {
        jr=this.ReadJournal(this.cursor);
        if this.pass==1 { ArrayPush(this.journalSample,jr); }
        else { this.journalSample[this.cursor].stable=this.SameJournal(this.journalSample[this.cursor],jr); }
      } else {
        index=this.cursor-journalCount;
        if index<factCount { actual=this.Fact(StringToName(SnapshotDataHS3.FactName(index))); }
        else {
          index-=factCount;
          let itemID=TDBID.Create(SnapshotDataHS3.Item(index));
          actual=IsDefined(TweakDBInterface.GetItemRecord(itemID))?tx.GetItemQuantity(player,ItemID.CreateQuery(itemID)):-1;
        }
        vr.value=actual;vr.stable=true;
        if this.cursor<journalCount+factCount {
          if this.pass==1 { ArrayPush(this.factSample,vr); } else { this.factSample[index].stable=this.factSample[index].value==actual; }
        } else {
          if this.pass==1 { ArrayPush(this.itemSample,vr); } else { this.itemSample[index].stable=this.itemSample[index].value==actual; }
        }
      }
      this.cursor+=1;budget+=1;
    }
    if !this.GateOpen(ticket,route) || jm.HasAnyDelayedStateChanges() { this.ResetCapture();return; }
    if this.cursor<SnapshotDataHS3.Count() { return; }
    if this.pass==1 { this.pass=2;this.cursor=0;return; }
    if this.revision>=2147483647 || !legacy.CaptureNativeHS3(ticket,route) { this.ResetCapture();return; }
    // Both systems publish from this one queued simulation request, without a
    // yield or CET access to any saved array. Publish committed last, ack after.
    if this.committed {
      this.previousJournals=this.journals;this.previousFacts=this.facts;this.previousItems=this.items;this.previousRevision=this.revision;
    }
    this.committed=false;this.journals=this.journalSample;this.facts=this.factSample;this.items=this.itemSample;
    this.schema=3;this.catalogue=SnapshotDataHS3.Fingerprint();this.revision+=1;this.committedTicket=ticket;this.route=route;
    this.fileToken=n"";this.exported=false;this.ClearJSON();this.committed=true;this.ResetCapture();
    this.detail="Save-local history committed before native cleanup; recovery export pending.";
    ModLog(n"PTFR_HistorySnapshot",this.detail);
    GameInstance.GetQuestsSystem(this.GetGameInstance()).SetFact(n"PTFRHS3_GateResult",1);
  }
  private func BoolJSON(value: Bool) -> String { return value?"true":"false"; }
  private func PrepareJSON() -> Void {
    if !this.committed || this.faulted || this.jsonReady || !this.Shape() { return; }
    let budget=0;let row: CaptureJournalHS3;let field: CaptureValueHS3;let body: String;let index: Int32;
    while budget<256 && this.jsonCursor<SnapshotDataHS3.Count() {
      if this.jsonCursor<SnapshotDataHS3.JournalCount() {
        row=this.journals[this.jsonCursor];
        body=",\"state\":"+ToString(row.state)+",\"counter\":"+ToString(row.counter)+",\"optional\":"+ToString(row.optional)+
          ",\"tracked\":"+ToString(row.tracked)+",\"stable\":"+this.BoolJSON(row.stable);
      } else {
        index=this.jsonCursor-SnapshotDataHS3.JournalCount();
        if index<SnapshotDataHS3.FactCount() { field=this.facts[index]; }
        else { field=this.items[index-SnapshotDataHS3.FactCount()]; }
        body=",\"value\":"+ToString(field.value)+",\"stable\":"+this.BoolJSON(field.stable);
      }
      ArrayPush(this.jsonRows,"{\"definition\":"+SnapshotDataHS3.Definition(this.jsonCursor)+body+"}");
      this.jsonCursor+=1;budget+=1;
    }
    if this.jsonCursor==SnapshotDataHS3.Count() {
      this.jsonHeader="{\"schema\":3,\"catalogue\":\""+NameToString(this.catalogue)+"\",\"origin\":\"pre_native_cleanup\",\"route\":"+
        ToString(this.route)+",\"ticket\":"+ToString(this.committedTicket)+",\"revision\":"+ToString(this.revision)+",\"rows\":[";
      this.jsonReady=true;
    }
  }
  public func CanExport() -> Bool { return this.running && !this.faulted && this.committed && this.jsonReady; }
  public func Exported() -> Bool { return this.exported; }
  public func Epoch() -> Int32 { return this.epoch; }
  public func Revision() -> Int32 { return this.revision; }
  public func Count() -> Int32 { return SnapshotDataHS3.Count(); }
  public func FileToken() -> String { return Equals(this.fileToken,n"")?"":NameToString(this.fileToken); }
  public func HeaderJSON() -> String { return this.CanExport()?this.jsonHeader:""; }
  public func RowJSON(i: Int32) -> String {
    if !this.CanExport() || i<0 || i>=ArraySize(this.jsonRows) { return ""; }return this.jsonRows[i];
  }
  public func AckFile(epoch: Int32,revision: Int32,token: String) -> Bool {
    if !this.CanExport() || epoch!=this.epoch || revision!=this.revision || Equals(token,"") { return false; }
    this.fileToken=StringToName(token);this.exported=true;this.detail="Save-local history and recovery export verified.";return true;
  }
  public func BeginExportHS3(epoch: Int32,revision: Int32,lease: String) -> Bool {
    if !this.CanExport() || epoch!=this.epoch || revision!=this.revision || Equals(lease,"") { return false; }
    this.exportLease=StringToName(lease);return true;
  }
  public func LeaseHS3() -> String { return NameToString(this.exportLease); }
  public func AckFileLeaseHS3(epoch: Int32,revision: Int32,token: String,lease: String) -> Bool {
    if Equals(lease,"") || NotEquals(this.exportLease,StringToName(lease)) { return false; }
    return this.AckFile(epoch,revision,token);
  }
  public func ReportIOFailure(epoch: Int32,revision: Int32) -> Void {
    if epoch==this.epoch && revision==this.revision { this.exported=false;this.detail="Recovery export pending; saved history retained."; }
  }
  // Future adapters read primitives only and must check stable before use.
  public func JournalState(i: Int32) -> Int32 {
    if !this.committed || this.faulted || !this.Shape() || this.committedTicket!=this.Fact(n"PTFRHS3_GateTicket") || i<0 || i>=ArraySize(this.journals) || !this.journals[i].stable { return -1; }
    return this.journals[i].state;
  }
  public func FactValue(i: Int32) -> Int32 {
    if !this.committed || this.faulted || !this.Shape() || this.committedTicket!=this.Fact(n"PTFRHS3_GateTicket") || i<0 || i>=ArraySize(this.facts) || !this.facts[i].stable { return -2147483647; }
    return this.facts[i].value;
  }
  public func Status() -> String {
    return "HS3 committed="+ToString(this.committed)+" ticket="+ToString(this.committedTicket)+" revision="+ToString(this.revision)+
      " fault="+ToString(this.faulted)+" exported="+ToString(this.exported)+" | "+this.detail;
  }
}
public class CaptureTickHS3 extends DelayCallback {
  private let owner: wref<CaptureArchiveHS3>;
  private let epoch: Int32;
  public static func Create(owner: ref<CaptureArchiveHS3>,epoch: Int32) -> ref<CaptureTickHS3> {
    let callback=new CaptureTickHS3();callback.owner=owner;callback.epoch=epoch;return callback;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
