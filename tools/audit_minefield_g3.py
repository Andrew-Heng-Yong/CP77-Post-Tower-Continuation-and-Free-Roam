"""Pinned G3 source/capture review, not a restoration adapter or freshness proof."""
import json
from catalog_gig_rollout_r2 import ROOT, read, sha, walk, value
from audit_activity_batches_b1 import flatten, references, stable_write
from audit_activity_lifecycles_b1 import scene_summary
from test_rite_g2 import SafeResource

OUT=ROOT/'research/gig_restoration/minefield_g3'
IDENT='sts_bls_ina_07'

def main():
    inventory=read(OUT/'sources/inventory.json')
    assert len(inventory)==10
    pins={}
    scenes=[]
    for row in inventory:
        raw=OUT/'sources/raw'/row['resource'];js=OUT/'sources/json'/(row['resource']+'.json')
        assert row['decode_error'] is None and sha(raw)==row['raw_sha256'] and sha(js)==row['json_sha256']
        pins[str(js.relative_to(ROOT)).replace('\\','/')]=sha(js)
        if row['resource'].endswith('.scene'):scenes.append(scene_summary(js))
    catalogue_path=ROOT/'research/gig_restoration/rollout_r2/catalogue.json'
    job=next(j for j in read(catalogue_path)['jobs'] if j['id']==IDENT)
    resources={}
    irreversible=[]
    types={'questGiveReward_NodeType','questAddRemoveItem_NodeType','questInjectLoot_NodeType','questSetVar_NodeType','questVehicleNodeCommandParams','VehicleQuestVisualDestructionEvent','questCheckpointNodeDefinition','questSceneNodeDefinition','questSetCommunity_NodeType','questSetPrefabVariant_NodeType'}
    for meta in job['native_resources']:
        path=ROOT/meta['source'];assert sha(path)==meta['sha256']
        pins[meta['source']]=sha(path)
        obj=read(path);r=SafeResource(obj);root=obj['Data']['EmbeddedFiles'][meta['embedded_index']]['Content']
        graphs=flatten(r,root)
        resources[meta['depot_path']]={'source':meta,'prefabs':root.get('phasePrefabs'),'graphs':graphs,'phase_references':references(root,'phaseResource'),'scene_references':references(root,'sceneFile')}
        for graph in graphs:
            for node in graph['nodes']:
                if any(v.get('$type') in types for v in walk(node)):
                    irreversible.append({'resource':meta['depot_path'],'graph':graph['path'],'node':node['id'],'payload':node})
    pair_path=ROOT/'research/gig_restoration/rollout_r2/live_pair.json'
    pair=read(pair_path)['pair'];captured=[]
    for sample in pair:
        snap=sample['snapshot'];assert snap['stable'] and not snap['errors'] and not snap['changed_facts']
        paths=[j['path'] for j in job['journal_entries']]
        states=[snap['journal'][p]['state'] for p in paths]
        facts={k:v for k,v in snap['facts'].items() if 'ina_07' in k or k in ('bls_achievement','bls_sts_counter')}
        captured.append({'world':sample['world'],'utc':sample['utc'],'ordered_states':states,'facts':facts,'not_captured':['#ina_07_ready','#ina_07_body_scan','bls_sts_counter']})
    assert {x['world'] for x in captured}=={'PRE_TOWER','POST_TOWER'}
    # Early journal stage differs only in Tower's failed active entries.
    pre=next(x for x in captured if x['world']=='PRE_TOWER')
    post=next(x for x in captured if x['world']=='POST_TOWER')
    assert pre['ordered_states']==[2,2,1,2,1,1,1,1,1,1,1,1,1,1,2]
    assert post['ordered_states']==[4,4,1,4,1,1,1,1,1,1,1,1,1,1,2]
    ow=resources[job['native_resources'][0]['depot_path']]
    initial=next(g for g in ow['graphs'] if g['path']=='root/10')
    initial_facts=[v for n in initial['nodes'] for v in walk(n) if v.get('$type')=='questSetVar_NodeType']
    assert any(value(v.get('factName'))=='ina_07_start' for v in initial_facts)
    damage=[x for x in irreversible if any(v.get('$type')=='VehicleQuestVisualDestructionEvent' and v.get('accumulate')==1 for v in walk(x['payload']))]
    assert len(damage)==1
    comments=next(s for s in scenes if s['johnny_cast'])
    assert len(scenes)==3 and sum(s['johnny_cast'] for s in scenes)==1
    actors={str(a['name']).casefold() for s in scenes for a in s['actors']}
    assert not actors.intersection({'panam','judy','kerry'})
    pins[str(catalogue_path.relative_to(ROOT)).replace('\\','/')]=sha(catalogue_path)
    pins[str(pair_path.relative_to(ROOT)).replace('\\','/')]=sha(pair_path)
    result={'status':'SOURCE_CAPTURE_AUDIT_CONTINUATION_NOT_IMPLEMENTED','id':IDENT,'title':job['title'],'resources':resources,'irreversible_actions':irreversible,'scene_reviews':scenes,'captures':captured,'source_inputs':pins,'damage_action':damage,'proposed_route':'Saved early find_car continuation; not fresh start or completed replay','findings':['Native initial route repeats additive ready/start and must be bypassed for prior-start continuation.','Physical owner contains accumulated vehicle visual damage; safe resume must not apply it twice.','Comments scene spawns Character.Silverhand; JV1 root-visual presentation is installed but renderer/audio behavior remains unproven.','No independently acquired props in this comments scene; detached FX/general prop coverage still unproven.','Dakota pre/debrief holocalls manipulate shared phone facts; native fallback and reward/outcome routes need exact review.','Badlands achievement/fixer-counter ownership must be audited separately from Watson.','Captured ready/body-scan/counter absence is missing evidence, not zero or freshness.'],'remaining':['Vehicle/community/save-state admission and non-repeating damage/setup','Exact play entry and chase/delivery variants','Dakota native phone fallback and guarded reward/counter ownership','Native failure and departure cleanup','Scoped native owner build, R3 dispatcher/history integration, offline checks/install','Combined native gameplay, Johnny voice/no-model, reward and new-save/reload test'],'admitted_new_activities':0,'completed_replay':False,'runtime_ready':False,'game_writes':0,'save_writes':0}
    stable_write(OUT/'source_review.json',result)
    print(json.dumps({'status':result['status'],'resources':len(resources),'graphs':sum(len(r['graphs']) for r in resources.values()),'scenes':len(scenes),'damage_node':damage[0]['node'],'admitted_new_activities':0},indent=2))
if __name__=='__main__':main()
