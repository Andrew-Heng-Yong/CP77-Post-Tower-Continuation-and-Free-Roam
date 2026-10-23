"""Integrated R11 exact payload checks, native guards, source contracts and compiler.

Predicate models and compilation are not engine animation/dialogue validation.
"""
import copy
import itertools
import json
import re
import subprocess
import sys
from pathlib import Path
from test_afterlife_booth_r6 import clean, read, sha, walk, differences
from test_afterlife_interactions_r9 import evaluate
from test_afterlife_interactions_r10 import trace_test
from test_afterlife_idles_r3 import lua_audit_test
from test_streetkid_scene_load_s3 import quest_edges

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/afterlife_world'; OUT=BASE/'interactions_r11'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
DRIVER=ROOT/'redscript/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds'
FACE=ROOT/'redscript/PTFR_Afterlife_Faces_R5/AfterlifeFacesR5.reds'
DIAG=ROOT/'diagnostics/PTFR_Afterlife_Behavior_Audit/init.lua'
RECEIPTS=('install_receipt.json','population_r2/install_receipt.json','idles_r3/install_receipt.json','faces_r5/install_receipt.json','booth_r6/install_receipt.json','emmerick_r7/install_receipt.json','interactions_r8/install_receipt.json','interactions_r9/install_receipt.json','interactions_r10/install_receipt.json')

