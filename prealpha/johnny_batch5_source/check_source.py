"""Check Batch 5 source parity and exercise the revised scene handoffs."""

from copy import deepcopy
from pathlib import Path
import sys

from resources import value, walk
from scene_edits import ReviewedScene

# The existing signal model imports its own JB1 prepare/verify modules.
JB1 = str(Path(__file__).resolve().parents[1] / 'johnny_batch2_jb1')
sys.path.insert(0, JB1)
try:
    from flow_fixtures import Signals
finally:
    sys.path.remove(JB1)


def phase_parity(depot, before, after):
    errors = []
    if Path(depot).name == 'sts_std_rcr_02_phase.questphase':
        errors = [{'kind': 'DANGLING_EDGE', 'graph': 'root', 'from': None, 'to': (node, 'In')}
                  for node in ('11', '13', '15', '2')]
    assert before['errors'] == after['errors'] == errors, depot
    for key in ('type', 'root_prefabs'):
        assert before[key] == after[key], (depot, key)
    assert before['graphs'].keys() == after['graphs'].keys(), depot
    for graph, old in before['graphs'].items():
        new = after['graphs'][graph]
        assert old['entries'] == new['entries'] and old['edges'] == new['edges'], (depot, graph)
        assert old['nodes'].keys() == new['nodes'].keys(), (depot, graph)
        for i, node in old['nodes'].items():
            for key in ('type', 'sockets', 'reads', 'writes', 'journal_paths', 'node_refs', 'prefabs'):
                assert node[key] == new['nodes'][i][key], (depot, graph, i, key)


def scene_parity(depot, before, after, doc, selection, change, relocations):
    filename = Path(depot).name
    s = ReviewedScene(doc, filename, change['bound_entries'])
    assert not before['errors'] and not after['errors'], depot
    old, new = (m['graphs']['scene'] for m in (before, after))
    assert old['entries'] == new['entries'] and old['nodes'].keys() == new['nodes'].keys(), depot
    original_scope = set(change['original_scope'])
    assert s.scope <= original_scope
    meta = deepcopy(before['metadata'])
    for key in ('entryPoints', 'exitPoints', 'screenplayStore', 'locStore', 'playerActors', 'props'):
        assert meta[key] == after['metadata'][key], (depot, key)
    for actor in meta['actors']:
        if actor['actorId']['id'] in s.actor_ids:
            actor['acquisitionPlan'] = 'spawnDespawn'
            for flag in ('isEnabled', 'alwaysSpawned', 'spawnOnStart', 'keepAlive',
                         'findInWorld', 'prefetchAppearance'):
                actor['spawnDespawnParams'][flag] = 0
    assert meta['actors'] == after['metadata']['actors'], depot

    cuts = {e['id']: e for e in change['events_removed']}
    assert len(cuts) == len(change['events_removed'])
    assert set(selection) == {i for i, e in cuts.items() if e['kind'] == 'scnDialogLineEvent'}, depot
    speakers = {line['itemId']['id']: line['speaker']['id'] for line in meta['screenplayStore']['lines']}
    menus = {row['node'] for row in change['options_removed']}
    assert menus == ({8} if filename == 'sts_wat_kab_03_johnny.scene' else set()), depot
    timers = {'sts_wat_nid_12_max_jones.scene': {889}, 'sts_wat_kab_05_johnny.scene': {39}}
    removed = set()
    for key, node in old['nodes'].items():
        i = int(key)
        expected = deepcopy(node['payload'])
        current = new['nodes'][key]['payload']
        for path in walk(expected):
            if path.get('$type') == 'ResourcePath' and value(path) in relocations:
                path['$value'] = relocations[value(path)]
        if i not in original_scope:
            assert expected == current, (depot, 'out of scope', i)
            continue
        expected['outputSockets'] = current['outputSockets']
        if i in menus:
            assert [o['screenplayOptionId']['id'] for o in expected['options']] == [2, 258, 514]
            expected['options'] = []
            expected['persistentLineEvents'] = [e for e in expected['persistentLineEvents']
                                                if str(e['id']) not in cuts]
        if i in timers.get(filename, ()):
            assert s.targeted(expected['questNode'])
            assert current['questNode']['condition']['type']['$type'] == 'questRealtimeDelay_ConditionType'
            expected['questNode']['condition'] = current['questNode']['condition']
        if 'actorBehaviors' in expected:
            expected['actorBehaviors'] = [a for a in expected['actorBehaviors']
                                          if a['actorId']['id'] not in s.actor_ids]
        timing = change['duration_changes'].get(i)
        shifts = {e['event']: e for e in timing['shifted_events']} if timing else {}
        if timing:
            assert expected['sectionDuration']['stu'] == timing['before_ms']
            expected['sectionDuration']['stu'] = timing['after_ms']
        if 'events' in expected:
            kept = []
            for event in expected['events']:
                eid = str(event['id']['id'])
                if eid in cuts:
                    assert cuts[eid]['node'] == i and cuts[eid]['kind'] == event['$type']
                    if eid in selection:
                        role = selection[eid]['speaker']
                        assert (speakers[event['screenplayLineId']['id']] in s.actor_ids) == (role == 'JOHNNY')
                    else:
                        assert s.targeted(event)
                    removed.add(eid)
                    continue
                if eid in shifts:
                    assert event['startTime'] == shifts[eid]['before']
                    event['startTime'] = shifts[eid]['after']
                kept.append(event)
            expected['events'] = kept
        assert expected == current, (depot, i)
        if i in s.scope:
            assert not s.targeted(current), (depot, 'Johnny presentation reachable', i)
            assert all(speakers[e['screenplayLineId']['id']] not in s.actor_ids
                       for e in current.get('events', []) if e['$type'] == 'scnDialogLineEvent'), (depot, i)
    assert removed == cuts.keys(), depot


