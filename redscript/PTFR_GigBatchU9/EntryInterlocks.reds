// CET hooks the harmless Probe only. No fields, facts or saved-state schema.
// Calling Ready from U9 executes script -> CET; absent/failed CET is false.
// This proves Probe delivery, not all eleven legacy mutator callbacks.
public abstract class GigBatchLockU9 {
  public static func Ready() -> Bool { return GigBatchLockU9.Probe(); }
  public static func Probe() -> Bool { return false; }
}
