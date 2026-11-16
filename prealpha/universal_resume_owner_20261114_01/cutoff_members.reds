  private persistent let timerSampleSchema: Int32;
  private persistent let timerSampleTicket: Int32;
  private persistent let timerSampleNode: Uint64;
  private persistent let timerSampleSeconds: Float;

  private func CaptureNativeWait(ticket: Int32, route: Int32) -> Void {
    this.timerSampleSchema = 0;
    this.timerSampleTicket = 0;
    this.timerSampleNode = 0ul;
    this.timerSampleSeconds = 0.0;
    if route != 1 || !this.GateOpen(ticket, route) { return; }

    // Original Go Your Own Way phase, with its separate possible owners.
    let node: Uint64 = 11125825902242431045ul;
    let quests = GameInstance.GetQuestsSystem(this.GetGameInstance());
    let seconds = ReadNativeWaitAtCutoff(quests, ticket, node);
    if seconds <= 0.0 || !this.GateOpen(ticket, route) { return; }
    this.timerSampleTicket = ticket;
    this.timerSampleNode = node;
    this.timerSampleSeconds = seconds;
    this.timerSampleSchema = 1;
  }
