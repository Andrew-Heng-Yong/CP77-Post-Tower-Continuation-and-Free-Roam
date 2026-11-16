"""Verify cooked speech, owner routing, and bounded scene/phase contracts."""

from collections import Counter, defaultdict
from copy import deepcopy
import sqlite3
import sys

from prepare import BASE, HERE, INPUT, NATIVE_POD_SCENE, PRIVATE_POD_SCENE, PROPHET, SPACE_POD_PHASE
from resources import Resource, WS, actor_reference, load, read, sha, value, walk, write

sys.path.append(str(BASE.parent))
from flow_fixtures import Signals


def name(path):
    return path.rsplit('\\', 1)[-1]


def edges(graph):
    return {tuple(edge) for edge in graph['edges']}


def has(graph, source, port, dest, input_port):
    return (str(source), port, str(dest), input_port) in edges(graph)


def spoken(model):
    return {str(e['id']['id']): (i, e) for i, n in model['graphs']['scene']['nodes'].items()
            for e in n['payload'].get('events', []) if e['$type'] == 'scnDialogLineEvent'}


PHASE_CHANGE_NODES = {
    'mq010_03_columbarium.questphase': {('root', '8')},
    'mq032_02_maelstrom.questphase': {('root', '83')},
}


def phase_parity(row, raw_model, new_model, plan):
    source = row['source']['depot']
    doc = load(row['source'])
    remap = plan['aliases'] | ({NATIVE_POD_SCENE: PRIVATE_POD_SCENE}
                              if name(source) == 'mq003_enemy_intercept.questphase' else {})
    counted = Counter()
    for x in walk(doc):
        if x.get('$type') == 'ResourcePath' and value(x) in remap:
            counted[value(x)] += 1
            x['$value'] = remap[value(x)]
    assert counted == row['reference_changes']
    reference = Resource(doc).normalize()
    assert reference['metadata'] == new_model['metadata'], source
    assert reference['embedded_files'] == new_model['embedded_files'], source
    assert reference['graphs'].keys() == new_model['graphs'].keys(), source
    changes = set()
    for path, original in reference['graphs'].items():
        g = new_model['graphs'][path]
        assert original['entries'] == g['entries']
        assert set(original['nodes']) <= set(g['nodes'])
        additions = set(g['nodes']) - set(original['nodes'])
        expected_additions = {'100', '101', '102'} if (
            name(source) == 'mq010_03_columbarium.questphase' and path == 'root') else set()
        assert additions == expected_additions, (source, path, additions)
        for i, n in original['nodes'].items():
            if n != g['nodes'][i]:
                changes.add((path, i))
        removed = edges(original) - edges(g)
        added = edges(g) - edges(original)
        if source in PROPHET and path == 'root':
            assert removed == {('1004', 'True', '1005', 'In')} and not added
            assert '1005' not in g['reachable'] and '1006' not in g['reachable']
        elif source == SPACE_POD_PHASE and path == 'root':
            assert removed == {('78', 'Out', '79', 'Active'), ('79', 'Out', '75', 'retrieve_pod_reaction')}
            assert added == {('78', 'Out', '75', 'retrieve_pod_reaction')}
        elif (name(source), path) == ('mq019_03_night_club.questphase', 'root/108'):
            assert removed == {('11', 'Out', '12', 'In'), ('29', 'Out', '15', 'In')} and not added
        elif name(source) == 'mq032_01_hook.questphase' and path == 'root':
            assert removed == {('24', 'True', '19', 'Active')} and added == {('24', 'True', '10', 'Active')}
        elif name(source) == 'mq032_02_maelstrom.questphase' and path == 'root':
            assert removed == {('127', 'True', '128', 'Active')} and added == {('127', 'True', '131', 'Active')}
        elif name(source) != 'mq010_03_columbarium.questphase':
            assert not removed and not added, (source, path, removed, added)
    assert changes == PHASE_CHANGE_NODES.get(name(source), set()), (source, changes)
    assert raw_model['root_prefabs'] == new_model['root_prefabs'], source


