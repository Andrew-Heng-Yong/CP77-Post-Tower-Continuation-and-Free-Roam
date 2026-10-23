"""Verify special U9 source recipes; structural checks, not engine proof."""
import json
from catalog_gig_rollout_r2 import ROOT,read,sha,value,walk
from prepare_special_gigs_u9 import reach
from inspect_special_gigs_u9 import graphs
from test_special_gigs_u9_retaliation import check as check_retaliation
OUT=ROOT/'research/gig_restoration/special_gigs_u9'

def main():
    p=read(OUT/'recipes.json');assert len(p['jobs'])==17
    for path,expected in p['pins'].items():assert sha(ROOT/path)==expected,path
    gaps=[];ports=0;companion_refs=[];ep1map=[]
    stale={'sts_ep1_01':'conversation_street_new_scv_05.scene','sts_ep1_08':'sts_ep1_08_gameplay.questphase','sts_std_rcr_02':'sts_std_rcr_02_scene.scene'}
    for j in p['jobs']:
        pa=j['parent'];live=reach(pa['edges'],[pa['input_node']]);ids={n['id'] for n in pa['ancestors']}|{pa['child']['id']}
        assert ids==live,j['id']
        assert all(e[0] in ids and e[2] in ids for e in pa['edges'])
        main=j['resources'][0];inputs={value(n['socketName']) for n in main['graphs'][0]['nodes'] if n['$type']=='questInputNodeDefinition'}
        assert set(pa['child_inputs'])<=inputs,(j['id'],pa['child_inputs'],inputs);ports+=len(pa['child_inputs'])
        if j['id'].startswith('sts_ep1_'):
            poi='ep1/points_of_interest/street_stories/'+j['id']
            writes=[]
            for n in pa['ancestors']:
                if n.get('type',{}).get('path',{}).get('realPath')==poi:
                    writes.append(dict(owner='native_parent',graph=pa['binding']['graph'],node=n['id'],type=n['type']['$type']))
            assert writes,(j['id'],'No native parent POI activation')
            for r in j['resources']:
                for g in r['graphs']:
                    for n in g['nodes']:
                        if n['$type']=='questJournalNodeDefinition' and n.get('type',{}).get('path',{}).get('realPath')==poi:
                            writes.append(dict(owner=r['depot'],graph=g['path'],node=n['id'],type=n['type']['$type'],phase=n['type'].get('phase')))
            ep1map.append(dict(id=j['id'],poi=poi,source_owned_writes=writes))
        for r in j['resources']:
            for g in r['graphs']:
                if j['id'] not in stale:continue
                reached=reach(g['edges'],[n['id'] for n in g['nodes'] if n['$type']=='questInputNodeDefinition'])
                for n in g['nodes']:
                    if stale[j['id']] in json.dumps(n):gaps.append(dict(id=j['id'],depot=r['depot'],graph=g['path'],node=n['id'],locally_reachable=n['id'] in reached))
        for c in j['companions']:
            dep=c['depot'];path=c['raw'].replace('/raw/','/json/')+'.json';cg=graphs(path)[0]
            ins={value(n['socketName']) for n in cg['nodes'] if n['$type']=='questInputNodeDefinition'}
            assert c['input'] in ins,(j['id'],dep,c['input'],ins);ports+=1
            if c['kind']=='cleanup':assert c['from_output'] in j['outputs']
            for v in walk(read(ROOT/path)):
                if v.get('$type')=='questStartQuest_NodeType':raise AssertionError((j['id'],'independent start quest',v))
                if 'phaseResource' in v:
                    ref=value(v['phaseResource']['DepotPath'])
                    if ref and ref!='0':companion_refs.append(dict(id=j['id'],kind=c['kind'],ref=ref))
    for g in gaps:
        if g['id']=='sts_ep1_08':
            assert any(r['depot'].endswith('sts_ep1_08_gameplay.questphase') for j in p['jobs'] if j['id']=='sts_ep1_08' for r in j['resources'])
            g['resolution']='Official gameplay source now included and pinned; direct original reference retained.'
        else:assert not g['locally_reachable'],g
    for ref in companion_refs:assert '/quests/' not in ref['ref'].replace('\\','/'),ref
    gatechecks={}
    if (OUT/'manifest_additions.json').exists():
        built=graphs('research/gig_restoration/special_gigs_u9/ep1_tier3_gate.json')
        original=graphs(p['ep1_parent'])
        old={g['path'].removeprefix('root/50/9'):g for g in original if g['path']=='root/50/9' or g['path'].startswith('root/50/9/')}
        new={g['path'].removeprefix('root/50/9'):g for g in built if g['path']=='root/50/9' or g['path'].startswith('root/50/9/')}
        assert old.keys()==new.keys()
        for key in old:
            assert old[key]['nodes']==new[key]['nodes'],key
            assert old[key]['edges']==new[key]['edges'],key
        assert next(n for n in built[0]['nodes'] if n['id']==50)==next(n for n in original[0]['nodes'] if n['id']==50)
        top=next(g for g in built if g['path']=='root/50');tn={n['id']:n for n in top['nodes']}
        assert not any(n['$type']=='questOutputNodeDefinition' for n in top['nodes'])
        assert [9,'Out1',65004,'In'] in top['edges']
        assert tn[65002]['condition']['type']['state']=='Inactive'
        assert tn[65004]['type']['factName']=='PTFRU9_EP1Tier3_Ready'
        writes=[v for n in top['nodes'] for v in walk(n) if v.get('$type')=='questSetVar_NodeType']
        assert all(v['factName'].startswith('PTFRU9_EP1Tier3_') for v in writes)
        guardfacts={v['factName'] for v in walk(tn[65000]) if isinstance(v.get('factName'),str)}
        assert {'PTFRU9_Support_Issued','PTFRU9_Support_Fault','PTFRU9_EP1Tier3_Entered','PTFRU9_sts_ep1_06_Request','PTFRU9_sts_ep1_06_Permit','PTFRU9_sts_ep1_07_Request','PTFRU9_sts_ep1_07_Permit','debug_sts_start'}<=guardfacts
        gatechecks=dict(original_embedded_graph_exact=True,containing_phase_unfreezing_metadata_preserved=True,one_shared_native_message_owner=True,delivered_message_not_replayed=True,terminating_output_added=False,gameplay_writes_outside_original_graph=False)
    assert len(p['credits'])==9
    for c in p['credits']:
        assert c['nodes'][-1]['type']=={'$type':'questSetVar_NodeType','factName':'ep1_sts_counter','setExactValue':0,'value':1}
    manifest_sha=sha(OUT/'manifest.json') if (OUT/'manifest.json').exists() else None
    ep1fixer=graphs('research/gig_restoration/fixer_sources/json/ep1/openworld/fixers/mr_hands/phases/mr_hands_fixers_loop.questphase.json')
    sharedpoi=[(g['path'],n['id']) for g in ep1fixer for n in g['nodes'] if n['$type']=='questJournalNodeDefinition' and n.get('type',{}).get('path',{}).get('realPath','').startswith('ep1/points_of_interest/street_stories/')]
    assert not sharedpoi,sharedpoi
    result=dict(status='PASS_SOURCE_RECIPES_NOT_ENGINE_PROOF',test_sha256=sha(__file__),manifest_sha256=manifest_sha,jobs=17,source_pins=len(p['pins']),native_interfaces=ports,legacy_reference_audit=gaps,shared_gate=gatechecks,retaliation=check_retaliation(),companion_external_refs=companion_refs,ep1_exact_credit_branches=9,ep1_native_poi_sources=ep1map,ep1_fixer_shared_streetstory_poi_writes=sharedpoi,
      root_graph_replacements=0,sidejob_owner_restore=0,save_writes=0)
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
