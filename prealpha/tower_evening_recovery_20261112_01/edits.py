"""Source changes for evening recovery and fast-travel cover diagnostics."""


def replace_once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new, 1)


def edit_recovery(source):
    source = replace_once(source, '    let checkpointTime = 11 * 3600 + 55 * 60;',
                          '    let checkpointTime = 23 * 3600 + 55 * 60;')
    source = replace_once(source, '  // Index of the latest 11:55 checkpoint, including the previous day before 11:55.',
                          '  // Index of the latest 23:55 checkpoint, including the previous day before 23:55.')
    source = replace_once(source, '  private let clampSent: Bool;\n', '')
    source = replace_once(source, '''  private func BeginChange(player: ref<PlayerPuppet>) -> Void {
    this.ready = false;
    this.pending = 12;
    this.clampSent = false;
    if Equals(this.pool, gamedataStatPoolType.Health) {''', '''  private func BeginChange(player: ref<PlayerPuppet>) -> Void {
    this.ready = false;
    if this.pending == 0 && Equals(this.pool, gamedataStatPoolType.Health) {''')
    start = source.index('  private func ReadBack(player: ref<PlayerPuppet>, maximum: Float, poolMaximum: Float)')
    end = source.index('  private func RemoveOwned(', start)
    start_before = '''        Cast<StatsObjectID>(player.GetEntityID()), this.pool, false);
    }
  }

'''
    assert source[:start].endswith(start_before)
    source = source[:start - len(start_before)] + '''        Cast<StatsObjectID>(player.GetEntityID()), this.pool, false);
    }
    this.pending = 12;
  }

  private func ReadBack(player: ref<PlayerPuppet>, maximum: Float, poolMaximum: Float) -> Void {
    if this.pending <= 0 { return; }
    if AbsF(poolMaximum - maximum) >= 0.05 {
      this.pending -= 1;
      if this.pending == 0 {
        ModLog(n"PTFR_Restrictions_R3", "Recovery pool still settling. Stat=" + ToString(maximum) +
          " pool maximum=" + ToString(poolMaximum));
      }
      return;
    }

    // Once the maximum settles, correct a possible refill once. Native healing
    // and damage can change the current value again before the next sample.
    this.pending = 0;
    if Equals(this.pool, gamedataStatPoolType.Health) {
      let pools = GameInstance.GetStatPoolsSystem(player.GetGame());
      let id = Cast<StatsObjectID>(player.GetEntityID());
      let excess = pools.GetStatPoolValue(id, this.pool, false) - this.ceiling;
      if excess > 0.01 {
        pools.RequestChangingStatPoolValue(id, this.pool, -excess, player, false, false);
      }
    }
  }

''' + source[end:]
    source = replace_once(source, '''    this.pending = 0;
    this.clampSent = false;
  }

  public func Disable''', '''    this.pending = 0;
  }

  public func Disable''')
    source = replace_once(source, '''    let id = Cast<StatsObjectID>(player.GetEntityID());
    let stats = GameInstance.GetStatsSystem(player.GetGame());
    let pools = GameInstance.GetStatPoolsSystem(player.GetGame());
    if this.pending > 0 {
      this.ReadBack(player, stats.GetStatValue(id, this.stat), pools.GetStatPoolMaxPointValue(id, this.pool));
      if this.pending > 0 { return; }
    }
    if IsDefined(this.modifier) {
      this.BeginChange(player);
      if !this.RemoveOwned(player) { this.Stop("Owned modifier could not be removed"); }
    }''', '''    if IsDefined(this.modifier) {
      this.BeginChange(player);
      if !this.RemoveOwned(player) { this.Stop("Owned modifier could not be removed"); }
      return;
    }
    let id = Cast<StatsObjectID>(player.GetEntityID());
    let stats = GameInstance.GetStatsSystem(player.GetGame());
    let pools = GameInstance.GetStatPoolsSystem(player.GetGame());
    this.ReadBack(player, stats.GetStatValue(id, this.stat), pools.GetStatPoolMaxPointValue(id, this.pool));''')
    source = replace_once(source, '''    this.ReadBack(player, maximum, poolMaximum);
    if this.fault || this.pending > 0 { return; }
    if AbsF(maximum - target) > 0.02 {''', '''    // Apply the newest cap even when the previous pool update is still settling.
    if AbsF(maximum - target) > 0.02 {''')
    return replace_once(source, '''    this.ready = AbsF(poolMaximum - target) < 0.05;
    this.detail = "target=" + ToString(target) + " stat=" + ToString(maximum) + " pool=" + ToString(poolMaximum);''',
                        '''    this.ReadBack(player, maximum, poolMaximum);
    let wasReady = this.ready;
    this.ready = AbsF(poolMaximum - target) < 0.05;
    this.detail = "target=" + ToString(target) + " stat=" + ToString(maximum) + " pool=" + ToString(poolMaximum);
    if this.ready && !wasReady { ModLog(n"PTFR_Restrictions_R3", this.Status()); }''')


