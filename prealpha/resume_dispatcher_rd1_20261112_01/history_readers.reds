  // RD1 exposes stable primitive observations; never a temporary saved row.
  public func HistoryRootRD1(id: String) -> Int32 {
    let i=SnapshotDataHS1.Index(id);
    return this.HasAdmissionRow(i)?this.AdmissionState(i,0):-1;
  }
  public func HistoryJournalRD1(id: String,path: String) -> Int32 {
    let i=SnapshotDataHS1.Index(id);
    if !this.HasAdmissionRow(i) { return -1; }
    let paths=SnapshotDataHS1.Paths(i);let k=0;
    while k<ArraySize(paths) {
      if Equals(paths[k],path) { return this.AdmissionState(i,k); }
      k+=1;
    }
    return -1;
  }
  public func HistoryFactRD1(id: String,name: String) -> Int32 {
    let i=SnapshotDataHS1.Index(id);
    if !this.HasAdmissionRow(i) { return -2147483647; }
    let names=SnapshotDataHS1.Facts(i);let k=0;
    while k<ArraySize(names) {
      if Equals(names[k],name) { return this.AdmissionFact(i,k); }
      k+=1;
    }
    return -2147483647;
  }
  public func HistoryCounterRD1(id: String,path: String) -> Int32 {
    let i=SnapshotDataHS1.Index(id);
    if !this.HasAdmissionRow(i) { return -1; }
    let paths=SnapshotDataHS1.Paths(i);let k=0;
    while k<ArraySize(paths) {
      if Equals(paths[k],path) {
        if this.useRetainedHistory { return this.previousRows[i].counters[k]; }
        return this.rows[i].counters[k];
      }
      k+=1;
    }
    return -1;
  }
