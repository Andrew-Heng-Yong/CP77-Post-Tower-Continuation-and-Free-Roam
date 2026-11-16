  private let testHistoryRequest: ref<SnapshotTestHistoryRequest>;
  private let testHistoryCursor: Int32;
  private let testHistoryRevision: Int32;
  private let testHistoryResult: String;

  public func TestHistoryStatus() -> String {
    return this.testHistoryResult;
  }

  public func UsePreEndingForTest(revision: Int32, exportedRows: array<String>) -> Void {
    let request = new SnapshotTestHistoryRequest();
    request.epoch = this.epoch;
    request.revision = revision;
    request.exportedRows = exportedRows;
    this.QueueRequest(request);
  }

  private func OnSnapshotTestHistoryRequest(request: ref<SnapshotTestHistoryRequest>) -> Void {
    if request.epoch != this.epoch || !this.running { return; }
    if this.testHistoryRevision > 0 || IsDefined(this.testHistoryRequest) { return; }
    if !this.Ready() || !this.Tower() || NotEquals(this.origin, n"post_ending_fallback") {
      this.testHistoryResult = "Wait for a verified post-Tower fallback in the test save.";
      return;
    }
    if request.revision <= 0 || request.revision >= this.revision ||
      ArraySize(request.exportedRows) != SnapshotDataHS1.Count() || !this.Shape(this.previousRows) {
      this.testHistoryResult = "Test override refused: matching retained history is unavailable.";
      return;
    }
    this.testHistoryRequest = request;
    this.testHistoryCursor = 0;
    this.testHistoryResult = "Checking the export against this save's retained history.";
  }

  private func CheckTestHistory() -> Void {
    let request = this.testHistoryRequest;
    if !IsDefined(request) { return; }
    if request.epoch != this.epoch || !this.Tower() {
      this.testHistoryRequest = null;
      this.testHistoryResult = "Test override cancelled at the save boundary.";
      return;
    }
    let stop = Min(this.testHistoryCursor + 16, SnapshotDataHS1.Count());
    while this.testHistoryCursor < stop {
      let i = this.testHistoryCursor;
      if NotEquals(request.exportedRows[i], this.SerializeRowHS2(i, this.previousRows[i])) {
        this.testHistoryRequest = null;
        this.testHistoryResult = "Test override refused: retained history differs from the export.";
        ModLog(n"PTFR_HistorySnapshot", this.testHistoryResult);
        return;
      }
      this.testHistoryCursor += 1;
    }
    if this.testHistoryCursor == SnapshotDataHS1.Count() {
      this.testHistoryRevision = request.revision;
      this.testHistoryRequest = null;
      this.testHistoryResult = "Using verified pre-ending revision " + ToString(this.testHistoryRevision) + " for this test session.";
      ModLog(n"PTFR_HistorySnapshot", this.testHistoryResult);
    }
  }

  private func ClearTestHistory() -> Void {
    this.testHistoryRequest = null;
    this.testHistoryCursor = 0;
    this.testHistoryRevision = 0;
    this.testHistoryResult = "Test override is off.";
  }

  private func AdmissionRow(i: Int32) -> SnapshotRowHS1 {
    if this.testHistoryRevision > 0 { return this.previousRows[i]; }
    return this.rows[i];
  }

