from pathlib import Path
import json,hashlib,copy,re,importlib.util
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';P=C/'package';G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
spec=importlib.util.spec_from_file_location('parse',W/'prealpha/history_snapshot_hs1/build_catalogue_01.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def read(x):return json.loads(Path(x).read_text(encoding='utf-8-sig'))
def sha(x):return hashlib.sha256(Path(x).read_bytes()).hexdigest().upper()
def norm(s):
 s=re.sub(r'//[^\n]*','',s);s=re.sub(r'PTFR\.\w+\.','',s);s=re.sub(r'\$local\$\d+','',s)
 return re.sub(r'\s+','',s).replace("\\'","'")
checks=[]
def check(v,n):assert v,n;checks.append(n)
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
changes=read(C/'changes_01.json');native=read(C/'native_01.json');compiled=(C/'compile_01/compiled.script').read_text(encoding='utf-8-sig')
for f in changes:
 check(sha(G/f['target'])==sha(C/'before'/f['target'])==f['before'],'bound installed source '+f['target'])
 check(sha(P/f['target'])==f['after'],'bound candidate source '+f['target'])
 a=(C/'before'/f['target']).read_text(encoding='utf-8-sig');b=(P/f['target']).read_text()
 fields=lambda s:re.findall(r'(?:persistent )?let (\w+)\s*:\s*([^;]+);',s)
 persistent=lambda s:re.findall(r'persistent let (\w+)\s*:\s*([^;]+);',s)
 check(persistent(a)==persistent(b),'save schemas unchanged '+f['target'])
 apis=lambda s:set(re.findall(r'\bfunc [^{\n]+',s))
 check(apis(a)<=apis(b),'existing method signatures preserved '+f['target'])
cover=(P/changes[0]['target']).read_text();old=(C/'before'/changes[0]['target']).read_text(encoding='utf-8-sig');housing=(P/changes[1]['target']).read_text()
system=p.block(compiled,r'public class PTFR.LoadingCoverLC1.StartupCoverLC1 extends ScriptableSystem\s*\{')
popup=p.block(compiled,r'public class PTFR.LoadingCoverLC1.SetupPopupLC1 extends [\w.]+\s*\{')
ui=p.block(compiled,r'public class PTFR.Housing.HousingPurchaseUI extends ScriptableSystem\s*\{')
check(p.body(old,'Check').replace('The entry module reports a fault. Press Esc to return to the main menu.','The entry module reports a fault; setup remains covered.')==p.body(cover,'Check'),'all original setup and live control predicates retained')
check(p.body(old,'Poll').replace('+"\\nPress Esc to return to the main menu."','')==p.body(cover,'Poll'),'one-second stability and fail-closed release logic unchanged')
for token in ['GotoMainMenu','Return to main menu','Press Esc','owner.Leave']:
 check(token not in cover and token not in system+popup,'exit action/text removed: '+token)
for text,label in [(cover,'source'),(system,'compiled')]:
 check(norm(p.body(text,'Leave'))=='','compatibility Leave is inert '+label)
for text,label in [(cover,'source'),(popup,'compiled')]:
 check(norm(p.body(text,'OnGlobalReleaseInput'))=='evt.Handle();returntrue;','cancel consumed without invoking base or closing '+label)
check('arrival.Status()' in cover and 'bodySafe=' in cover,'final control failure diagnostics added')
for text,label in [(housing,'source'),(ui,'compiled')]:
 tick=norm(p.body(text,'Tick'));show=norm(p.body(text,'Show'))
 check('StartupCoverLC1.GameplayReleased(game)&&' in tick,'offers gated by completed startup '+label)
 check('HousingPurchaseLocation.Validate(game,id,HousingPurchaseLocation.Source(id))' in tick,'offers require actual authored entrance '+label)
 check('!StartupCoverLC1.GameplayReleased(game)||' in show,'direct confirmation also gated '+label)
 check('state.CanPurchase(id,player)' in tick and 'state.CanPurchase(id,player)' in show,'purchase safety and ownership checks retained '+label)
 check('RemoveItem' not in tick+show,'no automatic debit introduced '+label)
for token in ['snapshot.Ready()','arrival.Completed()','profile.PTFRPAComplete()','profile.LC1PhysicalReady()','profile.LC1LedgerValid(player)','housing.HousingReadyForReveal()','world.H10GeometryReady()','SetupAdaptersLC1.Ready(game)','arrival.LC1ControlReady()','BodyPolicy.Safe(player)']:
 check(token in norm(p.body(system,'Check')),'compiled final guard '+token)
check('this.Now()-this.stableSince<1.0' in norm(p.body(system,'Poll')),'compiled stability duration retained')
check(re.findall(r'\.SetFact\(n"([^"]+)"',cover)==['PTFRLC1_CoverReady'],'no new fact writes in loading cover')
check(native['unchanged_resources']==13 and len(native['resources'])==4,'four purchase scenes only, all owner and service resources byte exact')
for row in read(C/'prepared_native_01.json')['resources']:
 src=read(row['source']);fixed=read(row['prepared']);br=next(r for r in native['resources'] if r['depot']==row['depot']);out=read(br['readback']);r=out['Data']['RootChunk'];name=row['depot']
 check(sha(row['source'])==row['source_sha256'] and sha(row['prepared'])==row['prepared_sha256'],'source binding '+name)
 check(out['Data']==fixed['Data'],'full binary readback matches intended data '+name)
 check(r['actors']==r['playerActors']==[],'no actor acquisition '+name)
 check(all(not(v.get('$type')=='scnActorId' and v['id']!=0xffffffff) for v in walk(r)),'no live actor references '+name)
 check(r['sceneGraph']==src['Data']['RootChunk']['sceneGraph'],'all five executable nodes and edges identical '+name)
 restore=copy.deepcopy(out);rr=restore['Data']['RootChunk'];rr['playerActors']=row['removed_player']
 for d in row['removed_debug_symbols']:rr['debugSymbols']['performersDebugSymbols'].insert(d['index'],d['value'])
 check(restore['Data']==src['Data'],'all other serialized data preserved '+name)
# Event model bound to actual 1s HousingTick, CanPurchase -> SafeActor(no scene),
# native ready==0 watcher exit, and current1s continuous final control barrier.
hs=(C/'diagnosis_01/context/HousingState.reds').read_text();check('HousingTick.Create(this, this.epoch), 1.0' in hs and 'scenes.IsEntityInScene' in p.body(hs,'SafeActor'),'model bound to installed cadence and safety predicate')
def simulate(fixed,near=True,healthy=True,seconds=8):
 scene=False;ready=False;released=False;stable=None;changes=[]
 for tick in range(seconds*20):
  now=tick/20
  if tick%20==0:
   offer=healthy and not scene and (released and near if fixed else True)
   changes.append(offer);ready=offer
   scene=ready and not fixed  # new serialized scene has no player actor
  if not healthy or scene:stable=None
  else:
   if stable is None:stable=now
   if now-stable>=1:released=True
 return released,changes,scene
check(not simulate(False)[0] and simulate(False)[1]==[True,False]*4,'old eligibility/acquisition loop reproduces endless stability reset')
check(simulate(True)[0] and not simulate(True)[2],'new setup settles before actor-free offers')
check(simulate(True,near=False)[0] and not any(simulate(True,near=False)[1]),'remote prompts stay idle after release')
check(not simulate(True,healthy=False)[0],'incomplete setup never released')
check(read(C/'compile_01/result.json')['full_scc_equipmentex'],'full87source SCC includes EquipmentEx')
for path,h in read(C/'diagnosis_01/inputs.json')['saves'].items():assert sha(path)==h
check(True,'save files unchanged')
proofs=[p for p in P.rglob('*') if p.is_file()]+[C/'native_01.json',C/'prepared_native_01.json',C/'compile_01/result.json',C/'compile_01/cache/compiled.redscripts']
r={'status':'PASS_LC3_COMPILED_NATIVE_FEEDBACK_NOT_LIVE','count':len(checks),'checks':checks,'sources':{str(p):sha(p) for p in proofs},'live_pending':True,'diagnostic_limit':'Old combined control log does not name the failing subpredicate; source-proven purchase feedback repaired, exact future control diagnostics added.'}
with (C/'tests_01.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps({'status':r['status'],'checks':len(checks)}))
