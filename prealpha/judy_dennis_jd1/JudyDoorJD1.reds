module PTFR.Housing

import PTFR.LoadingCoverLC1.*

public abstract class JudyDoorJD1 {
  public static func Path() -> String {
    return "$/03_night_city/c_watson/kabuki/loc_q026_judys_apartment_prefabAH52EHQ/loc_sq026_judys_apartment_gameplay_prefab63MT4ZA/#loc_sq026_judys_apartment_devices/{sq026_dvc_judys_door_apartment}_prefabBWADAAA/#sq026_dvc_judys_door_apartment";
  }
  public static func Source() -> EntityID {
    return Cast<EntityID>(ResolveNodeRef(CreateNodeRef(JudyDoorJD1.Path()), Cast<GlobalNodeRef>(GlobalNodeID.GetRoot())));
  }
  public static func Active(game: GameInstance) -> Bool {
    let state = HousingState.Get(game);
    return IsDefined(state) && state.Enforcing() && state.HousingReadyForReveal() && StartupCoverLC1.GameplayReleased(game);
  }
  public static func InteriorDistance(game: GameInstance, door: ref<GameObject>, out distance: Float) -> Bool {
    let player = GetPlayer(game) as PlayerPuppet;
    if !IsDefined(door) || !IsDefined(player) { return false; }
    let marker = ResolveNodeRef(CreateNodeRef("$/03_night_city/c_watson/kabuki/loc_q026_judys_apartment_prefabAH52EHQ/#loc_sq026_judys_apartment_questdesign/#sq026_pr_judys/#sq026_spwn_player_judys_apartment"), Cast<GlobalNodeRef>(GlobalNodeID.GetRoot()));
    let transform: Transform;
    // Native interior spawn marker, retained even if its quest prefab is inactive.
    let inside = new Vector4(-902.682373, 1855.74219, 42.3472099, 1.0);
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
    if !HousingDevices.Matches(source, JudyDoorJD1.Path()) || !JudyDoorJD1.Active(game) { return false; }
    let door = GameInstance.FindEntityByID(game, source) as GameObject;
    let distance: Float;
    return JudyDoorJD1.InteriorDistance(game, door, distance) && distance < 0.35;
  }
  public static func Tick(game: GameInstance) -> Void {
    if !JudyDoorJD1.Active(game) { return; }
    let object = GameInstance.FindEntityByID(game, JudyDoorJD1.Source()) as GameObject;
    let door = object as Door;
    let judyDoor = object as JudysDoor;
    let distance: Float;
    if (!IsDefined(door) && !IsDefined(judyDoor)) || !JudyDoorJD1.InteriorDistance(game, object, distance) { return; }
    let ps: ref<DoorControllerPS>;
    if IsDefined(door) { ps = door.GetDevicePS(); } else { ps = judyDoor.GetDevicePS(); }
    if !IsDefined(ps) { return; }
    let changed = false;
    if distance >= 0.35 { changed = ps.JudyLockJD1(false); }
    if distance <= -0.75 {
      changed = ps.JudyLockJD1(true);
      if ps.IsOpen() { ps.SetIsOpened(false); changed = true; }
    }
    if changed {
      if IsDefined(door) { door.JudyRefreshJD1(); } else { judyDoor.JudyRefreshJD1(); }
      ModLog(n"PTFR_JudyDoorJD1", "Private door reconciled; insideDistance="+ToString(distance)+" locked="+ToString(ps.IsLocked()));
    }
  }
}

@addField(DoorControllerPS)
private persistent let judyJD1OwnLock: Bool;

@addMethod(DoorControllerPS)
public final func JudyLockJD1(lock: Bool) -> Bool {
  if lock {
    if !this.IsLocked() { this.SetIsLocked(true); this.judyJD1OwnLock = true; return true; }
  } else if this.judyJD1OwnLock {
    this.SetIsLocked(false); this.judyJD1OwnLock = false; return true;
  }
  return false;
}

@addMethod(Door)
public final func JudyRefreshJD1() -> Void { this.UpdateDeviceState(); }

@addMethod(JudysDoor)
public final func JudyRefreshJD1() -> Void { this.UpdateDeviceState(); }

@wrapMethod(DoorControllerPS)
public func GetActions(out actions: array<ref<DeviceAction>>, context: GetActionsContext) -> Bool {
  let result = wrappedMethod(actions, context);
  if JudyDoorJD1.DenyEntry(this.GetGameInstance(), PersistentID.ExtractEntityID(this.GetID())) { ArrayClear(actions); return false; }
  return result;
}

@wrapMethod(DoorControllerPS)
public final func SetIsOpened(isOpened: Bool) -> Void {
  if isOpened && JudyDoorJD1.DenyEntry(this.GetGameInstance(), PersistentID.ExtractEntityID(this.GetID())) { isOpened = false; }
  wrappedMethod(isOpened);
}

@wrapMethod(DoorControllerPS)
public final func SetIsLocked(isLocked: Bool) -> Void {
  if !isLocked && JudyDoorJD1.DenyEntry(this.GetGameInstance(), PersistentID.ExtractEntityID(this.GetID())) {
    this.judyJD1OwnLock = true; isLocked = true;
  }
  wrappedMethod(isLocked);
}

@wrapMethod(Door)
private final func MoveDoor(shouldBeOpened: Bool, immediate: Bool, opt movingSpeedMultiplier: Float) -> Bool {
  if shouldBeOpened && JudyDoorJD1.DenyEntry(this.GetGame(), this.GetEntityID()) {
    // Synchronize a saved open state before native MoveDoor calls UpdateDeviceState.
    // Otherwise its visual/state mismatch can recursively request another open.
    this.GetDevicePS().SetIsOpened(false); shouldBeOpened = false;
  }
  return wrappedMethod(shouldBeOpened, immediate, movingSpeedMultiplier);
}

@wrapMethod(JudysDoor)
private final func MoveDoor(shouldBeOpened: Bool, immediate: Bool, force: Bool, opt movingSpeedMultiplier: Float) -> Bool {
  if shouldBeOpened && JudyDoorJD1.DenyEntry(this.GetGame(), this.GetEntityID()) {
    this.GetDevicePS().SetIsOpened(false); shouldBeOpened = false;
  }
  return wrappedMethod(shouldBeOpened, immediate, force, movingSpeedMultiplier);
}
