module PTFR.MistyViktorAuto
import PTFR.LoadingCoverLC1.StartupCoverLC1
import PTFR.RestrictionsR1.CyberwarePolicy

// The manual camera volume and two cinematic weather volumes overlap the roof.
// Naming their setups keeps the original pickup active until the completed handoff.
public class MistyRoofExposure extends ScriptableService {
  private let boundSector: wref<worldStreamingSector>;
  private let bindingGeneration: Uint32;
  private let flightSector: wref<worldStreamingSector>;
  private let flightGeneration: Uint32;

  public static func Address() -> NodeRef {
    return CreateNodeRef("$/03_night_city/#ptfr_misty_q307_rooftop_exposure");
  }

  public func CurrentBinding() -> Uint32 {
    return IsDefined(this.boundSector) ? this.bindingGeneration : 0u;
  }

  public static func TrailerAddress() -> NodeRef {
    return CreateNodeRef("$/03_night_city/#ptfr_misty_q307_trailer_environment");
  }

  public static func FlightAddress() -> NodeRef {
    return CreateNodeRef("$/03_night_city/#ptfr_misty_q307_flight_environment");
  }

  public func FlightBinding() -> Uint32 {
    return IsDefined(this.flightSector) ? this.flightGeneration : 0u;
  }

  private cb func OnLoad() {
    GameInstance.GetCallbackSystem().RegisterCallback(n"Resource/PostLoad", this, n"BindRoof")
      .AddTarget(ResourceTarget.Path(r"base\\worlds\\03_night_city\\_compiled\\default\\exterior_-7_4_0_2.streamingsector"));
    GameInstance.GetCallbackSystem().RegisterCallback(n"Resource/PostLoad", this, n"BindFlight")
      .AddTarget(ResourceTarget.Path(r"base\\worlds\\03_night_city\\_compiled\\default\\exterior_-1_0_0_6.streamingsector"));
  }

  private func EnvironmentSetup(sector: ref<worldStreamingSector>, instance: Int32, node: Int32, priority: Int32,
    blend: Float, x: Float, y: Float, z: Float) -> ref<WorldNodeSetupWrapper> {
    let setup = sector.GetNodeSetup(instance);
    if !IsDefined(setup) || Cast<Int32>(setup.GetNodeIndex()) != node { return null; }
    let area = sector.GetNode(node) as worldTriggerAreaNode;
    if !IsDefined(area) || ArraySize(area.notifiers) != 1 { return null; }
    let env = area.notifiers[0] as worldEnvAreaNotifier;
    if !IsDefined(env) || Cast<Int32>(env.priority) != priority || env.blendTimeIn != blend ||
      env.blendTimeOut != blend { return null; }
    let pos = setup.GetPosition();
    if AbsF(pos.X - x) > 0.01 || AbsF(pos.Y - y) > 0.01 || AbsF(pos.Z - z) > 0.01 { return null; }
    return setup;
  }

  private func BindAddress(setup: ref<WorldNodeSetupWrapper>, address: NodeRef) -> Bool {
    if !IsDefined(setup) { return false; }
    // The setup holds a global ID. Use the same root resolution as a world-state request.
    let id: GlobalNodeID;
    id.hash = ResolveNodeRef(address, Cast<GlobalNodeRef>(GlobalNodeID.GetRoot())).hash;
    if !GlobalNodeID.IsDefined(id) { return false; }
    let existing = setup.GetGlobalNodeID();
    if GlobalNodeID.IsDefined(existing) { return existing.hash == id.hash; }
    setup.SetGlobalNodeID(id);
    return setup.GetGlobalNodeID().hash == id.hash;
  }

  private cb func BindRoof(event: ref<ResourceEvent>) {
    let sector = event.GetResource() as worldStreamingSector;
    if !IsDefined(sector) || sector.GetNodeSetupCount() != 2992 || sector.GetNodeCount() != 214 { return; }
    let setup = this.EnvironmentSetup(sector, 2940, 207, 6, 5.0, -1547.29395, 1204.39954, 51.57344);
    if !this.BindAddress(setup, MistyRoofExposure.Address()) { return; }
    this.boundSector = sector;
    this.bindingGeneration += 1u;
  }

  private cb func BindFlight(event: ref<ResourceEvent>) {
    let sector = event.GetResource() as worldStreamingSector;
    if !IsDefined(sector) || sector.GetNodeSetupCount() != 427 || sector.GetNodeCount() != 204 { return; }
    let trailer = this.EnvironmentSetup(sector, 413, 190, 6, 3.0, -1547.30005, 1204.39990, 5.500002);
    let flight = this.EnvironmentSetup(sector, 414, 191, 5, 3.0, -1547.30005, 1204.39990, 5.500002);
    if !this.BindAddress(trailer, MistyRoofExposure.TrailerAddress()) ||
      !this.BindAddress(flight, MistyRoofExposure.FlightAddress()) { return; }
    this.flightSector = sector;
    this.flightGeneration += 1u;
  }
}

// Arms the already-installed R7 world owner after genuine Tower completion.
// The rooftop lift uses the original device controllers and actions.
public class MistyViktorAuto extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let rooftopLiftActions: array<CName>;
  private let rooftopLiftRestrictionsCleared: Bool;
  private let exposureRequestedFor: Uint32;
  private let flightRequestedFor: Uint32;

  private func OnAttach() -> Void {
    this.exposureRequestedFor = 0u;
    this.flightRequestedFor = 0u;
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
    this.exposureRequestedFor = 0u;
    this.flightRequestedFor = 0u;
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

  private func ReleaseRooftopExposure(game: GameInstance, q: ref<QuestsSystem>, p: ref<PlayerPuppet>) -> Void {
    let service = GameInstance.GetScriptableServiceContainer().GetService(n"PTFR.MistyViktorAuto.MistyRoofExposure") as MistyRoofExposure;
    if !IsDefined(service) { return; }
    let binding = service.CurrentBinding();
    let flight = service.FlightBinding();
    let roofPending = binding != 0u && binding != this.exposureRequestedFor;
    let flightPending = flight != 0u && flight != this.flightRequestedFor;
    if !roofPending && !flightPending { return; }
    if !this.Completed(q) || !StartupCoverLC1.GameplayReleased(game) || !this.SafeStreet(p) || p.IsDead() ||
      GameInstance.GetPlayerSystem(game).GetLocalPlayerControlledGameObject() != p { return; }
    let world = GameInstance.GetWorldStateSystem();
    if !IsDefined(world) || !world.IsReady() { return; }
    if roofPending {
      world.ToggleNode(MistyRoofExposure.Address(), false);
      this.exposureRequestedFor = binding;
      ModLog(n"PTFR_MistyRoof", "Requested removal of the Tower pickup exposure volume");
    }
    if flightPending {
      world.ToggleNode(MistyRoofExposure.TrailerAddress(), false);
      world.ToggleNode(MistyRoofExposure.FlightAddress(), false);
      this.flightRequestedFor = flight;
      ModLog(n"PTFR_MistyRoof", "Requested removal of the trailer and flight lighting volumes at the roof");
    }
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
      this.ReleaseRooftopExposure(game, q, p);
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