def run(args):
    result=subprocess.run(args,capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    return result.stdout+result.stderr

def main():
    m=read(OUT/'manifest.json'); old=read(BASE/'interactions_r10/manifest.json')
    assert m['packed_readback'] and sha(m['archive'])==m['sha256']
    assert m['resources']==old['resources'] and len(m['resources'])==13
    for path,h in m['source_hashes'].items(): assert sha(path)==h,path
    changed=[p for p in m['resources'] if sha(Path(m['source_root'])/p)!=sha(Path(old['source_root'])/p)]
    assert set(changed)==set(m['changed_payloads']) and len(changed)==4
    dancer='towercontinued\\afterlife_r1\\dancers.questphase'
    for p in m['resources']:
        expected=Path(m['source_root'] if p==dancer else old['source_root'])/p
        assert sha(Path(m['safe_source_root'])/p)==sha(expected),p
    assert sha(m['safe_archive'])==m['safe_archive_sha256']
    r10_driver=next(f for f in read(BASE/'interactions_r10/install_receipt.json')['files'] if 'Interactions_R8' in f['relative'])
    assert sha(m['safe_driver'])==m['safe_driver_sha256']==r10_driver['sha256']
    helpers=['emmerick','rogue','retirement']
    for name in helpers:
        run([sys.executable,str(ROOT/f'tools/test_afterlife_{name}_r11.py')])
    before=clean(BASE/'interactions_r10/owner.questphase.json')
    after=clean(OUT/'owner.questphase.json');expected=copy.deepcopy(before)
    ns={n['id']:n for n in expected['graph']['nodes']}
    ns[2]['type']['value']=11
    r9={n['id']:n for n in clean(BASE/'interactions_r9/owner.questphase.json')['graph']['nodes']}
    old_r={n['id']:n for n in r9[204]['phaseGraph']['nodes']}
    new_r={n['id']:n for n in ns[204]['phaseGraph']['nodes']}
    new_r[4]['interruptionOperations']=old_r[4]['interruptionOperations']
    assert expected==after,differences(expected,after)[:10]
    raw=read(OUT/'owner.questphase.json')['Data']['RootChunk']
    edges,nodes=quest_edges(raw);ec=len(edges);nc=len(nodes)
    for n in nodes:
        if n.get('phaseGraph'):
            e,local=quest_edges({'graph':n['phaseGraph']});ec+=len(e);nc+=len(local)
    assert (nc,ec)==(45,50)
    child={n['id']:n for n in ns[104]['phaseGraph']['nodes']}
    facts=dict(read(BASE/'interactions_r8/manifest.json')['guards'])
    facts.update(PTFRAL1_Actor26Ready=1,PTFRAL8_EContinue=1,PTFRAL8_EStart=1,PTFRAL10_ENear=1)
    loaded={'$/03_night_city/#'+s for s in ('PTFRAL8_EmmerickStart','PTFRAL8_EntranceTrigger','PTFRAL1_PatronSpot78')}
    condition=child[3]['condition']; assert evaluate(condition,facts,loaded,True,0)
    negatives=0
    for k,v in facts.items():
        assert not evaluate(condition,{**facts,k:1-v},loaded,True,0),k;negatives+=1
    for missing in loaded:
        assert not evaluate(condition,facts,loaded-{missing},True,0);negatives+=1
    assert not evaluate(condition,facts,loaded,False,0);negatives+=1
    runtime=DRIVER.read_text(); face=FACE.read_text(); diagnostic=DIAG.read_text()
    # Bind the predicate models below to the integrated source, not a proposed branch.
    for token in ('playerFree && !rActive','gameplay && (!playerDialogue || ownDialogue)',
                  'if rActive && rSame { ownDialogue = scene.AreEntitiesInDialogue',
                  'rActive && rSame && scene.IsEntityInScene(r.GetEntityID())',
                  '(!tokensBlocked || (rActive && rSame)) && !rewind',
                  'gameplay && !playerDialogue && !tokensBlocked && !rewind',
                  'eStart = eAllowed && eNear && !eActive && playerFree',
                  'eAllowed && !eActive && playerFree','this.eAge >= 80',
                  'this.quiet >= 2','facing >= 0.991445','<= 0.1225','<= 0.15',
                  'distance <= 144.0','distance <= 1024.0','> 225.0',
                  'ArraySize(ids) != 1','npc.GetRecordID() != record'):
        assert token in runtime,token
    assert '!inScene' not in runtime
    assert runtime.count('IsEntityInScene(player.GetEntityID())')==1 # diagnostics only
    assert 'GameObjectEffectHelper.StartEffectEvent' not in runtime
    assert runtime.count('GameObjectEffectHelper.BreakEffectLoopEvent')==1
    for source in (runtime,face):
        assert not any(x in source for x in ('ScheduleAppearanceChange(', 'Teleport(', 'ChangeAppearance(', '@wrapMethod'))
    assert re.findall(r'func (\w+)\(',re.sub(r'//[^\n]*','',face))==['GetStatus']
    for node in walk(after):
        if node.get('$type')=='questSetVar_NodeType': assert node['factName'].startswith('PTFR')
    # Passive scene ownership may coexist; busy/cinematic and unrelated dialogue may not.
    cases=0
    for ambient,gameplay,dialogue,r_active,r_same,paired,e_active,tokens,rewind in itertools.product((False,True),repeat=9):
        own=r_active and r_same and paired
        free=gameplay and not dialogue and not tokens and not rewind
        e_allow=free and not r_active
        r_allow=gameplay and (not dialogue or own) and (not tokens or (r_active and r_same)) and not rewind and not e_active and (not r_active or r_same)
        r_start=r_allow and not r_active and free
        if not gameplay: assert not e_allow and not r_allow
        if rewind: assert not e_allow and not r_allow
        if tokens: assert not e_allow and not r_start
        if dialogue: assert not e_allow and not r_start
        if dialogue and not own: assert not r_allow
        if r_active and not r_same: assert not r_allow
        if r_start: assert not e_active
        cases+=1
    assert cases==512
    # The installed R10 read-only logger carries new status fields automatically.
    old_lua=lua_audit_test(diagnostic.replace('pcall(logInteractions)',''))
    light_lua=trace_test(diagnostic)
    log=run([str(ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'),'compile',
             '-s',str(DRIVER.parent),'-s',str(FACE.parent),'-s',str(ROOT/'redscript/PTFR_Afterlife_Idles_R3'),
             '-s',str(GAME/'red4ext/plugins/Codeware/Scripts'),'-b',str(GAME/'r6/cache/final.redscripts'),
             '-o',str(OUT/'compile.redscripts')])
    (OUT/'compile.log').write_text(log)
    assert 'Output successfully saved' in log and 'ERROR' not in log,log
    prior={}
    for receipt in RECEIPTS:
        for f in read(BASE/receipt)['files']:prior[f['relative'].replace('\\','/')]=f['sha256']
    for p,h in prior.items():assert sha(GAME/p)==h,p
    assert sha(DIAG)==prior['bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_Afterlife_Behavior_Audit/init.lua']
    specs=[('archive/pc/mod/TowerContinued_AfterlifeR1.archive',Path(m['archive'])),
           ('r6/scripts/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds',DRIVER),
           ('r6/scripts/PTFR_Afterlife_Faces_R5/AfterlifeFacesR5.reds',FACE)]
    files=[dict(relative=p,source=str(s.relative_to(ROOT)),sha256=sha(s),before_sha256=prior[p]) for p,s in specs]
    check_paths=['tools/build_afterlife_interactions_r11.ps1','tools/test_afterlife_interactions_r11.py',
                 'tools/audit_scene_actor_ids.py']
    for name in helpers:
        check_paths += [f'tools/build_afterlife_{name}_r11.ps1',f'tools/test_afterlife_{name}_r11.py']
    checked={p:sha(ROOT/p) for p in check_paths}
    result=dict(status='PASS_R11_OFFLINE_LIVE_PENDING',manifest_sha256=sha(OUT/'manifest.json'),
                checked_sources=checked,files=files,safe_rollback=m['safe_rollback'],
                packed_readback=True,redscript_compile=True,faces_retired=True,dancers_retired=True,
                unchanged_r10_payloads=9,native_nodes=nc,native_edges=ec,native_negative_conditions=negatives,
                player_dialogue_ownership_model_cases=cases,diagnostic_lua_cases=old_lua+light_lua,
                protected_prior_afterlife_files=len(prior),new_actor_identities=0,story_fact_writes=0,
                fallback_preserves_both_retirements=True,crash_root_cause_unproven=True,live_tested=False)
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