def scene_parity(row, src, cooked, selected, index):
    depot = row['source']['depot']
    evidence = row['scene_evidence']
    cast = [a for a in cooked['metadata']['actors'] if 'johnny' in a['actorName'].lower()]
    assert cast and all(a['acquisitionPlan'] == 'spawnDespawn' and
                        all(not a['spawnDespawnParams'][f] for f in ('isEnabled', 'alwaysSpawned', 'spawnOnStart'))
                        for a in cast)
    actor_ids = {a['actorId']['id'] for a in cast}
    original, after = spoken(src), spoken(cooked)
    deleted = set(original) - set(after)
    assert set(selected) <= deleted
    assert set(after) <= set(original)
    assert index.keys() == original.keys(), (depot, set(original) ^ index.keys())
    assert all(index[i][0] != 'JOHNNY' for i in after), depot
    for i in deleted:
        assert index[i][0] == 'JOHNNY' or index[i][0] == 'V', (depot, i, index[i])
        if i not in selected:
            assert index[i][0] == 'V' and name(depot) in {
                'mq003_pod.scene', 'mq010_03_columbarium.scene', 'mq019_04_manager.scene'}
    assert deleted == {e['id'] for e in evidence['events_removed'] if 'speaker' in e}
    original_graph, edited_graph = src['graphs']['scene'], cooked['graphs']['scene']
    assert original_graph['entries'] == edited_graph['entries']
    assert set(original_graph['nodes']) == set(edited_graph['nodes'])
    assert src['metadata']['exitPoints'] == cooked['metadata']['exitPoints']
    for i in edited_graph['reachable']:
        p = edited_graph['nodes'][i]['payload']
        assert not actor_reference(p.get('questNode'), actor_ids), (depot, i)
        if p['$type'] == 'scnChoiceNode':
            assert not actor_reference(p, actor_ids), (depot, i)
        for event in p.get('events', []):
            if event['$type'] != 'scnDialogLineEvent':
                assert not actor_reference(event, actor_ids), (depot, i, event['id'])
    for i, (node, event) in after.items():
        prior_node, before = original[i]
        expected = deepcopy(before)
        timing = evidence['duration_changes'].get(node, {})
        for change in timing.get('shifted_events', []):
            if change['event'] == i:
                expected['startTime'] = change['after']
        assert prior_node == node and event == expected, (depot, i)
    if name(depot) == 'mq030_01_melisa.scene':
        for i, before in original_graph['nodes'].items():
            before_payload, after_payload = before['payload'], edited_graph['nodes'][i]['payload']
            assert before_payload.get('sectionDuration') == after_payload.get('sectionDuration')
            events = {str(e['id']['id']): e for e in before_payload.get('events', [])}
            for e in after_payload.get('events', []):
                assert events[str(e['id']['id'])] == e, (i, e['id'])
    return Counter(index[i][0] for i in deleted)


