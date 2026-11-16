// Appended inside the existing PTFR.RestrictionsR3 module.
public abstract class RecoverySettings {
  public static func DurationDays() -> Int32 { return 30; }
  public static func BruiseDays() -> Int32 { return 14; }
  public static func StartingHealth() -> Float { return 25.00; }
  public static func RecoveredHealth() -> Float { return 125.00; }
  public static func StartingStamina() -> Float { return 25.00; }
  public static func RecoveredStamina() -> Float { return 75.00; }

  public static func ElapsedDays(startSeconds: Int32, nowSeconds: Int32, savedDays: Int32) -> Int32 {
    if startSeconds < 0 || nowSeconds < startSeconds { return savedDays; }
    let days = (nowSeconds - startSeconds) / 86400;
    return days > savedDays ? days : savedDays;
  }

  public static func Curve(progress: Float) -> Float { return progress; }

  private static func Progress(days: Int32) -> Float {
    if days <= 0 { return 0.00; }
    let duration = RecoverySettings.DurationDays();
    if days >= duration { return 1.00; }
    return ClampF(RecoverySettings.Curve(Cast<Float>(days) / Cast<Float>(duration)), 0.00, 1.00);
  }

  public static func Health(days: Int32) -> Float {
    let start = RecoverySettings.StartingHealth();
    return start + (RecoverySettings.RecoveredHealth() - start) * RecoverySettings.Progress(days);
  }

  public static func Stamina(days: Int32) -> Float {
    let start = RecoverySettings.StartingStamina();
    return start + (RecoverySettings.RecoveredStamina() - start) * RecoverySettings.Progress(days);
  }

  public static func VitalsValid() -> Bool {
    return RecoverySettings.DurationDays() > 0 &&
      RecoverySettings.StartingHealth() >= 1.00 && RecoverySettings.RecoveredHealth() >= RecoverySettings.StartingHealth() &&
      RecoverySettings.RecoveredHealth() <= 100000.00 &&
      RecoverySettings.StartingStamina() >= 1.00 && RecoverySettings.RecoveredStamina() >= RecoverySettings.StartingStamina() &&
      RecoverySettings.RecoveredStamina() <= 100000.00;
  }
}

// Owns one unsaved modifier, and for Health only, the bounded no-refill
// correction used by the previous profile. Never sweeps another stat owner.
public class RecoveryVital extends IScriptable {
  private let stat: gamedataStatType;
  private let pool: gamedataStatPoolType;
  private let modifier: ref<gameStatModifierData>;
  private let factor: Float;
  private let ready: Bool;
  private let fault: Bool;
  private let detail: String;
  private let ceiling: Float;
  private let pending: Int32;
  private let clampSent: Bool;

  public static func Create(stat: gamedataStatType, pool: gamedataStatPoolType) -> ref<RecoveryVital> {
    let vital = new RecoveryVital();
    vital.stat = stat;
    vital.pool = pool;
    vital.factor = 1.00;
    return vital;
  }

  public static func ActorReady(player: ref<PlayerPuppet>) -> Bool {
    return IsDefined(player) && player.IsAttached() && !player.IsDead() && !player.IsReplacer() &&
      GameInstance.GetPlayerSystem(player.GetGame()).GetLocalPlayerMainGameObject() == player;
  }

  public func PoolReady(player: ref<PlayerPuppet>) -> Bool {
    if !RecoveryVital.ActorReady(player) { return false; }
    let stats = GameInstance.GetStatsSystem(player.GetGame());
    let pools = GameInstance.GetStatPoolsSystem(player.GetGame());
    if !IsDefined(stats) || !IsDefined(pools) { return false; }
    let id = Cast<StatsObjectID>(player.GetEntityID());
    let maximum = stats.GetStatValue(id, this.stat);
    let poolMax = pools.GetStatPoolMaxPointValue(id, this.pool);
    return maximum > 0.00 && maximum < 1000000.00 && poolMax > 0.00 && poolMax < 1000000.00;
  }

  private func Stop(message: String) -> Void {
    this.fault = true;
    this.ready = false;
    this.detail = "STOPPED: " + message;
    ModLog(n"PTFR_Restrictions_R3", this.Status());
  }

  private func BeginChange(player: ref<PlayerPuppet>) -> Void {
    this.ready = false;
    this.pending = 12;
    this.clampSent = false;
    if Equals(this.pool, gamedataStatPoolType.Health) {
      this.ceiling = GameInstance.GetStatPoolsSystem(player.GetGame()).GetStatPoolValue(
        Cast<StatsObjectID>(player.GetEntityID()), this.pool, false);
    }
  }

