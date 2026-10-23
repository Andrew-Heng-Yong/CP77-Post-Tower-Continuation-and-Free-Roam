"""Exact scene/graph-delta and availability/ending-guard regression audit."""
import binascii
import hashlib
import json
import re
from pathlib import Path
from audit_world_interactions import walk
from audit_scene_actor_ids import audit_scene_actor_ids
from test_streetkid_scene_load_s3 import quest_edges

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'research/b0_club_dancing'
def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def clean(v):
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items() if k not in ('HandleId', 'HandleRefId', 'sockets')}
    if isinstance(v, list):
        return [clean(x) for x in v]
    return v
def transform(v, short, full):
    if isinstance(v, dict):
        out = {k: transform(x, short, full) for k, x in v.items()}
        if v.get('$type') == 'NodeRef' and v.get('$value') == short:
            out['$value'] = full
        return out
    if isinstance(v, list):
        return [transform(x, short, full) for x in v]
    return v
def eval_fact_condition(c, state):
    if c['$type'] == 'questLogicalCondition':
        results = [eval_fact_condition(x['Data'], state) for x in c['conditions']]
        return all(results) if c['operation'] == 'AND' else any(results)
    t = c['type']['Data']; x = state.get(t['factName'], 0); y = t['value']
    return {'Equal': x == y, 'NotEqual': x != y, 'Less': x < y, 'GreaterOrEqual': x >= y}[t['comparisonType']]

m = read(A / 'manifest.json')
assert {s['key'] for s in m['sites']} == {'riot', 'empathy', '7th_hell', 'totentanz'}
assert m['excluded'] == ['atlantis'] and len(m['resources']) == 12
expected = dict(PostTowerFreeRoamActive=1, PTFRP0_DR13=1, q307_active=0,
                q307_done=1, q307_finished=1, q307_2079=1,
                q307_main_game_killed=1, q307_ep1_killed=1,
                q305_johnny_scene_active=0, q115_point_of_no_return=0,
                PTFRBASE_Suspended=0, PTFRDANCE_Suspended=0, PTFRDANCE_QuestOwns=0)
assert m['guards'] == expected
ids = {}
for xl in (ROOT / 'archive').rglob('*.xl'):
    for depot in re.findall(r'path:\s*([^\s#]+\.questphase)', xl.read_text(encoding='utf-8-sig')):
        ids.setdefault(binascii.crc_hqx((depot + ':1').encode(), 65535), set()).add(depot)
