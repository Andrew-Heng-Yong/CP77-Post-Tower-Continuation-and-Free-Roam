module PTFR.Housing

import PTFR.LoadingCoverLC1.*

// H10's existing private entrance only. No public building or lift door changes.
public abstract class HousingDoorH2 {
  public static func Door(game: GameInstance) -> ref<Door> {
    return GameInstance.FindEntityByID(game, HousingPurchaseLocation.Source("h10")) as Door;
  }

  public static func Unpaid(game: GameInstance) -> Bool {
    let state = HousingState.Get(game);
    return IsDefined(state) && state.Enforcing() && state.HousingReadyForReveal() && !state.Entitled("h10");
  }

  // Determine the interior from the native bed marker, never a guessed door side.
  // Query live transforms: no dependence on the obsolete cooked-buffer parser.
  public static func InteriorDistance(game: GameInstance, door: ref<Door>, out distance: Float) -> Bool {
    let player = GetPlayer(game) as PlayerPuppet;
    if !IsDefined(door) || !IsDefined(player) { return false; }
    let marker = ResolveNodeRef(CreateNodeRef("$/03_night_city/c_watson/little_china/loc_megabuilding_a_prefab4KCU2IQ/loc_megabuilding_a_questdesign_prefabT5LKYXQ/#mq000_pr_apartment/{mq000_01_apartment}_prefabZISCAPY/#mq000_01_ch_sleep"), Cast<GlobalNodeRef>(GlobalNodeID.GetRoot()));
    let transform: Transform;
    // The bed marker's prefab may be inactive while unpaid. This fallback is
    // its verified current 2.5 world placement, not a service/prefab activation.
    let inside = new Vector4(-1377.66956, 1275.32336, 123.554993, 1.0);
    if GameInstance.GetNodeTransform(game, marker, transform) { inside = Transform.GetPosition(transform); }
    let origin = door.GetWorldPosition();
    let forward = door.GetWorldForward();
    let anchor = (inside.X-origin.X)*forward.X + (inside.Y-origin.Y)*forward.Y;
    if AbsF(anchor) < 0.50 || Vector4.Distance(inside, origin) > 25.0 { return false; }
    let position = player.GetWorldPosition();
    distance = (position.X-origin.X)*forward.X + (position.Y-origin.Y)*forward.Y;
    if anchor < 0.0 { distance = -distance; }
    return true;
  }

  public static func DenyEntry(game: GameInstance, source: EntityID) -> Bool {
    if !HousingDevices.Matches(source, HousingPurchaseLocation.Path("h10")) || !HousingDoorH2.Unpaid(game) { return false; }
    let door = GameInstance.FindEntityByID(game, source) as Door;
    let distance: Float;
    // Unknown geometry is deferred, so a save loaded inside is never trapped.
    return HousingDoorH2.InteriorDistance(game, door, distance) && distance < 0.35;
  }

  public static func Tick(game: GameInstance) -> Void {
    if !StartupCoverLC1.GameplayReleased(game) { return; }
    let door = HousingDoorH2.Door(game);
    if IsDefined(door) { door.HousingReconcileH2(); }
  }
}

@addField(DoorControllerPS)
private persistent let housingH2OwnLock: Bool;

@addField(Door)
private let housingH2Reported: Bool;

@addMethod(DoorControllerPS)
public final func HousingLockH2(lock: Bool) -> Bool {
  if lock {
    if !this.IsLocked() { this.SetIsLocked(true); this.housingH2OwnLock = true; return true; }
  } else if this.housingH2OwnLock {
    this.SetIsLocked(false); this.housingH2OwnLock = false; return true;
  }
  return false;
}

@addMethod(Door)
public final func HousingReconcileH2() -> Void {
  let game = this.GetGame();
  if !HousingDevices.Matches(this.GetEntityID(), HousingPurchaseLocation.Path("h10")) { return; }
  let state = HousingState.Get(game);
  if !IsDefined(state) || !state.Enforcing() { return; }
  let ps = this.GetDevicePS();
  if state.Entitled("h10") {
    if ps.HousingLockH2(false) { this.UpdateDeviceState(); }
    return;
  }
  let distance: Float;
  if !HousingDoorH2.InteriorDistance(game, this, distance) { return; }
  if !this.housingH2Reported {
    this.housingH2Reported = true;
    ModLog(n"PTFR_HousingH2", "H10 private door resolved; interior distance="+ToString(distance)+"; unpaid entry guarded.");
  }
  if distance >= 0.35 {
    // A retained save may load indoors. It grants exit, not home entitlement.
    if ps.HousingLockH2(false) { this.UpdateDeviceState(); }
  } else if distance <= -0.75 {
    // Leave a threshold margin so the door cannot close through the player.
    let changed = ps.HousingLockH2(true);
    if ps.IsOpen() { ps.SetIsOpened(false); changed = true; }
    if changed { this.UpdateDeviceState(); }
  }
}

// Every native open route ultimately reaches these setters/visual movement:
// automatic proximity, direct action, authorization, quickhack and force-open.
@wrapMethod(DoorControllerPS)
public final func SetIsOpened(isOpened: Bool) -> Void {
  if isOpened && HousingDoorH2.DenyEntry(this.GetGameInstance(), PersistentID.ExtractEntityID(this.GetID())) { isOpened = false; }
  wrappedMethod(isOpened);
}

@wrapMethod(DoorControllerPS)
public final func SetIsLocked(isLocked: Bool) -> Void {
  if !isLocked && HousingDoorH2.DenyEntry(this.GetGameInstance(), PersistentID.ExtractEntityID(this.GetID())) {
    // We are suppressing a native unlock: retain ownership of that restriction
    // so payment/inside egress can release it even before the first polling tick.
    this.housingH2OwnLock = true;
    isLocked = true;
  }
  wrappedMethod(isLocked);
}

@wrapMethod(Door)
private final func MoveDoor(shouldBeOpened: Bool, immediate: Bool, opt movingSpeedMultiplier: Float) -> Bool {
  if shouldBeOpened && HousingDoorH2.DenyEntry(this.GetGame(), this.GetEntityID()) { shouldBeOpened = false; }
  return wrappedMethod(shouldBeOpened, immediate, movingSpeedMultiplier);
}
