module PTFR.AfterlifeInteractionsR8

// R11 retains class/fact identity. Emmerick's scene controls only Emmerick;
// Rogue uses the dense-cast local dialogue scene, not the sparse R8 scene.
// Never spawn actors, change appearance, force story facts or play phone scenes.
public class AfterlifeInteractionsR8 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let emmerick: wref<NPCPuppet>;
  private let rogue: wref<NPCPuppet>;
  private let glowOwner: wref<NPCPuppet>;
  private let quiet: Int32;
  private let previous: Vector4;
  private let hasPrevious: Bool;
  private let eAge: Int32;
  private let eChecks: String;
  private let pChecks: String;
  private let rChecks: String;

  private func OnAttach() -> Void {
    this.epoch += 1; this.running = true; this.warmup = 4;
    this.quiet = 0; this.hasPrevious = false;
    this.ClearPermissions();
    this.Schedule();
  }
  private func OnDetach() -> Void {
    this.running = false; this.epoch += 1;
    this.ClearPermissions(); this.ReleaseGlow();
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(AfterlifeInteractionsR8Tick.Create(this, this.epoch), 0.25, false);
  }
  private func Set(q: ref<QuestsSystem>, name: CName, value: Bool) -> Void {
    let next = value ? 1 : 0;
    if q.GetFact(name) != next { q.SetFact(name, next); }
  }
  private func ClearPermissions() -> Void {
    let q = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(q) { return; }
    this.Set(q, n"PTFRAL8_DriverReady", false);
    this.Set(q, n"PTFRAL8_EContinue", false);
    this.Set(q, n"PTFRAL8_EAvailable", false);
    this.Set(q, n"PTFRAL8_EStart", false);
    this.Set(q, n"PTFRAL10_ENear", false);
    this.Set(q, n"PTFRAL8_RContinue", false);
    this.Set(q, n"PTFRAL8_RAvailable", false);
    this.Set(q, n"PTFRAL8_RStart", false);
    this.Set(q, n"PTFRAL8_RDeparted", false);
  }
  private func Allowed(q: ref<QuestsSystem>) -> Bool {
    return q.GetFact(n"PostTowerFreeRoamActive") == 1 && q.GetFact(n"PTFRP0_DR13") == 1 &&
      q.GetFact(n"q307_active") == 0 && q.GetFact(n"q307_done") == 1 &&
      q.GetFact(n"q307_finished") == 1 && q.GetFact(n"q307_2079") == 1 &&
      q.GetFact(n"q307_main_game_killed") == 1 && q.GetFact(n"q307_ep1_killed") == 1 &&
      q.GetFact(n"q305_johnny_scene_active") == 0 && q.GetFact(n"q115_point_of_no_return") == 0 &&
      q.GetFact(n"PTFRBASE_Suspended") == 0 && q.GetFact(n"PTFRWORLD_Suspended") == 0 &&
      q.GetFact(n"PTFRAL1_Enabled") == 1 && q.GetFact(n"PTFRAL1_QuestOwns") == 0 &&
      q.GetFact(n"PTFRAL1_Suspended") == 0 && q.GetFact(n"PTFRAL1_WorldApplied") == 1 &&
      q.GetFact(n"PTFRAL8_Suspended") == 0;
  }
  private func Resolve(path: String, entry: CName, record: TweakDBID) -> ref<NPCPuppet> {
    let ids: array<EntityID>; let names: array<CName>;
    ArrayPush(names, entry);
    GetFixedEntityIdsFromEntityReference(CreateEntityReference(path, names), this.GetGameInstance(), ids);
    if ArraySize(ids) != 1 { return null; }
    let npc = GameInstance.FindEntityByID(this.GetGameInstance(), ids[0]) as NPCPuppet;
    if !IsDefined(npc) || npc.GetRecordID() != record { return null; }
    return npc;
  }
  private func Healthy(npc: ref<NPCPuppet>, active: Bool) -> Bool {
    if !IsDefined(npc) || npc.IsDead() || ScriptedPuppet.IsDefeated(npc) || npc.IsAboutToDieOrDefeated() || NPCPuppet.IsInCombat(npc) { return false; }
    let scene = GameInstance.GetSceneSystem(this.GetGameInstance()).GetScriptInterface();
    if active { return true; }
    return !scene.IsEntityInScene(npc.GetEntityID()) && Equals(npc.GetHighLevelStateFromBlackboard(), gamedataNPCHighLevelState.Relaxed);
  }
  private func ReleaseGlow() -> Void {
    // Only clean up an exact actor observed in our active local scene.
    // Scene events own Play/Break; never force a permanent or periodic glow.
    if IsDefined(this.glowOwner) { GameObjectEffectHelper.BreakEffectLoopEvent(this.glowOwner, n"eye_glow_gold"); }
    this.glowOwner = null;
  }
  private func PlayerGameplay(player: ref<PlayerPuppet>) -> Bool {
    if !IsDefined(player) || player.IsDead() || player.IsInCombat() { return false; }
    let game = this.GetGameInstance();
    let workspots = GameInstance.GetWorkspotSystem(game);
    let bb = player.GetPlayerStateMachineBlackboard();
    if !IsDefined(workspots) || !IsDefined(bb) { this.pChecks = "unavailable"; return false; }
    let high = bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.HighLevel);
    let tier = bb.GetInt(GetAllBlackboardDefs().PlayerStateMachine.SceneTier);
    let inWorkspot = workspots.IsActorInWorkspot(player);
    let mount = GameInstance.GetMountingFacility(game).GetMountingInfoSingleWithObjects(player);
    let mounted = EntityID.IsDefined(mount.parentId);
    let blocked = GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked();
    this.pChecks = "high=" + ToString(high) + " tier=" + ToString(tier) +
      " workspot=" + ToString(inWorkspot) + " mounted=" + ToString(mounted) + " tokensBlocked=" + ToString(blocked);
    return (high == 1 || high == 2) && (tier == 1 || tier == 2) && !inWorkspot && !mounted;
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    let game = this.GetGameInstance();
    let q = GameInstance.GetQuestsSystem(game);
    let player = GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
    let scene = GameInstance.GetSceneSystem(game).GetScriptInterface();
    if !IsDefined(q) || !IsDefined(player) || !IsDefined(scene) {
      this.ClearPermissions(); this.ReleaseGlow(); return;
    }
    let eActive = q.GetFact(n"PTFRAL8_EActive") == 1;
    let rActive = q.GetFact(n"PTFRAL8_RActive") == 1;
    let e = this.Resolve("$/03_night_city/#PTFRAL1_Emmerick", n"emmerick", t"Character.Emmerick");
    let r = this.Resolve("$/03_night_city/#PTFRAF1_RogueCommunity", n"rogue", t"Character.Rogue");
    if IsDefined(this.glowOwner) && (!rActive || this.glowOwner != r) { this.ReleaseGlow(); }
    if this.warmup > 0 || !this.Allowed(q) || player.IsInCombat() || player.IsDead() {
      this.eChecks = "global guard/warmup/player combat";
      if this.warmup > 0 { this.warmup -= 1; }
      this.ClearPermissions(); this.ReleaseGlow(); this.hasPrevious = false; this.quiet = 0; return;
    }
    // Actor replacement while a scene is active fails closed. Never grant a
    // saved Active fact to a newly resolved actor on its first observation.
    let eSame = IsDefined(e) && this.emmerick == e;
    let rSame = IsDefined(r) && this.rogue == r;
    this.emmerick = e; this.rogue = r;
    let inScene = scene.IsEntityInScene(player.GetEntityID());
    let playerDialogue = scene.IsEntityInDialogue(player.GetEntityID());
    let gameplay = this.PlayerGameplay(player);
    let tokensBlocked = GameInstance.GetQuestsContentSystem(game).IsTokensActivationBlocked();
    let rewind = scene.IsRewindableSectionActive();
    let playerFree = gameplay && !playerDialogue && !tokensBlocked && !rewind;
    let ownDialogue = false;
    if rActive && rSame { ownDialogue = scene.AreEntitiesInDialogue(player.GetEntityID(), r.GetEntityID()); }
    // Ambient scenes may share V in native free gameplay. Actual dialogue,
    // workspots, mounts and cinematic tiers are separate admission blockers.
    let eAllowed = this.Healthy(e, eActive && eSame) && (!eActive || eSame) &&
      playerFree && !rActive && q.GetFact(n"PTFRAL1_Actor26Ready") == 1;
    let rAllowed = this.Healthy(r, rActive && rSame) && (!rActive || rSame) &&
      gameplay && (!playerDialogue || ownDialogue) && (!tokensBlocked || (rActive && rSame)) && !rewind &&
      !eActive && q.GetFact(n"PTFRAL1_Actor27Ready") == 1 &&
      q.GetFact(n"rogue_default_on") > 0 && q.GetFact(n"q116_rogue_dead") == 0;
    let eStart = false;
    let eNear = false;
    let rStart = false;
    let rDeparted = Vector4.DistanceSquared(player.GetWorldPosition(), new Vector4(-1421.31909, 1012.98596, 16.8802929, 1.0)) > 225.0;
    if eActive { this.eAge += 1; } else { this.eAge = 0; }
    if this.eAge >= 80 { eAllowed = false; }
    this.eChecks = "resolved=" + ToString(IsDefined(e)) + " permit=" + ToString(eAllowed) +
      " playerScene=" + ToString(inScene) + " otherActive=" + ToString(rActive) +
      " playerFree=" + ToString(playerFree) + " playerDialogue=" + ToString(playerDialogue) + " rewind=" + ToString(rewind);
    if eAllowed {
      let start = new Vector4(-1458.48499, 1026.3302, 16.7932014, 1.0);
      let pos = e.GetWorldPosition();
      eAllowed = Vector4.DistanceSquared(pos, start) <= 16.0 && Vector4.DistanceSquared(player.GetWorldPosition(), start) <= 3600.0;
      // Use the already exact-resolved NPC. The native source's <=5m bound
      // stays unchanged without a second community-area distance resolver.
      eNear = eAllowed && Vector4.DistanceSquared(pos, player.GetWorldPosition()) <= 25.0;
      if !this.hasPrevious || Vector4.DistanceSquared(pos, this.previous) > 0.0004 { this.quiet = 0; }
      else { this.quiet += 1; }
      this.previous = pos; this.hasPrevious = true;
      // Compare the authored quaternion directly; q and -q are equivalent.
      // Avoid hard-coded assumptions about the engine's forward-axis basis.
      let authored = new Quaternion(0.0, 0.0, -0.0548490323, 0.998494744);
      let facing = AbsF(Quaternion.Dot(e.GetWorldOrientation(), authored));
      let atAnchor = Vector4.DistanceSquared(pos, start) <= 0.1225 && AbsF(pos.Z - start.Z) <= 0.15;
      let inWorkspot = GameInstance.GetWorkspotSystem(game).IsActorInWorkspot(e);
      this.eChecks += " anchor=" + ToString(atAnchor) + " facingDot=" + ToString(facing) +
        " workspot=" + ToString(inWorkspot) + " quiet=" + ToString(this.quiet) +
        " distance=" + ToString(Vector4.Distance(pos, player.GetWorldPosition()));
      eStart = eAllowed && eNear && !eActive && playerFree && this.quiet >= 2 &&
        atAnchor && facing >= 0.991445 && inWorkspot;
    } else { this.hasPrevious = false; this.quiet = 0; }
    if rAllowed {
      let booth = new Vector4(-1421.31909, 1012.98596, 16.8802929, 1.0);
      let distance = Vector4.DistanceSquared(player.GetWorldPosition(), booth);
      rAllowed = Vector4.DistanceSquared(r.GetWorldPosition(), booth) <= 4.0 && distance <= 1024.0;
      rStart = rAllowed && !rActive && playerFree && distance <= 144.0;
    }
    if !rAllowed { this.ReleaseGlow(); }
    else {
      if rActive && rSame && scene.IsEntityInScene(r.GetEntityID()) { this.glowOwner = r; }
    }
    this.rChecks = "resolved=" + ToString(IsDefined(r)) + " permit=" + ToString(rAllowed) +
      " same=" + ToString(rSame) + " ownDialogue=" + ToString(ownDialogue) + " departed=" + ToString(rDeparted);
    // All permission updates precede Ready. Native graphs independently check
    // policy, stream readiness, player trigger and permission immediately.
    this.Set(q, n"PTFRAL8_EContinue", eAllowed);
    this.Set(q, n"PTFRAL8_EAvailable", eAllowed && !eActive && playerFree);
    this.Set(q, n"PTFRAL8_EStart", eStart);
    this.Set(q, n"PTFRAL10_ENear", eNear);
    this.Set(q, n"PTFRAL8_RContinue", rAllowed);
    this.Set(q, n"PTFRAL8_RAvailable", rStart);
    this.Set(q, n"PTFRAL8_RStart", rStart);
    this.Set(q, n"PTFRAL8_RDeparted", rDeparted);
    this.Set(q, n"PTFRAL8_DriverReady", true);
  }
  public func GetStatus() -> String {
    let q = GameInstance.GetQuestsSystem(this.GetGameInstance());
    return "Interactions R11 faces=retired dancers=retire-only native=" + ToString(q.GetFact(n"PTFRAL8_NativeRevision")) +
      " stage=" + ToString(q.GetFact(n"PTFRAL8_EStage")) + " ready=" + ToString(q.GetFact(n"PTFRAL8_DriverReady")) +
      " completed/cancelled=" + ToString(q.GetFact(n"PTFRAL8_ECompleted")) + "/" + ToString(q.GetFact(n"PTFRAL8_ECancelled")) +
      " ENear=" + ToString(q.GetFact(n"PTFRAL10_ENear")) +
      " E[permit/start/active/requests]=" + ToString(q.GetFact(n"PTFRAL8_EContinue")) + "/" + ToString(q.GetFact(n"PTFRAL8_EStart")) + "/" + ToString(q.GetFact(n"PTFRAL8_EActive")) + "/" + ToString(q.GetFact(n"PTFRAL8_ERequests")) +
      " R[permit/start/active/requests]=" + ToString(q.GetFact(n"PTFRAL8_RContinue")) + "/" + ToString(q.GetFact(n"PTFRAL8_RStart")) + "/" + ToString(q.GetFact(n"PTFRAL8_RActive")) + "/" + ToString(q.GetFact(n"PTFRAL8_RRequests")) + " | E " + this.eChecks + " | P " + this.pChecks + " | R " + this.rChecks;
  }
}
public class AfterlifeInteractionsR8Tick extends DelayCallback {
  private let driver: wref<AfterlifeInteractionsR8>;
  private let epoch: Int32;
  public func Call() -> Void { if IsDefined(this.driver) { this.driver.Poll(this.epoch); } }
  public static func Create(driver: ref<AfterlifeInteractionsR8>, epoch: Int32) -> ref<AfterlifeInteractionsR8Tick> {
    let tick = new AfterlifeInteractionsR8Tick(); tick.driver = driver; tick.epoch = epoch; return tick;
  }
}
