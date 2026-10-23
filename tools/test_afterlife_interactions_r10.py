"""R10 safety containment, native conditions, real compile and passive trace tests."""
import copy
import json
import re
import subprocess
import sys
from pathlib import Path
from test_afterlife_booth_r6 import clean, read, sha, walk, differences
from test_afterlife_idles_r3 import lua_audit_test
from test_afterlife_interactions_r9 import evaluate
from test_streetkid_scene_load_s3 import quest_edges
from audit_scene_actor_ids import audit_scene_actor_ids

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/afterlife_world'; OUT=BASE/'interactions_r10'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
DRIVER=ROOT/'redscript/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds'
FACE=ROOT/'redscript/PTFR_Afterlife_Faces_R5/AfterlifeFacesR5.reds'
DIAG=ROOT/'diagnostics/PTFR_Afterlife_Behavior_Audit/init.lua'

def trace_test(source):
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
events={}; rows={}; writes=0; closes=0; mode="ok"
function registerForEvent(n,f)events[n]=f end
function Observe()end
function IsDefined(v)return type(v)=="table"end
function print()end
json={encode=function(r)table.insert(rows,r);return "{}"end}
io={open=function()if mode=="io_fail"then return nil end;return {
write=function()writes=writes+1 end,close=function()closes=closes+1 end}end}
pos={x=-1458,y=1026,z=17}
player={GetWorldPosition=function()return pos end}
driver={GetStatus=function()if mode=="status_fail"then error("unavailable")end;return "Interactions R10 quarantine=1"end}
Game={GetPlayer=function()if mode=="no_player"then return nil end;return player end,
GetQuestsSystem=function()return {GetFactStr=function(self,n)if n=="PTFRAL10_ENear"then return 1 else return 0 end end}end,
GetScriptableSystemsContainer=function()return {Get=function()if mode=="no_driver"then return nil end;return driver end}end}
''')
    lua.execute(source);g=lua.globals()
    g.events.onUpdate(.5);assert len(g.rows)==0
    g.events.onUpdate(.5);assert len(g.rows)==1
    assert g.rows[1].facts.PTFRAL10_ENear==1
    assert g.rows[1].status=='Interactions R10 quarantine=1'
    for mode in ('no_driver','status_fail'):
        g.mode=mode;g.events.onUpdate(1);assert g.rows[len(g.rows)].status=='UNKNOWN'
    n=len(g.rows);g.mode='no_player';g.events.onUpdate(1);assert len(g.rows)==n
    g.mode='ok';g.pos.x=0;g.events.onUpdate(1);assert len(g.rows)==n
    g.pos.x=-1458;g.mode='io_fail';g.events.onUpdate(1)
    assert g.writes==g.closes==3
    assert not any(x in source for x in ('SetFact','SendCommand','Teleport','ScheduleAppearanceChange','QueueEvent','GetWorkspotInstance','GetExtendedInfo','ResolveCommunityEntryDataFromEntityID'))
    return 8

def main():
    m=read(OUT/'manifest.json');old=read(BASE/'interactions_r9/manifest.json')
    assert m['packed_readback'] and m['rogue_quarantined'] and sha(m['archive'])==m['sha256']
    assert m['resources']==old['resources'] and len(m['resources'])==13
    for p,h in m['source_hashes'].items():assert sha(p)==h,p
    changed=[p for p in m['resources'] if sha(Path(m['source_root'])/p)!=sha(Path(old['source_root'])/p)]
    assert set(changed)==set(m['changed_payloads']) and len(changed)==2
    # Independent actor-free scene audit also checks exact prior socket identity.
    run=subprocess.run([sys.executable,str(OUT/'scene_review/test_quarantine.py')],capture_output=True,text=True)
    assert run.returncode==0,run.stdout+run.stderr
    scene=clean(OUT/'scene_review/rogue_quarantine.scene.json')
    assert audit_scene_actor_ids(scene)['actor_ids']==[]
    assert audit_scene_actor_ids(clean(BASE/'interactions_r8/emmerick.scene.json'))['actor_ids']==[0,1]
    before=clean(BASE/'interactions_r9/owner.questphase.json')
    after=clean(OUT/'owner.questphase.json');expected=copy.deepcopy(before)
    nodes={n['id']:n for n in expected['graph']['nodes']}
    nodes[2]['type']['value']=10
    child={n['id']:n for n in nodes[104]['phaseGraph']['nodes']}
    replacements=0
    for ident in (3,9):
        conditions=child[ident]['condition']['conditions']
        for i,c in enumerate(conditions):
            if c['$type']=='questDistanceCondition':
                conditions[i]={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRAL10_ENear','value':1}}
                replacements+=1
    assert replacements==2
    rogue_nodes={n['id']:n for n in nodes[204]['phaseGraph']['nodes']}
    assert len(rogue_nodes[4]['interruptionOperations'])>0
    rogue_nodes[4]['interruptionOperations']=[]
    assert expected==after,differences(expected,after)[:10]
    assert not any(n.get('$type')=='questDistanceCondition' for n in walk(after))
    raw=read(OUT/'owner.questphase.json')['Data']['RootChunk']
    edges,ns=quest_edges(raw);edge_count=len(edges);node_count=len(ns)
    for n in ns:
        if n.get('phaseGraph'):
            e,local=quest_edges({'graph':n['phaseGraph']});edge_count+=len(e);node_count+=len(local)
    assert (node_count,edge_count)==(45,50)
    facts=dict(read(BASE/'interactions_r8/manifest.json')['guards'])
    facts.update(PTFRAL1_Actor26Ready=1,PTFRAL8_EContinue=1,PTFRAL8_EStart=1,PTFRAL10_ENear=1)
    loaded={'$/03_night_city/#'+s for s in ('PTFRAL8_EmmerickStart','PTFRAL8_EntranceTrigger','PTFRAL1_PatronSpot78')}
    condition=child[3]['condition'];assert evaluate(condition,facts,loaded,True,0)
    negative=0
    for k,v in facts.items():
        assert not evaluate(condition,{**facts,k:1-v},loaded,True,0),k;negative+=1
    for missing in loaded:
        assert not evaluate(condition,facts,loaded-{missing},True,0);negative+=1
    assert not evaluate(condition,facts,loaded,False,0);negative+=1
    # Stage3 can pass without anchor readiness; stage4 cannot.
    assert evaluate(child[9]['condition'],{**facts,'PTFRAL8_EStart':0},loaded,True,0)
    assert not evaluate(child[11]['condition'],{**facts,'PTFRAL8_EStart':0},loaded,True,0)
    runtime=DRIVER.read_text();face=FACE.read_text();diagnostic=DIAG.read_text()
    assert 'eNear = eAllowed && Vector4.DistanceSquared(pos, player.GetWorldPosition()) <= 25.0' in runtime
    assert 'eStart = eAllowed && eNear' in runtime and 'AbsF(Quaternion.Dot' in runtime
    for name in ('PTFRAL8_RContinue','PTFRAL8_RAvailable','PTFRAL8_RStart'):
        assert not re.search(r'this.Set\(q, n"'+name+r'", (?!false)',runtime)
    assert 'Character.Rogue' not in runtime and 'EffectHelper.' not in runtime
    assert 'ScheduleAppearanceChange(' not in face and 'return false;' in face.split('private func Enabled')[1].split('}')[0]
    assert 'if !this.Enabled()' in face.split('private func Allowed')[1].split('private func OnFaceTick')[0]
    assert 'GetWorkspotInstance' not in diagnostic
    # Existing crowd classification tests remain; isolate the separately-tested
    # lightweight logger so that the legacy mock's lastrow still means crowd.
    old_lua_cases=lua_audit_test(diagnostic.replace('pcall(logInteractions)',''))
    lua_cases=trace_test(diagnostic)
    cmd=[str(ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'),'compile','-s',str(DRIVER.parent),'-s',str(FACE.parent),'-s',str(ROOT/'redscript/PTFR_Afterlife_Idles_R3'),'-s',str(GAME/'red4ext/plugins/Codeware/Scripts'),'-b',str(GAME/'r6/cache/final.redscripts'),'-o',str(OUT/'compile.redscripts')]
    result=subprocess.run(cmd,capture_output=True,text=True);log=result.stdout+result.stderr
    (OUT/'compile.log').write_text(log)
    assert result.returncode==0 and 'Output successfully saved' in log and 'ERROR' not in log,log
    prior={}
    for receipt in ('install_receipt.json','population_r2/install_receipt.json','idles_r3/install_receipt.json','faces_r5/install_receipt.json','booth_r6/install_receipt.json','emmerick_r7/install_receipt.json','interactions_r8/install_receipt.json','interactions_r9/install_receipt.json'):
        for f in read(BASE/receipt)['files']:prior[f['relative'].replace('\\','/')]=f['sha256']
    for p,h in prior.items():assert sha(GAME/p)==h,p
    specs=[('archive/pc/mod/TowerContinued_AfterlifeR1.archive',Path(m['archive'])),('r6/scripts/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds',DRIVER),('bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_Afterlife_Behavior_Audit/init.lua',DIAG),('r6/scripts/PTFR_Afterlife_Faces_R5/AfterlifeFacesR5.reds',FACE)]
    files=[dict(relative=p,source=str(s.relative_to(ROOT)),sha256=sha(s),before_sha256=prior[p]) for p,s in specs]
    safe=read(BASE/'interactions_r9/tests.json')['safe_rollback']
    for f in safe:
        if f['sha256']:assert sha(f['source'])==f['sha256']
    crash=read(OUT/'crash/evidence.json')
    assert '1d9779' in json.dumps(crash) and '10029921' in json.dumps(crash)
    result=dict(status='PASS_R10_SAFETY_OFFLINE_LIVE_PENDING',manifest_sha256=sha(OUT/'manifest.json'),builder_sha256=sha(ROOT/'tools/build_afterlife_interactions_r10.ps1'),validator_sha256=sha(__file__),roguehelper_sha256=sha(ROOT/'tools/build_afterlife_rogue_quarantine_r10.ps1'),actor_auditor_sha256=sha(ROOT/'tools/audit_scene_actor_ids.py'),files=files,safe_rollback=safe,packed_readback=True,redscript_compile=True,rogue_quarantined=True,faces_suspended=True,automatic_diagnostics=True,emmerick_root_cause_unproven=True,crash_root_cause_unproven=True,native_nodes=node_count,native_edges=edge_count,saved_condition_negative_cases=negative,unchanged_r9_payloads=11,legacy_diagnostic_cases=old_lua_cases,lightweight_trace_cases=lua_cases,protected_prior_afterlife_files=len(prior),new_actor_identities=0,story_fact_writes=0,live_tested=False,rollback_keeps_face_suspension_and_diagnostics=True)
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
