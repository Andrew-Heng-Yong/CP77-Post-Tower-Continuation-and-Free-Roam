"""R9 crash regression, exact payload delta and saved-native-condition tests."""
import copy
import json
import math
import re
import struct
import subprocess
from pathlib import Path
from audit_scene_actor_ids import audit_scene_actor_ids, walk as typed_walk
from inspect_native_crash import Dump
from test_afterlife_booth_r6 import clean, read, sha, walk, differences
from test_streetkid_scene_load_s3 import quest_edges

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/afterlife_world'; OLD=BASE/'interactions_r8'; OUT=BASE/'interactions_r9'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
DRIVER=ROOT/'redscript/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds'

def rejected(scene):
    try: audit_scene_actor_ids(scene)
    except ValueError: return True
    return False

def evaluate(c, facts, loaded, inside, distance):
    kind=c['$type']
    if kind=='questLogicalCondition':
        return (all if c['operation']=='AND' else any)(evaluate(n,facts,loaded,inside,distance) for n in c['conditions'])
    if kind=='questFactsDBCondition':
        n=c['type']; a=facts.get(n['factName'],0); b=n['value']
        return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'LessOrEqual':a<=b}[n['comparisonType']]
    if kind=='questNodeLoadingCondition': return (c['objectRef']['$value'] in loaded) != bool(c['inverted'])
    if kind=='questTriggerCondition':
        assert c['isPlayerActivator']==1
        return inside if c['type']=='IsInside' else not inside
    if kind=='questDistanceCondition':
        assert c['type']['comparisonType']=='LessOrEqual'
        assert c['type']['distanceDefinition2']['distanceValue']==5
        return distance<=5
    raise AssertionError(kind)

