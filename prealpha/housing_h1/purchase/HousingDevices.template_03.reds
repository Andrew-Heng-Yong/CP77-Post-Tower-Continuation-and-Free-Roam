module PTFR.Housing

public abstract class HousingDevices {
  public static func Property(source: EntityID, kind: String) -> String {
    if !EntityID.IsDefined(source) { return ""; }
@@DEVICE_MATCHES@@
    return "";
  }

  public static func Matches(source: EntityID, path: String) -> Bool {
    let expected = Cast<EntityID>(ResolveNodeRef(CreateNodeRef(path), Cast<GlobalNodeRef>(GlobalNodeID.GetRoot())));
    return EntityID.IsDefined(expected) && source == expected;
  }

  public static func RestrictedRelationship(source: EntityID, kind: String) -> Bool {
    if !EntityID.IsDefined(source) { return false; }
@@RELATIONSHIP_DEVICE_MATCHES@@
    return false;
  }

  public static func Denied(game: GameInstance, source: EntityID, kind: String) -> Bool {
    let state = HousingState.Get(game);
    if !IsDefined(state) || !state.Enforcing() { return false; }
    // Relationship homes are not ordinary apartments and have no purchase receipt.
    if HousingDevices.RestrictedRelationship(source, kind) { return true; }
    let id = HousingDevices.Property(source, kind);
    if Equals(id, "") { return false; }
    return !state.Entitled(id);
  }

  public static func NativePayDenied(game: GameInstance, source: EntityID) -> Bool {
    if Equals(HousingDevices.Property(source, "door"), "") { return false; }
    let state = HousingState.Get(game);
    return IsDefined(state) && state.Enforcing();
  }
}

// Only exact home devices are intercepted; shared stash contents are untouched.
@wrapMethod(StashControllerPS)
public func GetActions(out actions: array<ref<DeviceAction>>, context: GetActionsContext) -> Bool {
  if HousingDevices.Denied(this.GetGameInstance(), PersistentID.ExtractEntityID(this.GetID()), "stash") { ArrayClear(actions); return false; }
  return wrappedMethod(actions, context);
}

@wrapMethod(StashControllerPS)
private final func OnOpenStash(evt: ref<OpenStash>) -> EntityNotificationType {
  if HousingDevices.Denied(this.GetGameInstance(), PersistentID.ExtractEntityID(this.GetID()), "stash") { return EntityNotificationType.DoNotNotifyEntity; }
  return wrappedMethod(evt);
}

@wrapMethod(Stash)
protected cb func OnOpenStash(evt: ref<OpenStash>) -> Bool {
  if HousingDevices.Denied(this.GetGame(), this.GetEntityID(), "stash") { return false; }
  return wrappedMethod(evt);
}

@wrapMethod(WardrobeControllerPS)
public func GetActions(out actions: array<ref<DeviceAction>>, context: GetActionsContext) -> Bool {
  if HousingDevices.Denied(this.GetGameInstance(), PersistentID.ExtractEntityID(this.GetID()), "wardrobe") { ArrayClear(actions); return false; }
  return wrappedMethod(actions, context);
}

@wrapMethod(WardrobeControllerPS)
protected final func OnOpenWardrobeUI(evt: ref<OpenWardrobeUI>) -> EntityNotificationType {
  if HousingDevices.Denied(this.GetGameInstance(), PersistentID.ExtractEntityID(this.GetID()), "wardrobe") { return EntityNotificationType.DoNotNotifyEntity; }
  return wrappedMethod(evt);
}

// H10 has no native sale. Its exact existing front-door device hosts one action.
public class HousingPurchaseAction extends ActionBool {
  public final func SetProperties() -> Void {
    this.actionName = n"HousingPurchaseAction";
    this.prop = DeviceActionPropertyFunctions.SetUpProperty_Bool(this.actionName, true, n"Purchase apartment", n"Purchase apartment");
    this.CreateInteraction();
    this.interactionChoice.caption = "Purchase apartment â€” â‚¬$25000";
    this.SetCanSkipPayCost(true);
    this.SetDisableSpread(true);
    this.SetShouldActivateDevice(false);
  }
}

@wrapMethod(DoorControllerPS)
public func GetActions(out actions: array<ref<DeviceAction>>, context: GetActionsContext) -> Bool {
  let game = this.GetGameInstance();
  let source = PersistentID.ExtractEntityID(this.GetID());
  let result = wrappedMethod(actions, context);
  // Keep opening/closing and egress intact, including a save loaded indoors.
  if HousingDevices.NativePayDenied(game, source) {
    let i = ArraySize(actions) - 1;
    while i >= 0 {
      if IsDefined(actions[i] as Pay) { ArrayErase(actions, i); }
      i -= 1;
    }
  }
  if !Equals(HousingDevices.Property(source, "door"), "h10") || NotEquals(context.requestType, gamedeviceRequestType.Direct) { return result; }
  let player = context.processInitiatorObject as PlayerPuppet;
  let state = HousingState.Get(game);
  if !IsDefined(player) || !IsDefined(state) || !state.CanPurchase("h10", player) || !HousingPurchaseLocation.Validate(game, "h10", source) { return result; }
  let action = new HousingPurchaseAction();
  action.clearanceLevel = 2;
  action.SetUp(this);
  action.SetExecutor(player);
  action.SetProperties();
  ArrayPush(actions, action);
  return true;
}

@addMethod(DoorControllerPS)
public final func OnHousingPurchaseAction(evt: ref<HousingPurchaseAction>) -> EntityNotificationType {
  let game = this.GetGameInstance();
  let source = PersistentID.ExtractEntityID(this.GetID());
  let ui = HousingPurchaseUI.Get(game);
  if IsDefined(ui) && Equals(HousingDevices.Property(source, "door"), "h10") { ui.Show("h10", source); }
  return EntityNotificationType.DoNotNotifyEntity;
}

// The device dispatch guard runs before native ProcessRPGAction / PayCost.
@wrapMethod(Device)
protected const final func ExecuteAction(action: ref<DeviceAction>, opt executor: wref<GameObject>) -> Bool {
  if IsDefined(action as Pay) && HousingDevices.NativePayDenied(this.GetGame(), this.GetEntityID()) { return false; }
  return wrappedMethod(action, executor);
}

@wrapMethod(DoorControllerPS)
public final func OnPay(evt: ref<Pay>) -> EntityNotificationType {
  if HousingDevices.NativePayDenied(this.GetGameInstance(), PersistentID.ExtractEntityID(this.GetID())) { return EntityNotificationType.DoNotNotifyEntity; }
  return wrappedMethod(evt);
}
