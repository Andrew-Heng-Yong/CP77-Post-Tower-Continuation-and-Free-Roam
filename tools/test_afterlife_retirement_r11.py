"""R11 exact dancer retirement and inert R5 saved-schema tests; no game writes."""
import copy
import json
import re
from pathlib import Path

from audit_world_interactions import walk
from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_access_r10 import read, sha
from test_afterlife_dancers import Model

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/afterlife_world'
OUT = BASE / 'interactions_r11/retirement'


def main():
    spec = read(BASE / 'dancers_manifest.json')
    manifest = read(OUT / 'manifest.json')
    assert sha(Path(manifest['artifact'])) == manifest['sha256']
    assert sha(Path(manifest['source'])) == manifest['source_sha256'] == spec['sha256']
    before = read(BASE / 'dancers_phase.json')['Data']['RootChunk']
    after = read(OUT / 'dancers.questphase.json')['Data']['RootChunk']
    old_h = handles(before)
    old_n = {i: canonical(n, old_h) for i, n in nodes(before).items()}
    new_h = handles(after)
    new_n = {i: canonical(n, new_h) for i, n in nodes(after).items()}
    expected = copy.deepcopy(old_n)
    for row in manifest['entries']:
        i = row['start']
        expected[i+1]['condition']['type']['seconds'] = 0
        expected[i+3]['actions'][0]['type']['action'] = 'Deactivate'
        expected[i+4]['type'].update(factName=row['ready_fact'], value=0, setExactValue=1)
        expected[i+5]['type']['value'] = 0
        expected[i+11] = copy.deepcopy(old_n[i+5])
        expected[i+11]['id'] = i+11
        expected[i+11]['type'].update(factName=row['retired_fact'], value=11)
        expected[i+6]['condition']['conditions'].append({
            '$type': 'questFactsDBCondition', 'type': {
                '$type': 'questVarComparison_ConditionType',
                'comparisonType': 'NotEqual', 'factName': row['retired_fact'], 'value': 11}})
    assert expected == new_n, 'Unexpected phase delta beyond retirement allowlist'
    old_edges = quest_edges(before)[0]
    new_edges = quest_edges(after)[0]
    expected_edges = set(old_edges)
    for row in manifest['entries']:
        i = row['start']
        expected_edges.remove((i+3, 'Out', i+4, 'In'))
        expected_edges.update(((i+3, 'Out', i+11, 'In'), (i+11, 'Out', i+4, 'In')))
    assert expected_edges == new_edges
    assert len(old_n) == 112 and len(new_n) == 122 and set(old_n) < set(new_n)
    assert before['phasePrefabs'] == after['phasePrefabs'] == []
    actions = [x for x in walk(new_n) if x.get('$type') == 'questCommunityTemplate_NodeType']
    assert len(actions) == 20
    for a in actions:
        assert a['action'] == 'Deactivate'
        assert a['spawnerReference']['$value'] == spec['spawner']
        assert a['communityEntryName']['$value'] in {f'dancer_{i:02}' for i in range(1, 11)}
        assert a['communityEntryPhaseName']['$value'] == 'default'
    for a in walk(new_n):
        assert a.get('$type') not in ('questSceneNodeDefinition', 'questTogglePrefabVariant_NodeTypeParams')
        if a.get('$type') == 'questSetVar_NodeType':
            assert a['factName'].startswith(('PTFRAL1_', 'PTFRAL11_'))
    facts = spec['guards']
    loaded = dict.fromkeys([e['ref'] for e in spec['entries']], True)
    fresh = Model(new_n, new_edges, facts, loaded)
    fresh.settle()
    assert len(fresh.actions) == 10 and {a[2] for a in fresh.actions} == {'Deactivate'}
    assert fresh.pending == {e['start']+6 for e in spec['entries']}
    fresh.actions.clear()
    fresh.time += 10000
    fresh.settle()
    assert not fresh.actions, 'Retirement repeatedly dispatched while stable'
    negative = 0
    for key, good in facts.items():
        for bad in (-1, 0, 1, 2):
            if good == bad:
                continue
            m = Model(new_n, new_edges, {**facts, key: bad}, loaded)
            m.finish()
            assert not m.actions
            negative += 1
    # Reconstruct every legacy branch node as a saved continuation with Ready1.
    # Deactivate is idempotent; migration must never retain/reacquire its dancer.
    saved_cases = 0
    for entry in manifest['entries']:
        for offset in range(11):
            m = Model(new_n, new_edges, {**facts, entry['ready_fact']: 1}, loaded)
            m.pending = {entry['start']+offset}
            m.finish()
            assert m.actions and all(a[1:] == (entry['entry'], 'Deactivate') for a in m.actions)
            assert m.facts[entry['ready_fact']] == 0
            assert m.facts[entry['retired_fact']] == 11
            assert m.pending == {entry['start']+6}
            m.actions.clear()
            m.finish()
            assert not m.actions
            saved_cases += 1
    # The previously owned wait must not retire through a competing/ending guard.
    handoff_cases = 0
    for entry in manifest['entries']:
        for key, good in facts.items():
            m = Model(new_n, new_edges, {**facts, entry['ready_fact']: 1, key: 1-good}, loaded)
            m.pending = {entry['start']+6}
            m.finish()
            assert not m.actions
            m.facts[key] = good
            m.finish()
            assert m.actions and all(a[2] == 'Deactivate' for a in m.actions)
            handoff_cases += 1
    stream_cases = 0
    for entry in manifest['entries']:
        m = Model(new_n, new_edges, facts, loaded)
        m.pending = {entry['start']}
        m.finish()
        m.actions.clear()
        m.loaded[entry['ref']] = False
        m.finish()
        assert [a[1:] for a in m.actions] == [(entry['entry'], 'Deactivate')]
        m.actions.clear()
        m.loaded[entry['ref']] = True
        m.finish()
        assert [a[1:] for a in m.actions] == [(entry['entry'], 'Deactivate')]
        stream_cases += 1
    # R2 ordinary-cohort owner does not contain an alternate tube acquisition.
    for name in ('owner.json', 'legacy_population.json'):
        text = (BASE / 'population_r2' / name).read_text(encoding='utf-8-sig')
        assert 'q005_com_afterlife_tube_dancers' not in text
        assert not re.search(r'"dancer_\d\d"', text)
    face_path = ROOT / 'redscript/PTFR_Afterlife_Faces_R5/AfterlifeFacesR5.reds'
    face = face_path.read_text(encoding='utf-8-sig')
    code = re.sub(r'//[^\n]*', '', face)
    assert re.findall(r'public class (\w+) extends (\w+)', code) == [
        ('FaceMemoryR5', 'IScriptable'), ('AfterlifeFacesR5', 'ScriptableSystem')]
    assert re.findall(r'(public|private) persistent let (\w+): ([^;]+);', code) == [
        ('public', 'id', 'EntityID'), ('public', 'role', 'Int32'), ('public', 'appearance', 'CName'),
        ('private', 'revision', 'Int32'), ('private', 'memory', 'array<ref<FaceMemoryR5>>')]
    assert re.findall(r'func (\w+)\(', code) == ['GetStatus']
    for forbidden in ('@wrapMethod', '@addMethod', 'DelayCallback', 'QueueRequest', 'NPCPuppet',
                      'ScheduleAppearanceChange', 'FaceCatalogR5', 'SetFact', 'OnAttach', 'new '):
        assert forbidden not in code
    report = dict(status='PASS_RETIREMENT_R11_OFFLINE_NOT_LIVE', artifact_sha256=manifest['sha256'],
                  face_shim_sha256=sha(face_path), exact_dancers=10, retained_nodes=112,
                  total_nodes=122, total_edges=len(new_edges), split_edges=10, cold_negative_cases=negative,
                  legacy_saved_node_cases=saved_cases, guarded_saved_wait_cases=handoff_cases,
                  stream_cases=stream_cases, r5_inert_persistent_schema_only=True,
                  npc_removal_acknowledgement_unproven=True)
    (OUT / 'tests.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