def fixtures(scene, phases):
    cases = {}

    def run(label, filename, start, ends, *, ordinal=0, **kwargs):
        result = Signals(scene[filename], **kwargs).start(start, ordinal).run()
        assert [e[1] for e in result.ends] == [str(i) for i in ends], (label, result.result())
        cases[label] = result.result()
        return result

    g = phases[SPACE_POD_PHASE]['graphs']['root']
    for wire in [(116, 'Out', 78, 'Succeeded'), (78, 'Out', 75, 'retrieve_pod_reaction'),
                 (75, 'retrieve_pod_reaction_out', 56, 'Succeeded'),
                 (75, 'johnny_disappear', 77, 'In2'), (89, 'Out', 77, 'In1')]:
        assert has(g, *wire), wire
    run('space_reward_then_cleanup', 'mq003_pod.scene', 41, [40, 68])
    run('space_soldier_bark_retained', 'mq003_pod.scene', 23, [24])

    plaque = 'mq010_03_columbarium.scene'
    for option in (0, 1):
        trace = run(f'plaque_option_{option}', plaque, 402, [2, 54], ordinal=1,
                    choices={'39': option}, conditions={'44': True})
        assert trace.ends[0][0] < trace.ends[1][0]
    run('plaque_without_selection_holds', plaque, 402, [], ordinal=1, conditions={'44': True})
    c = phases['mq010_03_columbarium.questphase']['graphs']['root']
    for wire in [(71, 'Out', 56, 'In'), (48, 'Out', 8, 'Start 0'), (71, 'Out', 21, 'In'),
                 (8, 'End 0', 100, 'In'), (100, 'CutSource', 21, 'CutDestination'),
                 (100, 'Out', 52, 'In'), (52, 'Out', 11, 'Succeeded'),
                 (21, 'Out', 101, 'In'), (101, 'CutSource', 8, 'CutDestination'),
                 (101, 'Out', 51, 'In'), (51, 'Out', 23, 'Failed'),
                 (11, 'Out', 102, 'In1'), (23, 'Out', 102, 'In2'),
                 (102, 'Out1', 9, 'In'), (9, 'Out', 14, 'In'),
                 (8, 'End 1', 59, 'In1'), (26, 'Out1', 59, 'In2')]:
        assert has(c, *wire), wire
    assert c['nodes']['102']['type'] == 'questLogicalXorNodeDefinition'
    assert not any(i in c['reachable'] for i in ('22', '25', '69'))

    stash = 'mq015_04_stash.scene'
    run('stash_without_open_holds', stash, 1, [])
    run('stash_open_without_take_holds', stash, 1, [], choices={'179': 0}, conditions={'21': False})
    for branch in (False, True):
        outcome = run(f'stash_grant_branch_{int(branch)}', stash, 1, [2, 222],
                      choices={'179': 0, '192': 0}, conditions={'21': branch})
        assert sum(row[1] == '195' for row in outcome.trace) == 1
        assert 'nix_old_school_expert' not in outcome.facts
    g = phases['mq015_03_stash.questphase']['graphs']['root']
    assert has(g, 12, 'out', 16, 'In') and has(g, 16, 'Out', 14, 'In')

    run('violence_skips_relic_and_cheating_exchange', 'mq019_04_manager.scene', 200, [202])
    graph = phases['mq019_03_night_club.questphase']['graphs']
    assert has(graph['root/51'], 38, 'Out', 30, 'Succeeded')
    assert has(graph['root/51'], 2, 'out_johnny', 39, 'In')
    assert has(graph['root/108'], 11, 'Out', 14, 'In') and has(graph['root/108'], 29, 'Out', 21, 'Succeeded')
    assert has(graph['root/108'], 8, 'Out', 17, 'In')

    m = scene['mq030_01_melisa.scene']['graphs']['scene']
    assert m['nodes']['1855']['payload']['options']
    assert {'24', '25', '780', '1000', '1281', '1282'}.isdisjoint(m['reachable'])
    g = phases['mq030.questphase']['graphs']
    assert has(g['root'], 43, 'Out1', 63, 'In1') and has(g['root'], 63, 'Out1', 64, 'In1')
    assert '#mq030_suit_store_com' in g['root/43']['nodes']['7']['node_refs']
    assert '#mq030_suit_store_com' in g['root/64']['nodes']['56']['node_refs']

    hook = scene['mq032_01_hook.scene']['graphs']['scene']
    assert not hook['nodes']['134']['payload']['options'] and '134' not in hook['reachable']
    monk = scene['mq032_02_maelstrom.scene']['graphs']['scene']
    assert has(monk, 463, '0:0', 231, '0:1')
    assert has(monk, 231, '0:0', 49, '0:0') and has(monk, 231, '0:0', 454, '0:1')
    assert 'FullGameplay' in str(monk['nodes']['231']['payload'])
    epilogue = scene['mq032_03_epilogue.scene']['graphs']['scene']
    assert len(epilogue['nodes']['61']['payload']['options']) == 3 and '77' not in epilogue['reachable']
    run('sacrum_epilogue_other_choices_wait', 'mq032_03_epilogue.scene', 61, [])
    run('sacrum_maelstrom_reward_and_control', 'mq032_02_maelstrom.scene', 463, [49], ordinal=1)

    result = run('car_approach_continues_investigation', 'mq050_johnny_start.scene', 1, [7, 2])
    assert result.ends[1][0] - result.ends[0][0] == 50
    return cases


