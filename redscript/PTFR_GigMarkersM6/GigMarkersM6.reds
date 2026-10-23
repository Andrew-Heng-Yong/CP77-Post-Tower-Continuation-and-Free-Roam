module PTFR.ActivityStateR3
import PTFR.JohnnyVoiceJV1.*

// M6.1: keep a session approach marker until the native journal activates.
// IMappin.IsVisible does not prove a rendered world-map icon.
public class GigMarkerDataM6 extends MappinScriptData {
  public let id: String;
}
public class GigMarkersM6 extends ScriptableSystem {
  private let running: Bool;
  private let epoch: Int32;
  private let warmup: Int32;
  private let markers: array<NewMappinID>;
  private let attempts: array<Int32>;
  private let details: array<String>;
  private func OnAttach() -> Void { this.running=true;this.Restored(); }
  private func OnDetach() -> Void { this.running=false;this.epoch+=1;this.Purge(); }
  private func Purge() -> Void {
    let ms=GameInstance.GetMappinSystem(this.GetGameInstance());
    if !IsDefined(ms) { return; }
    let all=ms.GetAllMappins();let k=0;
    while k<ArraySize(all) {
      let d=IsDefined(all[k]) ? all[k].GetScriptData() as GigMarkerDataM6 : null;
      // This dedicated subclass belongs only to us, including stale data on load.
      if IsDefined(d) { ms.UnregisterMappin(all[k].GetNewMappinID()); };k+=1;
    }
  }
  public func Restored() -> Void {
    this.epoch+=1;this.Purge();let empty: NewMappinID;
    this.markers=[empty,empty,empty];this.attempts=[0,0,0];this.details=["","",""];this.warmup=5;
    if this.running { this.Schedule(); }
  }
  private func Schedule() -> Void { GameInstance.GetDelaySystem(this.GetGameInstance()).DelayCallback(GigMarkerTickM6.Create(this,this.epoch),2.0,false); }
  public static func Index(id: String) -> Int32 { return Equals(id,"sts_wbr_hil_07") ? 0 : Equals(id,"sts_wbr_hil_01") ? 1 : Equals(id,"sts_wbr_jpn_02") ? 2 : -1; }
  private func ID(i: Int32) -> String { return i==0 ? "sts_wbr_hil_07" : i==1 ? "sts_wbr_hil_01" : "sts_wbr_jpn_02"; }
  private func Root(i: Int32) -> String { return i==2 ? FreshGigsB6.Root() : FreshGigsB5.Root(i); }
  private func Own(i: Int32,suffix: String) -> Int32 { return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(StringToName((i==0 ? "PTFRB5_H7_" : i==1 ? "PTFRB5_H1_" : "PTFRB6_J2_")+suffix)); }
  private func Tower() -> Bool { let v=GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1") as JohnnyVoiceJV1;return IsDefined(v) && v.CompletedTower(); }
  public static func Want(tower: Bool,request: Int32,started: Int32,finished: Int32,fault: Int32,root: Int32,poi: Int32) -> Bool { return tower && request==1 && started==1 && finished==0 && fault==0 && root==1 && poi==2; }
  private func Location(i: Int32) -> Vector4 {
    // Authored official streamingsector trigger/waypoint positions, not guesses.
    return i==0 ? new Vector4(-75.2505112,-324.191193,6.2,1.0) : i==1 ? new Vector4(-8.7444849,25.3564377,14.8524351,1.0) : new Vector4(-247.972321,1639.41895,41.1923256,1.0);
  }
  private func Owned(i: Int32) -> wref<IMappin> {
    let ms=GameInstance.GetMappinSystem(this.GetGameInstance());
    if !IsDefined(ms) { return null; }
    let marker=ms.GetMappin(this.markers[i]);let d=IsDefined(marker) ? marker.GetScriptData() as GigMarkerDataM6 : null;
    return IsDefined(d) && Equals(d.id,this.ID(i)) ? marker : null;
  }
  private func Remove(i: Int32,nativeMarker: wref<IMappin>) -> Void {
    let ms=GameInstance.GetMappinSystem(this.GetGameInstance());let empty: NewMappinID;
    if NotEquals(this.markers[i],empty) {
      let mine=this.Owned(i);
      if IsDefined(mine) {
        // Preserve only tracking of our marker if a native replacement exists.
        if IsDefined(nativeMarker) && Equals(ms.GetManuallyTrackedMappinID(),this.markers[i]) { ms.SetMappinTrackingAlternative(this.markers[i],nativeMarker.GetNewMappinID()); }
        ms.UnregisterMappin(this.markers[i]);
      }
      this.markers[i]=empty;
    }
    this.attempts[i]=0;
  }
  private func NativeCandidate(entry: ref<JournalQuest>) -> wref<IMappin> {
    if !IsDefined(entry) { return null; }
    let ms=GameInstance.GetMappinSystem(this.GetGameInstance());let jm=GameInstance.GetJournalManager(this.GetGameInstance());
    let marker=ms.GetMappinFromQuest(entry);
    if IsDefined(marker) { return marker; }
    let all=ms.GetAllMappins();let k=0;
    while k<ArraySize(all) {
      let p=all[k] as PointOfInterestMappin;
      if IsDefined(p) && p.GetJournalQuestPathHash()==Cast<Uint32>(jm.GetEntryHash(entry)) { return p; };k+=1;
    }
    return null;
  }
  private func CanTransfer(root: Int32,marker: wref<IMappin>) -> Bool {
    if root!=2 || !IsDefined(marker as QuestMappin) || !marker.IsActive() || !marker.IsVisible() || Equals(marker.GetPhase(),gamedataMappinPhase.CompletedPhase) { return false; }
    let p=marker.GetWorldPosition();
    return p.X!=0.0 || p.Y!=0.0 || p.Z!=0.0;
  }
  private func Describe(marker: wref<IMappin>) -> String {
    if !IsDefined(marker) { return "none"; }
    let p=marker.GetWorldPosition();let markerID=marker.GetNewMappinID();
    return "id="+ToString(markerID.value)+" active="+ToString(marker.IsActive())+" visibleFlag="+ToString(marker.IsVisible())+" phase="+ToString(EnumInt(marker.GetPhase()))+" xyz="+ToString(p.X)+","+ToString(p.Y)+","+ToString(p.Z);
  }
  public func Poll(epoch: Int32) -> Void {
    if !this.running || epoch!=this.epoch { return; };this.Schedule();if this.warmup>0 { this.warmup-=1;return; }
    let ms=GameInstance.GetMappinSystem(this.GetGameInstance());let jm=GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(ms) || !IsDefined(jm) || jm.HasAnyDelayedStateChanges() { return; }
    let tower=this.Tower();let i=0;
    while i<3 {
      let quest=jm.GetEntryByString(this.Root(i),"gameJournalQuest") as JournalQuest;
      let poi=jm.GetEntryByString("points_of_interest/street_stories/"+this.ID(i),"gameJournalPointOfInterestMappin");
      let root=IsDefined(quest) ? EnumInt(jm.GetEntryState(quest)) : -1;
      let state=IsDefined(poi) ? EnumInt(jm.GetEntryState(poi)) : -1;
      if !GigMarkersM6.Want(tower,this.Own(i,"Request"),this.Own(i,"Started"),this.Own(i,"OwnerFinished"),this.Own(i,"Fault"),root,state) {
        let nativeMarker=IsDefined(quest) ? ms.GetMappinFromQuest(quest) : null;
        this.Remove(i,tower && this.CanTransfer(root,nativeMarker) ? nativeMarker : null);
        this.details[i]=root==2 ? "Native journal active; approach marker released." : "No eligible unencountered owned gig; no approach marker.";
      } else {
        let empty: NewMappinID;
        // Retain any issued handle even before readback, avoiding duplicate
        // registrations if the map system acknowledges it on a later tick.
        if Equals(this.markers[i],empty) && this.attempts[i]<3 {
          this.attempts[i]+=1;let d=new GigMarkerDataM6();d.id=this.ID(i);let data: MappinData;
          data.mappinType=t"Mappins.DefaultStaticMappin";data.variant=i==0 ? gamedataMappinVariant.RetrievingVariant : i==1 ? gamedataMappinVariant.ThieveryVariant : gamedataMappinVariant.ClientInDistressVariant;
          data.active=true;data.visibleThroughWalls=false;data.scriptData=d;data.localizedCaption=quest.title;data.debugCaption="PTFR location: "+quest.GetTitle(jm);
          this.markers[i]=ms.RegisterMappin(data,this.Location(i));
        }
        this.details[i]=IsDefined(this.Owned(i)) ? "Approach marker retained until native journal activation; native registration alone cannot remove it." : "Marker registration not acknowledged; at most three attempts per eligibility period.";
      }
      i+=1;
    }
  }
  public func Inspect(id: String) -> String {
    let i=GigMarkersM6.Index(id);if i<0 || ArraySize(this.details)!=3 { return "M6.1 unsupported/not initialized."; }
    let jm=GameInstance.GetJournalManager(this.GetGameInstance());let ms=GameInstance.GetMappinSystem(this.GetGameInstance());
    if !IsDefined(jm) || !IsDefined(ms) { return "M6.1 journal/map system unavailable."; }
    let quest=jm.GetEntryByString(this.Root(i),"gameJournalQuest") as JournalQuest;let marker=this.Owned(i);
    return "Marker M6.1 "+id+": fallback="+ToString(IsDefined(marker))+" root="+ToString(IsDefined(quest) ? EnumInt(jm.GetEntryState(quest)) : -1)+" attempts="+ToString(this.attempts[i])+" | "+this.details[i]+" | owned{"+this.Describe(marker)+"} native{"+this.Describe(this.NativeCandidate(quest))+"}; registration flags are not rendered-icon proof.";
  }
}
public class GigMarkerTickM6 extends DelayCallback {
  private let owner: wref<GigMarkersM6>;private let epoch: Int32;
  public static func Create(owner: ref<GigMarkersM6>,epoch: Int32) -> ref<GigMarkerTickM6> { let t=new GigMarkerTickM6();t.owner=owner;t.epoch=epoch;return t; }
  public func Call() -> Void { if IsDefined(this.owner) { this.owner.Poll(this.epoch); } }
}
@wrapMethod(PlayerDevelopmentData)
public final func OnRestored(gameInstance: GameInstance) -> Void { wrappedMethod(gameInstance);let s=GameInstance.GetScriptableSystemsContainer(gameInstance).Get(n"PTFR.ActivityStateR3.GigMarkersM6") as GigMarkersM6;if IsDefined(s) { s.Restored(); } }
