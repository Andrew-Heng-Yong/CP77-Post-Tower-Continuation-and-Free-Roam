"""Independently check the Meet Kirk route, provider readback and saved owners."""

from collections import Counter
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parents[1]
sys.path.insert(0, str(PREALPHA / 'resume_dispatcher_rd5_gigs_20261113_01'))
from verify_batch import ancestry, graph, load_export, normalize, read, readonly, reachable, registrations, saved_records, sha, value, write


def verify_copy(name, part, original, emitted, plan):
    assert original['support'] == emitted['support'], name
    old_scopes = {item['path']: item for item in original['graphs']}
    new_scopes = {item['path']: item for item in emitted['graphs']}
    expected_new_scopes = {'root/61002'} if name == 'hook' else set()
    assert new_scopes.keys() == old_scopes.keys() | expected_new_scopes
    shells = {f'root/{node_id}' for node_id, _ in part.get('calls', [])}
    for path in old_scopes.keys() - {'root'} - shells:
        assert old_scopes[path] == new_scopes[path], (name, path)
    for path in shells:
        shell = new_scopes[path]
        old_shell = old_scopes[path]
        assert shell['nodes'][:-1] == old_shell['nodes']
        assert shell == old_shell | {'nodes': shell['nodes'], 'inputs': [*old_shell['inputs'], part['shell_entry']]}
        assert shell['nodes'][-1]['id'] == part['shell_entry']
        assert shell['nodes'][-1]['type'] == 'questInputNodeDefinition'
        assert value(shell['nodes'][-1]['parameters']['socketName']) == plan['socket']
        assert shell['edges'] == []
    if name == 'hook':
        assert new_scopes['root/61002'] == old_scopes['root/6'] | {'path': 'root/61002'}

    old, old_edges = graph(original, 'root')
    new, new_edges = graph(emitted, 'root')
    additions = [(a, socket, 'Output', b, target, 'Input') for a, socket, b, target in part['edges']]
    assert Counter(new_edges) == Counter(old_edges) + Counter(additions)
    assert new.keys() == old.keys() | {part['entry'], *(b for _, b in part.get('clones', []))}
    assert new[part['entry']]['$type'] == 'questInputNodeDefinition'
    assert value(new[part['entry']]['socketName']) == plan['socket']
    before_nodes = {node['id']: node for node in old_scopes['root']['nodes']}
    after_nodes = {node['id']: node for node in new_scopes['root']['nodes']}
    redirected = dict(part.get('calls', []))
    for node_id, prior in old.items():
        current = after_nodes[node_id]
        before = before_nodes[node_id]
        if node_id in redirected:
            assert value(new[node_id]['phaseResource']['DepotPath']) == plan['prefix'] + redirected[node_id] + '.questphase'
            assert new[node_id]['phaseResource']['Flags'] == prior['phaseResource']['Flags']
            assert new[node_id] | {'phaseResource': prior['phaseResource']} == prior
            assert current['sockets'] == [*before['sockets'], {'name': plan['socket'], 'type': 'Input'}]
            assert current['from_any_input'] == before['from_any_input']
        else:
            assert current == before, (name, node_id)
    for source_id, clone_id in part.get('clones', []):
        assert after_nodes[clone_id] == before_nodes[source_id] | {'id': clone_id, 'parameters': old[source_id] | {'id': clone_id}}


def from_entry(resource, scope, entry):
    _, edges = graph(resource, scope)
    return reachable([entry], [(a, b) for a, _, x, b, _, y in edges if (x, y) == ('Output', 'Input')])


