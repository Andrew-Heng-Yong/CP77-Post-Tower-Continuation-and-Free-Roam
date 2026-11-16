// The test request carries the export's exact row strings. Admission switches
// only after every row matches history already retained by this save.
public class SnapshotTestHistoryRequest extends ScriptableSystemRequest {
  public let epoch: Int32;
  public let revision: Int32;
  public let exportedRows: array<String>;
}

