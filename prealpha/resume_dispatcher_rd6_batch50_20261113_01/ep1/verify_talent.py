"""Verify the serialized Talent Academy entrance against the pinned source."""
from pin_dogtown_inputs import HERE, baseline, read, sha, write
from pin_inputs import BATCH
from verify_batch import graph, load_export, normalize, reachable, value, walk
from verify import typed_edges, load_source


def connected(nodes, edges):
    return reachable(nodes, [(a, b) for a, _, x, b, _, y in edges if (x, y) == ('Output', 'Input')])


def verify_additive_body(plan, source, body):
    assert source['support'] == body['support']
    new_socket = {'name': plan['socket'], 'type': 'Input'}
    for before, after in zip(source['graphs'], body['graphs'], strict=True):
        path = before['path']
        assert path == after['path']
        if path not in plan['graphs']:
            assert before == after, path
            continue
        edit = plan['graphs'][path]
        initial, initial_edges = graph(source, path)
        result, result_edges = graph(body, path)
        new_id = edit['input']
        assert set(result) - set(initial) == {new_id}
        assert all(result[node] == row for node, row in initial.items())
        assert result[new_id]['$type'] == 'questInputNodeDefinition'
        assert value(result[new_id]['socketName']) == plan['socket']
        assert after['inputs'] == [*before['inputs'], new_id]
        assert set(result_edges) == set(initial_edges) | typed_edges(edit['edges'])
        old_sockets = {r['id']: r['sockets'] for r in before['nodes']}
        expected = {k: v + [new_socket] if k in edit.get('phase_inputs', []) else v for k, v in old_sockets.items()}
        assert {r['id']: r['sockets'] for r in after['nodes'] if r['id'] != new_id} == expected
        assert connected(before['inputs'], initial_edges) == connected(before['inputs'], result_edges)


def verify_stage(plan, source, body):
    root, root_edges = graph(body, 'root')
    assert connected([plan['graphs']['root']['input']], root_edges) == {2, 3, 6, 1000}
    assert value(root[6]['socketName']) == 'Out1'
    stage = plan['stage_graph']
    nodes, edges = graph(body, stage)
    reached = connected([plan['graphs'][stage]['input']], edges)
    expected_tail = connected(plan['stage_seeds'], graph(source, stage)[1])
    assert reached == expected_tail | {plan['graphs'][stage]['input']}
    assert not reached.intersection(plan['consumed_nodes'])
    assert {1, 8, 9, 10, 11, 184, 194, 195, 257, 258, 259, 311, 312} <= reached
    assert value(nodes[1]['socketName']) == 'Out1'
    assert typed_edges([
        [10, 'Out', 8, 'In'], [8, 'Out', 11, 'In'], [11, 'Out', 9, 'In'],
        [9, 'Out', 10, 'In'], [8, 'Out', 311, 'In'], [9, 'Out', 312, 'In'],
        [257, 'Out', 258, 'In'], [258, 'Out', 259, 'Succeeded'], [259, 'Out', 194, 'Active'],
    ]) <= set(edges)
    for node, action in ((8, 'Block'), (9, 'Unblock')):
        token = nodes[node]['type']['subtype']
        assert token['action'] == action and value(token['source']) == plan['quest']
    return sorted(expected_tail)


