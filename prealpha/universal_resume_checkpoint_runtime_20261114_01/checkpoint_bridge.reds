  private func ReadExecution(reader: ref<ReflectionStaticFunc>, ticket: Int32, route: Int32,
                             historyRevision: Int32, presentation: array<Uint64>) -> array<Uint64> {
    let game = this.GetGameInstance();
    let args: array<Variant>;
    ArrayPush(args, ToVariant(GameInstance.GetQuestsSystem(game)));
    ArrayPush(args, ToVariant(GameInstance.GetDelaySystem(game)));
    ArrayPush(args, ToVariant(GameInstance.GetTimeSystem(game)));
    ArrayPush(args, ToVariant(ticket));
    ArrayPush(args, ToVariant(route));
    ArrayPush(args, ToVariant(historyRevision));
    ArrayPush(args, ToVariant(presentation));
    let called = false;
    let result = reader.Call(args, called);
    if called && IsDefined(result) { return FromVariant<array<Uint64>>(result); }
    let unavailable: array<Uint64>;
    return unavailable;
  }

  private func DecodeExecution(decoder: ref<ReflectionStaticFunc>, data: array<Uint64>) -> String {
    if !IsDefined(decoder) { return ""; }
    let args: array<Variant>;
    ArrayPush(args, ToVariant(data));
    let called = false;
    let result = decoder.Call(args, called);
    return called && IsDefined(result) ? FromVariant<String>(result) : "";
  }

  private func PrimeExecutionCheckpoint(ticket: Int32, route: Int32) -> Void {
    let reader = Reflection.GetGlobalFunction(n"PTFR.HistorySnapshotHS1.ReadExecutionCheckpoint");
    if IsDefined(reader) {
      let unobserved: array<Uint64>;
      this.ReadExecution(reader, ticket, route, 0, unobserved);
    }
  }
