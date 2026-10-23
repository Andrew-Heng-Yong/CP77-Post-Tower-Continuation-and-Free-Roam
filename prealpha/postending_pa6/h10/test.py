"""PA6 H10 permission timing: bounded source/native-contract tests, not engine simulation."""
from pathlib import Path
import hashlib, json, math, re

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'research/postending_pa6/h10'
SOURCE = ROOT / 'prealpha/postending_pa6/h10/source/RestorationBaseline.reds'
BASE = ROOT / 'prealpha/postending_pa5/h10/source/RestorationBaseline.reds'
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
LIVE = ROOT / 'research/postending_pa6/live_20261014T011540242Z'
checks = []
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def check(name, ok):
    checks.append({'name': name, 'pass': bool(ok)})
    assert ok, name
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x, list):
        for v in x: yield from walk(v)

assert not (OUT / 'tests.json').exists(), 'Use fresh evidence destination'
old, new = BASE.read_text().rstrip(), SOURCE.read_text().rstrip()
check('PA5 baseline pinned', sha(BASE) == '416BB22FB921BDD6DA3DB4D9887378BA6887BDD7F19D9CCB782F5416023789EB')
check('Installed baseline still PA5', sha(GAME / 'r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds') == sha(BASE))
helper_re = r'  // PA6: permission to use the EXISTING native interaction owner,.*?(?=  public func H10Status)'
timing_re = r'    // Arm the existing actions while the post-ending player is safely offsite,.*?    let h10Actions = [^\n]+;\n'
check('Exactly one new helper', len(re.findall(helper_re, new, re.S)) == 1)
check('Exactly one permission timing expansion', len(re.findall(timing_re, new, re.S)) == 1)
reversed_text = re.sub(helper_re, '', new, flags=re.S)
reversed_text = re.sub(timing_re, '', reversed_text, flags=re.S)
reversed_text = reversed_text.replace('if h10Actions &&', 'if h10 &&').replace('H10 PA6:', 'H10 PA5:')
reversed_text = reversed_text.replace('      " actionsArmed=" + ToString(this.H10ActionsArmed()) +\n', '')
reversed_text = reversed_text.replace('Armed is permission only; native apartment trigger controls prompts. Native ownership is not rendered-geometry proof;', 'Native owner acknowledgements are not rendered-geometry proof;')
check('Exact normalized delta; unrelated baseline logic unchanged', reversed_text == old)
check('All write statements remain byte-identical', re.findall(r'this\.Set\([^\n]+', new) == re.findall(r'this\.Set\([^\n]+', old))
helper = re.search(helper_re, new, re.S).group()
check('Getter has no mutations', not re.search(r'SetFact|this\.Set\(|Enable\(|Start\(', helper))
check('Getter distinguishes permission from active scene', all(s in helper for s in ['_Ready") == 1','_Enabled") == 1','_Interrupted") == 0']))
check('No new action owner, phase registration or resets', all(s not in new for s in ['PTFRPA6_', 'RegisterQuest', 'PTFRB0H10P_Enabled",0']))
check('No preparation circularity', all(s not in helper for s in ['PTFRPA2_Prepared','PTFRPA2_Finished','PTFRPA2_Reveal']))
check('Offsite arm requires safe tier and geometry acknowledgement', 'h10 || (high == 1 && tier == 1 && this.H10OffsiteReady(q,p) && this.H10GeometryReady())' in new)

block = re.search(r'// H10 interactions\s+if h10Actions &&(.*?)this.Set\(q,n"PTFRB0H10P_Enabled",1\);', new, re.S).group(1)
guards = dict((k,int(v)) for k,v in re.findall(r'q.GetFact\(n"([^"]+)"\) == (\d+)', block))
check('Every original action fact guard retained', guards == dict((k,int(v)) for k,v in re.findall(r'q.GetFact\(n"([^"]+)"\) == (\d+)', re.search(r'// H10 interactions\s+if h10 &&(.*?)this.Set\(q,n"PTFRB0H10P_Enabled",1\);',old,re.S).group(1))))
def allows(facts, near=False, offsite=True, geom=True, high=1, tier=1, safe=True):
    return safe and (near or high == tier == 1 and offsite and geom) and all(facts.get(k,0)==v for k,v in guards.items())
check('Street safe owner permission admitted', allows(guards))
check('Prior near-apartment permission retained', allows(guards, near=True, offsite=False))
for fact, value in guards.items():
    for mutation in [value+1, value-1]:
        bad = dict(guards); bad[fact] = mutation
        check('Retain action guard '+fact+'='+str(mutation), not allows(bad))
for kw in [{'safe':False},{'geom':False},{'offsite':False},{'high':2},{'tier':2}]:
    check('Unsafe new offsite case refused '+str(kw), not allows(guards, **kw))
facts = dict(guards)
check('Enabled once', allows(facts)); facts['PTFRB0H10P_Enabled']=1
check('Saved enabled owner not rearmed', not allows(facts))
facts['PTFRB0H10P_Enabled']=0; facts['PTFRB0H10P_Active']=1
check('Existing scene not started again', not allows(facts))

