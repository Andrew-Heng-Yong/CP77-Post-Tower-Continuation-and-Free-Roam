"""Verify the unregistered Treating Symptoms objective and debrief entrance."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from pin_dogtown_inputs import baseline, read, sha, write
from verify_talent import connected, verify_additive_body, graph, typed_edges, value, walk, load_source, normalize, load_export


def verify_stage(plan, source, body):
    root, edges = graph(body, 'root')
    before, before_edges = graph(source, 'root')
    seeds = plan['stage_seeds']
    # The nested resume input cannot emit the fresh-only after_talk output.
    resume_edges = [edge for edge in edges if edge[:2] != (154, 'after_talk')]
    native_tail = connected(seeds, [edge for edge in before_edges if edge[:2] != (154, 'after_talk')])
    stage = connected([1000], resume_edges)
    assert stage == native_tail | {1000}
    assert not stage.intersection(plan['consumed_nodes'])
    assert not stage.intersection({0, 12, 105, 156, 157})
    assert typed_edges([
        [154, 'after_talk', 209, 'In1'], [347, 'Out', 209, 'In2'], [209, 'Out1', 115, 'In'],
        [115, 'True', 113, 'Active'], [115, 'False', 116, 'Active'],
        [113, 'Out', 114, 'In'], [116, 'Out', 114, 'In'], [114, 'Out', 117, 'Succeeded'],
    ]) <= set(before_edges)
    assert root[115]['condition']['type']['factName'] == 'ep1_12_test_def'
    assert root[114]['condition']['type'] == 'IsInside'
    assert {root[n]['type']['path']['realPath'] for n in (113, 116, 117)} == {
        'ep1/quests/street_stories/sts_ep1_12/sts_ep1_12/01_get_inside_complex'
    }
    assert {1, 61, 68, 114, 118, 288, 290, 294} <= stage
    assert before[288]['type'] == {
        '$type': 'questSetVar_NodeType', 'factName': 'dogtown_gigs_achievement', 'setExactValue': 0, 'value': 1
    }

    debrief, edges = graph(body, 'root/154')
    debrief_tail = connected([1000], edges)
    assert {1, 16, 20, 23, 24, 27, 29, 36, 37, 38} <= debrief_tail
    assert not debrief_tail.intersection({0, 2, 7, 8, 9, 10, 11, 12, 31, 39, 40})
    assert debrief[20]['condition']['type']['factName'] == 'sts_ep1_12_finished'
    assert debrief[36]['type']['factName'] == 'sts_ep1_12_briefings_done'
    assert typed_edges([
        [29, 'kill', 27, 'In1'], [28, 'Out1', 27, 'In2'], [27, 'Out1', 36, 'In'],
    ]) <= set(edges)
    lock, edges = graph(body, 'root/154/29')
    assert typed_edges([
        [0, 'Out', 15, 'In'], [0, 'Out', 18, 'In'], [15, 'Out', 14, 'In'], [17, 'Out', 16, 'In'],
        [18, 'Out', 19, 'In'], [19, 'Out', 1, 'In'],
    ]) <= set(edges)
    assert lock[18]['condition']['type']['factName'] == 'sts_ep1_12_finished'
    assert [lock[n]['type']['subtype']['action'] for n in (14, 16, 19)] == ['Block', 'Unblock', 'Unblock']
    assert [value(lock[n]['type']['subtype']['source']) for n in (14, 16, 19)] == [plan['quest']] * 3
    return sorted(native_tail), sorted(debrief_tail - {1000})


def verify_ownership(plan, sources):
    wrapper, edges = graph(sources[plan['wrapper']], 'root/50')
    assert typed_edges([
        [65002, 'Out', 65007, 'In'], [65007, 'Out', 65003, 'In'],
        [65003, 'Out', 64001, 'In1'], [26, 'Out1', 64000, 'In1'], [26, 'Out1', 65005, 'In'],
        [64000, 'Out1', 65006, 'In'],
    ]) <= set(edges)
    assert wrapper[65007]['type']['factName'] == 'PTFRQR7_RonaldNews_Armed_sts_ep1_12'
    assert wrapper[65005]['type']['factName'] == 'PTFRU9_sts_ep1_12_MainFinished'
    assert wrapper[65006]['type']['factName'] == 'PTFRU9_sts_ep1_12_OwnerFinished'
    assert any(row.get('factName') == 'sts_ep1_12_start' and row.get('value') == 0 for row in walk(wrapper[65002]))
    assert graph(sources[12895], 'root/17') == graph(sources[14760], 'root/17')
    assert graph(sources[12895], 'root/20') == graph(sources[14760], 'root/20')
    assert graph(sources[12895], 'root/14')[0][4]['sceneFile'] != graph(sources[14760], 'root/14')[0][4]['sceneFile']
    reward, reward_id = plan['completion']['reward']
    root, _ = graph(sources[plan['body']], 'root')
    assert [value(entry) for entry in root[reward]['type']['rewards']] == [reward_id]
    credit, edges = graph(sources[plan['completion']['credit']], 'root')
    assert typed_edges([[65001, 'Out', 4, 'In'], [4, 'Out', 14, 'In'], [14, 'Out', 65002, 'In']]) <= set(edges)
    assert credit[4]['condition']['type']['factName'] == 'sts_ep1_12_finished'
    assert credit[14]['type'] == {
        '$type': 'questSetVar_NodeType', 'factName': 'ep1_sts_counter', 'setExactValue': 0, 'value': 1
    }
    setup, _ = graph(sources[plan['body']], 'root/103')
    assert [value(setup[n]['type']['params'][0]['deviceAction']) for n in (37, 38, 39)] == ['ForceOpen', 'ForceOpen', 'ForceUnlock']
    courier, _ = graph(sources[plan['body']], 'root/105/49')
    assert {courier[n]['type']['$type'] for n in (6, 7)} == {'questInjectLoot_NodeType'}


def verify_briefings():
    path = HERE.parent / 'evidence_01/saved_briefs.json'
    data = read(path)
    assert data['status'] == 'READ_ONLY_DOGTOWN_BRIEFINGS'
    assert {row['slot'] for row in data['saves']} == {'ManualSave-26', 'AutoSave-3', 'AutoSave-5'}
    assert data['save_writes'] == 0
    briefing = 'contacts/mr_hands/sts_ep1_12/brief'
    assert len({row['journals'][briefing]['raw15'] for row in data['saves']}) == 1
    for row in data['saves']:
        assert row['journals'][briefing]['state_u32'] == 2
        expected = {'codex_milko_alexis': 1, 'codex_voodoo_boys_in_dogtown': 2,
                    'CP77-36823': 1, 'CP77-58921': 1, 'CP77-58937': 1}
        assert {name: row['facts'][name] for name in expected} == expected
        assert {'sts_ep1_12_briefings_done', 'wst_ep1_02_start', 'wst_ep1_02_finished'} <= set(row['absent_fact_records'])
    return sha(path)


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
    body_file = out / 'sts_ep1_12_body.questphase'
    export_file = out / 'sts_ep1_12_body.questphase.json'
    assert sha(body_file) == receipt['body_sha256'] and sha(export_file) == receipt['export_sha256']
    source = sources[plan['body']]
    body = normalize(load_export(export_file))
    verify_additive_body(plan, source, body)
    main_tail, debrief_tail = verify_stage(plan, source, body)
    verify_ownership(plan, sources)
    briefing_sha = verify_briefings()
    output = evidence / 'assessment.json'
    if output.exists():
        raise FileExistsError(output)
    write(output, {
        'status': 'PASS_TREATING_SYMPTOMS_UNREGISTERED_OBJECTIVE_AND_DEBRIEF_BODY',
        'baseline_sha256': pins['baseline_sha256'], 'archive_sha256': pins['archive_sha256'],
        'plan_sha256': pins['plan_sha256'], 'body_sha256': receipt['body_sha256'],
        'body_readback_sha256': sha(out / 'readback.json'), 'saved_briefs_sha256': briefing_sha,
        'main_tail_nodes': main_tail, 'debrief_tail_nodes': debrief_tail,
        'registrations': 0, 'game_writes': 0, 'save_writes': 0,
        'required_support_handoff': [12, 105], 'retained_native_bugfix': 12895,
    })
    print(f'Verified the serialized entrance with {len(main_tail)} main and {len(debrief_tail)} debrief nodes.')


if __name__ == '__main__':
    main()
