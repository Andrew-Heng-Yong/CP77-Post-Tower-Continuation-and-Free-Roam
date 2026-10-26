from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_01';D=W/'diagnostics/h10_services_20261025_01'
R='r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def block(s,pat):
 m=re.search(pat,s);assert m,pat
 i=s.index('{',m.start());n=1
 for t in re.finditer(r'"(?:\\.|[^"\\])*"|\{|\}',s[i+1:]):
  n+=(t.group()=='{')-(t.group()=='}')
  if n==0:return s[m.start():i+1+t.end()]
 raise AssertionError('Unclosed block '+pat)
checks=[]
def ck(n,b):assert b,n;checks.append(n)
old=(C/'before'/R).read_text();new=(C/'package'/R).read_text()
a=old.index('    // H1: geometry remains public;');b=old.index('    // Coyote public mirror',a)
ck('Ownership/revocation/idle/native acknowledgement predicates unchanged',old[a:b] in new)
modified=old[:a]+old[b:];la=modified.index('    let h10 = this.D2(');lb=modified.index('    let coyoteOutside',la);modified=modified[:la]+modified[lb:]
ck('Every unrelated Startup statement unchanged',block(modified,r'  private func Startup\b')==block(new,r'  private func Startup\b'))
oldguard=old[old.index('    if q.GetFact(n"PTFRBASE_Suspended")'):old.index('    // Only perform the pre-tested geometry')]
guard=block(new,r'  private func HousingServicesH6\b');guard=guard[guard.index('    if q.GetFact(n"PTFRBASE_Suspended")'):guard.index('    let h10 =')]
guard=re.sub(r'this.HousingWaitH6\(q, "[^"]+"\); ','',guard)
ck('Only actor safety change is ambient scene -> actual dialogue',guard==oldguard.replace('scenes.IsEntityInScene(player.GetEntityID())','scenes.IsEntityInDialogue(player.GetEntityID())'))
op=block(old,r'  public func Poll\b');np=block(new,r'  public func Poll\b')
ck('One-second reconciliation precedes unchanged startup throttle',np==op.replace('    this.Set(q,n"PTFRBASE_Ready",1);','    this.Set(q,n"PTFRBASE_Ready",1);\n    this.HousingServicesH6(q,player,p);'))
ck('No new persistent state', 'persistent let' not in new)
ck('No additional fact writes or transactions',new.count('this.Set(')==old.count('this.Set(') and 'RemoveItem' not in new and 'Purchase(' not in new)
ck('No scene/owner resets',all(x not in block(new,r'  private func HousingServicesH6\b') for x in ['SetFact(', 'Set(q,n"PTFRB0H10P_Active"', 'Set(q,n"PTFRB0H10P_Interrupted"', 'Restart', 'CutScene']))
condition=old[a:b];condition=condition[condition.index('if IsDefined(housing) && housing.HousingReadyForReveal()'):condition.index('this.Set(q,n"PTFRB0H10P_Enabled",1)')]
pairs=re.findall(r'q.GetFact\(n"([^"]+)"\) == (\d)',condition);values={k:int(v) for k,v in pairs}
def permits(facts,paid=True,ready=True,local=True):return paid and ready and local and all(facts[k]==int(v) for k,v in pairs)
ck('Valid paid idle fixture admitted',permits(values))
for key,value in values.items():
 f=dict(values);f[key]=1-value;ck('Blocks changed prerequisite '+key,not permits(f))
for kw in ['paid','ready','local']:ck('Blocks missing '+kw,not permits(values,**{kw:False}))
base=(W/'prealpha/h10_h5/candidate_01/compile_01/compiled.script').read_text(encoding='utf-8-sig');compiled=(C/'compile_03/compiled.script').read_text(encoding='utf-8-sig')
for cl in ['PTFR.Housing.HousingState','PTFR.Housing.HousingPrice','PTFR.Housing.HousingDialogueH5','PTFR.Housing.HousingMapH3','PTFR.Housing.HousingDoorH2']:
 ck('Compiled '+cl+' unchanged',block(base,r'public (?:abstract )?(?:final )?class '+re.escape(cl)+r'\b')==block(compiled,r'public (?:abstract )?(?:final )?class '+re.escape(cl)+r'\b'))
hs2=(W/'prealpha/snapshot_reload_hs2/candidate_01/compile_01/compiled.script').read_text(encoding='utf-8-sig')
ck('Compiled installed HS2 fix retained',block(compiled,r'public class PTFR.HistorySnapshotHS1.SnapshotStateHS1\b')==block(hs2,r'public class PTFR.HistorySnapshotHS1.SnapshotStateHS1\b'))
ck('Full current stack compiled',read(C/'compile_03/result.json')['full_scc_equipmentex'])
ck('Exact compiled candidate',sha(C/'compile_03/scripts/game/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds')==sha(C/'package'/R))
for slot in ['AutoSave-19','AutoSave-2']:
 state=read(D/'saved_systems_01'/f'{slot}.PTFR.Housing.HousingState.json');row=state['records']['$value'][0]['Data']
 ck(slot+' single successful paid receipt',row['debitAttempts']['$value']==1 and row['debitReturned']['$value']==1 and row['balanceBefore']['$value']-row['balanceAfter']['$value']==25000 and row['purchaseState']['$value']==3)
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077');sv=read(D/'inputs_02/receipt.json')['save_hashes']
ck('Captured save slots unchanged across user load attempt',all(sha(S/p)==h for p,h in sv.items() if p!='user.gls'))
closed=[x for x in read(W/'prealpha/snapshot_reload_hs2/candidate_01/install_manifest_01.json')['protected'] if x['kind']=='save']
ck('All post-crash closed baseline save files unchanged',all(sha(Path(x['path']))==x['sha256'] for x in closed))
changes=read(C/'changes_01.json');changes[0]['after']=sha(C/'package'/R)
(C/'changes_02.json').write_text(json.dumps(changes,indent=2)+'\n')
out=dict(status='PASS_H6_OFFLINE_LIVE_PENDING',checks=checks,count=len(checks),save_files_checked=len(sv),compiled_sha256=sha(C/'compile_03/cache/compiled.redscripts'))
(C/'tests_01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='checks'}))
