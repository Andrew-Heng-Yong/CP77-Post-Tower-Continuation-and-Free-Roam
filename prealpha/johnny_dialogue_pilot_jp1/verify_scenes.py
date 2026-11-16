"""Independently constrain cooked JP1 semantics and the native pickup route."""
import collections
import copy
import json
import sys
from pathlib import Path
from prepare_changes import HERE, WS, FREEZER, read, sha, walk, write

sys.path.insert(0, str(WS / 'tools/parity_audit'))
from model import Resource


def without_selected_references(value, removed):
    if isinstance(value, dict):
        return {key: without_selected_references(child, removed) for key, child in value.items()}
    if isinstance(value, list):
        return [without_selected_references(child, removed) for child in value if not (
            isinstance(child, dict) and child.get('$type') == 'scnSceneEventId' and str(child.get('id')) in removed)]
    return value


def main():
    out = HERE / 'validation_05'
    assert not out.exists()
    out.mkdir()
    plan = read(HERE / 'input_03/plan.json')
    cooked = read(HERE / 'readback_03/cooked.json')
    assert cooked['plan_sha256'] == sha(HERE / 'input_03/plan.json')
    actuals = {r['resource_id']: r for r in cooked['resources']}
    results = []
    total_removed = 0
    for edit in plan['edits']:
        rid = edit['resource']['resource_id']
        row = actuals[rid]
        assert sha(row['path']) == row['sha256'] and sha(row['readback']) == row['readback_sha256']
        before_raw = Resource(read(edit['source_json']))
        after_raw = Resource(read(row['readback']))
        before = before_raw.normalize()
        after = after_raw.normalize()
        assert not before['errors'] and not after['errors']
        assert before['metadata'] == after['metadata'], 'Actor, line/localization, marker or other root metadata changed.'
        assert before['root_prefabs'] == after['root_prefabs'] and before['embedded_files'] == after['embedded_files']
        assert set(before['graphs']) == set(after['graphs'])
        removed = set(edit['removed_event_ids'])
        for gp, b in before['graphs'].items():
            a = after['graphs'][gp]
            assert b['entries'] == a['entries'] and set(b['nodes']) == set(a['nodes'])
            for nid, original in b['nodes'].items():
                actual = a['nodes'][nid]
                expected = copy.deepcopy(original['payload'])
                expected['events'] = [e for e in expected.get('events', []) if not (
                    e.get('$type') == 'scnDialogLineEvent' and str(e['id']['id']) in removed)] if 'events' in expected else expected.get('events')
                if expected.get('events') is None:
                    expected.pop('events', None)
                expected = without_selected_references(expected, removed)
                if rid == FREEZER and gp == 'scene' and nid in ('28', '284'):
                    stamp, old, new = (2, 40, 42) if nid == '28' else (0, 88, 90)
                    sock, = [s for s in expected['outputSockets'] if s['stamp']['name'] == stamp and s['stamp']['ordinal'] == 0]
                    assert sock['destinations'][0]['nodeId']['id'] == old
                    sock['destinations'][0]['nodeId']['id'] = new
                assert actual['payload'] == expected, ('Unexpected node semantic change', rid, gp, nid)
                for field in original:
                    if field not in ('payload', 'payload_sha256'):
                        assert actual[field] == original[field], (rid, gp, nid, field)
            original_edges = collections.Counter(tuple(e) for e in b['edges'])
            actual_edges = collections.Counter(tuple(e) for e in a['edges'])
            if rid == FREEZER and gp == 'scene':
                assert original_edges - actual_edges == collections.Counter({('28', '2:0', '40', '0:0'): 1, ('284', '0:0', '88', '0:0'): 1})
                assert actual_edges - original_edges == collections.Counter({('28', '2:0', '42', '0:0'): 1, ('284', '0:0', '90', '0:0'): 1})
                assert set(b['reachable']) - set(a['reachable']) == {'40', '82', '85', '539', '88', '93'}
                assert not set(a['reachable']) - set(b['reachable'])
                for nid in ['90', '461', '470', '638', '252', '45', '460', '473', '476', '631', '490', '671']:
                    assert nid in a['reachable'], ('Native pickup/controller path lost', nid)
                for menu in ('40', '88'):
                    assert a['nodes'][menu]['type'] == b['nodes'][menu]['type']
                    assert a['nodes'][menu]['id'] == b['nodes'][menu]['id']
                    assert a['nodes'][menu]['payload']['options'] == b['nodes'][menu]['payload']['options'], 'Saved option IDs/indices must remain stable.'
            else:
                assert original_edges == actual_edges and b['reachable'] == a['reachable']
        before_dialogue = {str(e['id']['id']): e for e in walk(before_raw.root) if e.get('$type') == 'scnDialogLineEvent'}
        after_dialogue = {str(e['id']['id']): e for e in walk(after_raw.root) if e.get('$type') == 'scnDialogLineEvent'}
        assert set(before_dialogue) - set(after_dialogue) == removed
        assert not set(after_dialogue) - set(before_dialogue)
        assert all(e == after_dialogue[key] for key, e in before_dialogue.items() if key not in removed)
        assert not [e for e in walk(after_raw.root) if e.get('$type') == 'scnSceneEventId' and str(e.get('id')) in removed]
        # Removing references/debug entries may not affect any other typed event ID.
        prior_ids = collections.Counter(str(e['id']) for e in walk(before_raw.root) if e.get('$type') == 'scnSceneEventId')
        new_ids = collections.Counter(str(e['id']) for e in walk(after_raw.root) if e.get('$type') == 'scnSceneEventId')
        assert {k: v for k, v in prior_ids.items() if k not in removed} == dict(new_ids)
        total_removed += len(removed)
        results.append({'depot': row['depot'], 'source_sha256': edit['resource']['raw_sha256'],
                        'after_sha256': row['sha256'], 'removed_dialogue_events': len(removed),
                        'retained_dialogue_events': len(after_dialogue), 'all_other_node_payloads_and_ids_preserved': True,
                        'source_graphs': list(before['graphs']), 'fixed_section_durations_preserved': edit['durations']})
    assert total_removed == 37 and len(plan['option_selections']) == 4
    assert sum(e['speaker'] == 'Johnny' for e in plan['dialogue_selections']) == 25
    assert not plan['unlisted_johnny_events_pending_review']
    write(out / 'scene_verification.json', {
        'status': 'PASS_JP1_COOKED_SEMANTIC_ALLOWLIST_AND_PICKUP_FLOW', 'plan_sha256': sha(HERE / 'input_03/plan.json'),
        'cooked_manifest_sha256': sha(HERE / 'readback_03/cooked.json'), 'resources': results,
        'spoken_events_removed': 37, 'johnny_events_removed': 25, 'v_events_removed': 12, 'options_bypassed_in_normal_entry_flow': 4,
        'saved_node_identity_policy': 'Keep menus 40/88 and their saved option IDs serialized; bypass via existing sections 42/90. Saves already in these menus retain native exits but are not removal-transition-qualified.',
        'recognition_history': 'Existing flag value retained; no synthetic recognition write, reset or replacement fact. The old flag increment remains serialized only on its legacy native choice path.',
        'native_callback_policy': 'Keep section 90 fixed duration, non-dialogue events, timed workspot socket, journal success and all Open/Take branches. No new fact writes, owners, rewards or forced inventory.',
        'gameplay_status': 'PENDING_USER_TEST', 'game_writes': 0, 'save_writes': 0})
    print('PASS: all 25 Johnny events and 12 V events removed; four options bypassed through two reviewed edge replacements; native pickup and other semantics retained.')


if __name__ == '__main__':
    main()
