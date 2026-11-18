module PTFR.MistyViktorAuto
import PTFR.LoadingCoverLC1.StartupCoverLC1
import PTFR.RestrictionsR1.CyberwarePolicy

// Arms the already-installed R7 world owner after genuine Tower completion.
// The rooftop lift uses the original device controllers and actions.
public class MistyViktorAuto extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let rooftopLiftActions: array<CName>;
  private let rooftopLiftRestrictionsCleared: Bool;

  private func OnAttach() -> Void {
    this.epoch += 1;
    this.running = true;
    this.ResetRooftopLift();
    let q = GameInstance.GetQuestsSystem(this.GetGameInstance());
    let players = GameInstance.GetPlayerSystem(this.GetGameInstance());
    this.SetRooftopSeatFact(q, n"PTFRMistySeat_Permit", 0);
    if IsDefined(q) && q.GetFact(n"PTFRWO1_CleanupPermit") != 0 {
      q.SetFact(n"PTFRWO1_CleanupPermit", 0);
    }
    // A qualified saved free-roam load may already be beside the street.
    if IsDefined(q) && IsDefined(players) {
      this.RefreshStreetCleanupPermit(q, players.GetLocalPlayerMainGameObject() as PlayerPuppet);
    }
    this.Schedule(this.epoch, 1.0);
  }
  private func OnRestored(saveVersion: Int32, gameVersion: Int32) -> Void {
    this.ResetRooftopLift();
    this.SetRooftopSeatFact(GameInstance.GetQuestsSystem(this.GetGameInstance()), n"PTFRMistySeat_Permit", 0);
  }
  private func ResetRooftopLift() -> Void {
    ArrayClear(this.rooftopLiftActions);
    this.rooftopLiftRestrictionsCleared = false;
  }
  private func OnDetach() -> Void {
    this.running = false;
    this.epoch += 1;
  }
  private func Schedule(epoch: Int32, seconds: Float) -> Void {
    let delay = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delay) { delay.DelayCallback(MistyViktorAutoTick.Create(this, epoch), seconds, false); }
  }
  private func Completed(q: ref<QuestsSystem>) -> Bool {
    return q.GetFact(n"PostTowerFreeRoamActive") == 1 &&
      q.GetFact(n"PTFRP0_DR13") == 1 && q.GetFact(n"q307_active") == 0 &&
      q.GetFact(n"q307_done") == 1 && q.GetFact(n"q307_finished") == 1 &&
      q.GetFact(n"q307_2079") == 1 && q.GetFact(n"q307_main_game_killed") == 1 &&
      q.GetFact(n"q307_ep1_killed") == 1 && q.GetFact(n"q305_johnny_scene_active") == 0 &&
      q.GetFact(n"q115_point_of_no_return") == 0 &&
      q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRWORLD_Suspended") == 0 &&
      q.GetFact(n"PTFRMV_Suspended") == 0 && q.GetFact(n"PTFRMV_QuestOwns") == 0 &&
      q.GetFact(n"PTFRMV_Registered") == 1 && q.GetFact(n"PTFRMV_Revision") == 7;
  }
  private func Safe(p: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(p) || p.IsInCombat() { return false; }
    let game = this.GetGameInstance();
    let scenes = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scenes) || !IsDefined(workspots) { return false; }
    if scenes.IsEntityInScene(p.GetEntityID()) || workspots.IsActorInWorkspot(p) { return false; }
    let mounting = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(p);
    if EntityID.IsDefined(mounting.parentId) { return false; }
    if GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked() { return false; }
    let locks: array<gameSaveLock>;
    if GameInstance.IsSavingLocked(game, locks) { return false; }
    let pos = p.GetWorldPosition();
    let dx = pos.X + 1542.0;
    let dy = pos.Y - 1210.0;
    return dx * dx + dy * dy > 6400.0;
  }
  // Keep the street owner separate from the clinic's 80-metre admission.
  // The native final state also restores the ordinary solid street variant.
  private func SafeStreet(p: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(p) || !p.IsAttached() || p.IsInCombat() { return false; }
    let game = this.GetGameInstance();
    let scenesSystem = GameInstance.GetSceneSystem(game);
    let workspots = GameInstance.GetWorkspotSystem(game);
    let mountingFacility = GameInstance.GetMountingFacility(game);
    let content = GameInstance.GetQuestsContentSystem(game);
    if !IsDefined(scenesSystem) || !IsDefined(workspots) ||
      !IsDefined(mountingFacility) || !IsDefined(content) { return false; }
    let scenes = scenesSystem.GetScriptInterface();
    if !IsDefined(scenes) { return false; }
    if scenes.IsEntityInScene(p.GetEntityID()) || workspots.IsActorInWorkspot(p) { return false; }
    let mounting = mountingFacility.GetMountingInfoSingleWithObjects(p);
    if EntityID.IsDefined(mounting.parentId) || content.IsTokensActivationBlocked() { return false; }
    let locks: array<gameSaveLock>;
    return !GameInstance.IsSavingLocked(game, locks);
  }
  // A fresh post-Tower load must release the final-scene street even nearby.
  private func RefreshStreetCleanupPermit(q: ref<QuestsSystem>, p: ref<PlayerPuppet>) -> Void {
    let permit = 0;
    if this.Completed(q) && this.SafeStreet(p) &&
      q.GetFact(n"PTFRMV_Applied") == 1 &&
      q.GetFact(n"PTFRWO1_CleanupRegistered") == 1 &&
      q.GetFact(n"PTFRWO1_CleanupDone") == 0 {
      permit = 1;
    }
    if q.GetFact(n"PTFRWO1_CleanupPermit") != permit {
      q.SetFact(n"PTFRWO1_CleanupPermit", permit);
    }
  }

  private func RooftopLiftNode(part: String) -> EntityID {
    let path = "$/03_night_city/c_watson/little_china/loc_q115_mistyc_mistys_ripperdoc_roof_prefabDR5IG6A/loc_q115_mystic_mistys_ripperdoc_roof_gameplay_prefab75UZAWI/loc_q115_mystic_mistys_ripperdoc_roof_devices_prefabNCP6VPY/lift_2_floors_prefabXK7C7ZI/" + part;
    return Cast<EntityID>(ResolveNodeRef(CreateNodeRef(path), Cast<GlobalNodeRef>(GlobalNodeID.GetRoot())));
  }

  private func RooftopLiftController(streetPanel: ref<ElevatorFloorTerminalControllerPS>, streetID: EntityID,
    roofID: EntityID) -> ref<LiftControllerPS> {
    let parents: array<ref<DeviceComponentPS>>;
    streetPanel.GetParents(parents);
    for parent in parents {
      let lift = parent as LiftControllerPS;
      if IsDefined(lift) {
        let floors = lift.GetFloors();
        if ArraySize(floors) == 2 && lift.GetFloorID(0) == streetID && lift.GetFloorID(1) == roofID {
          return lift;
        }
      }
    }
    return null;
  }

  private func RequestRooftopLiftAction(device: ref<ScriptableDeviceComponentPS>, actionName: CName, part: CName) -> Void {
    if ArrayContains(this.rooftopLiftActions, part) { return; }
    let action = device.GetQuestActionByName(actionName) as ScriptableDeviceAction;
    if !IsDefined(action) { return; }
    let showFloor = action as QuestShowFloor;
    if IsDefined(showFloor) { showFloor.SetProperties(1); }
    device.ExecutePSAction(action);
    ArrayPush(this.rooftopLiftActions, part);
    ModLog(n"PTFR_MistyLift", NameToString(part) + " requested " + NameToString(actionName));
  }

  private func RestoreRooftopLift(game: GameInstance) -> Void {
    let streetID = this.RooftopLiftNode("lift_terminal_1");
    let roofID = this.RooftopLiftNode("lift_terminal_2");
    if !EntityID.IsDefined(streetID) || !EntityID.IsDefined(roofID) { return; }
    let terminal = GameInstance.FindEntityByID(game, streetID) as ElevatorFloorTerminal;
    if !IsDefined(terminal) { return; }
    let streetPanel = terminal.GetDevicePS();
    if !IsDefined(streetPanel) { return; }
    let lift = this.RooftopLiftController(streetPanel, streetID, roofID);
    if !IsDefined(lift) || lift.IsMoving() { return; }

    // Restore the device states cached before q307 disabled the lift and street panel.
    let liftDisabled = lift.IsDisabled();
    let streetPanelDisabled = streetPanel.IsDisabled();
    if liftDisabled { this.RequestRooftopLiftAction(lift, n"ForceEnabled", n"lift"); }
    if streetPanelDisabled { this.RequestRooftopLiftAction(streetPanel, n"ForceEnabled", n"street-panel"); }
    if liftDisabled || streetPanelDisabled { return; }

    let floors = lift.GetFloors();
    let roofHidden = floors[1].m_isHidden;
    if roofHidden { this.RequestRooftopLiftAction(lift, n"ShowFloor", n"roof-stop"); }

    // Unsealing leaves the landing door under the lift's normal interlock.
    let landing = GameInstance.FindEntityByID(game, this.RooftopLiftNode("lift_door_1")) as Door;
    if !IsDefined(landing) { return; }
    let door = landing.GetDevicePS();
    if !IsDefined(door) { return; }
    if door.IsSealed() {
      this.RequestRooftopLiftAction(door, n"ForceUnseal", n"street-landing");
      return;
    }
    if !roofHidden {
      this.rooftopLiftRestrictionsCleared = true;
      ModLog(n"PTFR_MistyLift", "Lift and street panel enabled, roof stop visible, street landing unsealed");
    }
  }

  private func SetRooftopSeatFact(q: ref<QuestsSystem>, fact: CName, value: Int32) -> Void {
    if IsDefined(q) && q.GetFact(fact) != value { q.SetFact(fact, value); }
  }

  private func RefreshRooftopSeat(q: ref<QuestsSystem>, p: ref<PlayerPuppet>) -> Void {
    if q.GetFact(n"PTFRMistySeat_Registered") != 1 { return; }
    let game = this.GetGameInstance();
    let eligible = IsDefined(p) && p.IsAttached() && !p.IsDead() && !p.IsInCombat() && this.Completed(q) &&
      StartupCoverLC1.GameplayReleased(game) &&
      GameInstance.GetPlayerSystem(game).GetLocalPlayerControlledGameObject() == p;
    let distanceSquared = 100.0;
    if eligible {
      let pos = p.GetWorldPosition();
      let dx = pos.X + 1541.07068;
      let dy = pos.Y - 1201.8988;
      let dz = pos.Z - 57.0021973;
      distanceSquared = dx * dx + dy * dy + dz * dz;
    }
    // Only the native scene can end a seated interaction.
    this.SetRooftopSeatFact(q, n"PTFRMistySeat_Depart", distanceSquared > 25.0 ? 1 : 0);
    let permit = 0;
    if eligible && distanceSquared <= 6.25 && q.GetFact(n"PTFRMistySeat_Active") == 0 &&
      q.GetFact(n"PTFRMistySeat_Interrupted") == 0 && CyberwarePolicy.Safe(p) &&
      IsDefined(GameInstance.FindEntityByID(game, this.RooftopLiftNode("lift_terminal_2"))) {
      permit = 1;
    }
    this.SetRooftopSeatFact(q, n"PTFRMistySeat_Permit", permit);
  }

  public func Poll(expectedEpoch: Int32) -> Void {
    if !this.running || expectedEpoch != this.epoch { return; }
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    let p = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    if IsDefined(q) && this.Safe(p) {
      let desired = this.Completed(q) ? 1 : 0;
      if q.GetFact(n"PTFRMV_Enabled") != desired { q.SetFact(n"PTFRMV_Enabled", desired); }
    }
    if IsDefined(q) {
      this.RefreshStreetCleanupPermit(q, p);
      this.RefreshRooftopSeat(q, p);
    }
    if !this.rooftopLiftRestrictionsCleared && IsDefined(q) && this.Completed(q) &&
      StartupCoverLC1.GameplayReleased(game) && this.SafeStreet(p) && !p.IsDead() {
      this.RestoreRooftopLift(game);
    }
    this.Schedule(expectedEpoch, 2.0);
  }
}

public class MistyViktorAutoTick extends DelayCallback {
  private let driver: wref<MistyViktorAuto>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<MistyViktorAuto>, epoch: Int32) -> ref<MistyViktorAutoTick> {
    let tick = new MistyViktorAutoTick();
    tick.driver = driver; tick.epoch = epoch;
    return tick;
  }
}