val = ROOT / 'research/b0_h10_persistent/validation'
owner = read(val / 'h10_owner.questphase.json')['Data']['RootChunk']
nodes = {n['Data']['id']:n['Data'] for n in owner['graph']['Data']['nodes']}
conditions = list(walk(nodes[2]['condition']))
triggers = [x for x in conditions if x.get('$type') == 'questTriggerCondition']
phones = [x for x in conditions if x.get('$type') == 'questPhoneCallPhase_ConditionType']
check('Native gate before scene has exact apartment IsInside', len(triggers)==1 and triggers[0]['type']=='IsInside' and triggers[0]['triggerAreaRef']['$value']=='#mq000_tr_vs_apartment' and triggers[0]['isPlayerActivator']==1)
check('Native gate before scene refuses incoming call', len(phones)==1 and phones[0]['callPhase']=='IncomingCall' and phones[0]['inverted']==1)
check('Native AND includes enabled1', nodes[2]['condition']['Data']['operation']=='AND' and any(x.get('factName')=='PTFRB0H10P_Enabled' and x.get('value')==1 for x in conditions))
check('Native active only follows gated branch', nodes[3]['type']['Data']['factName']=='PTFRB0H10P_Active' and nodes[3]['type']['Data']['value']==1 and nodes[4]['sceneFile']['DepotPath']['$value']=='towercontinued\\b0_h10_persistent\\h10_interactions.scene')
check('Owner interruption retained', nodes[8]['type']['Data']['factName']=='PTFRB0H10P_Interrupted' and nodes[8]['type']['Data']['value']==1)
edges=(ROOT/'research/b0_h10_persistent/graph_analysis/edges.csv').read_text()
check('Native node2→3→4 scene ordering preserved', ',14,2,questPauseConditionNodeDefinition,Out,79,3,questFactsDBManagerNodeDefinition,In' in edges and ',79,3,questFactsDBManagerNodeDefinition,Out,85,4,questSceneNodeDefinition,in' in edges)
compare = read(ROOT/'research/post_ending_regression_20261013/h10_package_compare.json')
check('Installed archive remains byte-identical to 24-member audit', sha(GAME/'archive/pc/mod/TowerContinued_PreAlpha.archive') == compare['active_archive_sha256'])
for member in compare['members']:
    if 'b0_h10_persistent' in member['depot']:
        raw = ROOT/'archive/b0_h10_persistent/source'/Path(member['depot'].replace('\\','/'))
        check('Compiled H10 member still exact '+raw.name, sha(raw)==member['active_sha256']==member['baseline_sha256'])
scene = read(val/'h10_interactions.scene.json')['Data']['RootChunk']
stock = read(ROOT/'research/b0_h10_generalization/extracted_interactions/json/base/quest/minor_quests/mq000/scenes/mq000_01_apartment.scene.json')['Data']['RootChunk']
check('Complete scene resource reference table identical to stock', scene['resouresReferences']==stock['resouresReferences'])
lips = scene['resouresReferences']['lipsyncAnimSets']
paths = [x['asyncRefLipsyncAnimSet']['DepotPath']['$value'] for x in lips]
indices = [x['id'] for x in walk(scene) if x.get('$type')=='scnLipsyncAnimSetSRRefId']
check('One H10 lipsync path, no Rogue duplicate-table shape', len(paths)==len(set(paths))==1)
check('All H10 lipsync indices in bounds or native sentinel', all(i == 4294967295 or 0<=i<len(paths) for i in indices))
check('H10 player index0 exact native V lipsync', scene['playerActors'][0]['lipsyncAnimSet']['id']==0 and paths[0].endswith('mq000_01_apartment\\v.anims'))

log=(LIVE/'scripting.log').read_text(errors='replace')
h10_lines=[s for s in log.splitlines() if '[PA5 restoration] H10 PA5:' in s]
check('Frozen latest logs confirm geometry acknowledged/actions not armed', any('geometryAcknowledged=true' in s and 'actions Ready/Enabled/Active/Interrupted=1/0/0/0' in s for s in h10_lines))
save=read(OUT/'autosave0_facts.json')
check('Auto0 matches frozen crash attached save byte-for-byte', save['sha256']==sha(LIVE/'crash/attch/sav.dat'))
check('Offline save source unchanged', save['source_unchanged'])
check('Offline readiness1 but no serialized actions enable', save['facts']['PTFRB0H10P_Ready'][0]['value']==1 and not save['facts']['PTFRB0H10P_Enabled'])
report={'status':'PASS_SOURCE_AND_NATIVE_CONTRACT_NOT_LIVE','source':str(SOURCE),'source_sha256':sha(SOURCE),'baseline_sha256':sha(BASE),'check_count':len(checks),'checks':checks,'native_lipsync':{'path_count':len(paths),'paths':paths,'indices':indices,'stock_reference_table_equal':True},'evidence':{'frozen_log':str(LIVE/'scripting.log'),'frozen_log_sha256':sha(LIVE/'scripting.log'),'save_report_sha256':sha(OUT/'autosave0_facts.json'),'compiled_owner_sha256':'3749424884D739DEFDD6F45EC03AC1C49CBAD10E47B56C9A3F26272B857984EF','compiled_scene_sha256':'2A97850D2470815331949A05D44BE2F1A0723A3EA959EBB13047D58AFF3708F2'},'limits':['Latest logged positions cover street and elevator, not the later apartment approach. Missing prompt root cause not completely measured.','Armed is permission only, not active/prompt proof. Existing native trigger and phone guards still govern startup.','No graph/scene/resource/index/entitlement/geometry changes. No owner reset.','Full integrated engine compilation and runtime acceptance are parent-owned.'],'runtime_writes':0,'save_writes':0}
(OUT/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
print('H10_PA6_CHECKS_PASS='+str(len(checks)))
