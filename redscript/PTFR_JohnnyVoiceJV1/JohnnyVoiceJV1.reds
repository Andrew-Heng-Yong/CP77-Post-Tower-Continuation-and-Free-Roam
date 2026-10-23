module PTFR.JohnnyVoiceJV1

// Presentation only. Keep the scene actor alive for voice, timing and output.
// No scene skip, despawn, equipment/AI toggle, quest write or persistent field.
public class JohnnyVoiceJV1 extends ScriptableSystem {
  private let actors: array<wref<NPCPuppet>>;
  private let running: Bool;
  private let epoch: Int32;
  private let visuals: Int32;

  private func OnAttach() -> Void { this.running = true; this.Restored(); }
  private func OnDetach() -> Void {
    this.running = false; this.epoch += 1; ArrayClear(this.actors);
  }
  public func Restored() -> Void {
    // Do not clear registrations: NPC attachment and restore callbacks may
    // arrive in either order. Poll prunes expired/detached weak references.
    this.epoch += 1;
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void {
    GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(JohnnyVoiceTick.Create(this, this.epoch), ArraySize(this.actors) > 0 ? 0.10 : 1.0, false);
  }
  public func CompletedTower() -> Bool {
    let facts = GameInstance.GetQuestsSystem(this.GetGameInstance());
    if !IsDefined(facts) { return false; }
    return facts.GetFact(n"PostTowerFreeRoamActive") == 1 && facts.GetFact(n"PTFRP0_DR13") == 1 &&
      facts.GetFact(n"q307_done") == 1 && facts.GetFact(n"q307_finished") == 1 && facts.GetFact(n"q307_2079") == 1 &&
      facts.GetFact(n"q307_main_game_killed") == 1 && facts.GetFact(n"q307_ep1_killed") == 1 &&
      facts.GetFact(n"q307_active") == 0 && facts.GetFact(n"q115_point_of_no_return") == 0 && facts.GetFact(n"q305_johnny_scene_active") == 0;
  }
  public func Register(actor: wref<NPCPuppet>) -> Void {
    if !IsDefined(actor) || actor.GetRecordID() != t"Character.Silverhand" { return; }
    let i = 0;
    while i < ArraySize(this.actors) {
      if this.actors[i] == actor { this.Hide(actor); return; }
      i += 1;
    }
    ArrayPush(this.actors, actor);
    this.Hide(actor);
  }
  private func Hide(actor: wref<NPCPuppet>) -> Int32 {
    if !IsDefined(actor) || !actor.IsAttached() || actor.GetRecordID() != t"Character.Silverhand" || !this.CompletedTower() { return 0; }
    let components = actor.GetComponents();
    let visual: ref<IVisualComponent>;
    let count = 0;
    let i = 0;
    while i < ArraySize(components) {
      visual = components[i] as IVisualComponent;
      if IsDefined(visual) {
        visual.TemporaryHide(true);
        count += 1;
      }
      i += 1;
    }
    return count;
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch != this.epoch { return; }
    this.Schedule();
    this.visuals = 0;
    let i = ArraySize(this.actors) - 1;
    while i >= 0 {
      if !IsDefined(this.actors[i]) || !this.actors[i].IsAttached() {
        ArrayErase(this.actors, i);
      } else {
        // Re-enumeration also covers newly loaded/replaced appearance meshes.
        this.visuals += this.Hide(this.actors[i]);
      }
      i -= 1;
    }
  }
  public func GetStatus() -> String {
    return "Johnny JV1: tower=" + ToString(this.CompletedTower()) + " tracked=" + ToString(ArraySize(this.actors)) +
      " visualComponentsLastPoll=" + ToString(this.visuals) + " | visual-only candidate; audio/scene untouched; independent props not covered.";
  }
}

public class JohnnyVoiceTick extends DelayCallback {
  private let owner: wref<JohnnyVoiceJV1>;
  private let epoch: Int32;
  public static func Create(owner: ref<JohnnyVoiceJV1>, epoch: Int32) -> ref<JohnnyVoiceTick> {
    let tick = new JohnnyVoiceTick(); tick.owner = owner; tick.epoch = epoch; return tick;
  }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}

@wrapMethod(NPCPuppet)
protected cb func OnGameAttached() -> Bool {
  let result = wrappedMethod();
  if this.GetRecordID() == t"Character.Silverhand" {
    let policy = GameInstance.GetScriptableSystemsContainer(this.GetGame()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;
    if IsDefined(policy) { policy.Register(this); }
  }
  return result;
}

@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void {
  wrappedMethod(gameInstance);
  let policy = GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;
  if IsDefined(policy) { policy.Restored(); }
}
