  public func ApplyGlobalHistoryHS4(rows: array<SnapshotRowHS1>,revision: Int32,ticket: Int32,token: String) -> Bool {
    if !this.running || revision<=0 || ticket<=0 || Equals(token,"") || !this.Shape(rows) ||
      (this.schema!=0 && (this.schema!=1 || NotEquals(this.catalogue,SnapshotDataHS1.Fingerprint()))) { return false; }
    // The user explicitly selected global-latest historical evidence. These
    // assignments never write native quest facts, progress, rewards or owners.
    this.rows=rows;this.schema=1;this.catalogue=SnapshotDataHS1.Fingerprint();this.revision=revision;
    this.nativeTicketHS3=ticket;this.origin=n"pre_ending";this.ready=true;this.frozen=true;this.faulted=false;
    this.ResetRetainedHistory();this.ResetRead();this.towerCutoffPending=false;
    this.jsonReadyHS2=false;this.jsonCursorHS2=0;ArrayClear(this.jsonRowsHS2);this.jsonHeaderHS2="";
    this.fileToken=StringToName(token);this.exported=true;
    this.detail="Global latest valid pre-ending snapshot loaded.";return true;
  }
  private func HistoryFileReadyHS4() -> Bool {
    let history=CaptureArchiveHS3.Get(this.GetGameInstance());
    return !IsDefined(history) || !history.RequiresLatestHS4() || history.GlobalFileReadyHS4();
  }
