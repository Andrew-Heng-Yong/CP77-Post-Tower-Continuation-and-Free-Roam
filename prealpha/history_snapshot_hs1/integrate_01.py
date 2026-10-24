"""Create candidate replacements from actual installed sources; do not install."""
from pathlib import Path
import json,hashlib,re,shutil
H=Path(__file__).resolve().parent;W=H.parent.parent;O=H/'candidate_01';P=O/'package'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def replace(s,old,new):assert s.count(old)==1,(old[:120],s.count(old));return s.replace(old,new)
manifest=[]
def edit(rel,fn):
 src=G/rel;s=src.read_text(encoding='utf-8-sig');new=fn(s)
 assert s!=new
 before=O/'before'/rel;before.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,before)
 dst=P/rel;assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(new,encoding='utf-8',newline='\n')
 manifest.append({'target':rel,'before':sha(src),'after':sha(dst)})
def imported(s):return replace(s,s.splitlines()[0],s.splitlines()[0]+'\nimport PTFR.HistorySnapshotHS1.*')
def entry(s):
 s=imported(s)
 s=replace(s,'private func Activated() -> Bool { return !this.faulted && this.Completed() && (this.endingObserved || this.certified || this.EstablishedHandoff()); }',
 '''private func Activated() -> Bool {
    // HS1: snapshot provenance controls quest admission, not core initialization.
    // Prepared/Finished are outputs of setup and must not be required here.
    return !this.faulted && this.Completed() && (this.endingObserved || this.certified || this.EstablishedHandoff() ||
      (SnapshotStateHS1.StartupReady(this.GetGameInstance()) && this.Fact(n"PTFRPA2_Started")==1 &&
       this.Fact(n"PTFRPA2_Teleported")==1 && this.Fact(n"PTFRPA2_ControlReady")==1 &&
       this.Fact(n"PTFRPA3_CoverReleased")==1 && this.Fact(n"PTFRPA4_CameraAligned")==1));
  }''')
 s=replace(s,'public func PostEndingAuthorized() -> Bool { return this.Activated(); }',
 'public func PostEndingAuthorized() -> Bool { return this.Activated(); }\n  public func SnapshotInitializationHealthy() -> Bool { return !this.faulted && this.Completed(); }')
 s=replace(s,'if !this.Activated() { this.activationTicks = 0; return; }',
 '''if !SnapshotStateHS1.StartupReady(this.GetGameInstance()) { this.detail="Waiting for save-bound snapshot and verified JSON file."; return; }
    if !this.Activated() { this.activationTicks = 0; return; }''')
 s=replace(s,'else { if this.DevelopmentArmed() { result = gigs.Start(id, "DISPOSABLE_SAVE"); }\n      else { result = "Excluded: no certified unstarted pre-Tower history."; } }',
 '''else {
        let snapshot=SnapshotStateHS1.Get(this.GetGameInstance());
        if IsDefined(snapshot) && snapshot.FreshU9(id) { result=gigs.RestoreSnapshot(id); }
        else { result="Preserved/deferred by accepted snapshot and existing progress guards."; }
      }''')
 s=replace(s,'this.detail = this.DevelopmentArmed() ? "Late-ending DEVELOPMENT dispatch: incomplete assumed unstarted; stock runtime/terminal guards remain." : "Certified pre-Tower dispatch: only observed unstarted whitelist entries.";',
 'this.detail="Snapshot admission pass complete. Pre-ending certificates take priority; accepted fallback preserves completed/failed/progressed entries.";')
 return s
edit('r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds',entry)
def gigs(s):
 s=imported(s)
 s=replace(s,'return IsDefined(history) && history.Certified(id) ? "Certified actual pre-Tower unstarted history." : "DEVELOPMENT incomplete-as-unstarted; no certified history.";',
 '''if IsDefined(history) && history.Certified(id) { return "Certified actual pre-Tower unstarted history."; }
    let snapshot=SnapshotStateHS1.Get(this.GetGameInstance());
    return IsDefined(snapshot) && snapshot.FreshU9(id) ? "Accepted save-bound snapshot; origin retained in JSON." : "No snapshot admission; explicit development route is separate.";''')
 anchor='public func RestoreCertified(id: String) -> String { return this.Request(id,"DISPOSABLE_SAVE",true); }'
 s=replace(s,anchor,anchor+'''
  public func RestoreSnapshot(id: String) -> String {
    let snapshot=SnapshotStateHS1.Get(this.GetGameInstance());
    if !IsDefined(snapshot) || !snapshot.FreshU9(id) { return "Refused: accepted snapshot does not admit a fresh start."; }
    // Same native entry/terminal/owner/reward/retaliation guards as certified starts.
    return this.Request(id,"DISPOSABLE_SAVE",false);
  }''')
 s=replace(s,'let safe=GigBatchLockU9.Ready()', 'let safe=SnapshotStateHS1.StartupReady(this.GetGameInstance()) && GigBatchLockU9.Ready()')
 return s
edit('r6/scripts/PTFR_PreAlpha/PTFR_NativeGigsU9/NativeGigsU9.reds',gigs)
for n in [2,22,23,24,25,27,28]:
 def side(s,n=n):
  s=imported(s)
  s=replace(s,'private func Common() -> Bool {','private func Common() -> Bool {\n    if !SnapshotStateHS1.StartupReady(this.GetGameInstance()) { return false; }')
  name='CanPermit' if n==2 else 'Ready'
  s=replace(s,f'private func {name}(i: Int32) -> Bool {{',f'private func {name}(i: Int32) -> Bool {{\n    if !SnapshotStateHS1.Admits(this.GetGameInstance(),SideJobDataS{n}.ID(i)) {{ return false; }}')
  if n==23:s=replace(s,'private func LegacyInactive() -> Bool {','private func LegacyInactive() -> Bool {\n    if !SnapshotStateHS1.Admits(this.GetGameInstance(),"mq005_alley") { return false; }')
  return s
 edit(f'r6/scripts/TowerContinued_SideJobs_S{n}/SideJobsS{n}.reds',side)
def u10(s):
 s=imported(s)
 s=replace(s,'private func BaseCommon() -> Bool {','private func BaseCommon() -> Bool {\n    if !SnapshotStateHS1.StartupReady(this.GetGameInstance()) { return false; }')
 s=replace(s,'private func Ready(i: Int32) -> Bool {','private func Ready(i: Int32) -> Bool {\n    if !SnapshotStateHS1.Admits(this.GetGameInstance(),GigDataU10.ID(i)) { return false; }')
 s=replace(s,'(this.familyHistorySchema == 1 && this.familyPreTowerCompleted);',
 '''(this.familyHistorySchema == 1 && this.familyPreTowerCompleted) ||
      SnapshotStateHS1.FamilyAccepted(this.GetGameInstance());''')
 # Ensure the saved real pre-Tower witness remains unchanged by fallback admission.
 return s
edit('r6/scripts/TowerContinued_Gigs_U10/GigsU10.reds',u10)
for source,rel in [('SnapshotStateHS1.reds','r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotStateHS1.reds'),
                   ('init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua')]:
 dst=P/rel;dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();shutil.copyfile(H/source,dst)
 manifest.append({'target':rel,'before':None,'after':sha(dst)})
rel='r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotDataHS1.reds';manifest.append({'target':rel,'before':None,'after':sha(P/rel)})
(O/'changes_01.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'replacements':sum(x['before'] is not None for x in manifest),'additions':sum(x['before'] is None for x in manifest)}))
