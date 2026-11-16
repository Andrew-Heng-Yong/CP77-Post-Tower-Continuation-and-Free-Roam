"""Verify the cooked resources, the retained quest paths and the combined input."""

from copy import deepcopy
from pathlib import Path
import sys

from baseline import HERE, OUT, PRE, REVIEW, read, sha, write
from edit_batch6 import Batch6Scene, reachable
from prepare_batch6 import ASSIGNMENT, DECISIONS, remap
from resources import Resource

sys.path.insert(0, str(PRE / 'johnny_batch2_jb1'))
from flow_fixtures import Signals
sys.path.pop(0)
from check_source import signal_checks as batch5_checks


def readback(batch):
    path = HERE / 'input_01' / (batch + '.json')
    proof = HERE / ('readback_' + batch) / 'manifest.json'
    plan, capture = read(path), read(proof)
    assert capture['status'] == 'JB4_RESOURCES_COOKED_AND_READ_BACK'
    assert capture['batch'] == batch and capture['plan_sha256'] == sha(path)
    rows = {r['depot']: r for r in capture['resources']}
    assert rows.keys() == {r['depot'] for r in plan['edits']} and len(rows) == len(capture['resources'])
    models, docs = {}, {}
    for edit in plan['edits']:
        depot = edit['depot']
        row = rows[depot]
        source = OUT / 'archive_source' / depot
        assert sha(source) == sha(row['raw']) == row['sha256'], depot
        assert sha(row['json']) == row['json_sha256']
        assert sha(edit['edited_json']) == edit['edited_json_sha256']
        expected = Resource(read(edit['edited_json'])).normalize()
        doc = read(row['json'])
        model = Resource(doc).normalize()
        assert expected == model, (depot, [k for k in expected if expected[k] != model[k]])
        if Path(depot).name == 'sts_std_rcr_02_phase.questphase':
            assert model['errors'] == [
                {'kind': 'DANGLING_EDGE', 'graph': 'root', 'from': None, 'to': (n, 'In')}
                for n in ('11', '13', '15', '2')
            ]
        else:
            assert not model['errors'], (depot, model['errors'])
        docs[depot], models[depot] = doc, model
    return plan, docs, models


def scene_parity(original, cooked, spec, evidence, aliases):
    filename = Path(spec['depot']).name
    remap(original, aliases, {})
    a, b = (Batch6Scene(d, spec) for d in (original, cooked))
    ma, mb = (s.r.normalize() for s in (a, b))
    old, new = (m['graphs']['scene'] for m in (ma, mb))
    assert old['entries'] == new['entries'] and old['nodes'].keys() == new['nodes'].keys()
    assert ma['metadata']['exitPoints'] == mb['metadata']['exitPoints']
    assert b.scope <= a.scope
    assert ma['metadata']['screenplayStore']['lines'] == mb['metadata']['screenplayStore']['lines']
    assert ma['metadata']['playerActors'] == mb['metadata']['playerActors']
    props = {int(i): v for i, v in evidence['removed_props'].items()}
    b.props = props
    b.prop_performers = {(i << 8) | 2 for i in props}
    assert [p for p in ma['metadata'].get('props', []) if p['propId']['id'] not in props] == mb['metadata'].get('props', [])
    for before, after in zip(ma['metadata']['actors'], mb['metadata']['actors'], strict=True):
        expected = deepcopy(before)
        if expected['actorId']['id'] in a.actor_ids:
            expected['acquisitionPlan'] = 'spawnDespawn'
            for key in ('isEnabled', 'alwaysSpawned', 'spawnOnStart', 'keepAlive',
                        'findInWorld', 'prefetchAppearance'):
                expected['spawnDespawnParams'][key] = 0
        assert expected == after
    targets = {e['event_id']: e['speaker_role'] for e in spec['speech_cuts']}
    cuts = {e['id']: e for e in evidence['events_removed']}
    assert targets == {i: e['speaker'] for i, e in cuts.items() if 'speaker' in e}
    menu_edits = {e['node_id']: e for e in spec['menu_edits']}
    for i, node in old['nodes'].items():
        before, after = node['payload'], new['nodes'][i]['payload']
        if node['type'] == 'scnQuestNode':
            # Branches change only at the scene sockets. Native command
            # payloads and their embedded quest sockets remain byte-equivalent.
            assert before['questNode'] == after['questNode'], (filename, i)
        if node['type'] == 'scnChoiceNode':
            expected = before['options']
            edit = menu_edits.get(i)
            if edit and edit['action'] == 'remove_johnny_exchange':
                expected = []
            elif edit and edit['action'] == 'consolidate_physical_choice':
                expected = expected[:1]
            assert expected == after['options'], (filename, i)
        if 'events' in before:
            timing = evidence['duration_changes'].get(i)
            shifts = {e['event']: e for e in timing['shifted_events']} if timing else {}
            expected = []
            for event in before['events']:
                eid = str(event['id']['id'])
                if eid in cuts:
                    assert cuts[eid]['node'] == int(i) and cuts[eid]['kind'] == event['$type']
                    assert eid in targets or b.targeted(event), (filename, i, eid)
                    continue
                event = deepcopy(event)
                if eid in shifts:
                    assert event['startTime'] == shifts[eid]['before']
                    event['startTime'] = shifts[eid]['after']
                expected.append(event)
            assert expected == after['events'], (filename, i)
        if int(i) in b.scope and node['type'] in ('scnQuestNode', 'scnChoiceNode'):
            assert not b.targeted(after), (filename, i)
    for row in spec['preserve_v']:
        assert row['event_id'] not in cuts
    assert all(int(r['node_id']) not in b.scope for r in spec['bark_dispatch_cuts'])

    allowed_lost_facts = {
        'sq023_07_restaurant.scene': {'sq023_j_smokes'},
        'sts_ep1_07_bomb_interaction.scene': {'sts_ep1_07_bomb_johnny_turning',
                                             'sts_ep1_07_bomb_johnny_pose',
                                             'sts_ep1_07_bomb_johnny_gesture'},
    }
    for entry, start in zip(spec['bound_entries'], a.starts, strict=True):
        before_scope = reachable(a.nodes, [start])
        after_scope = reachable(b.nodes, [start])
        for i in before_scope - after_scope:
            n = old['nodes'][str(i)]
            assert n['type'] != 'scnEndNode' and not n['reward'] and not n['journal_paths'], (filename, entry, i)
            if filename == 'sts_ep1_13_v_auction.scene' and i == 2014:
                assert 2011 in after_scope and n['writes'] == new['nodes']['2011']['writes']
            else:
                assert {w['factName'] for w in n['writes']} <= allowed_lost_facts.get(filename, set()), (filename, entry, i)
            assert n['type'] != 'scnChoiceNode' or str(i) in menu_edits, (filename, entry, i)
            assert all(e['$type'] != 'scnDialogLineEvent' or str(e['id']['id']) in targets
                       for e in n['payload'].get('events', [])), (filename, entry, i)
    return len(targets)


