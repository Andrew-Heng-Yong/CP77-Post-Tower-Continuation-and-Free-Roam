"""Bounded C5 regression: preserve the full vanilla scene except its exit NodeRef."""
import hashlib
import binascii
import re
import json
from pathlib import Path
from test_streetkid_scene_load_s3 import quest_edges

root = Path(__file__).resolve().parents[1]
folder = root / 'research/b0_mirror_rollout/validation_c5_red_dirt'
original = json.loads((folder / 'red_dirt_original.scene.json').read_text(encoding='utf-8-sig'))
candidate = json.loads((folder / 'red_dirt_candidate.scene.json').read_text(encoding='utf-8-sig'))
manifest = json.loads((folder / 'build_manifest.json').read_text(encoding='utf-8-sig'))
changes = []

def compare(a, b, path=()):
    assert type(a) is type(b), path
    if isinstance(a, dict):
        assert a.keys() == b.keys(), path
        for key in a:
            compare(a[key], b[key], path + (key,))
    elif isinstance(a, list):
        assert len(a) == len(b), path
        for index, (left, right) in enumerate(zip(a, b)):
            compare(left, right, path + (index,))
    elif a != b:
        changes.append((path, a, b))

compare(original['Data'], candidate['Data'])
assert len(changes) == 1, changes
path, before, after = changes[0]
assert path[-2:] == ('triggerAreaRef', '$value'), changes
assert before == '#mirror_tr_red_dirt', changes
assert after == manifest['sites'][0]['trigger'], changes
assert manifest['opt_in_fact'] == 'PTFRBM42_Enabled'
assert manifest['automatic'] is False
assert [site['id'] for site in manifest['sites']] == [42]
assert manifest['vanilla_replacements'] == []
assert len(manifest['resources']) == 3
assert all(p.startswith('towercontinued\\ordinary_mirrors_c5_red_dirt\\') for p in manifest['resources'])
archive = root / 'build/OrdinaryMirrors_C5_RED_DIRT' / manifest['archive']
assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest['sha256']

def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)

expected = dict(PostTowerFreeRoamActive=1, PTFRP0_DR13=1, q307_active=0,
                q307_done=1, q307_finished=1, q307_2079=1,
                q307_main_game_killed=1, q305_johnny_scene_active=0,
                mirror_interaction_disabled=0, q115_point_of_no_return=0,
                PTFRBM42_Enabled=1, PTFRBASE_Suspended=0, PTFRBM42_Interrupted=0)
expected['sq011_mirror_off '] = 0
for name, count in [('gate', 3), ('owner', 11)]:
    data = json.loads((folder / (name + '.json')).read_text(encoding='utf-8-sig'))
    nodes = data['Data']['RootChunk']['graph']['Data']['nodes']
    assert len(nodes) == count
    guard = next(n['Data']['condition'] for n in nodes if n['Data']['id'] == 1)
    comparisons = [x for x in walk(guard) if x.get('$type') == 'questVarComparison_ConditionType']
    assert {x['factName']: x['value'] for x in comparisons} == expected
    assert all(x['comparisonType'] == 'Equal' for x in comparisons)
    edges, _ = quest_edges(data['Data']['RootChunk'])
    if name == 'gate':
        assert edges == {(0,'Out',1,'In'),(1,'Out',2,'In1')}
    else:
        assert edges == {(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),
                         (3,'Out',4,'mirror_interaction'),(4,'mirror_interaction_out',5,'In'),
                         (5,'Out',6,'In'),(6,'Out',7,'In'),(7,'Out',1,'In'),
                         (4,'Default INT',8,'In'),(8,'Out',9,'In'),
                         (9,'Out',10,'In'),(10,'Out',7,'In')}
    for x in walk(data):
        if x.get('$type') == 'questSetVar_NodeType':
            assert x['factName'].startswith('PTFRBM42_'), x
gate_path = 'towercontinued\\ordinary_mirrors_c5_red_dirt\\m42_gate.questphase'
crc = binascii.crc_hqx((gate_path + ':1').encode(), 65535)
assert crc == manifest['sites'][0]['registration_id']
for f in (root / 'archive').rglob('*.xl'):
    for p in re.findall(r'path:\s*([^\s#]+\.questphase)', f.read_text(encoding='utf-8-sig')):
        if p != gate_path:
            assert binascii.crc_hqx((p + ':1').encode(), 65535) != crc, (f, p)
print('PASS: exact single exit-NodeRef delta; all scene gates/actions unchanged; one-site opt-in archive hash matches')
