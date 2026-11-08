"""Qualify graph callers and inventory every indexed Johnny occurrence in five closures."""
import json
import sqlite3
import sys
from pathlib import Path
from prepare_sources import TASK, WS, load, sha

sys.path.insert(0, str(WS / 'tools/parity_audit'))
from model import Resource


def main():
    source = load(TASK / 'evidence_01/source_inventory.json')
    exports = load(TASK / 'evidence_02/sources.json')
    models = {}
    for row in exports['resources']:
        assert row['status'] == 'EXPORTED', row
        assert sha(row['raw']) == row['sha256'] and sha(row['json']) == row['json_sha256']
        model = Resource(load(row['json'])).normalize()
        assert not model['errors'], (row['depot'], model['errors'])
        models[row['depot'].lower()] = {'source': row, 'model': model}
    con = sqlite3.connect((WS / 'prealpha/johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3').as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    quests = []
    for quest in source['quests']:
        calls = []
        for resource in quest['resources']:
            if resource['depot'].lower() not in models:
                continue
            m = models[resource['depot'].lower()]['model']
            for gp, graph in m['graphs'].items():
                for nid, node in graph['nodes'].items():
                    if node['type'] != 'questSceneNodeDefinition':
                        continue
                    payload = node['payload']
                    depot = payload.get('sceneFile', {}).get('DepotPath', {}).get('$value')
                    if not depot:
                        continue
                    inputs = [e for e in graph['edges'] if e[2] == nid and e[3] != 'CutDestination']
                    calls.append({'phase': resource['depot'], 'phase_sha256': resource['sha256'],
                                  'graph_path': gp, 'node_id': nid, 'scene_depot': depot,
                                  'incoming_edges': inputs, 'entry_names': sorted({e[3] for e in inputs}),
                                  'may_reachable_in_phase': nid in graph['reachable'],
                                  'caller_payload': payload})
        scenes = []
        for resource in quest['resources']:
            if 'indexed' not in resource:
                continue
            indexed = resource['indexed']
            root = indexed['resource_id'] + '/root'
            johnny = [dict(r) for r in con.execute("select * from search_items where resource_id=? and kind='DIALOGUE_EVENT' and speaker_role='JOHNNY'", (indexed['resource_id'],))]
            dispatch = [dict(r) for r in con.execute("select * from dispatches where resource_id=?", (indexed['resource_id'],))]
            callers = [c for c in calls if c['scene_depot'].lower() == resource['depot'].lower()]
            scenes.append({'resource': indexed, 'johnny_events': johnny, 'dispatches': dispatch,
                           'callers': callers, 'entries': [dict(r) for r in con.execute('select * from entries where root_id=?', (root,))]})
        q = {'id': quest['id'], 'title': quest['title'], 'registry': quest['registry'],
             'entry': quest['entry'], 'scenes': scenes, 'source_boundaries': quest['source_boundaries']}
        quests.append(q)
        print(q['id'], 'scenes', len(scenes), 'Johnny', sum(len(s['johnny_events']) for s in scenes),
              'dispatch_params', sum(len(s['dispatches']) for s in scenes))
        for scene in scenes:
            if scene['johnny_events']:
                print(' ', scene['resource']['resource_id'], 'Johnny', len(scene['johnny_events']),
                      'caller inputs', [(c['node_id'], c['entry_names']) for c in scene['callers']])
    out = TASK / 'evidence_03'
    assert not out.exists()
    out.mkdir()
    (out / 'phase_graphs.json').write_text(json.dumps(models, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'quest_dialogue_inventory.json').write_text(json.dumps({'quests': quests}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