def edit_cover(source):
    source = replace_once(source, '  private let lastHeartbeat: Float;', '''  private let lastHeartbeat: Float;
  private let travelSampleAt: Float;''')
    source = replace_once(source, '    this.continuation=false;', '''    this.continuation=false;
    this.travelSampleAt=0.0;''')
    source = replace_once(source, '''    if !this.running || epoch!=this.epoch { return; }this.Schedule();
    if this.leaving || this.released { return; }''', '''    if !this.running || epoch!=this.epoch { return; }this.Schedule();
    if this.travelSampleAt>0.0 && this.EngineNow()>=this.travelSampleAt {
      this.travelSampleAt=0.0;
      this.TraceFastTravel(n"follow-up");
    }
    if this.leaving || this.released { return; }''')
    source = replace_once(source, '  public func Status() -> String { return "LC3', '''  public func TraceFastTravel(stage: CName) -> Void {
    if !this.running || !this.Required() || this.Fact(n"PTFRPA2_Finished")!=1 { return; }
    if Equals(stage,n"native-start") { this.travelSampleAt=this.EngineNow()+5.0; }
    let game=this.GetGameInstance();
    let defs=GetAllBlackboardDefs().FastTRavelSystem;
    let boards=GameInstance.GetBlackboardSystem(game);
    let travel=boards.Get(defs);
    if !IsDefined(travel) { return; }
    let start=FromVariant<TweakDBID>(travel.GetVariant(defs.StartingPoint));
    let destination=FromVariant<TweakDBID>(travel.GetVariant(defs.DestinationPoint));
    let player=GameInstance.GetPlayerSystem(game).GetLocalPlayerControlledGameObject();
    let position="unavailable";
    if IsDefined(player) {
      let point=player.GetWorldPosition();
      position=ToString(point.X)+"/"+ToString(point.Y)+"/"+ToString(point.Z);
    }
    let popups=SetupPopupPoolLC1.Get();
    let ui=boards.Get(GetAllBlackboardDefs().UI_System);
    let inMenu=IsDefined(ui) && ui.GetBool(GetAllBlackboardDefs().UI_System.IsInMenu);
    ModLog(n"PTFR_FastTravel", NameToString(stage)+" start="+TDBID.ToStringDEBUG(start)+
      " destination="+TDBID.ToStringDEBUG(destination)+" player="+position+
      " started/loading/finished="+ToString(travel.GetBool(defs.FastTravelStarted))+"/"+
      ToString(travel.GetBool(defs.FastTravelLoadingScreenStarted))+"/"+
      ToString(travel.GetBool(defs.FastTravelLoadingScreenFinished))+
      " cover visible/released/popup="+ToString(this.visible)+"/"+ToString(this.released)+"/"+
      ToString(IsDefined(popups) && popups.HasPopup())+" inMenu="+ToString(inMenu));
  }
  public func Status() -> String { return "LC3''')
    source = replace_once(source, '''  public func Released(popup:ref<SetupPopupLC1>) -> Void { if this.current==popup { this.current=null; } }''',
                          '''  public func HasPopup() -> Bool { return IsDefined(this.current); }
  public func Released(popup:ref<SetupPopupLC1>) -> Void { if this.current==popup { this.current=null; } }''')
    start = source.index('  protected cb func OnShow() -> Void {')
    end = source.index('  protected cb func OnCoverFrame', start)
    source = source[:start] + '''  private func ActiveCover() -> Bool {
    return !this.closing && IsDefined(this.owner) && this.owner.Accepts(this.epoch);
  }
  protected cb func OnShow() -> Void {
    let root=this.GetRootWidget();
    if !this.ActiveCover() {
      root.SetVisible(false);
      GameInstance.GetDelaySystem(this.GetGame()).DelayCallback(SetupPopupCloseLC1.Create(this),0.0,false);
      return;
    }
    root.SetVisible(true);root.SetOpacity(1.0);
    this.owner.Attached(this.epoch);
    // Acknowledge a fully drawn cover for this session only.
    let alpha=new inkAnimTransparency();alpha.SetStartTransparency(1.0);alpha.SetEndTransparency(1.0);alpha.SetDuration(0.10);
    let anim=new inkAnimDef();anim.AddInterpolator(alpha);
    this.m_transitionAnimProxy=root.PlayAnimation(anim);
    this.m_transitionAnimProxy.RegisterToCallback(inkanimEventType.OnFinish,this,n"OnCoverFrame");
  }
''' + source[end:]
    source = replace_once(source, '''  protected cb func OnGlobalReleaseInput(evt:ref<inkPointerEvent>) -> Bool {
    evt.Handle();return true;
  }''', '''  protected cb func OnGlobalReleaseInput(evt:ref<inkPointerEvent>) -> Bool {
    if !this.ActiveCover() { return false; }
    evt.Handle();return true;
  }''')
    source = replace_once(source, '''  public func Dismiss() -> Void { this.closing=true;if this.IsInitialized() { this.Detach(); } }''', '''  public func Dismiss() -> Void {
    this.closing=true;
    if this.IsInitialized() {
      this.GetRootWidget().SetVisible(false);
      this.Detach();
    }
  }''')
    return source + '''
// Record native progress and the owned cover state around a post-Tower trip.
@wrapMethod(FastTravelSystem)
private final func SetFastTravelStarted() -> Void {
  wrappedMethod();
  let cover=StartupCoverLC1.Get(this.GetGameInstance());
  if IsDefined(cover) { cover.TraceFastTravel(n"native-start"); }
}

@wrapMethod(FastTravelSystem)
protected cb func OnLoadingScreenFinished(value: Bool) -> Bool {
  let result=wrappedMethod(value);
  if value {
    let cover=StartupCoverLC1.Get(this.GetGameInstance());
    if IsDefined(cover) { cover.TraceFastTravel(n"native-finished"); }
  }
  return result;
}
'''
