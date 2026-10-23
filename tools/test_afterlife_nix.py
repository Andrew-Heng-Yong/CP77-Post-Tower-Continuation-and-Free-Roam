"""Independent verification of the exact Nix stale activity guard correction."""
import copy
import hashlib
import json
from pathlib import Path
from audit_world_interactions import walk
from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_access_r10 import read, sha

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/afterlife_world'

def evaluate(c,f):
    if c['$type']=='questLogicalCondition':
        values=[evaluate(x,f) for x in c['conditions']]
        return all(values) if c['operation']=='AND' else any(values)
    p=c['type'];actual=f.get(p['factName'],0)
    if p['comparisonType']=='Equal':return actual==p['value']
    assert p['comparisonType']=='Greater'
    return actual>p['value']

def main():
    m=read(BASE/'nix_manifest.json');receipt=read(ROOT/'research/b0_story_eight/validation/install_receipt.json')
    old=read(ROOT/'research/b0_story_eight/validation/nix.questphase.json')['Data']['RootChunk']
    new=read(BASE/'nix_repaired_phase.json')['Data']['RootChunk']
    oh,nh=handles(old),handles(new)
    on,nn=nodes(old),nodes(new)
    assert set(on)==set(nn)==set(range(7))
    assert on[2]['$type']==nn[2]['$type']=='questPauseConditionNodeDefinition'
    oldguard=canonical(on[2]['condition'],oh);newguard=canonical(nn[2]['condition'],nh)
    assert oldguard['operation']==newguard['operation']=='AND'
    removed=[c for c in oldguard['conditions'] if c['type']['factName']=='mq016_active']
    assert len(removed)==1 and removed[0]['type']['comparisonType']=='Equal' and removed[0]['type']['value']==0
    expected=copy.deepcopy(canonical(old,oh))
    expected['graph']['nodes'][2]['condition']['conditions'].remove(removed[0])
    assert expected==canonical(new,nh), 'Unexpected Nix semantic delta'
    assert quest_edges(old)[0]==quest_edges(new)[0]
    assert quest_edges({'graph':on[5]['phaseGraph']})[0]==quest_edges({'graph':nn[5]['phaseGraph']})[0]
    changed=[r for r in m['resource_deltas'] if r['before']!=r['after']]
    assert len(changed)==1 and changed[0]['depot']==r'towercontinued\b0_story_eight\nix.questphase'
    assert len(m['resource_deltas'])==16
    for r in m['resource_deltas']:assert sha(Path(m['source_root'])/r['depot'])==r['after']
    assert sha(Path(m['archive']))==m['sha256']
    # Reconstruct the old driver from the proposed one and compare its receipt
    # hash. This verifies the seven other sites and all runtime safety are exact.
    script=Path(m['script']).read_bytes()
    token=b'q.GetFact(n"PTFRB0S4NIX_QuestOwns") == 0, commit)'
    assert script.count(token)==1 and b'mq016_active' not in script
    prior=script.replace(token,b'q.GetFact(n"PTFRB0S4NIX_QuestOwns") == 0 && q.GetFact(n"mq016_active") == 0, commit)')
    # apply_patch normalized the edited line ending; normalize to the source's
    # uniform CRLF convention before checking the original receipt bytes.
    prior=prior.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
    priorhash=hashlib.sha256(prior).hexdigest().upper()
    oldscript=next(f for f in receipt['files'] if f['path'].endswith('.reds'))
    assert priorhash==oldscript['sha256']==m['previous_script_sha256']
    assert sha(Path(m['script']))==m['script_sha256']
    clauses={c['type']['factName']:c['type'] for c in newguard['conditions']}
    required={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'q307_active':0,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q305_johnny_scene_active':0,'q115_point_of_no_return':0,'q000_done':1,'PTFRBASE_Suspended':0,'PTFRB0S4_Suspended':0,'PTFRB0S4NIX_Excluded':0,'PTFRB0S4NIX_QuestOwns':0,'PTFRB0S4NIX_Enabled':1,'nix_default_on':1}
    assert set(clauses)==set(required)
    assert evaluate(newguard,required|{'mq016_active':1})
    assert not evaluate(oldguard,required|{'mq016_active':1})
    negatives=0
    for key,value in required.items():
        bad=(0,-1) if key=='nix_default_on' else tuple(v for v in (-1,0,1,2) if v!=value)
        for v in bad:
            assert not evaluate(newguard,required|{key:v,'mq016_active':1});negatives+=1
    assert not evaluate(newguard,required|{'PTFRB0S4NIX_Enabled':0,'mq016_active':1})
    pre=read(BASE/'preending_save_facts.json');post=read(BASE/'afterlife_save_facts.json')
    for state in (pre,post):
        assert state['unchanged'] and state['facts']['nix_default_on']==[1] and state['facts']['mq016_active']==[1]
    assert post['facts']['q307_main_game_killed']==[1] and post['facts']['q307_done']==[1]
    assert post['facts']['PTFRB0S4NIX_Ready']==[1]
    assert post['facts']['PTFRB0S4NIX_Enabled']==[] and post['facts']['PTFRB0S4NIX_OwnerActive']==[]
    # Native phase stays parked on exactly the same node; driver transitions its
    # existing private enable flag. Actual engine save-token rebinding is live pending.
    assert {o['factName'] for o in walk(new) if o.get('$type')=='questSetVar_NodeType'}=={o['factName'] for o in walk(old) if o.get('$type')=='questSetVar_NodeType'}
    report=dict(status='PASS_NIX_GUARD_DELTA_OFFLINE_LIVE_PENDING',archive_sha256=m['sha256'],script_sha256=m['script_sha256'],changed_native_conditions=1,unchanged_payloads=15,only_driver_delta='Remove mq016_active == 0 in Nix eligibility',wrapper_node_ids_unchanged=True,nested_owner_edges_unchanged=True,negative_guard_cases=negatives,pre_and_post_mq016_active=1,pre_and_post_nix_default_on=1,sampled_ready=1,sampled_enable_and_owneractive_absent=True,save_token_migration='same native wait ID and resource; actual cold-load execution pending')
    (BASE/'nix_tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
