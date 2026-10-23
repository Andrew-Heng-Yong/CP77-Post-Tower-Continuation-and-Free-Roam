// The consolidated installer removes obsolete PTFR entry scripts and CET hooks.
// A compiled package marker replaces the old script -> CET Probe dependency.
// Runtime services still independently require their own archive Ready/Revision.
public abstract class PreAlphaPackagePA1 {
  public static func Revision() -> Int32 { return 1; }
}
public abstract class GigBatchLockU9 {
  public static func Ready() -> Bool { return PreAlphaPackagePA1.Revision()==1; }
  public static func Probe() -> Bool { return GigBatchLockU9.Ready(); }
}
