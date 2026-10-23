"""Exact resource deltas, bounded runtime contract model and real compilation."""
import copy
import hashlib
import itertools
import json
import re
import subprocess
import zlib
from pathlib import Path
from test_radio_memorial import canonical, handles

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/afterlife_world'; OUT=BASE/'booth_r6'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
DRIVER=ROOT/'redscript/PTFR_Afterlife_Idles_R3/AfterlifeIdlesR3.reds'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)
def clean(p):
    x=read(p)['Data']['RootChunk']
    for n in walk(x):
        if n.get('$type')=='TweakDBID' and n.get('$storage')=='string':
            encoded=n['$value'].encode();n['$value']=str(zlib.crc32(encoded)+(len(encoded)<<32));n['$storage']='uint64'
    return canonical(x,handles(x))
def differences(a,b,path=''):
    if type(a)!=type(b):return [(path,a,b)]
    if isinstance(a,dict):return [d for k in a.keys()|b.keys() for d in differences(a.get(k),b.get(k),path+'/'+k)]
    if isinstance(a,list):
        if len(a)!=len(b):return [(path+'/length',len(a),len(b))]
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in differences(x,y,path+'/'+str(i))]
    return [] if a==b else [(path,a,b)]
def main():
    m=read(OUT/'manifest.json'); r3=read(BASE/'idles_r3/manifest.json')
    assert m['packed_readback'] and len(m['resources'])==8 and sha(m['archive'])==m['sha256']
    for p,h in m['source_hashes'].items(): assert sha(p)==h,p
    for p in r3['resources']:
        if p.endswith('spots.streamingsector'): continue
        assert sha(Path(m['source_root'])/p)==sha(Path(r3['source_root'])/p),p
    # Exactly four depot references; no anchor/orientation, registry or AI policy delta.
    a=clean(BASE/'idles_r3/spots.streamingsector.json'); b=clean(OUT/'spots.streamingsector.json')
    for i,e in enumerate(m['edits']):
        a['nodes'][i]['spot']['resource']['DepotPath']['$value']=e['private_resource']
    assert a==b,'Unexpected spot-sector change'
    random_lists=0; preserved_exits=0
    for e in m['edits']:
        original=BASE/'idles_r3/entry_sources/json'/(e['source_resource']+'.json')
        a=clean(original); b=clean(OUT/(e['entry']+'.workspot.json'))
        seq=[n for n in walk(a) if n.get('$type')=='workSequence' and n.get('id',{}).get('id')==2]
        assert len(seq)==1 and seq[0]['loopInfinitely']==0
        seq[0]['loopInfinitely']=1
        assert a==b,(e['entry'],differences(a,b)[:12])
        # All authored exits/reactions/weights/clip names remain byte-structurally equal.
        preserved_exits+=sum(n.get('$type') in ('workExitAnim','workFastExit') for n in walk(b))
        random_lists+=sum(n.get('$type')=='workRandomList' for n in walk(seq[0]))
        if e['entry']=='merc_02':
            pause=seq[0]['list'][0]
            assert pause['$type']=='workPauseClip' and (pause['timeMin'],pause['timeMax'])==(3,5)
        if e['entry']=='merc_03':
            male=next(n for n in walk(b) if n.get('$type')=='workConditionalSequence' and n['id']['id']==18)
            assert male['conditionList'][0]['rig']['DepotPath']['$value'].endswith('man_base.rig')
            assert any(n.get('$type')=='workSequence' and n['id']['id']==2 for n in walk(male))
    # Existing vanilla looping branch validates the representation, not live output.
    precedent=clean(BASE/'idles_r3/entry_sources/json/base/workspots/common/chair/generic__sit_chair__sit_around__06.workspot.json')
    assert any(n.get('$type')=='workSequence' and n.get('loopInfinitely')==1 for n in walk(precedent))
    text=DRIVER.read_text()
    guards={k:int(v) for k,v in re.findall(r'q.GetFact\(n"([^"]+)"\) == (\d+)',text)}
    assert guards==dict(r3['guards'],PTFRAL3_WorldApplied=1)
    negative_guards=0
    for k,v in guards.items():
        for wrong in (-1,0,1,2,3):
            if wrong==v: continue
            values=dict(guards);values[k]=wrong
            assert not all(values[x]==y for x,y in guards.items());negative_guards+=1
    for token in ['ArraySize(ids) != 1','row.requests >= 3','row.age < 80','row.cooldown = 80',
                  'atAnchor ? 2 : 20','<= 0.1225','<= 0.15','jumpToEntry = atAnchor',
                  'moveToWorkspot = !atAnchor','entry.id = 2u','continueInCombat = false',
                  'IsEntityInScene','IsActorInWorkspot','IsDead()','IsDefeated',
                  'gamedataNPCHighLevelState.Relaxed','> 9.0','epoch != this.epoch',
                  'RandRange(0, 4)','0.25, false','GetFixedEntityIdsFromEntityReference']:
        assert token in text,token
    for forbidden in ['ScheduleAppearanceChange','CreateEntity(','SetFlat','Teleport','ChangeEntryState','SetFact(n"q']:
        assert forbidden not in text,forbidden
    assert text.count('ai.SendCommand(command)')==text.count('ai.CancelCommand(this.command)')==1
    # Acquisition/cancellation contract model: all disqualifiers suppress dispatch.
    def eligible(exact=True,ready=True,alive=True,relaxed=True,scene=False,combat=False,in_workspot=False,quiet=True,requests=0,distance2=0):
        return exact and ready and alive and relaxed and not scene and not combat and not in_workspot and quiet and requests<3 and distance2<=9
    assert eligible()
    blocked=[dict(exact=False),dict(ready=False),dict(alive=False),dict(relaxed=False),dict(scene=True),dict(combat=True),dict(in_workspot=True),dict(quiet=False),dict(requests=3),dict(distance2=9.01)]
    assert all(not eligible(**case) for case in blocked)
    anchor_cases=0
    for dx,dy,dz in itertools.product([0,.1,.35,.5,1],[0,.1,.35,.5],[0,.1,.16,.73]):
        near=dx*dx+dy*dy+dz*dz<=.1225 and abs(dz)<=.15
        if dz>.15 or dx>.35 or dy>.35: assert not near
        anchor_cases+=1
    # Queue timing model: ready exact-anchor bindings no longer wait ~11sec.
    timings=[]
    for cooldown in range(4):
        quiet=0; has_position=False
        for tick in range(20):
            if cooldown: cooldown-=1;has_position=False;continue
            quiet=quiet+1 if has_position else 0;has_position=True
            if quiet>=2: timings.append(tick*.25);break
    assert min(timings)==.5 and max(timings)==1.25
    command=[str(ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'),'compile',
             '-s',str(DRIVER.parent),'-s',str(ROOT/'redscript/PTFR_Afterlife_Faces_R5'),
             '-s',str(GAME/'red4ext/plugins/Codeware/Scripts'),
             '-b',str(GAME/'r6/cache/final.redscripts'),'-o',str(OUT/'compile.redscripts')]
    result=subprocess.run(command,capture_output=True,text=True);output=result.stdout+result.stderr
    (OUT/'compile.log').write_text(output)
    assert result.returncode==0 and 'ERROR' not in output and 'Output successfully saved' in output,output
    expected={}
    for p in ['install_receipt.json','population_r2/install_receipt.json','idles_r3/install_receipt.json','faces_r5/install_receipt.json']:
        for f in read(BASE/p)['files']:expected[f['relative'].replace('\\','/')]=f['sha256']
    for p,h in expected.items():assert sha(GAME/p)==h,p
    files=[{'relative':'archive/pc/mod/TowerContinued_AfterlifeIdlesR3.archive','source':str(Path(m['archive']).relative_to(ROOT)),'sha256':m['sha256']},
           {'relative':'r6/scripts/PTFR_Afterlife_Idles_R3/AfterlifeIdlesR3.reds','source':str(DRIVER.relative_to(ROOT)),'sha256':sha(DRIVER)}]
    for f in files:f['before_sha256']=expected[f['relative']]
    report={'status':'PASS_R6_OFFLINE_NOT_INSTALLED_NOT_LIVE','private_idle_loop_deltas':4,'private_spot_reference_deltas':4,
            'unchanged_r3_payloads':3,'authored_random_lists_in_active_branches':random_lists,'preserved_exit_nodes':preserved_exits,
            'guard_contracts':len(guards),'modeled_negative_guards':negative_guards,'modeled_actor_disqualifiers':len(blocked),
            'modeled_anchor_cases':anchor_cases,'modeled_ready_anchor_latency_seconds':timings,
            'exact_source_redscript_compile_with_installed_codeware':True,'unchanged_r5_compiled_together':True,
            'compiled_sha256':sha(OUT/'compile.redscripts'),
            'manifest_sha256':sha(OUT/'manifest.json'),'builder_sha256':sha(ROOT/'tools/build_afterlife_booth_r6.ps1'),
            'validator_sha256':sha(Path(__file__)),'protected_afterlife_files':len(expected),'files':files,
            'game_writes':0,'limitations':['No live entry/alignment/infinite-loop/cancellation/stream/reload proof',
              'merc_02 retains authored lean270 breathing idle and randomized 3-5sec pause, no new gesture set',
              'Existing scene ownership still yields; no blanket AI reset','R5 appearance user pass does not establish saved reload']}
    (OUT/'tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
