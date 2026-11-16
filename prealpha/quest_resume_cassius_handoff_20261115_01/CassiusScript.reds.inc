
// Cassius bridge for the shared native handoff. The original cutoff and the
// post-Tower script worker submit observations through the same native owner.
public abstract class SharedCassiusResume {
  public static func Invoke(game: GameInstance, operation: Int32, sample: array<Uint64>) -> Int32 {
    let bridge = Reflection.GetGlobalFunction(n"PTFR.HistorySnapshotHS1.CassiusResumeBridge");
    let quests = GameInstance.GetQuestsSystem(game);
    if !IsDefined(bridge) || !IsDefined(quests) { return -1; }
    let args: array<Variant>;
    ArrayPush(args, ToVariant(quests));
    ArrayPush(args, ToVariant(operation));
    ArrayPush(args, ToVariant(sample));
    let called: Bool;
    let reply = bridge.Call(args, called);
    return called && IsDefined(reply) ? FromVariant<Int32>(reply) : -1;
  }

  public static func AdapterBlocked(game: GameInstance) -> Bool {
    let qs = GameInstance.GetQuestsSystem(game);
    if !IsDefined(qs) || qs.GetFact(n"PTFRSharedCassiusOwner") != 0 { return true; }
    let empty: array<Uint64>;
    // The installed adapter still works when the native bridge is absent.
    // Issued scripts and existing fallback predicates continue to own it.
    return SharedCassiusResume.Invoke(game, 0, empty) > 0;
  }

  public static func Keys() -> array<Int32> { return [3891, 3892, 3893, 3895, 3896]; }

  private static func Safe(game: GameInstance, player: ref<PlayerPuppet>) -> Bool {
    return StartupCoverLC1.GameplayReleased(game) && BodyPolicy.Safe(player);
  }

  public static func Sample(game: GameInstance, player: ref<PlayerPuppet>, jm: ref<JournalManager>,
                            out words: array<Uint64>) -> Bool {
    ArrayClear(words);
    let tx = GameInstance.GetTransactionSystem(game);
    if !IsDefined(player) || !IsDefined(tx) || !IsDefined(jm) || jm.HasAnyDelayedStateChanges() { return false; }
    let keys = SharedCassiusResume.Keys();
    let i = 0;
    while i < ArraySize(keys) {
      let path = SnapshotDataHS3.Path(keys[i]);
      let className = SnapshotDataHS3.Class(keys[i]);
      let entry = jm.GetEntryByString(path, className);
      if !IsDefined(entry) { return false; }
      ArrayPush(words, Cast<Uint64>(EnumInt(jm.GetEntryState(entry))));
      i += 1;
    }
    if !IsDefined(TweakDBInterface.GetItemRecord(t"Items.YakuzaTattoo")) ||
       !IsDefined(TweakDBInterface.GetItemRecord(t"Items.AdvancedYakuzaTattoo")) { return false; }
    ArrayPush(words, Cast<Uint64>(tx.GetItemQuantity(player, ItemID.CreateQuery(t"Items.YakuzaTattoo"))));
    ArrayPush(words, Cast<Uint64>(tx.GetItemQuantity(player, ItemID.CreateQuery(t"Items.AdvancedYakuzaTattoo"))));
    ArrayPush(words, Cast<Uint64>(SharedCassiusResume.Safe(game, player) ? 1 : 0));
    return !jm.HasAnyDelayedStateChanges();
  }

  public static func Poll(game: GameInstance, player: ref<PlayerPuppet>, jm: ref<JournalManager>) -> Void {
    let empty: array<Uint64>;
    if SharedCassiusResume.Invoke(game, 1, empty) != 1 { return; }
    let sample: array<Uint64>;
    if !SharedCassiusResume.Sample(game, player, jm, sample) { return; }
    let command = SharedCassiusResume.Invoke(game, 2, sample);
    if command != 2 && command != 3 { return; }

    // Only the three entries selected from the matching cutoff can change.
    // Preserve the two earlier settled objectives, tracking and counters.
    let keys = SharedCassiusResume.Keys();
    let slots: array<Int32> = [0, 1, 4];
    let expected = command == 2 ? 4 : 2;
    let target = command == 2 ? gameJournalEntryState.Active : gameJournalEntryState.Failed;
    let i = 0;
    while i < ArraySize(slots) {
      let slot = slots[i];
      if Cast<Int32>(sample[slot]) == expected {
        let key = keys[slot];
        jm.ChangeEntryState(SnapshotDataHS3.Path(key), SnapshotDataHS3.Class(key), target, JournalNotifyOption.DoNotNotify);
      }
      i += 1;
    }
  }
}
