  private persistent let nativeExportPendingHS4: Bool;
  private persistent let importedGlobalHS4: Bool;
  private let clientLeaseHS4: CName;
  private let requireLatestHS4: Bool;
  private let fileLoadedHS4: Bool;
  private let importHS4: CName;
  private let importFaultHS4: Bool;
  private let importRevisionHS4: Int32;
  private let importLegacyRevisionHS4: Int32;
  private let importTicketHS4: Int32;
  private let importRouteHS4: Int32;
  private let importHS1TokenHS4: CName;
  private let importHS3TokenHS4: CName;
  private let legacyCursorHS4: Int32;
  private let extendedCursorHS4: Int32;
  private let importedLegacyHS4: array<SnapshotRowHS1>;
  private let importedJournalsHS4: array<CaptureJournalHS3>;
  private let importedFactsHS4: array<CaptureValueHS3>;
  private let importedItemsHS4: array<CaptureValueHS3>;

  private func ResetLatestHS4() -> Void {
    this.clientLeaseHS4=n"";this.requireLatestHS4=false;this.fileLoadedHS4=false;this.ClearImportHS4();
  }
  private func ClearImportHS4() -> Void {
    this.importHS4=n"";this.importFaultHS4=false;this.legacyCursorHS4=0;this.extendedCursorHS4=0;
    ArrayClear(this.importedLegacyHS4);ArrayClear(this.importedJournalsHS4);
    ArrayClear(this.importedFactsHS4);ArrayClear(this.importedItemsHS4);
  }
  public func OpenClientHS4(lease: String) -> Bool {
    if !this.running || Equals(lease,"") { return false; }
    this.clientLeaseHS4=StringToName(lease);return true;
  }
  public func ClientLeaseHS4() -> String { return NameToString(this.clientLeaseHS4); }
  private func ClientHS4(epoch: Int32,lease: String) -> Bool {
    return this.running && epoch==this.epoch && NotEquals(lease,"") && Equals(this.clientLeaseHS4,StringToName(lease));
  }
  public func RequireLatestHS4(epoch: Int32,lease: String) -> Void {
    if this.ClientHS4(epoch,lease) { this.requireLatestHS4=true; }
  }
  public func RequiresLatestHS4() -> Bool { return this.requireLatestHS4; }
  public func GlobalFileReadyHS4() -> Bool { return this.running && this.fileLoadedHS4 && !this.importFaultHS4; }
  public func NativeExportPendingHS4() -> Bool { return this.nativeExportPendingHS4; }
  public func MayLoadLatestHS4() -> Bool {
    return this.running && !this.nativeExportPendingHS4 && this.Fact(n"PTFRHS3_GateOpen")==0 &&
      (this.schema==0 || (this.schema==3 && Equals(this.catalogue,SnapshotDataHS3.Fingerprint())));
  }
  public func DefinitionHS4(channel: Int32,index: Int32) -> String {
    if channel==1 && index>=0 && index<SnapshotDataHS1.Count() { return SnapshotDataHS1.MetadataJSON(index); }
    if channel==3 && index>=0 && index<SnapshotDataHS3.Count() { return SnapshotDataHS3.Definition(index); }
    return "";
  }
  public func BeginFileHS4(epoch: Int32,lease: String,transaction: String,ticket: Int32,route: Int32,
      revision: Int32,legacyRevision: Int32,token1: String,token3: String) -> Void {
    let r=new FileBeginRequestHS4();r.epoch=epoch;r.lease=lease;r.transaction=transaction;r.ticket=ticket;r.route=route;
    r.revision=revision;r.legacyRevision=legacyRevision;r.token1=token1;r.token3=token3;this.QueueRequest(r);
  }
  private func OnFileBeginRequestHS4(r: ref<FileBeginRequestHS4>) -> Void {
    if !this.ClientHS4(r.epoch,r.lease) || !this.MayLoadLatestHS4() || Equals(r.transaction,"") ||
      r.ticket<=0 || (r.route!=1 && r.route!=2) || r.revision<=0 || r.legacyRevision<=0 ||
      Equals(r.token1,"") || Equals(r.token3,"") || StrLen(r.token1)>96 || StrLen(r.token3)>96 { return; }
    this.ClearImportHS4();this.requireLatestHS4=true;this.fileLoadedHS4=false;this.importHS4=StringToName(r.transaction);
    this.importRevisionHS4=r.revision;this.importLegacyRevisionHS4=r.legacyRevision;
    this.importTicketHS4=r.ticket;this.importRouteHS4=r.route;
    this.importHS1TokenHS4=StringToName(r.token1);this.importHS3TokenHS4=StringToName(r.token3);
  }
  public func ImportTransactionHS4() -> String { return NameToString(this.importHS4); }
  public func ImportCursorHS4(channel: Int32) -> Int32 { return channel==1?this.legacyCursorHS4:this.extendedCursorHS4; }
  public func ImportFaultHS4() -> Bool { return this.importFaultHS4; }
  public func SendPacketHS4(epoch: Int32,lease: String,transaction: String,channel: Int32,start: Int32,count: Int32,data: array<Int32>) -> Void {
    let r=new FilePacketRequestHS4();r.epoch=epoch;r.lease=lease;r.transaction=transaction;
    r.channel=channel;r.start=start;r.count=count;r.data=data;this.QueueRequest(r);
  }
  private func ImportCurrentHS4(epoch: Int32,lease: String,transaction: String) -> Bool {
    return this.ClientHS4(epoch,lease) && this.MayLoadLatestHS4() && !this.importFaultHS4 &&
      NotEquals(transaction,"") && Equals(this.importHS4,StringToName(transaction));
  }

  // PACKET_READERS_HS4

  public func FinishFileHS4(epoch: Int32,lease: String,transaction: String) -> Void {
    let r=new FileFinishRequestHS4();r.epoch=epoch;r.lease=lease;r.transaction=transaction;this.QueueRequest(r);
  }
  private func OnFileFinishRequestHS4(r: ref<FileFinishRequestHS4>) -> Void {
    if !this.ImportCurrentHS4(r.epoch,r.lease,r.transaction) || this.legacyCursorHS4!=SnapshotDataHS1.Count() ||
      this.extendedCursorHS4!=SnapshotDataHS3.Count() || ArraySize(this.importedJournalsHS4)!=SnapshotDataHS3.JournalCount() ||
      ArraySize(this.importedFactsHS4)!=SnapshotDataHS3.FactCount() || ArraySize(this.importedItemsHS4)!=SnapshotDataHS3.ItemCount() { return; }
    let legacy=SnapshotStateHS1.Get(this.GetGameInstance());
    if !IsDefined(legacy) || !legacy.ApplyGlobalHistoryHS4(this.importedLegacyHS4,this.importLegacyRevisionHS4,
      this.importTicketHS4,NameToString(this.importHS1TokenHS4)) { this.importFaultHS4=true;return; }
    this.journals=this.importedJournalsHS4;this.facts=this.importedFactsHS4;this.items=this.importedItemsHS4;
    this.schema=3;this.catalogue=SnapshotDataHS3.Fingerprint();this.revision=this.importRevisionHS4;
    this.committedTicket=this.importTicketHS4;this.route=this.importRouteHS4;this.committed=true;this.faulted=false;
    this.importedGlobalHS4=true;
    this.fileToken=this.importHS3TokenHS4;this.ResetCapture();this.ClearJSON();this.exported=true;this.fileLoadedHS4=true;
    this.detail="Global latest valid pre-ending snapshot loaded; historical observations ready.";
    ModLog(n"PTFR_HistorySnapshot",this.detail);this.ClearImportHS4();
  }