def signal_checks(models):
    checks = []

    def record(name, signal, passed):
        assert passed, name
        checks.append({'name': name, **signal.result()})

    backs = models['sts_wat_kab_03_johnny.scene']
    for acknowledged, waiting in (((), '183'), ((183,), '192'), ((183, 192), '166')):
        s = Signals(backs, acknowledgements=acknowledged).start(1).run()
        record('Backs waits for world trigger ' + waiting, s, not s.ends
               and [x[1] for x in s.held] == ['117', waiting]
               and s.writes == [[100, 'kab_03_gun_shot', 1]])
    for meds in (False, True):
        ack = (117, 183, 192, 166) if meds else (183, 192, 166)
        s = Signals(backs, acknowledgements=ack).start(1).run()
        record('Backs gunshot and native exit with meds ' + str(meds), s,
               s.writes == [[50 if meds else 100, 'kab_03_gun_shot', 1]]
               and s.ends == [[3100 if meds else 3150, '2', 'Terminating']])
    parent = models['sts_wat_kab_03_openworld.questphase']['graphs']['root/16']
    assert ['10', 'End 0', '13', 'In'] in parent['edges']
    assert parent['nodes']['13']['node_refs'] == ['#kab_03_tr_johnny_dead_body']

    greed = models['sts_wbr_jpn_12_silverhand.scene']
    s = Signals(greed).start(1).run()
    record('Greed optional code waits for the doorway', s,
           [0, '80', 'NATIVE_CONDITION_ACK_REQUIRED'] in s.held and not s.writes)
    s = Signals(greed, acknowledgements=(80,)).start(1).run()
    record('Greed doorway enables the original code objective signal', s,
           s.writes == [[50, 'jpn_12_optional_code', 1]])
    s = Signals(greed, acknowledgements=(80,)).start(1).run(until=0)
    s.emit(20, '99', (1, 0))
    s.run()
    record('Greed native cancellation prevents a late code signal', s, not s.writes)
    s = Signals(greed, choices={'422': 0}, facts={'jpn_12_button_clicked': 1}).start(1).run()
    record('Greed movable fridge inspection still uses the V bark and player choice', s,
           [0, '425', 0, 1] in s.trace and s.writes == [[2000, 'jpn_12_movable_object_scanned', 1]])
    s = Signals(greed, acknowledgements=(155,), facts={'jpn_12_movable_object_scanned': 1}).start(1).run()
    record('Greed movable fridge button retains its device acknowledgement', s,
           [0, '38', 0, 1] in s.trace and s.writes == [[0, 'jpn_12_button_clicked', 1]])
    parent = models['sts_wbr_jpn_12_openworld.questphase']['graphs']['root/4/114']
    assert all(e in parent['edges'] for e in (
        ['13', 'Out', '4', 'Active'], ['4', 'Out', '7', 'In'], ['4', 'Out', '8', 'In'],
        ['7', 'Out', '9', 'Succeeded'], ['8', 'Out', '9', 'Succeeded'],
    ))

    family = models['sts_std_rcr_05_clues.scene']
    s = Signals(family).start(1).run()
    record('Family Matters safe waits for the clue choice or shard', s, not s.writes and not s.ends
           and s.held == [[0, '295', 'PLAYER_CHOICE'], [0, '337', 'NATIVE_CONDITION_ACK_REQUIRED']])
    s = Signals(family, choices={'295': 0}, acknowledgements=(267,)).start(1).run()
    record('Family Matters safe choice retains V and native clue and release facts', s,
           [0, '309', 0, 1] in s.trace and s.writes == [
               [0, 'rcr_05_johnny_scene_active', 1], [1050, 'rcr_05_pointed_to_safe', 1],
               [1050, 'rcr_05_johnny_scene_active', 0],
           ] and s.ends == [[1050, '2', 'Terminating']])
    s = Signals(family, acknowledgements=(337,)).start(1).run()
    record('Family Matters existing shard retains its alternative exit', s,
           not s.writes and s.ends == [[0, '2', 'Terminating']])

    freedom = models['sts_wat_nid_12_max_jones.scene']
    s = Signals(freedom).start(1280).run()
    record('Freedom waits for Max to be defeated or unconscious', s, not s.writes and not s.ends
           and s.held == [[0, '691', 'NATIVE_CONDITION_ACK_REQUIRED']])
    for q101 in (0, 1):
        s = Signals(freedom, acknowledgements=(691,), facts={'q101_done': q101}).start(1280).run()
        ends = [[2232, '421', 'NonTerminating']] + ([[2282, '1297', 'Terminating']] if q101 else [])
        record('Freedom retains V and native extraction exits on q101=' + str(q101), s,
               [0, '482', 0, 0] in s.trace and s.ends == ends
               and s.writes == [[0, 'nid_12_carry_max_start', 1]])

    last = models['sts_wat_kab_05_johnny.scene']
    s = Signals(last, acknowledgements=(51,)).start(27).run()
    record('Last Login waits for the actual body interaction', s,
           not s.ends and s.held == [[0, '50', 'PLAYER_CHOICE']])
    s = Signals(last, choices={'50': 0}, acknowledgements=(51,)).start(27).run()
    record('Last Login preserves the V bark and body focus cleanup', s,
           [0, '68', 0, 1] in s.trace and [2050, '60', 0, 1] in s.trace
           and s.ends == [[2100, '28', 'Terminating']])

    nasty = models['sts_std_arr_06_scn.scene']
    s = Signals(nasty, facts={'arr_06_johnny': 1}, stop=(140,)).start(53).run()
    record('Nasty Hangover keeps the real conversation with the old fact present', s,
           bool(s.stopped) and not {x[1] for x in s.trace} & {'293', '174'})
    s = Signals(nasty, stop=(661,)).start(207, 1).run()
    record('Nasty Hangover payment receipt is still connected', s,
           s.stopped == [[0, '661', 0, 1]] and s.writes == [[0, 'arr_06_johnny', 1]])

    for filename, start, end, kind in (
        ('sts_std_rcr_02_johnny.scene', 1, 2, 'Terminating'),
        ('sts_wbr_hil_06_johnny.scene', 1, 2, 'Terminating'),
        ('sts_hey_gle_04_johnny.scene', 1, 2, 'Terminating'),
        ('sts_wat_lch_05_johnny.scene', 1, 2, 'NonTerminating'),
        ('sts_wat_lch_05_johnny.scene', 16, 19, 'Terminating'),
    ):
        s = Signals(models[filename]).start(start).run()
        record(f'{filename} entry {start} skips to its native exit', s,
               s.ends == [[0, str(end), kind]] and not s.held and not s.writes)
    return checks
