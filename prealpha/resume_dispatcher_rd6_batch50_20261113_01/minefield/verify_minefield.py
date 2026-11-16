"""Compare all serialized graphs and check the Minefield continuation and terminal edges."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RD6 = HERE.parents[1] / 'resume_dispatcher_rd6_gigs_20261113_01'
sys.path.insert(0, str(RD6))
from verify import baseline, graph, load_source, read, reachable, sha, typed_edges, value, write

EDIT_SCOPE = 'root/11/620'
REMOVED = typed_edges([(18, 'True', 38, 'Inactive'), (38, 'Out', 8, 'In')])
ADDED = typed_edges([(18, 'True', 8, 'In')])


def flow(source, scope, *edges):
    assert typed_edges(edges) <= set(graph(source, scope)[1]), (scope, edges)


def load_body(binary, binary_hash, export_hash):
    assert sha(binary) == binary_hash
    return load_source({'export_path': str(binary) + '.json', 'export_sha256': export_hash})


def main():
    installed = baseline()
    plan = RD6 / 'entrances.json'
    assert sha(plan) == 'B2DD7649B8E1C4A2CE69CD931421D7B11EB49E86ABBBCD4097471F9872AA6269'
    spec = next(quest for quest in read(plan)['quests'] if quest['id'] == 'sts_bls_ina_07')
    name = spec['id'] + '_body.questphase'
    prior_readback = RD6 / 'graph_02/readback.json'
    assert sha(prior_readback) == '901592721AC65D09C0F9737D23E1312DE2F2DB691E8439BA3E26B62172652C2E'
    pin = next(row for row in read(prior_readback)['bodies'] if row['id'] == spec['id'])
    prior_assessment = RD6 / 'evidence_02/assessment.json'
    assert sha(prior_assessment) == 'B2F00A2CA8E6021847C2EA8BE70B9EB9C162C02D0D9CFE7EB127E7C93B217348'
    prior_evidence = read(prior_assessment)
    assert prior_evidence['baseline_archive_sha256'] == installed['archive_sha256']
    old = load_body(RD6 / 'graph_02' / name, pin['sha256'], pin['export_sha256'])

    out = HERE / 'graph_01'
    result = read(out / 'readback.json')
    assert result['status'] == 'UNREGISTERED_BODY_READBACK'
    assert result['archive_sha256'] == installed['archive_sha256']
    assert result['prior_sha256'] == pin['sha256'] == prior_evidence['routes'][spec['id']]['body_sha256']
    body = load_body(out / name, result['body_sha256'], result['export_sha256'])
    assert old['support'] == body['support']
    for before, after in zip(old['graphs'], body['graphs'], strict=True):
        assert before['path'] == after['path']
        if before['path'] != EDIT_SCOPE:
            assert before == after, before['path']
            continue
        assert all(before[key] == after[key] for key in before if key not in ('edges', 'nodes'))
        assert REMOVED <= set(before['edges']) and not ADDED & set(before['edges'])
        assert set(after['edges']) == (set(before['edges']) - REMOVED) | ADDED
        assert len(after['edges']) == len(before['edges']) - 1
        for original, successor in zip(before['nodes'], after['nodes'], strict=True):
            if original['id'] == 38:
                assert original['from_any_input'] and not successor['from_any_input']
                assert dict(original, from_any_input=False) == successor
            else:
                assert original == successor

    nested, edges = graph(body, EDIT_SCOPE)
    assert '/sts_pac_cvi_02/' in nested[38]['type']['path']['realPath']
    assert not any(row[0] == 38 or row[3] == 38 for row in edges)
    for node, event in ((18, 'OnMount'), (8, 'OnUnmount')):
        condition = nested[node]['condition']['type']
        assert condition['condition'] == event and condition['childIsPlayer'] == 1
        assert condition['role'] == 'Driver' and value(condition['parentRef']['reference']) == '#ina_07_com_car'
    flow(body, EDIT_SCOPE, (18, 'False', 9, 'In'), (18, 'True', 8, 'In'), (8, 'Out', 2, 'In'))

    flow(body, 'root', (1000, 'Out', 11, 'ResumeFindTheCar'), (11, 'Out1', 17, 'In'),
         (11, 'failed', 13, 'sts_failed'), (17, 'Out', 13, 'In1'), (13, 'Out1', 1, 'In'))
    flow(body, 'root/11', (595, 'Out', 1, 'In'), (565, 'Out', 370, 'In'))
    flow(body, 'root/13', (0, 'Out', 3, 'In'), (3, 'Out', 9, 'In'), (17, 'Out', 9, 'In'),
         (11, 'Out', 25, 'In1'), (25, 'Out1', 13, 'In'), (13, 'Out', 1, 'In'))
    terminal, _ = graph(body, 'root/13')
    assert terminal[3]['type']['factName'] == 'ina_07_finished'
    assert terminal[3]['type']['value'] == terminal[3]['type']['setExactValue'] == 1
    assert value(graph(body, 'root')[0][17]['type']['rewards'][0]) == 'QuestRewards.sts_bls_ina_07_completion'
    assert any('bls_sts_counter' in writers for writers in prior_evidence['credit_writers'].values())
    _, local_edges = graph(body, 'root/11')
    active = reachable([1000], [(a, b) for a, _, x, b, _, y in local_edges if (x, y) == ('Output', 'Input')])
    assert {1, 370, 620} <= active and not {590, 591} & active
    assert sorted(active) == prior_evidence['routes'][spec['id']]['reachable_stage_nodes']

    evidence = HERE / 'evidence_01'
    evidence.mkdir()
    write(evidence / 'assessment.json', {
        'status': 'PASS_UNREGISTERED_MINEFIELD_SUCCESSOR', 'depot': result['depot'],
        'body_sha256': result['body_sha256'], 'prior_sha256': result['prior_sha256'],
        'baseline_archive_sha256': installed['archive_sha256'], 'scanned_archives': result['scanned_archives'],
        'changed_graph': EDIT_SCOPE, 'removed_edges': sorted(REMOVED), 'added_edges': sorted(ADDED),
        'terminal_checks': ['success_reward', 'failure_no_reward', 'completion_fact', 'cleanup_terminal'],
        'retained_owner_review': prior_evidence['routes'][spec['id']]['pending'],
        'runtime_admission': 0, 'game_writes': 0, 'save_writes': 0,
    })
    print('Verified exact graph differences, vehicle unmount, and the success and failure terminals.')


if __name__ == '__main__':
    main()
