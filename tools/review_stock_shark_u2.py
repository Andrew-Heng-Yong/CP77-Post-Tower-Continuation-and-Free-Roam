"""Evidence for stock dependencies, not a native-engine simulation."""
import json,sys
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT,read,sha,walk
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
OUT=ROOT/'research/gig_restoration/stock_shark_u2'

def graph(path):
    r=SafeResource(read(ROOT/path));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}

def main():
    assert not (OUT/'install_receipt.json').exists()
    sources={}
    def load(path):sources[path]=sha(ROOT/path);return graph(path)
    qpath='research/q307_extracted/json/ep1/quest/main_quests/q307/q307.quest.json'
    q=load(qpath);root=q['root'];service=q['root/6']
    assert [16,'Out',18,'In'] in root['edges'] and [18,'Out',17,'In'] in root['edges']
    assert [17,'CutSource',6,'CutDestination'] in root['edges']
    assert [8,'Out1',5,'reset_in'] in service['edges']
    phonepath='research/gig_restoration/stock_shark_u2/sources/json/base/quest/holocalls/holocall_initializers.questphase.json'
    phone=load(phonepath)['root'];pn={n['id']:n for n in phone['nodes']}
    assert pn[84]['phaseResource']['DepotPath']['$value']==r'base\quest\holocalls\reggie\reggie_holocall.questphase'
    assert [25,'Out1',84,'In1'] in phone['edges']
    regpath='research/gig_restoration/stock_shark_u2/sources/json/base/quest/holocalls/reggie/reggie_holocall.questphase.json'
    reg=load(regpath)['root'];rn={n['id']:n for n in reg['nodes']}
    assert rn[37]['type']['factName']=='holo_reggie_calls_v_start_activate_count' and rn[37]['type']['value']==1
    assert rn[9]['type']['factName']=='holo_reggie_calls_v_start_activate_count' and rn[9]['type']['value']==-1
    countpath='research/gig_restoration/lifecycle_sources/json/base/open_world/street_stories/street_stories_new_fixer_loop.questphase.json'
    count=load(countpath)['root/2/5'];cn={n['id']:n for n in count['nodes']}
    assert cn[3]['condition']['type']['factName']=='kab_06_finished'
    assert cn[25]['type']=={'$type':'questSetVar_NodeType','factName':'wat_sts_counter','setExactValue':0,'value':1}
    assert [0,'Out',3,'In'] in count['edges'] and [3,'Out',25,'In'] in count['edges']
    assert sum(e[2]==25 for e in count['edges'])>1
    prepath='research/gig_restoration/batch_b4/sources/json/base/open_world/street_stories/watson/kabuki/sts_wat_kab_06/phase/sts_wat_kab_06_prestate_control.questphase.json'
    pre=load(prepath)['root'];nodes={n['id']:n for n in pre['nodes']}
    assert [30,'False',4,'In'] in pre['edges'] and [4,'False',5,'In'] in pre['edges']
    assert [26,'Out',3,'In'] in pre['edges'] and [3,'Out',22,'In'] in pre['edges']
    assert nodes[5]['type']['factName']=='kab_06_prestate_triggered'
    scenes=[]
    sceneRoot=ROOT/'research/gig_restoration/batch_b4/sources/json/base/open_world/street_stories/watson/kabuki/sts_wat_kab_06/scenes'
    for p in sceneRoot.glob('*.scene.json'):
        rel=str(p.relative_to(ROOT)).replace('\\','/');sources[rel]=sha(p)
        facts=sorted({v['factName'] for v in walk(read(p)) if isinstance(v.get('factName'),str) and v['factName'].startswith('holo_')})
        scenes.append(dict(path=rel,facts=facts))
    assert any('holo_reggie_calls_v_start_activate' in r['facts'] for r in scenes)
    installed=read(ROOT/'research/gig_restoration/native_reuse_u1/install_receipt.json')
    for f in installed['files']:assert sha(Path(installed['game_root'])/f['relative'])==f['sha256']
    result=dict(status='PASS_U2_STOCK_DEPENDENCY_SOURCE_AUDIT_NOT_ENGINE_PROOF',sources=sources,
        stock_completion_branch=dict(resource=countpath,graph='root/2/5',nodes=[0,3,25],edges=[[0,'Out',3,'In'],[3,'Out',25,'In']],whole_loop_replay_unsafe=True),
        stock_phone_lifecycle=dict(q307=qpath,initializer=phonepath,regina=regpath,
            startup='Q307 root/6 node5 enters stock initializer reset_in; initializer node84 starts Regina handler.',
            shutdown='Q307 root16 waits before_tomorrow Succeeded, then18->17 cuts service phase6.',
            caveat='Static source path; current runtime instance existence is NOT observable from an idle fact snapshot alone. Do not duplicate handler based solely on zero flags.'),
        prestate_dependency=dict(resource=prepath,warning='Original prestate modifies shop/service/security/mail/door state around tier gating. Not included in U1; current state and service overlap must be checked before restarting.'),
        scene_handshakes=scenes,installed_u1_hashes_unchanged=True,
        next='Use installed original-phase U1 on a pre-batch unused Shark snapshot and trace native call request/ack. Do not force phone locks or start duplicate global owners. Scope stock completion branch and missing dependencies after evidence.')
    (OUT/'source_review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result['status'])

if __name__=='__main__':main()
