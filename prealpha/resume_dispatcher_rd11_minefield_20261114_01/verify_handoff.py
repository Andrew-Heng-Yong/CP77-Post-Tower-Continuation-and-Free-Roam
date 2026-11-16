"""Verify the private handoff and pinpoint the remaining shared patrol ownership gap."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
REGISTRY = PREALPHA / 'quest_resume_registry_20261112_01'
sys.path.insert(0, str(REGISTRY))
from model import load_export, normalize, value

sys.path.insert(0, str(PREALPHA / 'resume_dispatcher_rd5_gigs_20261113_01'))
from capture import read, sha, write
from verify_batch import graph

STAGE = 'ResumeFindTheCar'
PARENT = 'sts_bls_ina_07_parent.questphase'
BODY = 'sts_bls_ina_07_body.questphase'
BODY_GRAPH = PREALPHA / 'resume_dispatcher_rd6_batch50_20261113_01/minefield/graph_01'


def questphase(binary, digest, export_digest=None):
    assert sha(binary) == digest, binary
    export = Path(str(binary) + '.json')
    if export_digest is not None:
        assert sha(export) == export_digest, export
    return normalize(load_export(export))


def actor(node):
    entity = node['entityReference']
    name, = entity['names']
    return value(entity['reference']), value(name)


def check_communities(evidence):
    samples = read(evidence)['saves']
    assert {row['slot'] for row in samples} == {'ManualSave-26', 'AutoSave-3', 'AutoSave-5'}
    expected = {'car': ('spawn', 1, [9000393]), 'drones': ('0spawn', 1, [9016109, 9016110, 9016111]),
                'bandits': ('0spawn', 0, [])}
    recorded = {}
    for sample in samples:
        assert set(sample['target_rows']) == set(expected)
        for name, (phase, active, ids) in expected.items():
            entry = sample['target_rows'][name]
            rows = entry['entry_rows']
            assert entry['in_outer_list'] and entry['spawner_row'] is None
            assert len(rows) == (len(ids) or 12)
            assert {row['phase'] for row in rows} == {phase}
            assert {row['row']['memory_0x46_u8'] for row in rows} == {active}
            assert sorted(entity for row in rows for field in ('array_0x00', 'array_0x20')
                          for entity in row['row'][field]) == ids
            comparable = {row['inner']: {k: v for k, v in row['row'].items()
                          if k not in ('start_offset', 'end_offset')} for row in rows}
            assert len(comparable) == len(rows)
            assert recorded.setdefault(name, comparable) == comparable, (sample['slot'], name)
    return [row['slot'] for row in samples]


def check_handoff(original, parent, body, gameplay, manifest):
    assert parent['support'] == original['support']
    prefab, = parent['support']['phasePrefabs']
    assert value(prefab['prefabNodeRef']) == '#sts_bls_ina_07_minefield_logic'
    assert [item['path'] for item in parent['graphs']] == ['root']
    nodes, edges = graph(parent, 'root')
    orig, _ = graph(original, 'root')
    assert set(nodes) == {1000, 273, 282, 117, 118, 235}
    assert nodes[1000]['$type'] == 'questInputNodeDefinition'
    assert value(nodes[1000]['socketName']) == STAGE
    assert all(nodes[node] == orig[node] for node in (273, 282, 117, 235))
    assert {k: v for k, v in nodes[118].items() if k != 'phaseResource'} == {
        k: v for k, v in orig[118].items() if k != 'phaseResource'
    }
    assert value(nodes[118]['phaseResource']['DepotPath']) == manifest['private_body']
    assert nodes[118]['phaseResource']['Flags'] == orig[118]['phaseResource']['Flags'] == 'Soft'
    assert nodes[235]['type'] == 'Terminating'
    expected = [
        (1000, 'Out', 273, 'In'), (273, 'Out', 282, 'In'), (282, 'Out', 117, 'In1'),
        (282, 'Out', 118, STAGE), (118, 'Out1', 235, 'In'),
    ]
    assert set(edges) == {(a, s, 'Output', b, t, 'Input') for a, s, b, t in expected}
    for child, socket in ((body, STAGE), (gameplay, 'In1')):
        child_nodes, _ = graph(child, 'root')
        entrance, = (node for node in child_nodes.values() if node['$type'] == 'questInputNodeDefinition'
                     and value(node['socketName']) == socket)
        assert entrance
    body_nodes, body_edges = graph(body, 'root')
    assert value(body_nodes[1]['socketName']) == 'Out1' and body_nodes[1]['type'] == 'Terminating'
    assert (11, 'Out1', 'Output', 17, 'In', 'Input') in body_edges
    assert (11, 'failed', 'Output', 13, 'sts_failed', 'Input') in body_edges
    assert (17, 'Out', 'Output', 13, 'In1', 'Input') in body_edges
    assert (13, 'Out1', 'Output', 1, 'In', 'Input') in body_edges
    assert value(body_nodes[17]['type']['rewards'][0]) == 'QuestRewards.sts_bls_ina_07_completion'
    return expected


def check_patrols(body, gameplay, evidence):
    release, edges = graph(body, 'root/13/25')
    release_sites = {actor(release[node]): node for node in range(11, 17)}
    assert len(release_sites) == 6
    assert all(value(release[node]['function']) == 'AIClearRoleCommandParams' for node in release_sites.values())
    assert set(edges) == {(0, 'Out', 'Output', 11, 'In', 'Input'),
                          (16, 'Success', 'Output', 1, 'In', 'Input')} | {
        (node, 'Success', 'Output', node + 1, 'In', 'Input') for node in range(11, 16)
    }
    requests = {}
    for scope in ('root/7/54', 'root/9/140'):
        chase, _ = graph(gameplay, scope)
        sites = {actor(chase[node]): node for node in range(10, 16)}
        assert set(sites) == set(release_sites)
        assert all(value(chase[node]['function']) == 'questCombatNodeParams_ShootAt'
                   and chase[node]['params']['duration'] == 10 for node in sites.values())
        requests[scope] = sites

    saved = read(evidence)
    expected = {'border_patrol': (5, []), 'heavy_patrol': (3, [9000058, 9000059, 9000060]),
                'droid_patrol': (3, [9000052, 9000053, 9000054])}
    assert {saved['refs'][name] for name in expected} == {ref for ref, _ in release_sites}
    result = {}
    for sample in saved['saves']:
        slot = sample['slot']
        result[slot] = {}
        for name, (count, ids) in expected.items():
            target = sample['target_rows'][name]
            rows = target['entry_rows']
            assert target['in_outer_list'] and target['spawner_row'] is None and len(rows) == count
            assert {row['phase'] for row in rows} == {'default'}
            assert {row['row']['memory_0x46_u8'] for row in rows} == {1}
            associated = sorted(entity for row in rows for field in ('array_0x00', 'array_0x20')
                                for entity in row['row'][field])
            assert associated == ids
            result[slot][name] = {'active_entries': count, 'associated_ids': associated}
    return [{'community': ref, 'entry': name, 'release_node': node,
             'shoot_at': {scope: sites[(ref, name)] for scope, sites in requests.items()}}
            for (ref, name), node in release_sites.items()], result


def main():
    out = HERE / 'graph_03'
    manifest = read(out / 'readback.json')
    assert manifest['runtime_admission'] == 0
    assert manifest['archive_sha256'] == '443339C64009C5DB99B1E0FD77B1EF526143C40DADDBEBB05EBEC6BB5D76BB45'
    pins = {pin['filename']: pin for pin in manifest['providers']}
    original = questphase(out / 'original.questphase', pins['original.questphase']['sha256'])
    gameplay = questphase(out / 'gameplay.questphase', pins['gameplay.questphase']['sha256'])
    parent = questphase(out / PARENT, manifest['parent_sha256'], manifest['parent_export_sha256'])
    body = questphase(BODY_GRAPH / BODY, manifest['body_sha256'],
                      '7AB1209ADD1AECDAE23A0B6840288B8E6D79DEDD40F997B84AFDCE7965AE45ED')
    communities = HERE / 'evidence_01/communities.json'
    fixtures = check_communities(communities)
    edges = check_handoff(original, parent, body, gameplay, manifest)
    patrol_evidence = HERE / 'evidence_01/communities_with_patrols.json'
    assert [row['slot'] for row in read(patrol_evidence)['saves']] == fixtures
    release, world_patrols = check_patrols(body, gameplay, patrol_evidence)
    assessment = HERE / 'evidence_01/assessment.json'
    if assessment.exists():
        raise FileExistsError(assessment)
    write(assessment, {'status': 'PASS_OFFLINE_PARENT_RUNTIME_DEFERRED', 'readback_sha256': sha(out / 'readback.json'),
                       'community_evidence_sha256': sha(communities), 'fixtures': fixtures, 'parent_edges': edges,
                       'shared_patrol_release': release, 'saved_world_patrols': world_patrols,
                       'patrol_evidence_sha256': sha(patrol_evidence),
                       'runtime_admission': 0, 'game_writes': 0, 'save_writes': 0})
    print(f'Verified {len(edges)} parent edges, {len(fixtures)} community fixtures, and {len(release)} shared patrol targets.')


if __name__ == '__main__':
    main()
