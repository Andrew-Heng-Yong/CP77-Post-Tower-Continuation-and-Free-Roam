"""Independent exact-delta and failing-index regression checks, no game writes."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent/'build'/(sys.argv[1] if len(sys.argv)>1 else 'rogue_02')
sys.path.insert(0,str(ROOT/'tools'))
from test_afterlife_booth_r6 import clean
from test_afterlife_rogue_r11 import contract

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
original=read(OUT/'original.json')['Data']['RootChunk']
patched=read(OUT/'patched.json')['Data']['RootChunk']
manifest=read(OUT/'build.json')
probe=read(ROOT/'research/postending_pa6/rogue/crash_probe.json')
checks=[]
def check(value,name):
    assert value,name
    checks.append(name)
def expected():
    r=copy.deepcopy(original)
    del r['resouresReferences']['lipsyncAnimSets'][1]
    r['playerActors'][0]['lipsyncAnimSet']['id']=1
    return r
def exact(p): return p==expected()
check(exact(patched),'Complete root permits exactly unused duplicate removal and V2->1')
check(original['resouresReferences']['lipsyncAnimSets'][0]==original['resouresReferences']['lipsyncAnimSets'][1],'Removed slot is byte-semantic duplicate of retained Rogue ref')
check(original['sceneGraph']==patched['sceneGraph'],'All47 graph nodes and event payloads unchanged')
check(original['actors']==patched['actors'],'Physical Rogue actor unchanged')
check(original['entryPoints']==patched['entryPoints'] and original['exitPoints']==patched['exitPoints'],'Saved scene interface unchanged')
check(original['locStore']==patched['locStore'] and original['screenplayStore']==patched['screenplayStore'] and original['voInfo']==patched['voInfo'],'Dialogue localization, screenplay, and voice info unchanged')
check(original['workspots']==patched['workspots'] and original['workspotInstances']==patched['workspotInstances'],'All workspot bindings unchanged')
check(original['interruptionScenarios']==patched['interruptionScenarios'],'Native interruption scenarios unchanged')
contract(clean(OUT/'patched.json'))
check(True,'Existing R11 dense actor,47node graph,localonly,noPhone,noJohnny acquisition,workspot and eye-glow contract passes')
refs=patched['resouresReferences']['lipsyncAnimSets']
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)
users=[x['id'] for x in walk(patched) if x.get('$type')=='scnLipsyncAnimSetSRRefId']
check(sorted(users)==[0,1] and len(refs)==2,'Every lipsync reference is dense and in bounds')
check(len({r['asyncRefLipsyncAnimSet']['DepotPath']['$value'] for r in refs})==2,'Two unique original localized resources remain')
check(probe['requested']==probe['count']==probe['capacity']==2,'Crash dump confirms requested2 against count/capacity2')
check(probe['player_actor_id']==1 and probe['player_lipsync_index']==2,'Crashed player definition matches original local scene actor1/index2')
check(probe['index_matches'] and probe['counter_matches'],'Native bad address matches table[index]*16 and handle counter')
check(probe['descriptor_rva']=='0x47be1e8' and probe['fault']=='Cyberpunk2077.exe+0x1d173be','Crash kind7 handle-copy instruction matches bounded disassembly')
check(probe['exception_parameters'][0]=='0x1','Crash is access-violation write, not OOM assertion')
check(patched['playerActors'][0]['lipsyncAnimSet']['id']<probe['count'],'New V index is within observed live table')
for name,mutate in [
    ('old player index',lambda p:p['playerActors'][0]['lipsyncAnimSet'].__setitem__('id',2)),
    ('wrong player index',lambda p:p['playerActors'][0]['lipsyncAnimSet'].__setitem__('id',0)),
    ('duplicate retained',lambda p:p['resouresReferences']['lipsyncAnimSets'].insert(1,copy.deepcopy(refs[0]))),
    ('Rogue actor changed',lambda p:p['actors'][0]['actorId'].__setitem__('id',2)),
    ('dialogue deleted',lambda p:p['screenplayStore'].clear()),
    ('workspot deleted',lambda p:p['workspots'].clear()),
]:
    mutant=copy.deepcopy(patched); mutate(mutant)
    check(not exact(mutant),'Exact-delta regression rejects '+name)
check(manifest['resource_count']==1 and manifest['depot']==r'towercontinued\afterlife_interactions_r8\rogue.scene','Archive contains only intended local Rogue resource')
check(sha(OUT/manifest['archive'])==manifest['archive_sha256'],'Archive manifest hash matches')
check(sha(OUT/'source'/manifest['depot'].replace('\\','/'))==manifest['patched_sha256'],'Patched resource manifest hash matches')
collisions=read(OUT/'collision_audit.json')
check([r['archive'] for r in collisions if r['target_hits']]==['TowerContinued_PreAlpha.archive'],'Only exact consolidated baseline has colliding target')
check(all(len(r['sha256'])==64 for r in collisions),'All scanned archives bound to SHA256')
check(manifest['explicit_modlist_absent'] and manifest['patch_name_ascii_before_baseline'] and manifest['archive']<'TowerContinued_PreAlpha.archive','First-wins ASCII patch precedence, no modlist override')
report=dict(status='PASS_EXACT_FAULT_REPAIR_OFFLINE_NOT_LIVE',build_sha256=sha(OUT/'build.json'),crash_probe_sha256=sha(ROOT/'research/postending_pa6/rogue/crash_probe.json'),checks=len(checks),details=checks,live_verified=False,limitations=['Actual resource selection and dialogue delivery require in-game test','Native table compaction implementation is inferred, not instrumented','Old R9 unrelated attachment-corruption writer remains unidentified'])
(OUT/'tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