def main():
    plan_path = INPUT / 'plan.json'
    rb_path = HERE / 'readback_02/manifest.json'
    out = HERE / 'verification_02.json'
    assert not out.exists()
    plan, rb = read(plan_path), read(rb_path)
    assert rb['plan_sha256'] == sha(plan_path)
    assert sha(plan['selection']) == plan['selection_sha256']
    selection = read(plan['selection'])
    selected = defaultdict(set)
    for e in selection['exact_speech_targets']:
        selected[e['depot']].add(str(e['event_id']))
    by_depot = {r['depot']: r for r in rb['resources']}
    assert set(by_depot) == {e['depot'] for e in plan['edits']}
    scenes, phases, removed = {}, {}, Counter()
    db = WS / 'prealpha/johnny_dialogue_index_20261107_02/index_05/dialogue.sqlite3'
    assert sha(db) == 'A60FEA94BDD5C7777484710E57753F558C80CFD36E553BE03DF02CB8EF459D2E'
    db_rows = defaultdict(dict)
    scene_depots = [row['source']['depot'] for row in plan['edits'] if row['scene_evidence']]
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as conn:
        placeholders = ', '.join('?' for _ in scene_depots)
        for depot, event_id, speaker, line in conn.execute(
            "SELECT s.depot,e.event_id,s.speaker_role,s.text FROM events e JOIN search_items s "
            "ON e.event_key=s.item_key WHERE s.kind='DIALOGUE_EVENT' AND s.depot IN (" + placeholders + ")",
            scene_depots):
            db_rows[depot][event_id] = (speaker, line)
    for row in plan['edits']:
        depot = row['depot']
        fresh = by_depot[depot]
        assert sha(fresh['raw']) == fresh['sha256'] and sha(fresh['json']) == fresh['json_sha256']
        assert sha(row['edited_json']) == row['edited_json_sha256']
        original = Resource(load(row['source'])).normalize()
        planned = Resource(read(row['edited_json'])).normalize()
        cooked = Resource(read(fresh['json'])).normalize()
        assert not original['errors'] and not cooked['errors'] and cooked == planned, depot
        if row['scene_evidence']:
            origin = row['source']['depot']
            removed.update(scene_parity(row, original, cooked, selected[origin], db_rows[origin]))
            scenes[name(depot)] = cooked
        else:
            phase_parity(row, original, cooked, plan)
            if row['is_new']:
                phases[name(depot)] = cooked
            else:
                phases[depot] = cooked
    assert removed == {'JOHNNY': 46, 'V': 24}, removed
    for option in selection['selected_native_options']:
        # Scope the reused numeric option ID to its own scene and choice.
        relevant = [row for row in plan['edits'] if row['source']['depot'] == option['depot']]
        row, = relevant
        cut, = row['scene_evidence']['options_removed']
        assert str(cut['node']) == str(option['node_id'])
        assert str(cut['option']['screenplayOptionId']['id']) == str(option['option_id'])
    for row in plan['edits']:
        assert row['depot'].startswith('towercontinued\\')
    old = read(plan['baseline_package'])
    assert all(p not in old['source_resources'] for p in plan['aliases'].values())
    compilation = read(HERE / 'compile_01/result.json')
    assert compilation['status'] == 'PASS_JB2_COMPLETE_SOURCE_COMPILE'
    assert compilation['overlays'] == plan['scripts'] and compilation['source_count'] == 148
    case_data = fixtures(scenes, phases)
    write(out, {'status': 'PASS_JB2_COOKED_AND_BOUNDED_FLOW',
                'plan_sha256': sha(plan_path), 'readback_sha256': sha(rb_path),
                'resources': len(by_depot), 'speech_removed': dict(removed),
                'fixture_count': len(case_data), 'fixtures': case_data,
                'scope': 'Readback and bounded signal checks. Scene engine, save transitions, presentation and gameplay remain live tests.',
                'game_writes': 0, 'save_writes': 0})
    print(f"Validated {len(by_depot)} cooked resources, {sum(removed.values())} spoken cuts and {len(case_data)} scene fixtures.")


if __name__ == '__main__':
    main()
