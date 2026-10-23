module PTFR.ActivityStateR3

// PA5 evidence only. Never activates a quest, changes a journal entry, registers
// a mappin, rewrites facts, changes map filters or restarts an existing U9 owner.
public class GigDiagnosticsPA5 extends ScriptableSystem {
  private func Fact(name: String) -> Int32 {
    return GameInstance.GetQuestsSystem(this.GetGameInstance()).GetFact(StringToName(name));
  }
  private func Own(id: String, suffix: String) -> Int32 { return this.Fact("PTFRU9_" + id + "_" + suffix); }
  private func State(path: String, cls: String) -> Int32 {
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    if !IsDefined(jm) { return -1; }
    let entry = jm.GetEntryByString(path, cls);
    return IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;
  }
  private func POIPath(i: Int32) -> String {
    return (Equals(NativeGigDataU9.Region(i), "ep1") ? "ep1/points_of_interest/street_stories/" : "points_of_interest/street_stories/") + NativeGigDataU9.ID(i);
  }
  private func Terminal(i: Int32) -> Bool {
    let paths = NativeGigDataU9.Paths(i);
    if ArraySize(paths) > 0 && this.State(paths[0], "gameJournalQuest") == 3 { return true; }
    let names = NativeGigDataU9.TerminalFacts(i); let k = 0;
    while k < ArraySize(names) { if this.Fact(names[k]) != 0 { return true; }; k += 1; }
    return false;
  }
  private func Describe(marker: wref<IMappin>) -> String {
    if !IsDefined(marker) { return "none"; }
    let pos = marker.GetWorldPosition(); let markerID = marker.GetNewMappinID();
    return "id=" + ToString(markerID.value) + " active=" + ToString(marker.IsActive()) +
      " visibleFlag=" + ToString(marker.IsVisible()) + " phase=" + ToString(EnumInt(marker.GetPhase())) +
      " xyz=" + ToString(pos.X) + "," + ToString(pos.Y) + "," + ToString(pos.Z);
  }
  private func MapDetail(i: Int32) -> String {
    let jm = GameInstance.GetJournalManager(this.GetGameInstance());
    let ms = GameInstance.GetMappinSystem(this.GetGameInstance());
    if !IsDefined(jm) || !IsDefined(ms) { return "journal/map system unavailable"; }
    let paths = NativeGigDataU9.Paths(i);
    if ArraySize(paths) == 0 { return "catalogue root missing"; }
    let quest = jm.GetEntryByString(paths[0], "gameJournalQuest") as JournalQuest;
    if !IsDefined(quest) { return "quest entry missing"; }
    let out = "questMarker{" + this.Describe(ms.GetMappinFromQuest(quest)) + "}";
    let hash = Cast<Uint32>(jm.GetEntryHash(quest));
    let all = ms.GetAllMappins(); let k = 0; let matches = 0;
    while k < ArraySize(all) {
      let poi = all[k] as PointOfInterestMappin;
      if IsDefined(poi) && poi.GetJournalQuestPathHash() == hash {
        matches += 1;
        // Retain a bounded diagnostic even if another mod has many duplicates.
        if matches <= 4 { out += " POI{" + this.Describe(poi) + "}"; }
      }
      k += 1;
    }
    return out + " poiMatches=" + ToString(matches) + " journalDelayed=" + ToString(jm.HasAnyDelayedStateChanges());
  }
  private func EntryDifferences(i: Int32) -> String {
    let paths = NativeGigDataU9.Paths(i); let classes = NativeGigDataU9.Classes(i);
    if ArraySize(paths) == 0 || ArraySize(paths) != ArraySize(classes) { return "catalogue-shape mismatch"; }
    let k = 0; let count = 0; let out = "";
    while k < ArraySize(paths) {
      let state = this.State(paths[k], classes[k]);
      if state != 1 { count += 1; if count <= 6 { out += " J{" + paths[k] + "=" + ToString(state) + "}"; } }
      k += 1;
    }
    let names = NativeGigDataU9.Facts(i); k = 0;
    while k < ArraySize(names) {
      let value = this.Fact(names[k]);
      if value != 0 { count += 1; if count <= 6 { out += " F{" + names[k] + "=" + ToString(value) + "}"; } }
      k += 1;
    }
    return "entryDifferences=" + ToString(count) + out;
  }
  private func ParentFacts(i: Int32) -> String {
    let names = GigDiagnosticsDataPA5.ParentFacts(i); let k = 0; let out = "";
    while k < ArraySize(names) { out += (k > 0 ? "," : "") + names[k] + "=" + ToString(this.Fact(names[k])); k += 1; }
    return out;
  }
  public func Summary() -> String {
    let requested = 0; let parent = 0; let main = 0; let finished = 0; let terminal = 0;
    let faults = 0; let activePOI = 0; let activeJournal = 0; let i = 0;
    while i < NativeGigDataU9.Count() {
      let id = NativeGigDataU9.ID(i); let paths = NativeGigDataU9.Paths(i);
      if this.Own(id, "Request") == 1 { requested += 1; }
      if this.Own(id, "ParentEntered") == 1 { parent += 1; }
      if this.Own(id, "Started") == 1 { main += 1; }
      if this.Own(id, "OwnerFinished") == 1 { finished += 1; }
      if this.Own(id, "Fault") != 0 { faults += 1; }
      if this.Terminal(i) { terminal += 1; }
      if this.Own(id, "Started") == 1 && this.State(this.POIPath(i), "gameJournalPointOfInterestMappin") == 2 { activePOI += 1; }
      if this.Own(id, "Started") == 1 && ArraySize(paths) > 0 && this.State(paths[0], "gameJournalQuest") == 2 { activeJournal += 1; }
      i += 1;
    }
    return "Gig visibility PA5 whitelist=" + ToString(NativeGigDataU9.Count()) + " requested/parent/main/cleanup=" +
      ToString(requested) + "/" + ToString(parent) + "/" + ToString(main) + "/" + ToString(finished) +
      " preservedTerminal=" + ToString(terminal) + " faults=" + ToString(faults) +
      " ownedMainActivePOI/Journal=" + ToString(activePOI) + "/" + ToString(activeJournal) +
      " | Requested is not main-entered; POI active/registered/visibleFlag is not rendered-icon proof. No quest/map mutations.";
  }
  public func Inspect(id: String) -> String {
    let i = NativeGigDataU9.Index(id);
    if i < 0 { return "PA5: ID is outside the 72-gig whitelist; no action."; }
    let owner = GameInstance.GetScriptableSystemsContainer(this.GetGameInstance()).Get(n"PTFR.ActivityStateR3.NativeGigsU9") as NativeGigsU9;
    let out = "Gig visibility PA5 " + NativeGigDataU9.Title(i) + " [" + id + "]: POI=" +
      ToString(this.State(this.POIPath(i), "gameJournalPointOfInterestMappin")) + " mapPermit/mapsEntered=" +
      ToString(this.Own(id, "MapPermit")) + "/" + ToString(this.Own(id, "Map0Entered")) + "/" +
      ToString(this.Own(id, "Map1Entered")) + "/" + ToString(this.Own(id, "Map2Entered")) +
      " | " + this.MapDetail(i) + " | parentFacts{" + this.ParentFacts(i) + "} | " + this.EntryDifferences(i);
    return out + " | " + (IsDefined(owner) ? owner.Inspect(id) : "native owner module unavailable") +
      " | Journal state: -1 missing,1 inactive,2 active,3 succeeded,4 failed. Getter only; root4 alone does not establish pre-Tower failure.";
  }
  public func InspectOwned() -> String {
    let out = this.Summary(); let i = 0;
    while i < NativeGigDataU9.Count() {
      let id = NativeGigDataU9.ID(i);
      if this.Own(id, "Started") == 1 && this.Own(id, "OwnerFinished") == 0 { out += "\n" + this.Inspect(id); }
      i += 1;
    }
    return out;
  }
}
