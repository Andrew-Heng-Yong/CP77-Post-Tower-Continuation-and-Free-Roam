from pathlib import Path
import hashlib,json,re,shutil
H=Path(__file__).resolve().parent; W=H.parent.parent; C=H/'candidate_04'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
C.mkdir(exist_ok=False); P=C/'package'; B=C/'before'; changes=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def load(rel):
 p=G/rel;b=B/rel;b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,b)
 return p.read_text(encoding='utf-8-sig')
def save(rel,s):
 p=P/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
 changes.append({'target':rel,'before':sha(B/rel) if (B/rel).exists() else None,'after':sha(p)})
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def body_span(s,name):
 m=re.search(r'\bfunc '+name+r'\([^\n]*\)[^{]*\{',s);assert m,name
 start=m.end();i=start;depth=1
 # Existing method bodies do not contain unmatched braces in strings/comments.
 while depth:
  if s[i]=='{':depth+=1
  if s[i]=='}':depth-=1
  i+=1
 return start,i-1
def end_method(s,name,code):
 a,b=body_span(s,name);return s[:b]+code+s[b:]
def begin(s,name,code):
 a,b=body_span(s,name);return s[:a]+code+s[a:]
def module_import(s):return s.replace('\n','\nimport PTFR.LoadingCoverLC1.*\n',1)
base='r6/scripts/PTFR_PreAlpha/'
r=base+'PTFR_Restrictions_R2/BodyPolicy.reds';s=load(r)
s=replace(s,'BodyTick.Create(this, this.epoch), 1.0, false','BodyTick.Create(this, this.epoch), this.LC1Interval(), false')
s=replace(s,'  private let settleTicks: Int32;','  private let settleTicks: Int32;\n  private let lc1StableSince: Float;')
s=s.replace('this.settleTicks = 0;', 'this.settleTicks = 0; this.lc1StableSince = -1.0;')
s=replace(s,'      this.settleTicks += 1;','      this.settleTicks += 1;\n      if this.lc1StableSince < 0.0 { this.lc1StableSince = EngineTime.ToFloat(GameInstance.GetSimTime(this.GetGameInstance())); }')
s=replace(s,'    if this.settleTicks < 4 { return; }','    if this.settleTicks < 4 || this.lc1StableSince < 0.0 || EngineTime.ToFloat(GameInstance.GetSimTime(this.GetGameInstance())) - this.lc1StableSince < 4.0 { return; }')
insert='''  private func LC1Interval() -> Float {
    // Only acknowledged refund work accelerates. Load/admission settling stays 1s.
    if this.warmup==0 && !this.queued && !this.inflight && (this.stage==2 || (this.stage==3 && this.relicEnabled && RelicCatalogue.Total(this.expected)>0)) { return 0.25; }
    return 1.0;
  }
  public func LC1Progress() -> String { return "Body ranks: "+ToString(this.refundedRanks)+" / "+ToString(this.startingRanks)+"; Relic ranks: "+ToString(this.refundedRelicRanks)+" / "+ToString(this.startingRelicRanks); }
'''
s=replace(s,'  private func Schedule() -> Void {',insert+'  private func Schedule() -> Void {');save(r,s)
r=base+'PTFR_Restrictions_R3/ProfilePolicy.reds';s=load(r)
s=replace(s,'this.cadence += 1; if this.cadence < 4 { return; } this.cadence = 0;','this.cadence += 1; if this.stage != 2 && this.cadence < 4 { return; } this.cadence = 0;')
s=replace(s,'  public func PTFRPAConfigured() -> Bool {','''  public func LC1LedgerValid(player:ref<PlayerPuppet>) -> Bool {
    if !this.PTFRPAComplete() || !this.MatchesDefinition() || !IsDefined(player) { return false; }
    let data=PlayerDevelopmentSystem.GetData(player);if !IsDefined(data) { return false; }
    let current=data.PTFRR2Snapshot();return current.valid && current.body==3 && BodyPolicy.Total(current)==0 && RelicCatalogue.Total(current)==0 && this.Total(current)==0;
  }
  public func LC1PhysicalReady() -> Bool { return this.PTFRPAComplete() && IsDefined(this.physical) && this.physical.HealthReady() && !this.physical.Faulted(); }
  public func LC1Progress() -> String { return "Other ranks: "+ToString(this.refunded)+" / "+ToString(this.starting); }
  public func PTFRPAConfigured() -> Bool {''');save(r,s)
r=base+'PA1/PreAlphaEntry.reds';s=module_import(load(r))
s=replace(s,'  private let detail: String;','  private let detail: String;\n  private let lc1Dispatched: Bool;\n  private let lc1SafeSince: Float;')
s=begin(s,'Restored','\n    this.lc1Dispatched=false;this.lc1SafeSince=-1.0;')
s=replace(s,'PreAlphaTick.Create(this, this.epoch), 1.0, false','PreAlphaTick.Create(this, this.epoch), this.Completed() ? 0.25 : 1.0, false')
s=s.replace('this.activationTicks = 0; return;', 'this.activationTicks = 0; this.lc1SafeSince=-1.0; return;')
s=replace(s,'this.activationTicks += 1; if this.activationTicks < 3 { return; }','this.activationTicks += 1; if this.lc1SafeSince<0.0 { this.lc1SafeSince=this.Now(); }; if this.Now()-this.lc1SafeSince<3.0 { return; }')
s=replace(s,'    if this.Now() - this.lastAttempt < 5.0 { return; }\n    this.lastAttempt = this.Now(); if !this.Dispatch() { return; }','''    if this.Now() - this.lastAttempt >= 5.0 || !this.lc1Dispatched {
      this.lastAttempt = this.Now(); if !this.Dispatch() { return; } this.lc1Dispatched=true;
    }''')
