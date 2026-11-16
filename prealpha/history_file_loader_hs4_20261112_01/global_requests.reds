public class FileBeginRequestHS4 extends ScriptableSystemRequest {
  public let epoch: Int32; public let lease: String; public let transaction: String;
  public let ticket: Int32; public let route: Int32;
  public let revision: Int32; public let legacyRevision: Int32;
  public let token1: String; public let token3: String;
}
public class FilePacketRequestHS4 extends ScriptableSystemRequest {
  public let epoch: Int32; public let lease: String; public let transaction: String;
  public let channel: Int32; public let start: Int32; public let count: Int32;
  public let data: array<Int32>;
}
public class FileFinishRequestHS4 extends ScriptableSystemRequest {
  public let epoch: Int32; public let lease: String; public let transaction: String;
}
