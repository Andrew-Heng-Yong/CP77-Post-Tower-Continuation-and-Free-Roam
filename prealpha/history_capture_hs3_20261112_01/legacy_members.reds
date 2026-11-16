  private persistent let nativeTicketHS3: Int32;
  private let exportLeaseHS3: CName;

  public func NativeTicketHS3() -> Int32 { return this.ready && this.frozen && !this.faulted ? this.nativeTicketHS3 : 0; }
  private func NativeHistoryCurrentHS3() -> Bool {
    let ticket=this.Fact("PTFRHS3_GateTicket");
    return ticket<=0 || ticket==this.nativeTicketHS3 || Equals(this.origin,n"post_ending_fallback");
  }
  private func NativeGateHS3(ticket: Int32,route: Int32) -> Bool {
    return ticket>0 && this.Fact("PTFRHS3_GateOpen")==1 && this.Fact("PTFRHS3_GateTicket")==ticket &&
      this.Fact("PTFRHS3_GateRoute")==route && this.Fact("PTFRHS3_GateResult")==0 && !this.Teardown() &&
      ((route==1 && this.Fact("q307_point_of_no_return")>0 && this.Fact("q115_point_of_no_return")==0) ||
       (route==2 && this.Fact("q115_point_of_no_return")==0 && this.Fact("q307_point_of_no_return")==0));
  }
  public func CaptureNativeHS3(ticket: Int32,route: Int32) -> Bool {
    if !this.running || this.faulted || this.revision>=2147483647 || !this.NativeGateHS3(ticket,route) { return false; }
    let jm=GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(jm) || jm.HasAnyDelayedStateChanges() { return false; }
    let captured: array<SnapshotRowHS1>;let row: SnapshotRowHS1;let check: SnapshotRowHS1;let i=0;
    while i<SnapshotDataHS1.Count() { row=this.ReadRow(i);ArrayPush(captured,row);i+=1; }
    i=0;
    while i<SnapshotDataHS1.Count() { check=this.ReadRow(i);captured[i].stable=this.Same(captured[i],check,-1);i+=1; }
    if !this.NativeGateHS3(ticket,route) || jm.HasAnyDelayedStateChanges() || !this.Shape(captured) { return false; }
    if this.ready { this.previousRows=this.rows; }
    this.ready=false;this.rows=captured;this.schema=1;this.catalogue=SnapshotDataHS1.Fingerprint();this.revision+=1;
    this.origin=n"pre_ending";this.frozen=true;this.nativeTicketHS3=ticket;this.fileToken=n"";this.exported=false;
    this.exportLeaseHS3=n"";this.jsonReadyHS2=false;this.jsonCursorHS2=0;ArrayClear(this.jsonRowsHS2);this.jsonHeaderHS2="";
    this.ResetRetainedHistory();this.ResetRead();this.towerCutoffPending=false;this.ready=true;
    this.detail="Native cutoff history committed in this save; verified export pending.";return true;
  }
  public func BeginExportHS3(epoch: Int32,revision: Int32,lease: String) -> Bool {
    if !this.CanExport() || epoch!=this.epoch || revision!=this.revision || Equals(lease,"") { return false; }
    this.exportLeaseHS3=StringToName(lease);return true;
  }
  public func LeaseHS3() -> String { return NameToString(this.exportLeaseHS3); }
  public func AckFileLeaseHS3(epoch: Int32,revision: Int32,token: String,lease: String) -> Bool {
    if Equals(lease,"") || NotEquals(this.exportLeaseHS3,StringToName(lease)) { return false; }
    return this.AckFile(epoch,revision,token);
  }
