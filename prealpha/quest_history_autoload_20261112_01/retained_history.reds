  private let retainedHistoryJSON: array<String>;
  private let retainedHistoryCandidate: Bool;
  private let useRetainedHistory: Bool;

  private func ResetRetainedHistory() -> Void {
    ArrayClear(this.retainedHistoryJSON);
    this.retainedHistoryCandidate = false;
    this.useRetainedHistory = false;
  }

  public func CanCompareRetainedHistory() -> Bool {
    return this.CanExport() && this.retainedHistoryCandidate &&
      ArraySize(this.retainedHistoryJSON) == SnapshotDataHS1.Count();
  }

  public func RetainedHistoryRowJSON(i: Int32) -> String {
    if !this.CanCompareRetainedHistory() || i < 0 || i >= ArraySize(this.retainedHistoryJSON) { return ""; }
    return this.retainedHistoryJSON[i];
  }

  public func AckFileWithRetainedHistory(epoch: Int32, revision: Int32, token: String, retainedRevision: Int32) -> Bool {
    if !this.CanCompareRetainedHistory() || retainedRevision <= 0 || retainedRevision >= revision { return false; }
    return this.CommitFileAck(epoch, revision, token, true);
  }

  private func HasAdmissionRow(i: Int32) -> Bool {
    if !this.Ready() || i < 0 || i >= ArraySize(this.rows) { return false; }
    if this.useRetainedHistory {
      return this.previousRows[i].stable && ArraySize(this.previousRows[i].states) > 0;
    }
    return this.rows[i].stable && ArraySize(this.rows[i].states) > 0;
  }

  // Index the backing rows directly. A field of a function-returned struct
  // is unsafe in the VM when an array opcode takes its address.
  private func AdmissionState(i: Int32, field: Int32) -> Int32 {
    if this.useRetainedHistory { return this.previousRows[i].states[field]; }
    return this.rows[i].states[field];
  }

  private func AdmissionFact(i: Int32, field: Int32) -> Int32 {
    if this.useRetainedHistory { return this.previousRows[i].facts[field]; }
    return this.rows[i].facts[field];
  }