def fixtures(models):
    checks = []

    def run(filename, description, start, verify, ordinal=0, **kwargs):
        signal = Signals(models[filename], **kwargs).start(start, ordinal).run()
        assert verify(signal), (description, signal.result())
        checks.append({'name': description, **signal.result()})

    for filename in ('sts_cct_dtn_05_johnny.scene', 'sts_pac_cvi_02_johnny.scene'):
        run(filename, filename + ' uses its native exit', 1, lambda s: s.ends == [[0, '2', 'Terminating']])
    run('sts_wbr_jpn_05_johnny.scene', 'Wakako retains the V observation and native exit', 1,
        lambda s: [x[1] for x in s.trace][:2] == ['1', '4'] and s.ends[0][1] == '2')

    bomb = 'sts_ep1_07_bomb_interaction.scene'
    run(bomb, 'Bomb interaction waits for the native workspot condition', 1,
        lambda s: s.held == [[0, '49', 'NATIVE_CONDITION_ACK_REQUIRED']] and not s.ends)
    run(bomb, 'Detonator swap signals before the V unmount and terminating exit', 51,
        lambda s: s.ends == [[0, '2', 'NonTerminating'], [100, '237', 'Terminating']]
        and [x[1] for x in s.trace] == ['51', '59', '2', '201', '237'], ordinal=1)

    auction = 'sts_ep1_13_v_auction.scene'
    run(auction, 'Stand remains a player choice', 913,
        lambda s: s.held == [[0, '913', 'PLAYER_CHOICE']] and not s.writes)
    run(auction, 'Stand writes the original fact and clears the stool collision', 913,
        lambda s: s.writes == [[0, 'sts_ep1_13_get_up_bar', 1]]
        and [x[1] for x in s.trace][-2:] == ['2626', '857'], choices={'913': 0}, stop=(857,))

    rinder = 'sts_ep1_03_wagner_standoff.scene'
    run(rinder, 'Regina is optional', 2466,
        lambda s: s.held == [[0, '2466', 'PLAYER_CHOICE']] and not s.writes)
    run(rinder, 'Regina prompt unlocks the genuine outcome after player selection', 2466,
        lambda s: s.writes == [[0, 'sts_ep1_03_regina_mentioned', 1]]
        and s.stopped == [[0, '590', 0, 0]], choices={'2466': 0}, acknowledgements=(591,), stop=(590,))

    restaurant = 'sq023_07_restaurant.scene'
    run(restaurant, 'Restaurant farewell still publishes the journal and actual stand choice', 635,
        lambda s: [x[1] for x in s.stopped] == ['1136', '1328'], stop=(1136, 1328))
    run(restaurant, 'Rachel refusal returns to the physical stand choice', 657,
        lambda s: [x[1] for x in s.stopped] == ['1871'] and
        any(w[1:] == ['sq023_07_dof_lock_2', 1] for w in s.writes), stop=(1871,))

    core = 'sq025_10_resolution.scene'
    run(core, 'Delamain debate skip activates both native core callbacks', 1264,
        lambda s: [x[1] for x in s.stopped] == ['3014', '1988'], stop=(1988, 3014))
    for qualifies in (False, True):
        run(core, 'Delamain core decision after native skill results ' + str(qualifies), 1289,
            lambda s: [x[1] for x in s.held if x[2] == 'PLAYER_CHOICE'] == ['8'] and not s.ends,
            conditions={'1297': qualifies, '3014': qualifies})

    leash = 'sts_hey_spr_01_johnny_clues.scene'
    run(leash, 'Truck clue waits for player inspection', 236, lambda s: not s.writes and
        s.held == [[0, '236', 'PLAYER_CHOICE']])
    run(leash, 'Truck inspection still reports both native clue facts', 236,
        lambda s: [w[1:] for w in s.writes] == [['spr_01_truck_scanned', 1], ['spr_01_silverhand', 1]]
        and [x[1] for x in s.stopped] == ['11'], choices={'236': 0}, stop=(11,))

    coaster = 'mq006_02_finale.scene'
    run(coaster, 'Ride remains a physical get-in choice', 335,
        lambda s: s.held == [[0, '335', 'PLAYER_CHOICE']])
    run(coaster, 'Cart runs its original start signal without the Johnny-only repeat loop', 98,
        lambda s: s.stopped == [[3816, '40', 0, 0]] and
        not {x[1] for x in s.trace} & {'915', '917'}, stop=(40,))
    return checks


