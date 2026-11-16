"""Check the serialized body, existing fixture guard and remaining owner obligations."""
from pin_empathy import HERE, baseline, read, sha, write
from verify import check_stage, load_source
from verify_batch import graph, value, walk


def edge(source, scope, node, output, target, input_socket):
    assert (node, output, 'Output', target, input_socket, 'Input') in graph(source, scope)[1], (scope, node)


def fact(source, scope, node, name, amount, exact):
    params = graph(source, scope)[0][node]['type']
    assert params['$type'] == 'questSetVar_NodeType'
    assert (params['factName'], params['value'], params['setExactValue']) == (name, amount, exact)


def node_values(source, scope, node, field):
    return [value(data[field]) for data in walk(graph(source, scope)[0][node]) if field in data]


def main():
    installed = baseline()
    out = HERE / 'graph_01'
    evidence = HERE / 'evidence_01'
    spec = read(HERE / 'empathy.json')
    pins = read(evidence / 'inputs.json')
    result = read(out / 'readback.json')
    assert sha(HERE / 'empathy.json') == pins['plan_sha256']
    assert installed['archive_sha256'] == pins['archive_sha256']
    assert result['status'] == 'UNREGISTERED_BODY_READBACK'
    assert result['pinned_providers'] == len(pins['resources']) == len(spec['providers'])
    sources = {row['rid']: load_source(row) for row in pins['resources'] if row['root_type'].startswith('quest')}
    body_pin = next(row for row in pins['resources'] if row['rid'] == spec['body'])
    assert sha(out / 'original.questphase') == body_pin['sha256']
    file = out / (spec['id'] + '_body.questphase')
    assert sha(file) == result['body_sha256'] and sha(str(file) + '.json') == result['export_sha256']
    body = load_source({'export_path': str(file) + '.json', 'export_sha256': result['export_sha256']})
    reached = check_stage(spec, body, sources[spec['body']])

    # Exact room, optional combat and settlement paths in the serialized body.
    room = 'root/5/154'
    assert node_values(body, room, 2, 'realPath')[0].endswith('/get_inside_server_room')
    edge(body, room, 0, 'Out', 2, 'Active')
    edge(body, room, 2, 'Out', 24, 'In1')
    edge(body, room, 2, 'Out', 3, 'In')
    edge(body, room, 3, 'Out', 4, 'Succeeded')
    edge(body, room, 4, 'Out', 5, 'Active')
    edge(body, room, 5, 'Out', 6, 'In')
    assert node_values(body, room, 6, 'deviceConditionFunction') == ['IsPersonalLinkConnected']
    edge(body, room, 6, 'Out', 7, 'In')
    edge(body, room, 7, 'Out', 8, 'In')
    assert node_values(body, room, 8, 'deviceAction') == ['QuestForceDisconnectPersonalLink']
    assert node_values(body, room, 9, 'deviceAction') == ['ForceUnpower']
    assert node_values(body, 'root/5', 165, 'realPath')[0].endswith('/avoid_combat')
    edge(body, 'root/5', 168, 'Out', 169, 'Failed')
    edge(body, 'root/5', 172, 'Out', 173, 'In')
    fact(body, 'root/5', 173, 'dtn_03_in_combat', 1, 0)
    assert node_values(body, 'root/5', 171, 'factName') == ['dtn_03_in_combat']
    edge(body, 'root/5', 171, 'False', 156, 'In1')
    edge(body, 'root/5', 171, 'True', 158, 'In1')
    fact(body, 'root/5/156', 5, 'dtn_03_finished', 1, 0)
    fact(body, 'root/5/158', 7, 'dtn_03_finished', 1, 0)
    edge(body, 'root', 5, 'Out1', 15, 'In')
    edge(body, 'root', 5, 'Out2', 15, 'In')
    edge(body, 'root', 15, 'Out', 14, 'In')
    edge(body, 'root', 14, 'Out', 13, 'In1')
    edge(body, 'root/13', 47, 'False', 2, 'In')
    edge(body, 'root/13', 48, 'Out', 2, 'In')
    edge(body, 'root/13', 15, 'Out1', 1, 'In')
    edge(body, 'root', 13, 'Out1', 1, 'In')
    fact(sources[15137], 'root', 10, 'cct_sts_counter', 1, 0)
    edge(sources[15137], 'root', 3, 'Out', 10, 'In')
    edge(sources[15137], 'root', 10, 'Out', 65002, 'In')

    # These original owners must be accounted for before adding a live caller.
    assert [value(row['prefabNodeRef']) for row in sources[9284]['support']['phasePrefabs']] == ['#sts_cct_dtn_03_streetstory']
    edge(sources[9284], 'root', 0, 'Out', 20, 'In1')
    edge(sources[9284], 'root', 0, 'Out', 21, 'In1')
    assert node_values(sources[9284], 'root', 21, 'DepotPath') == [next(row['depot'] for row in pins['resources'] if row['rid'] == 5595)]
    assert node_values(body, 'root/11', 21, 'deviceAction') == ['ForceOpen']
    assert graph(body, 'root/11')[0][14]['type']['$type'] == 'questInjectLoot_NodeType'
    assert node_values(sources[6099], 'root/4', 8, 'deviceAction') == ['ForceEnabled']
    assert node_values(sources[6099], 'root/5', 7, 'deviceConditionFunction') == ['GetIsStoringPlayerEquipement']

    prior = HERE.parents[1] / 'resume_dispatcher_rd5_gigs_20261113_01/evidence_01/batch_assessment.json'
    assert sha(prior) == 'E12CFF4425667D6A4DBDD3CB4A48D9F161CED530ABC058FC62AD3B088FEE7354'
    fixture = next(row for row in read(prior)['stages'] if row['id'] == spec['id'])
    guard = fixture['fixture_guard']
    states = {row['path'].rsplit('/', 1)[-1]: (row['history'], row['live']) for row in guard['journals']}
    assert states['get_in_the_club'] == (3, 3)
    assert states['get_inside_server_room'] == states['avoid_combat'] == (2, 4)
    assert guard['facts']['dtn_03_start'] == 1
    assert guard['facts']['dtn_03_finished'] == guard['facts']['dtn_03_weapons_deposit'] == guard['facts']['dtn_03_in_combat'] == 0
    assert node_values(sources[15050], 'root', 65002, 'factName').count('dtn_03_start') == 1
    start = next(row for row in walk(graph(sources[15050], 'root')[0][65002]) if row.get('factName') == 'dtn_03_start')
    assert start['comparisonType'] == 'Equal' and start['value'] == 0

    write(evidence / 'assessment.json', {
        'status': 'PASS_UNREGISTERED_EMPATHY_BODY', 'baseline_archive_sha256': installed['archive_sha256'],
        'graph_readback_sha256': sha(out / 'readback.json'), 'body_sha256': result['body_sha256'],
        'reachable_stage_nodes': reached, 'fixture_guard': guard,
        'prior_rejected_fixture_mutations': fixture['rejected_fixture_mutations'],
        'remaining_owner_review': {
            'main_and_combat': {'parent_rid': 9284, 'prefab': '#sts_cct_dtn_03_streetstory', 'combat_rid': 5595},
            'parallel_world_setup': ['root/11', 'root/12', 'root/5/133', 'root/5/152'],
            'locker_companion': {'rid': 6099, 'branches': ['root/4', 'root/5']},
            'credit': {'rid': 15137, 'node': 10, 'requires_single_claim': True},
        },
        'runtime_admission': 0, 'game_writes': 0, 'save_writes': 0,
    })
    print('Verified the serialized entrance, both outcomes, reward/credit boundaries and recorded fixture scope.')


if __name__ == '__main__':
    main()