negative = 0
for s in m['sites']:
    key = s['key']; prefix = f'PTFRDANCE_{key}_'; short = f'#dancefloor_tr_{key}'
    b = read(A / f'{key}_original_owner.json')['Data']['RootChunk']
    o = read(A / f'{key}_owner.json')['Data']['RootChunk']
    gate = read(A / f'{key}_gate.json')['Data']['RootChunk']
    scene = read(A / f'{key}_scene.json')['Data']['RootChunk']
    bs = read(A / f'{key}_original_scene.json')['Data']['RootChunk']
    assert clean(scene) == clean(transform(bs, short, s['trigger'])), key
    audit_scene_actor_ids(scene)
    assert scene['actors'] == [] and len(scene['playerActors']) == 1
    assert scene['playerActors'][0]['actorId']['id'] == 0
    assert not any(x.get('$type') == 'questSetVar_NodeType' for x in walk(scene))
    assert not any('johnny' in str(x.get('actorName', '')).lower() for x in walk(scene))
    # Vanilla provides only Dance; movement input is the normal cancellation,
    # not an explicit Stop choice. Verify its path to the cleanup cut.
    sn = {n['Data']['nodeId']['id']: n['Data'] for n in scene['sceneGraph']['Data']['graph']}
    choices = [n for n in sn.values() if n['$type'] == 'scnChoiceNode']
    assert len(choices) == 1 and [o['caption']['$value'] for o in choices[0]['options']] == ['dance']
    exit_condition = sn[65]['questNode']['Data']['condition']['Data']
    assert exit_condition['operation'] == 'OR'
    inputs = [x for x in walk(exit_condition) if x.get('$type') == 'questInputAction_ConditionType']
    assert len(inputs) == 4
    assert sorted((x['inputAction']['$value'], x['axisAction'], x['valueMoreThan'], x['valueLessThan']) for x in inputs) == sorted([
        ('MoveX', 1, inputs[0]['valueMoreThan'], 1), ('MoveX', 1, -inputs[0]['valueMoreThan'], -1),
        ('MoveY', 1, inputs[0]['valueMoreThan'], 1), ('MoveY', 1, -inputs[0]['valueMoreThan'], -1)])
    assert abs(inputs[0]['valueMoreThan'] - 0.1) < 0.00001
    scene_edges = {(ident, d['nodeId']['id']) for ident, n in sn.items() for socket in n.get('outputSockets', []) for d in socket.get('destinations', [])}
    assert (37, 65) in scene_edges
    cuts = [sn[dest] for src, dest in scene_edges if src == 65]
    assert len(cuts) == 1 and cuts[0]['$type'] == 'scnCutControlNode'
    cleanup_dest = cuts[0]['outputSockets'][0]['destinations'][0]['nodeId']['id']
    assert sn[cleanup_dest]['$type'] == 'scnSectionNode'
    cleanup_targets = [sn[dest] for src, dest in scene_edges if src == cleanup_dest]
    assert any(x.get('function') == 'StopWorkspot' for n in cleanup_targets for x in walk(n))
    assert any(x.get('tier') == 'Tier1_FullGameplay' for n in cleanup_targets for x in walk(n))
    # Cleanup stays identical: restriction removal, workspot stop, HUD restore.
    effects = [x for x in walk(scene) if x.get('$type') == 'questGameplayRestrictions_NodeType']
    assert len(effects) == 2
    add, remove = sorted(effects, key=lambda x: x['action'])
    assert add['action'] == 'AddRestriction' and remove['action'] == 'RemoveRestriction'
    assert add['source'] == remove['source'] and add['restrictionIDs'] == remove['restrictionIDs']
    assert any(x.get('function') == 'StopWorkspot' for x in walk(scene))
    be, bn = quest_edges(b); oe, on = quest_edges(o)
    bn = {n['id']: n for n in bn}; on = {n['id']: n for n in on}
    into = (s['entry'], 'Out', 9, f'dancefloor_{key}_in')
    out = (9, f'dancefloor_{key}_out', 10, 'In')
    assert oe == (be - {into, out}) | {
        (s['entry'], 'Out', 20, 'In'), (20, 'Out', 9, into[3]),
        (9, out[1], 21, 'In'), (21, 'Out', 10, 'In')}
    assert set(on) == set(bn) | {20, 21}
    ge, gn = quest_edges(gate); gn = {n['id']: n for n in gn}
    assert ge == {(0, 'Out', 1, 'In'), (1, 'Out', 2, 'In1')} and gate['phasePrefabs'] == []
    assert gn[2]['phaseResource']['DepotPath']['$value'] == f'towercontinued\\club_dancing\\{key}_owner.questphase'
    guard = gn[1]['condition']['Data']; assert guard['operation'] == 'AND'
    guard_facts = {x['factName']: (x['comparisonType'], x['value']) for x in walk(guard) if x.get('$type') == 'questVarComparison_ConditionType'}
    assert guard_facts == {f: ('Equal', v) for f, v in expected.items()} | {
        s['availability']: ('GreaterOrEqual', 1), prefix + 'Suspended': ('Equal', 0)}
    entry = on[s['entry']]['condition']['Data']
    assert clean(entry['conditions'][:-1]) == clean(guard['conditions'])
    assert clean(entry['conditions'][-1]['Data']) == clean(transform(bn[s['entry']]['condition']['Data'], short, s['trigger']))
    stop = on[4]['condition']['Data']; assert stop['operation'] == 'OR'
    assert clean(stop['conditions'][0]['Data']) == clean(bn[4]['condition']['Data'])
    sf = {x['factName']: (x['comparisonType'], x['value']) for x in walk(stop) if x.get('$type') == 'questVarComparison_ConditionType'}
    assert sf == {f: ('NotEqual', v) for f, v in expected.items()} | {
        s['availability']: ('Less', 1), prefix + 'Suspended': ('NotEqual', 0)}
    state = expected | {s['availability']: 1, prefix + 'Suspended': 0}
    assert eval_fact_condition(guard, state) and not eval_fact_condition(stop, state)
    for fact, target in state.items():
        for bad in (-1, 0, 1, 2):
            if bad == target or (fact == s['availability'] and bad >= 1):
                continue
            assert not eval_fact_condition(guard, state | {fact: bad})
            assert eval_fact_condition(stop, state | {fact: bad}); negative += 1
    assert eval_fact_condition(guard, state | {s['availability']: 2})
    transformed = transform(b, short, s['trigger'])
    expected_nodes = {n['Data']['id']: n['Data'] for n in transformed['graph']['Data']['nodes']}
    for ident in bn:
        orig = clean(expected_nodes[ident]); actual = clean(on[ident])
        if ident == s['init']:
            orig['type']['Data']['factName'] = prefix + 'Registered'
        if ident in (4, s['entry']):
            orig['condition'] = actual['condition']
        if ident == 9:
            orig['sceneFile']['DepotPath']['$value'] = f'towercontinued\\club_dancing\\{key}.scene'
        assert orig == actual, (key, ident)
    writers = [x for x in walk(o) if x.get('$type') == 'questSetVar_NodeType']
    assert sorted((x['factName'], x['value'], x['setExactValue']) for x in writers) == sorted([
        (prefix + 'Registered', 1, 1), (prefix + 'Requests', 1, 0), (prefix + 'Returns', 1, 0)])
    assert len(o['phasePrefabs']) == 1 and o['phasePrefabs'][0]['prefabNodeRef']['$value'] == s['prefab']
    world = read(A / f'world/json/base/worlds/03_night_city/_compiled/default/{s["sector"]}.streamingsector.json')['Data']['RootChunk']
    assert len(world['nodes']) == 1 and world['nodes'][0]['Data']['$type'] == 'worldTriggerAreaNode'
    assert world['nodes'][0]['Data']['notifiers'][0]['Data']['isEnabled'] == 1
    assert world['nodeData']['Data'][0]['QuestPrefabRefHash']['$value'] == s['trigger']
    depot = f'towercontinued\\club_dancing\\{key}_gate.questphase'
    crc = binascii.crc_hqx((depot + ':1').encode(), 65535)
    assert crc == s['registration_id'] and ids[crc] == {depot}
archive = ROOT / 'build/ClubDancing/TowerContinued_ClubDancing.archive'
assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == m['sha256']
xl = Path(str(archive) + '.xl')
assert hashlib.sha256(xl.read_bytes()).hexdigest().upper() == m['xl_sha256']
assert re.findall(r'path:\s*([^\s#]+\.questphase)', xl.read_text()) == [f'towercontinued\\club_dancing\\{s["key"]}_gate.questphase' for s in m['sites']]
print(f'PASS: four exact vanilla scenes and scoped leaf deltas; actor/cleanup/native edge checks; {negative} negative guards; no vanilla fact writes; trigger/registration/archive checks')
