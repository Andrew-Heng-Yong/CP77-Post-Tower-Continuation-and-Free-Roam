"""Offline geometry payload/identity tests; no engine execution."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/misty_viktor_world'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def canonical(value):
    if isinstance(value,dict):
        return {k:canonical(v) for k,v in value.items() if k not in ('HandleId','BufferId')}
    if isinstance(value,list):
        return [canonical(v) for v in value]
    return value

def main():
    plan=read(BASE/'geometry_selection.json')
    manifest=read(BASE/'shell_manifest.json')
    assert manifest['status']=='OFFLINE_GEOMETRY_ARTIFACT_ONLY_NOT_REGISTERED_OR_INSTALLED'
    identities=set();counts={};checked=0
    for slot,row in enumerate(plan['source_ranges']):
        path=ROOT/row['raw_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['raw_sha256']
        source_json=str(row['raw_path']).replace('\\raw\\','\\json\\').replace('/raw/','/json/')+'.json'
        old=read(ROOT/source_json)['Data']['RootChunk']
        new=read(BASE/f'shell_{slot}.json')['Data']['RootChunk']
        assert new['variantIndices']==[0]
        assert len(new['nodeData']['Data'])==len(row['selected'])
        for placement,selection in zip(new['nodeData']['Data'],row['selected']):
            old_placement=old['nodeData']['Data'][selection['data_index']]
            old_node=old['nodes'][selection['node_index']]['Data']
            new_node=new['nodes'][placement['NodeIndex']]['Data']
            assert new_node['$type'] in plan['allow_types']
            assert canonical(old_node)==canonical(new_node),(slot,selection['data_index'],'node payload')
            expected={k:v for k,v in old_placement.items() if k not in ('Id','NodeIndex','QuestPrefabRefHash')}
            actual={k:v for k,v in placement.items() if k not in ('Id','NodeIndex','QuestPrefabRefHash')}
            assert canonical(expected)==canonical(actual),(slot,selection['data_index'],'placement transform/bounds')
            identity=placement['Id']
            assert identity not in identities and identity!=old_placement['Id']
            identities.add(identity)
            assert placement['QuestPrefabRefHash']['$value'] in ('0','')
            counts[new_node['$type']]=counts.get(new_node['$type'],0)+1
            checked+=1
        # No additional buffers/resources/annotations were silently introduced.
        assert set(old)==set(new)
    assert counts=={'worldCollisionNode':5,'worldStaticDecalNode':149,'worldStaticMeshNode':688},counts
    block=read(BASE/'shell_block.json')['Data']['RootChunk']
    assert len(block['descriptors'])==3
    private_ids={d['variants'][0]['variantId'] for d in block['descriptors']}
    assert len(private_ids)==1
    # Private range identity must not alias a vanilla world variant.
    for source_block in {row['source_block'] for row in plan['source_ranges']}:
        vanilla=read(ROOT/source_block)['Data']['RootChunk']
        assert not private_ids.intersection(v['variantId'] for d in vanilla['descriptors']
                                             for v in d.get('variants',[]))
    for slot,descriptor in enumerate(block['descriptors']):
        assert descriptor['numNodeRanges']==1
        assert descriptor['data']['DepotPath']['$value']==manifest['sectors'][slot]['depot']
        assert len(descriptor['variants'])==1
        variant=descriptor['variants'][0]
        assert variant['enabledByDefault']==0
        assert variant['name']['$value']==manifest['private_variant']
        assert variant['nodeRef']['$value']==manifest['variant_owner']
        assert variant['rangeIndex']==0 and variant['parentVariantID']==0
    assert hashlib.sha256(Path(manifest['archive']).read_bytes()).hexdigest().upper()==manifest['sha256']
    report={'status':'PASS_OFFLINE_INERT_GEOMETRY_ONLY_NOT_REGISTERED_INSTALLED_OR_LIVE_TESTED',
            'placements':checked,'new_unique_placement_ids':len(identities),
            'types':counts,'source_node_payloads_and_collision_buffers_preserved':True,
            'source_placement_transforms_and_bounds_preserved':True,
            'private_variant_id_has_no_source_world_block_collision':True,
            'original_variant_changes':0,'entities_triggers_communities_scenes':0,
            'default_enabled':False,'archive_sha256':manifest['sha256'],
            'pending':['native guarded ownership/controller','registration/live resolution',
                       'actual collider streaming/door route/lighting/visual pass']}
    (BASE/'shell_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
