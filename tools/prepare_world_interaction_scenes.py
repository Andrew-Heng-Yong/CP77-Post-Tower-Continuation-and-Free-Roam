"""Generate a V/cart-only derivative of vanilla's standalone coaster route."""
import copy
import json
from pathlib import Path
from audit_world_interactions import walk
from audit_interaction_routes import reachable

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/b0_world_interactions'

def rebuild_handles(document, definitions):
    """Retain shared identity, including definitions first serialized in removed nodes."""
    assigned = {}
    def visit(x):
        if isinstance(x, list):
            return [visit(v) for v in x]
        if not isinstance(x, dict):
            return x
        if 'HandleId' in x or 'HandleRefId' in x:
            old = str(x.get('HandleId', x.get('HandleRefId')))
            if old in assigned:
                return {'HandleRefId': assigned[old]}
            new = str(len(assigned))
            assigned[old] = new
            data = x.get('Data', definitions[old])
            return {'HandleId': new, 'Data': visit(data)}
        return {k: visit(v) for k,v in x.items()}
    return visit(document)

def prepare():
    p = BASE / 'dependencies/json/base/quest/minor_quests/mq006/scenes/mq006_02_finale.scene.json'
    doc = json.loads(p.read_text(encoding='utf-8-sig'))
    defs = {str(o['HandleId']): o['Data'] for o in walk(doc) if 'HandleId' in o}
    r = doc['Data']['RootChunk']
    # Only the standalone start is retained. Remove the optional Jean-party
    # lifepath chatter branch, not any ride, mount, unmount or cleanup edge.
    nodes = {n['Data']['nodeId']['id']: n['Data'] for n in r['sceneGraph']['Data']['graph']}
    for socket in nodes[515]['outputSockets']:
        socket['destinations'] = [d for d in socket['destinations'] if d['nodeId']['id'] != 932]
    # Revision3: Hands up reproduced a native fault in the optional cinematic
    # cheer path. Keep the gesture via the same mounted-seat workspot mechanism
    # already used by vanilla641/643/645, not a simultaneous SkAnim overlay.
    # Fresh handles are essential when cloning shared scene-node templates.
    fresh_id = 10000
    def fresh_copy(value):
        nonlocal fresh_id
        assigned = {}
        def visit(x):
            nonlocal fresh_id
            if isinstance(x, list): return [visit(v) for v in x]
            if not isinstance(x, dict): return x
            if 'HandleId' in x or 'HandleRefId' in x:
                old = str(x.get('HandleId', x.get('HandleRefId')))
                if old in assigned: return {'HandleRefId': assigned[old]}
                ident = str(fresh_id); fresh_id += 1; assigned[old] = ident
                return {'HandleId': ident, 'Data': visit(x.get('Data', defs[old]))}
            return {k:visit(v) for k,v in x.items()}
        result = visit(value)
        defs.update({str(o['HandleId']):o['Data'] for o in walk(result) if 'HandleId' in o})
        return result
    workspot_paths = []
    out = BASE / 'batch'
    out.mkdir(exist_ok=True)
    wp_path = BASE / 'coaster_crash/json/base/workspots/quest/minor_quests/mq006/player__sit_rollercoaster_train_lean_back__sit_around__02.workspot.json'
    wp_original = json.loads(wp_path.read_text(encoding='utf-8-sig'))
    clip_path = BASE / 'coaster_crash/json/base/workspots/common/ground/generic__stand_ground__stand_around__02.workspot.json'
    clip_template = next(o for o in walk(json.loads(clip_path.read_text(encoding='utf-8-sig'))) if o.get('$type') == 'workAnimClip')
    for variant,node_id in ((1,558),(2,559)):
        wp = copy.deepcopy(wp_original)
        wh = {str(o['HandleId']):o['Data'] for o in walk(wp) if 'HandleId' in o}
        tree = wp['Data']['RootChunk']['workspotTree']['Data']
        seq = tree['rootEntry']['Data']['list'][0]['Data']
        idle = copy.deepcopy(seq);idle['id']['id']=6;idle['loopInfinitely']=1
        idle['list'][0]['Data']['id']['id']=7
        clip = copy.deepcopy(clip_template);clip['id']['id']=5
        clip['animName']['$value']=f'sit_rollercoaster__2h_on_chest__01__cheer__0{variant}'
        seq['list']=[{'HandleId':'1000','Data':clip},{'HandleId':'1001','Data':idle}]
        tree['idCounter']=7
        wh.update({str(o['HandleId']):o['Data'] for o in walk(wp) if 'HandleId' in o})
        (out/f'coaster_hands_{variant}_prepared.json').write_text(json.dumps(rebuild_handles(wp,wh),indent=2),encoding='utf-8')
        depot=f'towercontinued\\world_interactions\\coaster_hands_{variant}.workspot'
        workspot_paths.append(depot)
        replacement=fresh_copy(nodes[643])
        replacement['nodeId']['id']=node_id
        replacement['questNode']['Data']['id']=node_id
        params=replacement['questNode']['Data']['paramsV1']['Data']
        params['workspotInstanceId']['id']=node_id
        # Preserve revision5's idle-mode experiment for a single-variable test.
        # Its live result was silent; idle0 has not proved action playback.
        params['enableIdleMode']=0
        # Revision6 candidate: explicitly target the authored cheer clip instead
        # of sequence2's calm idle. Keep revision5's other parameters unchanged
        # so this tests entry selection alone; visible playback is not yet proven.
        params['entryId']['id']=5
        # Native callbacks require BOTH declared sockets, even when unused.
        # Revision4 omitted Success0; its dump shows the engine reading one
        # record past the table on that callback. Keep its empty destination.
        for socket in replacement['outputSockets']:
            socket['destinations']=[]
        nodes[node_id].clear();nodes[node_id].update(replacement)
        instance=copy.deepcopy(next(w for w in r['workspotInstances'] if w['workspotInstanceId']['id']==643))
        instance['workspotInstanceId']['id']=node_id;instance['dataId']['id']=4000000000+variant
        r['workspotInstances'].append(instance)
        wp_def=fresh_copy(next(w for w in r['workspots'] if w.get('Data',{}).get('dataId',{}).get('id')==2386669590))
        wp_def['Data']['dataId']['id']=4000000000+variant
        wp_def['Data']['workspotResource']['DepotPath']['$value']=depot
        r['workspots'].append(wp_def)
    # The old section's start input is ordinal0; quest action In is ordinal1.
    # Keeping ordinal0 silently invokes CutDestination instead of UseWorkspot.
    for socket in nodes[561]['outputSockets']:
        for destination in socket['destinations']:
            assert destination['nodeId']['id'] in (558,559)
            destination['isockStamp']['ordinal']=1
    _, keep = reachable(r, 509)
    r['sceneGraph']['Data']['graph'] = [n for n in r['sceneGraph']['Data']['graph'] if n['Data']['nodeId']['id'] in keep]
    r['entryPoints'] = [x for x in r['entryPoints'] if x['nodeId']['id'] == 509]
    r['exitPoints'] = [x for x in r['exitPoints'] if x['nodeId']['id'] in keep]
    r['notablePoints'] = []
    for key in r['debugSymbols']:
        if key != '$type':
            assert isinstance(r['debugSymbols'][key], list)
            r['debugSymbols'][key] = []
    assert not any(e['Data']['$type'] == 'scnDialogLineEvent' for i in keep for e in nodes[i].get('events', []))
    r['screenplayStore']['lines'] = []
    # Dense indexing is mandatory: ordinary cart0, player1. The prologue
    # crash precedent showed why simply deleting Johnny is insufficient.
    r['actors'] = [r['actors'][6]]
    # Revision4 combined repair: the live standalone lipsync table contains
    # one entry, while the original player's index6 survived cast reduction.
    # The exit dump proves index6/count1 at native resource acquisition. Use
    # the V-only index0 pattern already validated by Streetkid S2 and mirrors.
    player_lip = r['playerActors'][0]['lipsyncAnimSet']['id']
    assert player_lip == 6
    r['resouresReferences']['lipsyncAnimSets'] = [r['resouresReferences']['lipsyncAnimSets'][player_lip]]
    r['playerActors'][0]['lipsyncAnimSet']['id'] = 0
    mapping = {6: 0, 7: 1}
    for n in r['sceneGraph']['Data']['graph']:
        if 'actorBehaviors' in n['Data']:
            n['Data']['actorBehaviors'] = [b for b in n['Data']['actorBehaviors'] if b['actorId']['id'] in mapping]
    for o in walk(r):
        if o.get('$type') == 'scnActorId' and o['id'] != 4294967295:
            assert o['id'] in mapping, ('Unexpected surviving actor', o)
            o['id'] = mapping[o['id']]
        if o.get('$type') == 'scnPerformerId' and o['id'] != 4294967040:
            actor, kind = o['id'] >> 8, o['id'] & 255
            assert actor in mapping, ('Unexpected surviving performer', o)
            o['id'] = mapping[actor] * 256 + kind
        if o.get('factName') == 'mq006_ride_finished':
            o['factName'] = 'PTFRWORLD_Coaster_Finished'
    # Preserve original cart/spline/trigger targets, but qualify every known
    # NodeRef using its unique compiled world instance.
    refs = {}
    for name in ('quest_f816da004b0f9f78', 'quest_dc94c198a1cbdae9'):
        sector = json.loads((BASE / f'extended/json/base/worlds/03_night_city/_compiled/default/{name}.streamingsector.json').read_text(encoding='utf-8-sig'))['Data']['RootChunk']
        for d in sector['nodeData']['Data']:
            full = d['QuestPrefabRefHash']['$value']
            short = full[full.rfind('/#')+1:]
            if short in refs:
                assert refs[short] == full
            refs[short] = full
    for o in walk(r):
        if o.get('$type') == 'NodeRef' and o.get('$value') in refs:
            o['$value'] = refs[o['$value']]
    result = rebuild_handles(doc, defs)
    (out / 'coaster_scene_prepared.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    (out / 'coaster_refs.json').write_text(json.dumps(refs, indent=2), encoding='utf-8')
    (out / 'coaster_scene_delta.json').write_text(json.dumps({'entry':509, 'nodes':sorted(keep), 'removed_chatter_edge':[515,932], 'actor_map':mapping, 'private_bridge':'PTFRWORLD_Coaster_Finished', 'hands_workspots':workspot_paths, 'hands_cinematic_sections_replaced':[558,559], 'player_lipsync_map':{6:0}, 'lipsync_table':'V only'}, indent=2), encoding='utf-8')
    print('Prepared standalone coaster:', len(keep), 'nodes; cart0/player1; no Johnny/Jean cast or quest progression')

if __name__ == '__main__':
    prepare()