s=replace(s,'  public func Status() -> String {','  public func LC1DispatchChecked() -> Bool { return this.lc1Dispatched && !this.faulted; }\n  public func Status() -> String {');save(r,s)
r=base+'PA1/PreAlphaArrivalPA1.reds';s=load(r)
s=replace(s,'  private func CameraStatus(player:', '  public func LC1ControlReady() -> Bool { return this.ControlReady(this.Player()); }\n  private func CameraStatus(player:');save(r,s)
r=base+'PTFR_RestorationBaseline/RestorationBaseline.reds';s=load(r)
s=replace(s,'this.Startup(q,player,p); this.startupTicks = 10;', 'this.Startup(q,player,p); this.startupTicks = this.H10GeometryReady() ? 10 : 2;');save(r,s)
r=base+'PTFR_NativeGigsU9/NativeGigsU9.reds';s=module_import(load(r))
s=begin(s,'Request','\n    if !StartupCoverLC1.GameplayReleased(this.GetGameInstance()) { return "Classified; native activation waits for setup cover release."; }')
s=replace(s,'let safe=SnapshotStateHS1.StartupReady', 'let safe=StartupCoverLC1.GameplayReleased(this.GetGameInstance()) && SnapshotStateHS1.StartupReady');save(r,s)
adapters=[]
for n in ['2','22','23','24','25','27','28','U10']:
 cls='GigsU10' if n=='U10' else 'SideJobsS'+n
 r='r6/scripts/'+('TowerContinued_Gigs_U10/GigsU10.reds' if n=='U10' else f'TowerContinued_SideJobs_S{n}/{cls}.reds')
 s=module_import(load(r));module=re.search(r'^module (\S+)',s).group(1);adapters.append((module,cls))
 s=replace(s,'  private let running: Bool;', '  private let running: Bool;\n  private let lc1Passes: Int32;')
 s=begin(s,'Restored','\n    this.lc1Passes=0;')
 safe='BodyPolicy.Safe(GameInstance.GetPlayerSystem(this.GetGameInstance()).GetLocalPlayerMainGameObject() as PlayerPuppet)' if n=='2' else 'this.Safe()'
 common='this.BaseCommon()' if n=='U10' else 'this.Common()'
 # A native prerequisite can defer an entry; it must not keep the loading screen
 # up forever. Every poll classified each owner as eligible/preserved/deferred.
 ok='this.running && this.warmup==0 && SnapshotStateHS1.StartupReady(this.GetGameInstance()) && IsDefined(ProfilePolicy.Get(this.GetGameInstance())) && ProfilePolicy.Get(this.GetGameInstance()).PTFRPAComplete() && this.Fact("PTFRPA2_Finished")==1'+(' && !this.faulted' if n=='2' else '')
 s=end_method(s,'Poll',f'    if {ok} {{ this.lc1Passes=Min(this.lc1Passes+1,2); }} else {{ this.lc1Passes=0; }}\n  ')
 s=replace(s,'  public func Poll(epoch: Int32)',f'  public func LC1SetupReady() -> Bool {{ return this.lc1Passes>=2 && {ok}; }}\n  public func Poll(epoch: Int32)')
 assert s.count('let value = allowed ? 1 : 0;')==(3 if n=='U10' else 1); s=s.replace('let value = allowed ? 1 : 0;', 'let value = allowed && StartupCoverLC1.GameplayReleased(this.GetGameInstance()) ? 1 : 0;')
 if n=='23':s=replace(s,'if fresh && this.legacyFreshPrevious {','if fresh && this.legacyFreshPrevious && StartupCoverLC1.GameplayReleased(this.GetGameInstance()) {')
 save(r,s)
out='module PTFR.LoadingCoverLC1\n'+''.join('import '+m+'.*\n' for m,c in adapters)
out+='public abstract class SetupAdaptersLC1 {\n  public static func Ready(game:GameInstance) -> Bool {\n    let container=GameInstance.GetScriptableSystemsContainer(game);\n'
for i,(m,c) in enumerate(adapters):out+=f'    let s{i}=container.Get(n"{m}.{c}") as {c};if !IsDefined(s{i}) || !s{i}.LC1SetupReady() {{ return false; }}\n'
out+='    return true;\n  }\n}\n';save('r6/scripts/TowerContinued_Loading_LC1/SetupAdaptersLC1.reds',out)
save('r6/scripts/TowerContinued_Loading_LC1/StartupCoverLC1.reds',(H/'StartupCoverLC1.reds').read_text())
(C/'changes_01.json').write_text(json.dumps(changes,indent=2)+'\n')
print('Generated',len(changes),'script files; native archive separate.')
