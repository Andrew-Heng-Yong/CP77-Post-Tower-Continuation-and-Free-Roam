module PTFR.AfterlifeFacesR5

// R11 retirement: keep the existing persistent type and field identities so
// saves containing R5 preferences still have their schema. The feature is gone:
// no NPC hooks, actor references, admission, catalog construction, scheduling,
// appearance requests, reservation policy, or writes to the saved preferences.
public class FaceMemoryR5 extends IScriptable {
  public persistent let id: EntityID;
  public persistent let role: Int32;
  public persistent let appearance: CName;
}

public class AfterlifeFacesR5 extends ScriptableSystem {
  private persistent let revision: Int32;
  private persistent let memory: array<ref<FaceMemoryR5>>;

  public func GetStatus() -> String {
    return "R5 live face changes removed R11; inert saved-schema compatibility only";
  }
}