def verify_owner_and_completion(plan, sources):
    wrapper, edges = graph(sources[plan['wrapper']], 'root/50')
    assert typed_edges([[6, 'Out1', 64000, 'In1'], [6, 'Out1', 65005, 'In'], [64000, 'Out1', 65006, 'In']]) <= set(edges)
    assert wrapper[65005]['type']['factName'] == 'PTFRU9_sts_ep1_13_MainFinished'
    assert wrapper[65006]['type']['factName'] == 'PTFRU9_sts_ep1_13_OwnerFinished'
    assert any(row.get('factName') == 'sts_ep1_13_start' and row.get('value') == 0 for row in walk(wrapper[65002]))
    main, edges = graph(sources[plan['main']], 'root')
    assert main[59]['actions'][0]['type']['action'] == 'Reactivate'
    assert value(main[59]['actions'][0]['type']['spawnerReference']) == '#sts_ep1_13_cars_com'
    assert typed_edges([[0, 'Out', 59, 'In'], [4, 'Out', 5, 'In1'], [4, 'Out', 6, 'In1'], [5, 'Out1', 1, 'In']]) <= set(edges)
    companion, edges = graph(sources[12477], 'root')
    assert companion[2]['condition']['type']['factName'] == 'travelling_merchant_lives'
    assert not any(row[0] == 2 for row in edges)
    completion = plan['completion']
    reward_node, reward_id = completion['reward']
    cleanup, edges = graph(sources[completion['cleanup']], 'root')
    assert [value(x) for x in cleanup[reward_node]['type']['rewards']] == [reward_id]
    assert typed_edges([[29, 'True', reward_node, 'In'], [reward_node, 'Out', 30, 'In'], [75, 'Out', 4, 'In']]) <= set(edges)
    assert cleanup[30]['type']['factName'] == 'sts_ep1_13_finished'
    assert cleanup[75]['type']['factName'] == 'sts_ep1_13_cleanup_done'
    for nodes, node, counter in ((cleanup, 72, 'dogtown_gigs_achievement'),
                                 (graph(sources[completion['credit']], 'root')[0], 14, 'ep1_sts_counter')):
        increment = nodes[node]['type']
        assert (increment['factName'], increment['setExactValue'], increment['value']) == (counter, 0, 1)


def main():
    installed = baseline()
    plan_file = HERE / 'plan.json'
    plan = read(plan_file)
    evidence = HERE / 'evidence_01'
    pins = read(evidence / 'inputs.json')
    assert pins['archive_sha256'] == installed['archive_sha256']
    assert sha(plan_file) == pins['plan_sha256']
    out = HERE / 'graph_01'
    receipt = read(out / 'readback.json')
    assert receipt['status'] == 'UNREGISTERED_BODY_READBACK'
    assert receipt['private_depot'] == plan['private_depot']
    assert receipt['pinned_providers'] == len(pins['resources'])
    rows = {row['rid']: row for row in pins['resources']}
    sources = {rid: load_source(row) for rid, row in rows.items()}
    assert sha(out / 'original.questphase') == rows[plan['body']]['sha256'] == receipt['original_sha256']
    body_file = out / 'sts_ep1_13_body.questphase'
    export_file = out / 'sts_ep1_13_body.questphase.json'
    assert sha(body_file) == receipt['body_sha256'] and sha(export_file) == receipt['export_sha256']
    source = sources[plan['body']]
    body = normalize(load_export(export_file))
    verify_additive_body(plan, source, body)
    tail = verify_stage(plan, source, body)
    verify_owner_and_completion(plan, sources)
    fixture = BATCH / 'evidence_01/batch_assessment.json'
    assert sha(fixture) == 'E12CFF4425667D6A4DBDD3CB4A48D9F161CED530ABC058FC62AD3B088FEE7354'
    guard = next(row['fixture_guard'] for row in read(fixture)['stages'] if row['id'] == plan['quest'])
    for fact, expected in {
        'start': 1, 'active': 1, 'holo_obj_done': 1, 'prebrief_received': 1,
        'met_hands_contact': 0, 'talked_to_hands_contact': 0, 'alarm_raised': 0, 'finished': 0,
    }.items():
        assert guard['facts'][f'sts_ep1_13_{fact}'] == expected
    journal = next(row for row in guard['journals'] if row['path'].endswith('/meet_mr_hands_contact'))
    assert (journal['history'], journal['live'], journal['counter']) == (2, 4, 0)
    output = evidence / 'assessment.json'
    if output.exists():
        raise FileExistsError(output)
    write(output, {
        'status': 'PASS_TALENT_ACADEMY_UNREGISTERED_BODY',
        'baseline_sha256': pins['baseline_sha256'], 'archive_sha256': pins['archive_sha256'],
        'plan_sha256': pins['plan_sha256'], 'body_sha256': receipt['body_sha256'],
        'body_readback_sha256': sha(out / 'readback.json'), 'fixture_sha256': sha(fixture),
        'fixture_guard': guard, 'stage_tail_nodes': tail, 'registrations': 0, 'game_writes': 0, 'save_writes': 0,
    })
    print(f'Verified additive graph changes, {len(tail)} native tail nodes and the existing cleanup/credit path.')


if __name__ == '__main__':
    main()
