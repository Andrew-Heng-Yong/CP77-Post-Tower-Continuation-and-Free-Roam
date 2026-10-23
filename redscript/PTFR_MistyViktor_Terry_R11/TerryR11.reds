module PTFR.MistyViktorTerryR11

// One private, nonpersistent Terry at his authored pre-assault alley position.
// A successful spawn is consumed for this runtime session, including after death.
// Failed asynchronous creation can retry up to three times; original actors are never selected.
public class TerryR11 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let entityID: EntityID;
  private let attempts: Int32;
  private let pendingTicks: Int32;
  private let everSpawned: Bool;
  private let dead: Bool;
  private let listenerRegistered: Bool;

  private func OnAttach() -> Void {
    this.epoch += 1;
    let emptyID: EntityID;
    this.entityID = emptyID;
    this.attempts = 0;
    this.pendingTicks = 0;
    this.everSpawned = false;
    this.dead = false;
    this.listenerRegistered = false;
    this.running = true;
    this.Schedule(this.epoch, 1.0);
  }
  private func OnDetach() -> Void {
    this.running = false;
    this.epoch += 1;
    let system = GameInstance.GetDynamicEntitySystem();
    if IsDefined(system) {
      if this.listenerRegistered {
        system.UnregisterListener(n"PTFRMV11_Terry", this, n"OnTerryEvent");
        this.listenerRegistered = false;
      }
      if system.IsReady() { this.Release(system); }
    }
  }
  private func Schedule(epoch: Int32, seconds: Float) -> Void {
    let delays = GameInstance.GetDelaySystem(this.GetGameInstance());
    if IsDefined(delays) { delays.DelayCallback(TerryR11Tick.Create(this, epoch), seconds, false); }
  }
  private func Count(name: CName) -> Void {
    let q = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if IsDefined(q) { q.SetFact(name, q.GetFact(name) + 1); }
  }
  private func Allowed(q: ref<QuestsSystem>) -> Bool {
    return q.GetFact(n"PostTowerFreeRoamActive") == 1 && q.GetFact(n"PTFRP0_DR13") == 1 &&
      q.GetFact(n"q307_active") == 0 && q.GetFact(n"q307_done") == 1 &&
      q.GetFact(n"q307_finished") == 1 && q.GetFact(n"q307_2079") == 1 &&
      q.GetFact(n"q307_main_game_killed") == 1 && q.GetFact(n"q307_ep1_killed") == 1 &&
      q.GetFact(n"q305_johnny_scene_active") == 0 && q.GetFact(n"q115_point_of_no_return") == 0 &&
      q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRWORLD_Suspended") == 0 &&
      q.GetFact(n"PTFRMV_Suspended") == 0 && q.GetFact(n"PTFRMV_QuestOwns") == 0 &&
      q.GetFact(n"PTFRMV_Enabled") == 1 && q.GetFact(n"PTFRMV_Applied") == 1 &&
      q.GetFact(n"PTFRMV11_Registered") == 1 && q.GetFact(n"PTFRMV_AccessRevision") == 11;
  }
  private func SafeForCreate(player: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(player) || player.IsInCombat() { return false; }
    let game = this.GetGameInstance();
    let scene = GameInstance.GetSceneSystem(game).GetScriptInterface();
    let workspots = GameInstance.GetWorkspotSystem(game);
    if !IsDefined(scene) || !IsDefined(workspots) { return false; }
    if scene.IsEntityInScene(player.GetEntityID()) || workspots.IsActorInWorkspot(player) { return false; }
    let mount = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(player);
    if EntityID.IsDefined(mount.parentId) { return false; }
    if GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked() { return false; }
    let locks: array<gameSaveLock>;
    if GameInstance.IsSavingLocked(game, locks) { return false; }
    let pos = player.GetWorldPosition();
    let dx = pos.X + 1551.20374;
    let dy = pos.Y - 1172.57251;
    let dz = pos.Z - 16.3103752;
    let distance = dx * dx + dy * dy + dz * dz;
    return distance <= 3600.0 && distance > 9.0;
  }
  private func MarkSpawned() -> Void {
    if !this.everSpawned {
      this.everSpawned = true;
      this.Count(n"PTFRMV11_TerrySpawned");
    }
  }
  private func MarkDead() -> Void {
    this.MarkSpawned();
    if !this.dead { this.dead = true; this.Count(n"PTFRMV11_TerryDead"); }
  }
  private func OnTerryEvent(event: ref<DynamicEntityEvent>) -> Void {
    if !this.running || !IsDefined(event) || !Equals(event.GetEntityTag(), n"PTFRMV11_Terry") { return; }
    if Equals(event.GetEventType(), DynamicEntityEventType.Spawned) { this.MarkSpawned(); }
    if Equals(event.GetEventType(), DynamicEntityEventType.Dead) { this.MarkDead(); }
  }
  private func Release(system: ref<DynamicEntitySystem>) -> Void {
    let ids = system.GetTaggedIDs(n"PTFRMV11_Terry");
    let index = 0;
    while index < ArraySize(ids) {
      if system.IsManaged(ids[index]) && system.IsTagged(ids[index], n"PTFRMV11_Terry") {
        if system.DeleteEntity(ids[index]) { this.Count(n"PTFRMV11_TerryReleaseRequests"); }
      }
      index += 1;
    }
    // Preserve everSpawned/dead across owner loss. No same-session resurrection.
  }
  private func Create(system: ref<DynamicEntitySystem>) -> Void {
    let record = TweakDBInterface.GetCharacterRecord(t"Character.PTFRMV_Terry");
    if !IsDefined(record) { return; }
    let tags = record.Tags();
    if ArrayContains(tags, n"Invulnerable") { return; }
    let spec = new DynamicEntitySpec();
    spec.recordID = t"Character.PTFRMV_Terry";
    spec.appearanceName = n"man_average__q307__streetkid_01";
    let position: Vector4;
    position.X = -1551.20374; position.Y = 1172.57251; position.Z = 16.3103752; position.W = 1.0;
    let orientation: Quaternion;
    orientation.i = -0.0191563722; orientation.j = -0.0170180015;
    orientation.k = 0.996187747; orientation.r = -0.0833877027;
    spec.position = position; spec.orientation = orientation;
    spec.persistState = false; spec.persistSpawn = false;
    // Keep the same single runtime object alive while owned: streaming cannot recreate its health.
    spec.alwaysSpawned = true; spec.spawnInView = true; spec.active = true;
    ArrayPush(spec.tags, n"PTFRMV11_Terry");
    this.attempts += 1;
    this.pendingTicks = 0;
    this.entityID = system.CreateEntity(spec);
    this.Count(n"PTFRMV11_TerryRequests");
    if !EntityID.IsDefined(this.entityID) { this.Count(n"PTFRMV11_TerryCreationFailures"); }
  }
  public func Poll(expectedEpoch: Int32) -> Void {
    if !this.running || expectedEpoch != this.epoch { return; }
    let system = GameInstance.GetDynamicEntitySystem();
    let q = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if IsDefined(system) && system.IsReady() && system.IsRestored() && IsDefined(q) {
      if !this.listenerRegistered {
        system.RegisterListener(n"PTFRMV11_Terry", this, n"OnTerryEvent");
        this.listenerRegistered = true;
      }
      if !this.Allowed(q) {
        this.Release(system);
      } else {
        let ids = system.GetTaggedIDs(n"PTFRMV11_Terry");
        if ArraySize(ids) > 0 {
          // Adopt an already-managed private instance, including a pending asynchronous spawn.
          this.entityID = ids[0];
          if system.IsSpawned(this.entityID) {
            this.MarkSpawned();
            let puppet = system.GetEntity(this.entityID) as NPCPuppet;
            if IsDefined(puppet) && puppet.IsDead() { this.MarkDead(); }
          } else {
            if !this.everSpawned && !system.IsSpawning(this.entityID) {
              this.pendingTicks += 1;
              if this.pendingTicks >= 15 {
                // Retry only after removal is acknowledged by absence on a later poll.
                if system.IsManaged(this.entityID) && system.IsTagged(this.entityID, n"PTFRMV11_Terry") && system.DeleteEntity(this.entityID) {
                  this.Count(n"PTFRMV11_TerryCreationFailures");
                }
                this.pendingTicks = 0;
              }
            }
          }
        } else {
          if !this.everSpawned && !this.dead && this.attempts < 3 {
            // A valid create ID can precede its tag registration; never race a pending spec.
            if !EntityID.IsDefined(this.entityID) || (!system.IsManaged(this.entityID) && !system.IsSpawning(this.entityID)) {
              let player = GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet;
              if this.SafeForCreate(player) { this.Create(system); }
            }
          }
        }
      }
    }
    this.Schedule(expectedEpoch, 2.0);
  }
}

public class TerryR11Tick extends DelayCallback {
  private let driver: wref<TerryR11>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<TerryR11>, epoch: Int32) -> ref<TerryR11Tick> {
    let tick = new TerryR11Tick(); tick.driver = driver; tick.epoch = epoch; return tick;
  }
}
