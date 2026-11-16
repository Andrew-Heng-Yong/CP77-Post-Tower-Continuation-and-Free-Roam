"""Resolve the saved Dogtown companion addresses to authored behavior."""
from capture import HERE, baseline, read, sha, write
from verify_batch import RD4, graph, load_export, normalize, readonly, value


def registered(companions, stage_id, resource, path, nodes):
    stage = next(s for s in companions['stages'] if s['id'] == stage_id)
    owner = next(p for p in stage['source_owner_paths'] if p['resource'] == resource
                 and [s[2] for s in p['source_path']] == path)
    for slot in ('AutoSave-11', 'AutoSave-3', 'AutoSave-5'):
        registrations = owner['controls'][slot]['descendant_nodes']
        assert sorted(n for address, n in registrations if address == path) == nodes
    return owner


def source(db, rid, providers):
    row = dict(db.execute('SELECT * FROM resources WHERE rid=?', (rid,)).fetchone())
    assert providers[row['depot']] == row['sha256']
    assert sha(row['export_path']) == row['export_sha256']
    return row, normalize(load_export(row['export_path']))


def merchant_pause(node, edges):
    assert node['$type'] == 'questPauseConditionNodeDefinition'
    assert node['condition']['type']['factName'] == 'travelling_merchant_lives'
    assert all(e[0] != node['id'] for e in edges)
    return node


def main():
    baseline()
    evidence = HERE / 'evidence_01'
    assessment_file = evidence / 'batch_assessment.json'
    provider_file = evidence / 'provider_readback.json'
    archive_file = RD4 / 'archive_01/readback.json'
    assessment = read(assessment_file)
    provider_check = read(provider_file)
    assert provider_check['status'] == 'PASS'
    providers = {r['depot']: r['sha256'] for r in provider_check['providers']}
    members = {r['depot']: r['sha256'] for r in read(archive_file)['members']}
    talent_owner = registered(assessment, 'sts_ep1_13', 12477, [1, 0, 10, 2, 3, 2, 12], [2])
    symptoms_owner = registered(assessment, 'sts_ep1_12', 12895, [1, 0, 10, 2, 3, 2, 11], [17, 18])

    with readonly('registry_02/registry.sqlite3') as db:
        talent, talent_graph = source(db, 12477, providers)
        symptoms, symptoms_graph = source(db, 12895, providers)
        private, private_graph = source(db, 14760, members)
        wrapper, wrapper_graph = source(db, 15393, providers)

    nodes, edges = graph(talent_graph, 'root')
    talent_pause = merchant_pause(nodes[2], edges)
    nodes, edges = graph(symptoms_graph, 'root')
    symptoms_pause = merchant_pause(nodes[18], edges)
    assert nodes[17]['$type'] == 'questPhaseNodeDefinition'
    assert nodes[17] == graph(private_graph, 'root')[0][17]
    branch, branch_edges = graph(symptoms_graph, 'root/17')
    assert (branch, branch_edges) == graph(private_graph, 'root/17')
    assert branch[3]['$type'] == 'questTeleportPuppetNodeDefinition'
    assert branch[3]['entityReference']['refLocalPlayer'] == 1
    assert branch[12]['type']['$type'] == 'questTogglePrefabVariant_NodeType'
    hatch = [branch[n]['type']['params'][0] for n in (8, 9)]
    assert [value(p['deviceAction']) for p in hatch] == ['ForceClose', 'ForceSeal']
    assert all(value(p['objectRef']) == '#sts_ep1_12_hatch_sewer_pipe' for p in hatch)
    nodes, edges = graph(wrapper_graph, 'root/50')
    assert value(nodes[64001]['phaseResource']['DepotPath']) == private['depot']
    assert (65003, 'Out', 'Output', 64001, 'In1', 'Input') in edges

    write(evidence / 'companion_review.json', {
        'status': 'AUTHORED_COMPANION_EFFECTS_CHECKED',
        'inputs': {p.name: sha(p) for p in (assessment_file, provider_file, archive_file)},
        'talent_academy': {'resource': talent, 'saved_owner': talent_owner,
                           'registered_pause': talent_pause},
        'treating_symptoms': {'resource': symptoms, 'private_counterpart': private, 'wrapper': wrapper,
                              'saved_owner': symptoms_owner, 'registered_pause': symptoms_pause,
                              'wrapper_entry': nodes[64001], 'matching_branch': branch,
                              'matching_branch_edges': branch_edges},
        'limits': 'Saved registrations and authored effects only. No duplicate execution observed.',
    })
    print('Resolved the surviving Dogtown registrations and verified the matching private hatch branch.')


if __name__ == '__main__':
    main()