def verify_ownership(plan):
    saved = PREALPHA / 'handler_preservation_hp1_20261112_01/saves_01'
    fixtures = {
        'ManualSave-26': '6BEFAEE9EA1FA77A515C5A1EC9C867EA5B5DACB166D637D24B1423260E9C2AA4',
        'AutoSave-10': 'FD6FF356B859E32281E3E8A885FA015CAACF9755FD37E964636129E181A23741',
        'AutoSave-11': '8CC828F9AA88A861E3B6E8DA8B8142A79264B1BC57FC0805B40B129C8253FD1D',
        'AutoSave-5': '2971FA17A5BF63ECCFCE7DB6CD1993A01F46928FDBEC7797DDE019FB3430DC01',
    }
    owners = {'body': 7347, 'kirk_phone': 7818, 'kirk_phone_cleanup': 10730,
              'encounter_bugfixes': 1535, 'quest_bugfixes': 5605, 'cinematic_bugfixes': 11185}
    with readonly('registry_02/registry.sqlite3') as db:
        for name, rid in owners.items():
            routes = ancestry(db, rid)
            assert len(routes) == 1, name
            assert [step[2] for step in routes[0]] == plan['native_saved_paths'][name], name

    results = {}
    for slot, digest in fixtures.items():
        fixture = saved_records(saved / slot)
        assert fixture[0]['source_sha256'] == digest
        paths = {name: registrations(tuple(prefix), fixture) for name, prefix in plan['native_saved_paths'].items()}
        results[slot] = {'source_sha256': digest, 'owners': paths}
        assert all(row['freezer_groups'] == 0 for row in paths.values())
        assert [row['cached_paths'] for row in paths.values()] == [5, 1, 0, 1, 7, 2]
        if slot in ('ManualSave-26', 'AutoSave-10'):
            assert [len(row['descendant_nodes']) for row in paths.values()] == [3, 8, 0, 1, 2, 1]
            assert [[0, 2, 82, 6, 22, 24, 2, 6], 4] in paths['body']['descendant_nodes']
        else:
            assert all(not row['descendant_nodes'] and not row['ancestor_nodes'] for row in paths.values())
    return results


def verify_stage(game):
    history = game / 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/snapshot_hs3_20261112T193931Z_1_3.json'
    assert sha(history) == 'C27598B50A97F3B7D3DD4905CEF1EB8C0F8FB67DF2865933E022B58D5D13D8F0'
    snapshot = read(history)
    assert (snapshot['schema'], snapshot['origin'], snapshot['route'], snapshot['ticket'], snapshot['revision']) == (3, 'pre_native_cleanup', 1, 1, 1)
    assert snapshot['catalogue'] == 'C518094308849C32611EB2C471A047C548BEC668C30F873B0CCFED00DD5B08DD'
    root = 'quests/minor_quest/mq017_streetkid'
    phase = root + '/mq017_streetkid'
    objective = phase + '/01_meet_kirk'
    wanted = {root, phase, objective, objective + '/description'}
    journals = {row['definition']['path']: row for row in snapshot['rows'] if row['definition']['kind'] == 'journal'
                and row['definition']['path'].startswith(root)}
    assert all(journals[path]['stable'] and journals[path]['state'] == 2 for path in wanted)
    later = {path: row for path, row in journals.items() if row['definition']['class'] == 'gameJournalQuestObjective' and path != objective}
    assert len(later) == 14
    assert all(row['stable'] and row['state'] == 1 for row in later.values())
    assert journals[objective]['optional'] == journals[objective]['counter'] == 0
    facts = {row['definition']['name']: row for row in snapshot['rows'] if row['definition']['kind'] == 'fact'}
    wanted_facts = {name: 0 for name in facts if name.startswith('mq017_')}
    wanted_facts |= {'mq017_started': 1, 'sq018_done': 1, 'q101_enable_side_content': 1, 'ep1_standalone': 0,
                     'holo_kirk_calls_v_start_count': 2, 'holo_kirk_calls_v_end_count': 1,
                     'holo_kirk_calls_v_interrupted': 1, 'holo_kirk_calls_v_start_activate': 0, 'holo_kirk_calls_v_end_activate': 0}
    assert all(facts[name]['stable'] and facts[name]['value'] == expected for name, expected in wanted_facts.items())

    post = PREALPHA / 'history_capture_hs3_20261112_01/fixtures_saves_01/ManualSave-27.json'
    assert sha(post) == '92290F8515EC5B3BC69EAE0F90F77881EE87FBA67D268D0FB4049E50E21B507A'
    saved = read(post)
    assert saved['sha256'] == 'D3BA63623BAE8306B854110D4746AB80B5DED502FF1BAC71387CD1FA0FF1108E'
    assert saved['facts']['q307_done'] == saved['facts']['q307_main_game_killed'] == saved['facts']['q307_ep1_killed'] == 1
    after = {path: row['uint32_at_4'] for row in saved['journal_matches'] for path in row['paths'] if path in wanted}
    assert after == {root: 4, phase: 4, objective: 4, objective + '/description': 2}
    assert all((saved['facts'][name] or 0) == expected for name, expected in wanted_facts.items())
    return {'history_sha256': sha(history), 'post_projection_sha256': sha(post), 'post_save_sha256': saved['sha256'],
            'same_run': False, 'active_to_failed': sorted(wanted - {objective + '/description'}),
            'unchanged_description': objective + '/description', 'later_objectives_inactive_at_cutoff': sorted(later),
            'matched_facts': wanted_facts}


