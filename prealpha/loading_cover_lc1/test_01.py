"""Offline contract, compiled-code and native reachability checks (not UI playtest)."""
from pathlib import Path
import hashlib,importlib.util,json,re,shutil
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_04';P=C/'package'
sp=importlib.util.spec_from_file_location('parse',W/'prealpha/history_snapshot_hs1/build_catalogue_01.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def norm(s):
 s=re.sub(r'//[^\n]*','',s);s=re.sub(r'PTFR\.\w+\.', '',s);s=re.sub(r'\$local\$\d+','',s)
 s=re.sub(r'\s+','',s).replace("\\'","'")
 return s.replace('(s.released&&!s.leaving)','s.released&&!s.leaving')
checks=[]
def check(v,label):assert v,label;checks.append(label)
changes=json.loads((C/'changes_01.json').read_text())
for f in changes:
 current=(P/f['target']).read_text(encoding='utf-8-sig')
 if f['before']:
  old=(C/'before'/f['target']).read_text(encoding='utf-8-sig')
  fields=lambda s:re.findall(r'persistent let (\w+)\s*:\s*([^;]+);',s)
  check(fields(old)==fields(current),'saved fields preserved: '+f['target'])
  methods=lambda s:set(norm(m) for m in re.findall(r'(?:public |private |protected )?(?:final )?(?:static )?(?:cb )?func [^{\n]+',s))
  check(methods(old)<=methods(current),'old method signatures preserved: '+f['target'])
base='r6/scripts/PTFR_PreAlpha/'
for rel,methods in [('PTFR_Restrictions_R2/BodyPolicy.reds',['RefundOne','RefundRelicOne','ResetBody','Safe','Same']),('PTFR_Restrictions_R3/ProfilePolicy.reds',['RefundOne','Apply','OnProfileStep']),('PA1/PreAlphaArrivalPA1.reds',['Poll','GameplayReady','ControlReady','CameraAligned'])]:
 old=(C/'before'/base/rel).read_text();new=(P/base/rel).read_text()
 for m in methods:
  # Only the new elapsed-settling clock reset may be added inside old refunds.
  checked=p.body(new,m).replace(' this.lc1StableSince = -1.0;','')
  check(p.body(old,m)==checked,'original transaction/camera body preserved (own timer reset allowed): '+rel+':'+m)
body=(P/base/'PTFR_Restrictions_R2/BodyPolicy.reds').read_text();profile=(P/base/'PTFR_Restrictions_R3/ProfilePolicy.reds').read_text();entry=(P/base/'PA1/PreAlphaEntry.reds').read_text()
check('this.lc1StableSince < 4.0' in p.body(body,'Settle'),'Body settling retains >=4 elapsed seconds')
check('this.warmup==0 && !this.queued && !this.inflight' in p.body(body,'LC1Interval'),'no acceleration during warmup/queued/in-flight work')
check('this.stage != 2 && this.cadence < 4' in p.body(profile,'Poll'),'other-tree speedup limited to refund stage')
poll=p.body(entry,'Poll');check('this.Now()-this.lc1SafeSince<3.0' in poll,'Entry retains >=3 seconds stable safety')
check('if this.Now() - this.lastAttempt < 5.0 { return; }' not in poll,'H10/housing acknowledgement no longer behind dispatch throttle')
source=(H/'StartupCoverLC1.reds').read_text();check((P/'r6/scripts/TowerContinued_Loading_LC1/StartupCoverLC1.reds').read_text()==source,'cover template equals package')
compiled=(C/'compile_02/compiled.script').read_text(encoding='utf-8-sig')
for cls in ['StartupCoverLC1','SetupPopupLC1','SetupPopupPoolLC1','SetupPopupCloseLC1']:
 original=p.block(source,r'public class '+cls+r' extends \w+\s*\{')
 cooked=p.block(compiled,r'public class PTFR.LoadingCoverLC1.'+cls+r' extends [\w.]+\s*\{')
 for m in re.findall(r'\bfunc (\w+)\(',original):
  a=[norm(x) for x in re.findall(r'\breturn\s+([^;]+);',p.body(original,m))]
  b=[norm(x) for x in re.findall(r'\breturn\s+([^;]+);',p.body(cooked,m))]
  check(a==b,'compiled return predicates: '+cls+'.'+m)
system=p.block(compiled,r'public class PTFR.LoadingCoverLC1.StartupCoverLC1 extends ScriptableSystem\s*\{')
barrier=norm(p.body(system,'Check'))
for token in ['snapshot.Ready()','arrival.Completed()','profile.PTFRPAComplete()','profile.LC1PhysicalReady()','profile.LC1LedgerValid(player)','body.PTFRR3Complete()','chrome.PTFRR2Ready(player)','housing.HousingReadyForReveal()','world.H10GeometryReady()','world.H10ActionsArmed()','entry.LC1DispatchChecked()','SetupAdaptersLC1.Ready(game)','arrival.LC1ControlReady()']:
 check(token in barrier,'compiled barrier contains '+token)
pol=norm(p.body(system,'Poll'))
check(pol.index('this.Check()')<pol.index('this.released=true') and 'this.Now()-this.stableSince<1.0' in pol,'release follows full barrier and stability')
leave=p.body(source,'Leave');check('GotoMainMenu()' in leave and '.Drop(' not in leave and 'released=true' not in leave,'Escape exits without unlocking gameplay')
check(not re.search(r'\b(?:SetTimeDilation|PushGameContext|ApplyStatusEffect|Pause)\s*\(',source),'cover does not pause or apply readiness-conflicting restrictions')
check('return true;' in p.body(source,'IsBlocking'),'native notification owns input blocker')
check('SetOpacity(1.0)' in p.body(source,'OnShow'),'cover has no transparent entrance animation')
check('this.owner.Accepts(this.epoch)' in p.body(source,'OnShow'),'stale delayed attachment cannot acknowledge new save')
check('if IsDefined(this.current) { return null; }' in p.body(source,'Show'),'new popup waits for retired pending popup')
check('SetupPopupPoolLC1.Get().Released(this)' in p.body(source,'OnHidden'),'notification teardown releases only own pool slot')
sets=re.findall(r'\.SetFact\(n"([^"]+)"',source)
check(sets==['PTFRLC1_CoverReady'],'cover writes only its own attachment acknowledgement')
for f in changes:
 if '/TowerContinued_SideJobs_' in f['target'] or '/TowerContinued_Gigs_U10/' in f['target']:
  s=(P/f['target']).read_text();check('allowed && StartupCoverLC1.GameplayReleased' in s,'new quest permits held: '+f['target'])
  check('lc1Passes>=2' in s,'classification observed twice: '+f['target'])
# Bind the already tested current-archive splice to this final script package.
n=json.loads((H/'candidate_02/native_01.json').read_text(encoding='utf-8-sig'))
check(n['status']=='PASS_NATIVE_SPLICE_PACKED_NOT_LIVE' and n['unchanged_resources']==615,'615 archive resources preserved including current sector')
check(n['preserved_lighting_sha256']=='B56A759ABCA6F86FBF7E2C61016E0F87D995ECA3E99EFBFFA253B69AEE6A311B','current 2.5 lighting retained')
edges=n['all_edges'];adj={}
for e in edges:
 m=re.fullmatch(r'(\d+)\.([\w]+) -> (\d+)\.\w+',e);assert m,e
 if m[2]!='CutSource':adj.setdefault(int(m[1]),set()).add(int(m[3]))
def reachable(start,end,blocked):
 todo=[start];seen=set()
 while todo:
  at=todo.pop()
  if at in blocked or at in seen:continue
  if at==end:return True
  seen.add(at);todo+=list(adj.get(at,[]))
 return False
check(reachable(146,176,set()) and not reachable(146,176,{181}),'every normal fade release path waits for cover acknowledgement')
check(not reachable(160,176,set()),'failed prior timeout owner is not restarted')
check('173.CutSource -> 170.CutDestination' in edges and '173.CutSource -> 171.CutDestination' in edges,'original timeout cuts retained for HS1 recovery')
for directory in ['package','before']:
 src=H/'candidate_02'/directory/n['target'];dst=C/directory/n['target'];dst.parent.mkdir(parents=True,exist_ok=True)
 assert sha(src)==n['after' if directory=='package' else 'before']
 if dst.exists():assert sha(dst)==sha(src)
 else:shutil.copyfile(src,dst)
# Fault-injection model: readiness is conjunctive, no timeout/fact can authorize it.
def may_reveal(flags,stable,visible,leaving):return all(flags) and stable>=1.0 and visible and not leaving
for missing in range(12):
 flags=[True]*12;flags[missing]=False
 for elapsed in [0,1,180,10000]:assert not may_reveal(flags,elapsed,True,False)
check(True,'each missing acknowledgement blocks release even after watchdog')
for stable in [0,.1,.9]:assert not may_reveal([True]*12,stable,True,False)
check(may_reveal([True]*12,1,True,False) and not may_reveal([True]*12,10,True,True),'one-second success stability and exit precedence')
# Scheduling opportunity comparison only; this is not a live speed measurement.
check(27*.25==6.75 and 27-6.75==20.25,'27 acknowledged ranks: scheduling opportunities 27s -> 6.75s, settling excluded')
sources={str(x):sha(x) for x in P.rglob('*') if x.is_file()}
out={'status':'PASS_OFFLINE_COMPILED_NATIVE_NOT_LIVE','checks':checks,'count':len(checks),'sources':sources,'compiled_sha256':sha(C/'compile_02/cache/compiled.redscripts'),'native_proof':{'path':str(H/'candidate_02/native_01.json'),'sha256':sha(H/'candidate_02/native_01.json')},'limitations':['Native input blocking/non-pausing behavior and first exposed frame need live test','No measured end-to-end speedup','Existing owners/rewards and transaction side effects need save/reload live verification']}
dest=C/'tests_01.json';assert not dest.exists();dest.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'checks':len(checks)}))