def main():
    result_path = HERE / 'verification_01.json'
    assert not result_path.exists()
    b5, _, m5 = readback('batch5')
    b6, d6, m6 = readback('batch6_02')
    assert sha(DECISIONS) == b6['decisions_sha256']
    assignment = read(ASSIGNMENT)
    capture = REVIEW / assignment['provider_scan']['manifest']
    assert sha(capture) == b6['capture_sha256']
    cap = {r['depot']: r for r in read(capture)['resources']}
    aliases = b6['aliases']
    scenes = {s['depot']: s for g in read(DECISIONS)['groups'] for s in g['scenes']}
    selected = 0
    for row in b6['edits']:
        depot = row['source_depot']
        if depot in scenes:
            path = capture.parent / cap[depot]['json']
            assert sha(path) == scenes[depot]['source_json_sha256']
            selected += scene_parity(read(path), d6[row['depot']], scenes[depot], row['scene_changes'], aliases)
    assert selected == 266
    phase_models = dict(m6)
    for call in b6['calls']:
        leaf = aliases.get(call['scene'], call['scene'])
        assert call['entry'] in m6[leaf]['graphs']['scene']['entries']
        for j, step in enumerate(call['chain']):
            parent = aliases.get(step['source'], step['source'])
            if parent not in phase_models:
                path = capture.parent / cap[parent]['json']
                assert sha(path) == cap[parent]['json_sha256']
                phase_models[parent] = Resource(read(path)).normalize()
            graph = phase_models[parent]['graphs'][step['graph']]
            assert step['edge'] in graph['edges']
            target = (call['chain'][j + 1]['source'] if j + 1 < len(call['chain']) else call['scene'])
            if target != step['source']:
                assert aliases.get(target, target) in graph['nodes'][step['edge'][2]]['refs']
    checked5 = batch5_checks({Path(d).name: m for d, m in m5.items()})
    checked6 = fixtures({Path(d).name: m for d, m in m6.items()})
    write(result_path, {
        'status': 'PASS_JB4_COOKED_AND_BOUNDED_FLOW',
        'batch5_plan_sha256': sha(HERE / 'input_01/batch5.json'),
        'batch6_plan_sha256': sha(HERE / 'input_01/batch6_02.json'),
        'batch5_readback_sha256': sha(HERE / 'readback_batch5/manifest.json'),
        'batch6_readback_sha256': sha(HERE / 'readback_batch6_02/manifest.json'),
        'batch5_resources': len(m5), 'batch6_resources': len(m6), 'batch6_scene_calls': len(b6['calls']),
        'batch5_signal_fixtures': checked5, 'batch6_signal_fixtures': checked6,
        'fixture_count': len(checked5) + len(checked6),
        'known_source_boundary': 'Four original Cuckoo phase null source endpoints were preserved in cooked readback.',
    })
    print(f'Verified {len(m5)+len(m6)} cooked resources and {len(checked5)+len(checked6)} bounded scene fixtures.')


if __name__ == '__main__':
    main()