  private func ReadBack(player: ref<PlayerPuppet>, maximum: Float, poolMaximum: Float) -> Void {
    if this.pending <= 0 { return; }
    if AbsF(poolMaximum - maximum) < 0.05 {
      if NotEquals(this.pool, gamedataStatPoolType.Health) {
        this.pending = 0;
        return;
      }
      let pools = GameInstance.GetStatPoolsSystem(player.GetGame());
      let id = Cast<StatsObjectID>(player.GetEntityID());
      let excess = pools.GetStatPoolValue(id, this.pool, false) - this.ceiling;
      if excess <= 0.01 {
        this.pending = 0;
        this.clampSent = false;
        return;
      }
      if !this.clampSent {
        pools.RequestChangingStatPoolValue(id, this.pool, -excess, player, false, false);
        this.clampSent = true;
      }
    }
    this.pending -= 1;
    if this.pending == 0 { this.Stop("Pool acknowledgement timed out"); }
  }

  private func RemoveOwned(player: ref<PlayerPuppet>) -> Bool {
    if IsDefined(this.modifier) {
      let stats = GameInstance.GetStatsSystem(player.GetGame());
      if !stats.RemoveModifier(Cast<StatsObjectID>(player.GetEntityID()), this.modifier) { return false; }
    }
    this.modifier = null;
    this.factor = 1.00;
    this.ready = false;
    return true;
  }

  public func Release(player: ref<PlayerPuppet>) -> Void {
    if IsDefined(player) && !this.RemoveOwned(player) { this.Stop("Owned modifier could not be released"); }
    this.pending = 0;
    this.clampSent = false;
  }

  public func Disable(player: ref<PlayerPuppet>) -> Void {
    this.ready = false;
    if !this.PoolReady(player) { return; }
    let id = Cast<StatsObjectID>(player.GetEntityID());
    let stats = GameInstance.GetStatsSystem(player.GetGame());
    let pools = GameInstance.GetStatPoolsSystem(player.GetGame());
    if this.pending > 0 {
      this.ReadBack(player, stats.GetStatValue(id, this.stat), pools.GetStatPoolMaxPointValue(id, this.pool));
      if this.pending > 0 { return; }
    }
    if IsDefined(this.modifier) {
      this.BeginChange(player);
      if !this.RemoveOwned(player) { this.Stop("Owned modifier could not be removed"); }
    }
  }

  public func Update(player: ref<PlayerPuppet>, target: Float) -> Void {
    if this.fault { return; }
    if !this.PoolReady(player) {
      this.ready = false;
      this.detail = "Waiting for native stat pool";
      return;
    }
    if !(target >= 1.00 && target <= 100000.00) { this.Stop("Invalid maximum target"); return; }
    let id = Cast<StatsObjectID>(player.GetEntityID());
    let stats = GameInstance.GetStatsSystem(player.GetGame());
    let pools = GameInstance.GetStatPoolsSystem(player.GetGame());
    let maximum = stats.GetStatValue(id, this.stat);
    let poolMaximum = pools.GetStatPoolMaxPointValue(id, this.pool);
    this.ReadBack(player, maximum, poolMaximum);
    if this.fault || this.pending > 0 { return; }
    if AbsF(maximum - target) > 0.02 {
      let nextFactor = this.factor * target / maximum;
      if !(nextFactor > 0.000001 && nextFactor < 100000.00) { this.Stop("Invalid maximum scaling factor"); return; }
      this.BeginChange(player);
      if !this.RemoveOwned(player) { this.Stop("Owned modifier could not be replaced"); return; }
      let next = RPGManager.CreateStatModifier(this.stat, gameStatModifierType.Multiplier, nextFactor);
      if !stats.AddModifier(id, next) { this.Stop("Owned modifier admission failed"); return; }
      this.modifier = next;
      this.factor = nextFactor;
      if AbsF(stats.GetStatValue(id, this.stat) - target) > 0.05 { this.Stop("Maximum stat did not match target"); return; }
      this.detail = "Target " + ToString(target) + "; awaiting pool readback";
      return;
    }
    this.ready = AbsF(poolMaximum - target) < 0.05;
    this.detail = "target=" + ToString(target) + " stat=" + ToString(maximum) + " pool=" + ToString(poolMaximum);
  }

  public func Ready() -> Bool { return this.ready && !this.fault; }
  public func Faulted() -> Bool { return this.fault; }
  public func Status() -> String {
    return EnumValueToString("gamedataStatType", Cast<Int64>(EnumInt(this.stat))) + " " + this.detail;
  }
}
