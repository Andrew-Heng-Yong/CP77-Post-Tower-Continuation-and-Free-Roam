"""Serialized waiter semantics, current native catalogue bindings, compiled barrier."""
from pathlib import Path
import json,re,hashlib,importlib.util,zlib
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';P=C/'package'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
sp=importlib.util.spec_from_file_location('parse',W/'prealpha/history_snapshot_hs1/build_catalogue_01.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p)
def sha(x):return hashlib.sha256(Path(x).read_bytes()).hexdigest().upper()
def read(x):return json.loads(Path(x).read_text(encoding='utf-8-sig'))
checks=[]
def check(v,n):assert v,n;checks.append(n)
def norm(s):
 s=re.sub(r'//[^\n]*','',s);s=re.sub(r'PTFR\.\w+\.','',s);s=re.sub(r'\$local\$\d+','',s)
 s=re.sub(r'(\d+)[uU][lL]?\b',r'\1ul',s)
 return re.sub(r'\s+','',s).replace("\\'","'").replace('(s.released&&!s.leaving)','s.released&&!s.leaving')
def tid(s):return len(s.encode())*2**32+zlib.crc32(s.encode())
changes=read(C/'changes_01.json')
for f in changes:
 check(sha(G/f['target'])==f['before'],'installed baseline: '+f['target'])
 check(sha(C/'before'/f['target'])==f['before'],'backup source: '+f['target'])
 if f['target'].endswith('.reds'):
  old=(C/'before'/f['target']).read_text(encoding='utf-8-sig');new=(P/f['target']).read_text()
  fields=lambda s:re.findall(r'persistent let (\w+)\s*:\s*([^;]+);',s)
  check(fields(old)==fields(new),'saved field identities retained: '+f['target'])
  methods=lambda s:set(norm(m) for m in re.findall(r'(?:public |private |protected )?(?:final )?(?:static )?(?:cb )?func [^{\n]+',s))
  check(methods(old)<=methods(new),'existing APIs retained: '+f['target'])
for f in read(W/'prealpha/loading_cover_lc1/candidate_04/install_manifest_01.json')['files']:
 check(sha(G/f['target'])==f['after'],'LC1 installed source/package bound: '+f['target'])
# Every old node except 181 is byte-payload equivalent after round trip.
def nodes(path):return {n['Data']['id']:n['Data'] for n in read(path)['Data']['RootChunk']['graph']['Data']['nodes']}
old=nodes(W/'prealpha/loading_cover_lc1/candidate_02/native_phase.json');new=nodes(C/'native_phase.json')
check(old.keys()==new.keys(),'native owner/node IDs unchanged')
def without_connections(v):
 if isinstance(v,dict):return {k:without_connections(x) for k,x in v.items() if k not in ['HandleId','HandleRefId','connections']}
 if isinstance(v,list):return [without_connections(x) for x in v]
 return v
for id in old:
 if id!=181:check(without_connections(old[id])==without_connections(new[id]),'native node payload retained: '+str(id))
check(old[181]['$type']=='questConditionNodeDefinition' and new[181]['$type']=='questPauseConditionNodeDefinition','regression: one-shot branch replaced by native waiting condition')
check(without_connections(old[181]['condition'])==without_connections(new[181]['condition']),'exact owned CoverReady==1 predicate retained')
check(new[180]['type']['Data']['factName']=='PTFRLC1_CoverReady' and new[180]['type']['Data']['value']==0,'native reset immediately precedes waiter')
n=read(C/'native_01.json');edges=n['all_edges']
check(n['removed_edges']==['181.True -> 176.In'] and n['added_edges']==['181.Out -> 176.In'],'only success socket rerouted; no ending or teleport replay')
check(n['unchanged_resources']==615 and n['preserved_lighting_sha256']=='B56A759ABCA6F86FBF7E2C61016E0F87D995ECA3E99EFBFFA253B69AEE6A311B','615 unrelated resources and current lighting preserved')
check(not any(x.startswith('160.') for x in edges),'old failed preparation owner remains cut')
for e in ['146.Out -> 180.In','180.Out -> 181.In','181.Out -> 176.In','176.Out -> 177.In','177.Out -> 178.In','178.Out -> 179.In']:
 check(e in edges,'native acquire/fade/Tier1 order: '+e)
# Interpret actual serialized condition-node kinds for late acknowledgements.
def simulate(node,events):
 waiting=True;exits=[]
 for event,value in events:
  if not waiting:continue
  if event=='cut':waiting=False;continue
  if node['$type']=='questConditionNodeDefinition':
   if event=='enter':exits.append('True' if value==1 else 'False');waiting=False
  elif event in ['enter','fact'] and value==1:exits.append('Out');waiting=False
 return exits
check(simulate(old[181],[('enter',0),('fact',1)])==['False'],'old graph reproduces discarded late acknowledgement')
for events,expected in [([('enter',0),('fact',0)],[]),([('enter',0),('fact',1)],['Out']),([('enter',1),('fact',1)],['Out']),([('enter',0),('cut',0),('fact',1)],[])]:
 check(simulate(new[181],events)==expected,'waiter event sequence: '+str(events))
# Verify stock data, not just a changed count constant.
audit=read(C/'diagnosis_01/perks_current.json');rows={r['id']:r for r in audit['records']};named={r['name']:r for r in rows.values() if r['name']}
for d in audit['database_sources']:check(sha(d['path'])==d['sha256'],'current native database bound: '+d['path'])
source=(P/'r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R3/ProfileDefinition.generated.reds').read_text()
compiled=(C/'compile_02/compiled.script').read_text(encoding='utf-8-sig')
cls=p.block(compiled,r'public abstract class PTFR.RestrictionsR3.ProfileCatalogue extends IScriptable\s*\{')
prior=(C/'before/r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R3/ProfileDefinition.generated.reds').read_text()
for method in ['ID','Revision','Fingerprint','Health','CyberwareAllowed','AllowedPerks','OtherBlocked','PreviousStrictBlocked']:
 check(p.body(prior,method)==p.body(source,method),'selected profile policy unchanged: '+method)
for text,label in [(source,'source'),(cls,'compiled')]:
 valid=p.body(text,'Valid');check('194' in valid and '!= 189' not in valid,'194 enum guard '+label)
 for category in ['Body','Espionage','Cool','Tech','Intelligence','Reflexes']:
  tree={'Tech':'TechnicalAbility'}.get(category,category);count=len(named['NewPerks.'+tree+'AttributeData']['fields']['perks'])
  check(re.search(r'tree'+category+r'(?:\$local\$\d+)?\.GetPerksCount\(\)\s*!=\s*'+str(count)+r'\b',valid) is not None,'actual tree roster '+label+': '+category)
 names=re.findall(r'(?:private|public) (?:final )?static func ((?:R\d+|LC2NewCool\d+))\(',text)
 check(len(names)==193,'all 193 exposed perk checks '+label)
 for method in names:
  b=p.body(text,method);bn=norm(b)
  name=re.search(r'GetNewPerkRecord\(gamedataNewPerkType\.(\w+)\)',b)[1];r=named['NewPerks.'+name];f=r['fields']
  check(not r['missing'] and r['id']==tid('NewPerks.'+name),'record identity '+label+': '+name)
  attr=re.search(r'Attribute\(\)\.GetID\(\)\s*!=\s*t"([^"]+)"',b)[1];assert f['attribute']==tid(attr)
  count=int(re.search(r'GetLevelsCount\(\)\s*!=\s*(\d+)',b)[1]);assert count==len(f['levels'])
  threshold=int(re.search(r'RequiredAttributePoints\(\)\s*!=\s*(\d+)',b)[1]);assert threshold==int(rows[f['tier']]['fields']['requiredAttributePoints'])
  deps=re.findall(r'deps(?:\$local\$\d+)?\[\d+\]\.GetID\(\)\s*!=\s*t"([^"]+)"',b);assert list(map(tid,deps))==f['requiresPerks']
  depcount=int(re.search(r'ArraySize\(deps(?:\$local\$\d+)?\)\s*!=\s*(\d+)',b)[1]);assert depcount==len(deps)
  levels=[int(x) for x in re.findall(r'TDBID.ToNumber\(levels(?:\$local\$\d+)?\[\d+\]\)\s*!=\s*(\d+)(?:u[lL]|[uU])',b)];assert levels==f['levels'],(label,method,levels,f['levels'],b)
  for i,l in enumerate(levels):
   row=rows[l]
   if row['missing']:assert l==91068214685 and f'ifIsDefined(record.GetLevelsItem({i}))' in bn
   else:
    assert f'!IsDefined(record.GetLevelsItem({i}))' in bn
    assert f')!={row["fields"]["dataPackage"]}ul' in bn,(label,method,row['fields']['dataPackage'],bn)
  check(True,'ranks/threshold/dependencies/level packages '+label+': '+name)
for name in ['BodyCatalogue','RelicCatalogue']:
 rel='r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R2/'+name+'.reds'
 a=(C/'before'/rel).read_text();b=(P/rel).read_text()
 check(a==b.replace('Count) != 194','Count) != 189').replace('all 194 current enum records','all 189 enum records'),'all '+name+' validation retained except audited enum size')
# Compiled barrier preserves every readiness conjunct and delayed reveal.
cover=(H/'StartupCoverLC1.reds').read_text();check(cover==(P/'r6/scripts/TowerContinued_Loading_LC1/StartupCoverLC1.reds').read_text(),'cover package matches template')
for name in ['StartupCoverLC1','SetupPopupLC1','SetupPopupPoolLC1','SetupPopupCloseLC1']:
 a=p.block(cover,r'public class '+name+r' extends \w+\s*\{');b=p.block(compiled,r'public class PTFR.LoadingCoverLC1.'+name+r' extends [\w.]+\s*\{')
 for method in re.findall(r'\bfunc (\w+)\(',a):
  check([norm(x) for x in re.findall(r'\breturn\s+([^;]+);',p.body(a,method))]==[norm(x) for x in re.findall(r'\breturn\s+([^;]+);',p.body(b,method))],'compiled return predicate '+name+'.'+method)
system=p.block(compiled,r'public class PTFR.LoadingCoverLC1.StartupCoverLC1 extends ScriptableSystem\s*\{');barrier=norm(p.body(system,'Check'))
for token in ['snapshot.Ready()','arrival.Completed()','profile.PTFRPAComplete()','profile.LC1PhysicalReady()','profile.LC1LedgerValid(player)','body.PTFRR3Complete()','chrome.PTFRR2Ready(player)','housing.HousingReadyForReveal()','world.H10GeometryReady()','world.H10ActionsArmed()','entry.LC1DispatchChecked()','SetupAdaptersLC1.Ready(game)','arrival.LC1ControlReady()','BodyPolicy.Safe(player)','entry.SnapshotInitializationHealthy()']:
 check(token in barrier,'compiled release guard '+token)
pol=norm(p.body(system,'Poll'))
check('this.Now()-this.attachedAt' not in pol and 'this.rendered&&' in pol,'native cover ack no longer depends on simulation elapsed time')
check(pol.index('this.Check()')<pol.index('this.completedSteps=12')<pol.index('this.released=true') and 'this.Now()-this.stableSince<1.0' in pol,'100 percent and reveal require full barrier plus stable simulation second')
check('this.EngineNow()-this.engineStarted>=120.0' in pol and 'this.Drop()' not in pol[pol.index('if!this.Check()'):pol.index('ifthis.stableSince')],'long-wait message cannot release gameplay')
check(re.findall(r'\.SetFact\(n"([^"]+)"',cover)==['PTFRLC1_CoverReady'],'only owned cover acknowledgement is written')
check('GotoMainMenu()' in p.body(cover,'Leave') and '.Drop(' not in p.body(cover,'Leave'),'Escape returns to menu while keeping cover')
check('return true;' in p.body(cover,'IsBlocking') and not re.search(r'\b(?:SetTimeDilation|PushGameContext|ApplyStatusEffect|Pause)\s*\(',cover),'input blocker retained without adding a pause/status restriction')
check('this.Accepts(epoch) && this.visible' in p.body(cover,'CoverFrame'),'old save UI callback cannot acknowledge new save')
check('Stop()' in p.body(cover,'OnHide'),'UI animation cleaned up on detach')
check('count*100/total' in p.body(cover,'UpdateProgress') and 'Now(' not in p.body(cover,'UpdateProgress'),'progress derives from completed checks, never elapsed time')
check('5.0' in p.body(cover,'Heartbeat') and 'engineElapsed=' in cover,'periodic engine/simulation diagnostics')
diag=read(C/'diagnosis_01/inputs.json')
for path,h in diag['saves'].items():assert sha(path)==h
check(True,'all '+str(len(diag['saves']))+' original save files unchanged')
out={'status':'PASS_OFFLINE_COMPILED_NATIVE_NOT_LIVE','count':len(checks),'checks':checks,'sources':{str(x):sha(x) for x in P.rglob('*') if x.is_file()},'compiled_sha256':sha(C/'compile_02/cache/compiled.redscripts'),'limitations':['No game launched; UI input/first frame and full setup require live test','Existing failed transactions are not reset','Old 189-entry saved ledgers are not silently reindexed','No measured end-to-end speedup']}
with (C/'tests_01.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'status':out['status'],'checks':len(checks)}))
