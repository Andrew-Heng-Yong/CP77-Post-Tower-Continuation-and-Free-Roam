from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
R='r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
C.mkdir(exist_ok=False)
old=(G/R).read_text(encoding='utf-8-sig')
a=old.index('    // H1: geometry remains public;');b=old.index('    // Coyote public mirror',a)
housing=old[a:b]
start=old.index('    if q.GetFact(n"PTFRBASE_Suspended") != 0');end=old.index('    // Only perform the pre-tested geometry',start)
guard=old[start:end]
guard=guard.replace('scenes.IsEntityInScene(player.GetEntityID())','scenes.IsEntityInDialogue(player.GetEntityID())')
guard=guard.replace('{ return; }','{ this.HousingWaitH6(q, "actor/context guard"); return; }')
# Preserve exact guard expressions; report individual failed expressions below.
import re
for match in list(re.finditer(r'if (.+?) \{ this.HousingWaitH6\(q, "actor/context guard"\); return; \}',guard)):
 expression=match.group(1)
 label=('suspended' if 'Suspended' in expression else 'systems unavailable' if '!IsDefined(scenes)' in expression else 'combat/dialogue/workspot' if 'IsInCombat' in expression else 'mounted' if 'parentId' in expression else 'state board unavailable' if '!IsDefined(board)' in expression else 'player high/tier' if 'high !=' in expression else 'quest tokens blocked' if 'IsTokensActivationBlocked' in expression else 'saving locked')
 guard=guard.replace(match.group(0),match.group(0).replace('actor/context guard',label))
loc='''    let h10 = this.D2(p,-1383.84473,1276.34424,124.820267) <= 400.0;
    let h10Actions = h10 || (high == 1 && tier == 1 && this.H10OffsiteReady(q,p) && this.H10GeometryReady());
'''
method='''  // H6: publish paid-home permission independently of unrelated ambient scenes.
  // The existing native owner still owns apartment/phone gates and all actions.
  // This never starts, cuts or resets a scene, rebuilds geometry or takes money.
  private func HousingServicesH6(q: ref<QuestsSystem>, player: ref<PlayerPuppet>, p: Vector4) -> Void {
'''+guard+loc+housing+'''    this.HousingWaitH6(q, this.H10ActionsArmed() ? "armed" : "waiting for ownership/location/native prerequisites");
  }
  private func HousingWaitH6(q: ref<QuestsSystem>, reason: String) -> Void {
    let housing = HousingState.Get(this.GetGameInstance());
    if !IsDefined(housing) || !housing.Entitled("h10") { return; }
    let status = reason + " Enabled/Active/Interrupted=" + ToString(q.GetFact(n"PTFRB0H10P_Enabled")) + "/" +
      ToString(q.GetFact(n"PTFRB0H10P_Active")) + "/" + ToString(q.GetFact(n"PTFRB0H10P_Interrupted"));
    if NotEquals(status, this.housingStatusH6) {
      this.housingStatusH6 = status;
      ModLog(n"PTFR_HousingH6", status + " | " + this.H10Status());
    }
  }
'''
new=old[:a]+old[b:]
la=new.index('    let h10 = this.D2(');lb=new.index('    let coyoteOutside',la)
new=new[:la]+new[lb:]
new=new.replace('  public func Poll(epoch: Int32) -> Void {',method+'  public func Poll(epoch: Int32) -> Void {')
needle='    this.Set(q,n"PTFRBASE_Ready",1);'
assert new.count(needle)==1
new=new.replace(needle,needle+'\n    this.HousingServicesH6(q,player,p);')
new=new.replace('  private let running: Bool;','  private let running: Bool;\n  private let housingStatusH6: String;')
new=new.replace('this.startupTicks = 0;','this.startupTicks = 0; this.housingStatusH6 = "";',1)
for folder in ['before','package']:(C/folder/R).parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(G/R,C/'before'/R);(C/'package'/R).write_text(new,encoding='utf-8',newline='\n')
(C/'changes_01.json').write_text(json.dumps([dict(target=R,before=sha(G/R),after=sha(C/'package'/R))],indent=2)+'\n')
shutil.copyfile(W/'prealpha/h10_h5/compile_01.py',H/'compile_01.py')
print('Built one-script H6 candidate; no game writes.')
