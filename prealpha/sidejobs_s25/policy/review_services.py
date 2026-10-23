"""Independent bounded S25 Gun/Paid ownership and no-reward-cycle review."""
import copy, json
from pathlib import Path
from prepare import ROOT, read, sha, graphs, walk
from native_inspect import SafeResource


def scene(path):
    r=SafeResource(read(path));return r.payload(r.obj['Data']['RootChunk'])


def nodes(s):return {n['nodeId']['id']:n for n in s['sceneGraph']['graph']}


def reach(ns,start):
    result=set();todo=list(start)
    while todo:
        i=todo.pop()
        if i in result:continue
        result.add(i)
        for socket in ns[i]['outputSockets']:
            todo.extend(d['nodeId']['id'] for d in socket['destinations'])
    return result


def main():
    build=ROOT/'prealpha/sidejobs_s25/services/build/services_06'
    m=read(build/'build.json');c=read(ROOT/m['contract']);owners={o['key']:o for o in c['owners']}
    for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
    for p,h in m['resources'].items():assert sha(build/'source'/p)==h,p
    tests=read(build/'tests.json');assert tests['component_sha256']==sha(build/'build.json')
    assert tests['tester_sha256']==sha(ROOT/'prealpha/sidejobs_s25/services/test.py')
    original=lambda raw:build/m['native_readbacks'][raw]
    gun=owners['GUN'];g=graphs(build/'readback/gun.json')['root'];gn={n['id']:n for n in g['nodes']}
    sn=nodes(scene(build/'readback/gun_scene.json'));stock=nodes(scene(original(gun['scene_native'])))
    assert reach(sn,[0])==set(sn)
    # Completing the order cannot loop back to the reward or ask-order entry.
    after_reward=[d['nodeId']['id'] for socket in sn[212]['outputSockets'] for d in socket['destinations']]
    post=reach(sn,after_reward)
    assert not ({42,209,212,281,369,430}&post)
    assert set(o['caption']['$value'] for o in sn[177]['options'])=={'Shop'}
    assert sn[212]==stock[212] and sn[281]==stock[281] and sn[430]==stock[430]
    assert sn[209]==stock[209] and sn[369]==stock[369]
    assert sn[369]['questNode']['type']['path']['realPath']==gun['journals'][0]['path']
    assert gn[1008]['condition']['type']['path']['realPath']==gun['journals'][0]['path']
    assert gn[1008]['condition']['type']['state']=='Succeeded'
    # Sole existing B0 body/actor lease retained; new branch is just scene choice.
    old=graphs(original(gun['body_current']))['root'];new=graphs(build/'readback/wilson_body.json')['root']
    on={n['id']:n for n in old['nodes']};nn={n['id']:n for n in new['nodes']}
    assert all(nn[i]==n for i,n in on.items())
    assert set(nn)-set(on)=={100,101}
    request=copy.deepcopy(on[5]);request['id']=101;request['sceneFile']['DepotPath']['$value']=gun['scene_depot']
    assert request==nn[101]
    edges=set(map(tuple,new['edges']));delta={(4,'Out',100,'In'),(100,'False',5,'wilson_default_in'),(100,'True',101,'wilson_default_in'),(12,'CutSource',101,'CutDestination')}
    assert (edges-delta)|{(4,'Out',5,'wilson_default_in')}==set(map(tuple,old['edges']))
    assert not any(p.endswith('owner.questphase') for p in m['resources'])
    assert not any(n['$type']=='questSpawnManagerNodeDefinition' for n in gn.values())
    assert not any(x.get('$type')=='questSetVar_NodeType' and x.get('factName') in {'PTFRB0WV_Near','q001_spawn_wilson_attention','q101_spawn_wilson_attention'} for x in walk(g))
    # Debt selector uses the existing Viktor scene; exact stock economic conditions.
    paid=owners['PAID'];vn=nodes(scene(build/'readback/viktor_scene.json'))
    before=nodes(scene(original(paid['scene_current'])));native=nodes(scene(original(paid['scene_native'])))
    assert set(vn)==set(before)==set(native)
    for i in set(vn)-{351,840}:assert vn[i]==before[i]
    for i in (351,840):
        option=vn[i]['options'][1];expected=native[i]['options'][1]
        assert option['bluelineCondition']==expected['bluelineCondition']
        cond=option['questCondition'];assert cond['operation']=='AND' and len(cond['conditions'])==5
        assert cond['conditions'][3]==expected['questCondition']
        assert vn[i]['outputSockets'][1]==native[i]['outputSockets'][1]
    newly_reachable=reach(vn,[1,640])-reach(before,[1,640])
    assert newly_reachable=={50,156,324,454,1129,1132,1136,1141,1144}
    assert all(vn[i]==native[i] for i in newly_reachable)
    pgraph=graphs(build/'readback/paid.json')['root'];pn={n['id']:n for n in pgraph['nodes']}
    assert pn[12]['condition']['type']['factName']=='victor_debt_paid_full'
    assert pn[11]['type']['path']['realPath']==paid['journals'][0]['path']
    for o,ns in ((gun,gn),(paid,pn)):
        # These two current captured roots are Succeeded, never a forced fresh test.
        row=next(x for x in read(ROOT/c['capture'])['second']['jobs'] if x['id']==o['id'])
        assert row['rootState']=='Succeeded'
        roots=[x for x in walk(ns[1003]['condition']) if x.get('$type')=='questJournalEntryState_ConditionType' and x['path']['realPath']==o['journals'][0]['path']]
        assert len(roots)==1 and roots[0]['state']=='Inactive'
        assert ns[1002]['condition']==ns[1003]['condition']
    result={'status':'PASS_INDEPENDENT_BOUNDED_REVIEW_NOT_LIVE','component_sha256':sha(build/'build.json'),'reviewer_sha256':sha(Path(__file__)),
            'post_reward_reachable_nodes':sorted(post),'reward_reachable_from_itself':False,'gun_existing_actor_owner_only':True,
            'native_payment_path_retained':True,'paid_newly_reachable_native_nodes':sorted(newly_reachable),'new_admission_inactive_only':True,
            'completed_capture_roots_protected':['sq_q001_wilson','mq045_victor_debt'],'findings':[],
            'source_pins':m['source_pins'],'limits':'No live new-save vendor-stock, dialogue, payment/reward, streaming interruption or saved-engine continuation proof. Aggregate official-byte/resource audit remains a deployment prerequisite.'}
    out=ROOT/'research/sidejobs_s25/policy/services_review_01.json';assert not out.exists()
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='source_pins'}))


if __name__=='__main__':main()