def main():
    m=read(OUT/'manifest.json'); old=read(OLD/'manifest.json')
    assert m['packed_readback'] and sha(m['archive'])==m['sha256']
    assert m['resources']==old['resources'] and len(m['resources'])==13
    for p,h in m['source_hashes'].items(): assert sha(p)==h,p
    changed=[p for p in m['resources'] if sha(Path(m['source_root'])/p)!=sha(Path(old['source_root'])/p)]
    assert set(changed)==set(m['changed_payloads']) and len(changed)==2
    prior=clean(OLD/'rogue.scene.json'); fixed=clean(OUT/'rogue.scene.json')
    assert rejected(prior), 'The exact scene that crashed must fail the gate'
    actor_audit=audit_scene_actor_ids(fixed)
    assert actor_audit['actor_ids']==[0,1]
    assert audit_scene_actor_ids(clean(OLD/'emmerick.scene.json'))['actor_ids']==[0,1]
    header_only=copy.deepcopy(prior);header_only['playerActors'][0]['actorId']['id']=1
    assert rejected(header_only), 'Fixing the header alone leaves invalid performers'
    # An independent typed transformation defines the complete permitted delta.
    expected=copy.deepcopy(prior);removed=remapped=0
    for p,n in list(typed_walk(expected)):
        if n.get('$type')=='scnPerformerId' and n['id']==257 and 'performersDebugSymbols' in p:
            pass
    symbols=expected['debugSymbols']['performersDebugSymbols']
    expected['debugSymbols']['performersDebugSymbols']=[n for n in symbols if n['performerId']['id']!=257]
    removed+=len(symbols)-len(expected['debugSymbols']['performersDebugSymbols'])
    for _,n in typed_walk(expected):
        if 'additionalSpeakers' in n:
            speakers=n['additionalSpeakers']['speakers']
            n['additionalSpeakers']['speakers']=[s for s in speakers if s['actorId']['id']!=1]
            removed+=len(speakers)-len(n['additionalSpeakers']['speakers'])
    for _,n in typed_walk(expected):
        kind=n.get('$type');v=n.get('id')
        assert not (kind=='scnActorId' and v==1), 'Unremoved hologram actor'
        assert not (kind=='scnPerformerId' and v==257), 'Unremoved hologram performer'
        if kind=='scnActorId' and v==2: n['id']=1;remapped+=1
        if kind=='scnPerformerId' and v==513: n['id']=257;remapped+=1
    assert expected==fixed,differences(expected,fixed)[:8]
    assert remapped+removed==len(m['actor_repairs'])
    # Individual stale references are rejected, even with a correct cast.
    mutants=0
    for kind,value in (('scnActorId',2),('scnPerformerId',513),('scnPerformerId',769)):
        bad=copy.deepcopy(fixed);bad['regressionProbe']={'$type':kind,'id':value}
        assert rejected(bad);mutants+=1
    assert len(fixed['sceneGraph']['graph'])==47
    assert not any(n.get('$type')=='questSetVar_NodeType' for n in walk(fixed))

    # Reproduce the actual dump's bad slot, not merely an invented counterexample.
    dump_path=Path(r'C:\Users\Ayong\AppData\Local\REDEngine\ReportQueue\Cyberpunk2077-20261006-014342-27432-3008\Cyberpunk2077.dmp')
    d=Dump(dump_path);report=d.report();assert report['fault']=='Cyberpunk2077.exe+0x545d0b'
    assert report['exception_parameters']==['0x0','0x34']
    regs={k:int(v,16) for k,v in report['registers'].items()};store=d.read(regs['r12'],0x30)
    count=struct.unpack_from('<I',store,0x14)[0];base=struct.unpack_from('<Q',store,0x18)[0];players=struct.unpack_from('<I',store,0x24)[0]
    index,remainder=divmod(regs['r15']-base,0xB0)
    definition=struct.unpack('<Q',d.read(regs['r15']+8,8))[0]
    valid=struct.unpack('<Q',d.read(base+8,8))[0];old_id=struct.unpack('<I',d.read(valid,4))[0]
    assert (count,players,index,remainder,definition,old_id)==(1,1,1,0,0,2)
    assert fixed['playerActors'][0]['actorId']['id']-count==0
    crash=dict(dump_sha256=sha(dump_path),fault=report['fault'],ordinary_actors=count,players=players,old_player_id=old_id,bad_player_index=index,corrected_player_index=0)

    before=clean(OLD/'owner.questphase.json');after=clean(OUT/'owner.questphase.json')
    old_nodes={n['id']:n for n in before['graph']['nodes']};new_nodes={n['id']:n for n in after['graph']['nodes']}
    for ident,n in old_nodes.items():
        if ident!=104: assert n==new_nodes[ident],ident
    a={n['id']:n for n in old_nodes[104]['phaseGraph']['nodes']};b={n['id']:n for n in new_nodes[104]['phaseGraph']['nodes']}
    for ident,n in a.items():
        if ident not in (2,3): assert n==b[ident],ident
    # Reciprocal sockets across each of the three scopes; no orphan/cross-graph links.
    raw=read(OUT/'owner.questphase.json')['Data']['RootChunk']
    edges,ns=quest_edges(raw);edge_count=len(edges);node_count=len(ns)
    for n in ns:
        if n.get('phaseGraph'):
            e,local=quest_edges({'graph':n['phaseGraph']});edge_count+=len(e);node_count+=len(local)
            if n['id']==104:
                assert {(0,'Out',2,'In'),(2,'Out',8,'In'),(8,'Out',9,'In'),(9,'Out',10,'In'),(10,'Out',11,'In'),(11,'Out',3,'In'),(3,'True',6,'In'),(14,'Out',4,'emmerick_entrance')}<=e
    assert (node_count,edge_count)==(45,50),(node_count,edge_count)
    for n in walk(after):
        if n.get('$type')=='questSetVar_NodeType': assert n['factName'].startswith('PTFRAL8_')
    facts=dict(old['guards']);facts.update(PTFRAL1_Actor26Ready=1,PTFRAL8_EContinue=1,PTFRAL8_EStart=1)
    loaded={'$/03_night_city/#'+s for s in ('PTFRAL8_EmmerickStart','PTFRAL8_EntranceTrigger','PTFRAL1_PatronSpot78')}
    assert evaluate(b[3]['condition'],facts,loaded,True,2.5)
    assert evaluate(b[2]['condition'],{**facts,'PTFRAL8_EStart':0},loaded,True,20)
    assert evaluate(b[9]['condition'],{**facts,'PTFRAL8_EStart':0},loaded,True,2.5)
    assert not evaluate(b[11]['condition'],{**facts,'PTFRAL8_EStart':0},loaded,True,2.5)
    negative_cases=0
    for k,v in facts.items():
        bad={**facts,k:1-v}
        assert not evaluate(b[3]['condition'],bad,loaded,True,2.5),k;negative_cases+=1
    for missing in loaded:
        assert not evaluate(b[3]['condition'],facts,loaded-{missing},True,2.5);negative_cases+=1
    for inside,distance in ((False,2),(True,5.01),(False,6)):
        assert not evaluate(b[3]['condition'],facts,loaded,inside,distance);negative_cases+=1
    distances=[n for n in walk(b[9]) if n.get('$type')=='questObjectDistance']
    assert len(distances)==1 and distances[0]['entityRef']['refLocalPlayer']==1
    assert distances[0]['nodeRef2']['reference']['$value']=='$/03_night_city/#PTFRAL1_Emmerick'
    assert [n['$value'] for n in distances[0]['nodeRef2']['names']]==['emmerick']
    # Actual screenshot quaternion and its sign inverse both pass. A90-degree
    # facing error fails, preserving root-motion anchor safety without axis guesses.
    authored=(0,0,-.0548490323,.998494744)
    for observed in ((0,0,.055,-.998),authored,tuple(-n for n in authored)):
        dot=abs(sum(a*b for a,b in zip(authored,observed)))
        assert dot>=.991445
    assert abs(math.cos(math.radians(90/2)))<.991445
    runtime=DRIVER.read_text()
    assert 'AbsF(Quaternion.Dot' in runtime and 'forward.X' not in runtime
    assert 'native vanilla <=5m' in runtime and 'distance) <= 25.0' not in runtime
    assert all(n in runtime for n in ('ArraySize(ids) != 1','this.eAge >= 80','PTFRAL8_EStage','PTFRAL8_ECancelled','this.eChecks','BreakEffectLoopEvent'))
    assert not any(n in runtime for n in ('SendCommand(', 'Spawn(', 'StartEffectEvent(', 'SetAppearance('))
    cmd=[str(ROOT/'research/finalboards_dismissal/tooling/redscript-cli.exe'),'compile','-s',str(DRIVER.parent),'-s',str(ROOT/'redscript/PTFR_Afterlife_Idles_R3'),'-s',str(ROOT/'redscript/PTFR_Afterlife_Faces_R5'),'-s',str(GAME/'red4ext/plugins/Codeware/Scripts'),'-b',str(GAME/'r6/cache/final.redscripts'),'-o',str(OUT/'compile.redscripts')]
    run=subprocess.run(cmd,capture_output=True,text=True);log=run.stdout+run.stderr;(OUT/'compile.log').write_text(log)
    assert run.returncode==0 and 'ERROR' not in log and 'Output successfully saved' in log,log
    prior_files={}
    for receipt in ('install_receipt.json','population_r2/install_receipt.json','idles_r3/install_receipt.json','faces_r5/install_receipt.json','booth_r6/install_receipt.json','emmerick_r7/install_receipt.json','interactions_r8/install_receipt.json'):
        for f in read(BASE/receipt)['files']:prior_files[f['relative'].replace('\\','/')]=f['sha256']
    for p,h in prior_files.items():assert sha(GAME/p)==h,p
    files=[]
    for relative,source in (('archive/pc/mod/TowerContinued_AfterlifeR1.archive',Path(m['archive'])),('r6/scripts/PTFR_Afterlife_Interactions_R8/AfterlifeInteractionsR8.reds',DRIVER)):
        files.append(dict(relative=relative,source=str(source.relative_to(ROOT)),sha256=sha(source),before_sha256=prior_files[relative]))
    safe=[]
    for f in read(OLD/'install_receipt.json')['files']:
        if f['before_sha256']:assert sha(f['backup'])==f['before_sha256']
        safe.append(dict(relative=f['relative'],sha256=f['before_sha256'],source=f['backup']))
    result=dict(status='PASS_R9_OFFLINE_LIVE_PENDING',manifest_sha256=sha(OUT/'manifest.json'),builder_sha256=sha(ROOT/'tools/build_afterlife_interactions_r9.ps1'),validator_sha256=sha(__file__),actor_auditor_sha256=sha(ROOT/'tools/audit_scene_actor_ids.py'),files=files,safe_rollback=safe,packed_readback=True,redscript_compile=True,actor_audit=actor_audit,old_crash_layout_rejected=True,header_only_rejected=True,stale_reference_mutants=mutants,removed_holo_references=removed,remapped_player_references=remapped,native_nodes=node_count,native_edges=edge_count,saved_condition_negative_cases=negative_cases,unchanged_r8_payloads=11,protected_prior_afterlife_files=len(prior_files),crash=crash,live_tested=False,emmerick_root_cause='Unproven from R8 trace; sequential native gates and axis-independent facing admission are a bounded candidate, with stage diagnostics',new_actor_identities=0,story_fact_writes=0)
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