def main():
    plan = read(HERE / 'entrance.json')
    pins = read(HERE / 'evidence_02/inputs.json')
    providers = {item['rid']: item for item in pins['resources']}
    out = HERE / 'graph_03'
    readback = read(out / 'readback.json')
    assert readback['pinned_providers'] == len(providers)
    emitted = {}
    for row in readback['resources']:
        name = row['name']
        spec = plan['resources'][name]
        source = providers[spec['rid']]
        assert sha(out / f"{spec['rid']}.original.questphase") == row['source_sha256'] == source['sha256']
        assert sha(out / f'{name}.questphase') == row['raw_sha256']
        assert sha(out / f'{name}.questphase.json') == row['export_sha256']
        assert sha(source['export_path']) == source['export_sha256']
        emitted[name] = normalize(load_export(out / f'{name}.questphase.json'))
        verify_copy(name, spec, normalize(load_export(source['export_path'])), emitted[name], plan)
    assert emitted.keys() == plan['resources'].keys()
    for parent, spec in plan['resources'].items():
        for node_id, child in spec.get('calls', []):
            shell_nodes, _ = graph(emitted[parent], f'root/{node_id}')
            child_nodes, _ = graph(emitted[child], 'root')
            assert shell_nodes[spec['shell_entry']] == child_nodes[plan['resources'][child]['entry']]
    assert from_entry(emitted['root'], 'root', 61000) == {61000, 24, 1}
    assert from_entry(emitted['main'], 'root', 61000) == {61000, 2, 3, 5, 4, 9, 1}
    assert from_entry(emitted['hook'], 'root', 61000) == {61000, 61001, 61002, 1}
    assert from_entry(emitted['hook'], 'root/61002', 0) == {0, 3, 4, 6, 8, 7, 1}
    assert {2, 4, 5, 7, 8, 10, 11, 12, 13} <= from_entry(emitted['hook'], 'root', 0)

    completion_source = providers[14906]
    assert sha(completion_source['export_path']) == completion_source['export_sha256']
    nodes, edges = graph(normalize(load_export(completion_source['export_path'])), 'root')
    assert nodes[6]['type']['factName'] == 'mq017_done'
    assert value(nodes[11]['type']['rewards'][0]) == 'QuestRewards.mq017_done'
    terminal = [(6, 11), (11, 19), (19, 7), (7, 1)]
    assert all((a, 'Out', 'Output', b, 'In', 'Input') in edges for a, b in terminal)

    result = {'status': 'PASS_UNREGISTERED_PRIVATE_ENTRANCE', 'archive_count': readback['scanned_archives'],
              'provider_count': len(providers), 'readback_sha256': sha(out / 'readback.json'),
              'stage': verify_stage(Path(pins['game'])), 'saved_owners': verify_ownership(plan),
              'terminal_source': {'provider': completion_source['depot'], 'nodes': terminal},
              'runtime_admission': False}
    write(HERE / 'evidence_02/assessment.json', result)
    print('Verified three serialized phases, two external input shells, nested support, original completion and six saved-owner paths.')


if __name__ == '__main__':
    main()
