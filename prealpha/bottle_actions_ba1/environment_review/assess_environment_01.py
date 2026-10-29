import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
out = root / 'assessment_01.json'
if out.exists():
    raise SystemExit('Preserve existing evidence')
checks = []
def check(name, value):
    checks.append({'name': name, 'pass': bool(value)})
    assert value, name
def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()
prefix = '$/03_night_city/c_pacifica/coastview/cvi_ce_prefabMZQN2IY/cs_goons_shooting_env_002_prefabBCFE3FQ/'
suffixes = ['target_object_001_prefabG6AJLQI', 'target_object_prefabG6AJLQI', 'cs_goons_shooting_sec_system', 'cs_goons_shooting_sec_area']
sector = r'base\worlds\03_night_city\_compiled\default\exterior_-33_-30_0_0.streamingsector'
census = read(root / 'census_exact_01/report_01.json')
check('125 current installed archives read', census['archives'] == 125)
for resource in census['resources']:
    hits = [x for x in census['hits'] if x['depot'] == resource]
    check('Only base+EP1 hits: ' + resource, sorted(Path(x['archive']).name for x in hits) == ['basegame_3_nightcity.archive', 'ep1_1_nightcity.archive'])

selected = {}
descriptors = {}
pins = [root / 'census_exact_01/report_01.json', root / 'decode_exact_03/report_01.json']
for archive in ['basegame_3_nightcity', 'ep1_1_nightcity']:
    stem = archive + '_11726666985050404615.streamingsector'
    np = root / ('decode_exact_03/' + stem + '.nodes.json')
    pp = root / ('decode_exact_03/' + stem + '.placements.json')
    nodes = {x['node']: x['definition'] for x in read(np)['nodes']}
    placements = read(pp)['placements']
    selected[archive] = []
    for suffix in suffixes:
        matches = [x for x in placements if x['quest_ref'] == prefix + suffix]
        check(archive + ': unique exact placement ' + suffix, len(matches) == 1)
        placement = {k: v for k, v in matches[0].items() if k != 'id'}
        selected[archive].append({'placement': placement, 'definition': nodes[placement['node']]})
    bp = root / ('census_exact_01/' + archive + '.archive/all.streamingblock.json')
    candidates = [x for x in read(bp)['Data']['RootChunk']['descriptors'] if x['data']['DepotPath']['$value'] == sector]
    check(archive + ': unique default block registration', len(candidates) == 1)
    desc = candidates[0]
    descriptors[archive] = desc
    check(archive + ': Exterior level0 non-quest descriptor', desc['category'] == 'Exterior' and desc['level'] == 0 and desc['questPrefabNodeRef']['$value'] == '0')
    check(archive + ': named variant refs are unrelated rave prefab', all('cs_goons_rave_party_env_prefabNDTZAKQ' in v['nodeRef']['$value'] for v in desc['variants']))
    raw = root / ('census_exact_01/' + archive + '.archive/exterior_-33_-30_0_0.streamingsector')
    original = root / ('nearby_01/' + stem)
    check(archive + ': decoded sector equals current extracted sector', sha(raw) == sha(original))
    pins += [np, pp, bp, raw, bp.with_suffix('')]

check('Base+EP1 selected definitions and placements equal excluding cooker ID', selected['basegame_3_nightcity'] == selected['ep1_1_nightcity'])
check('Base+EP1 exact Exterior descriptor equal', descriptors['basegame_3_nightcity'] == descriptors['ep1_1_nightcity'])
rows = selected['ep1_1_nightcity']
for row in rows[:2]:
    node = row['definition']
    check('Native AI target entity: ' + node['debugName']['$value'], node['$type'] == 'worldEntityNode' and node['entityTemplate']['DepotPath']['$value'] == r'base\gameplay\ai\ai_objects\target_object.ent' and node['isVisibleInGame'] == 1 and node['instanceData'] is None)
system, area = [x['definition'] for x in rows[2:]]
links = {(c['deviceClassName']['$value'], tuple(v['$value'] for v in c['nodeRefs'])) for c in system['deviceConnections']}
check('Security system links exact sibling area', ('SecurityAreaControllerPS', ('~/../cs_goons_shooting_sec_area',)) in links)
check('Security system links exact CE112 community', ('CommunityProxyPS', ('#ce_pac_cvi_112_com',)) in links)
def ps(node, typename):
    return next(c['persistentState']['Data'] for c in node['instanceData']['Data']['buffer']['Data']['Chunks'] if c.get('persistentState', {}).get('Data', {}).get('$type') == typename)
system_ps = ps(system, 'SecuritySystemControllerPS')
area_ps = ps(area, 'SecurityAreaControllerPS')
check('Authored security system on and not strict quest control', system_ps['deviceState'] == 'ON' and system_ps['isUnderStrictQuestControl'] == 0)
check('Authored security area on and restricted', area_ps['deviceState'] == 'ON' and area_ps['securityAreaType'] == 'RESTRICTED')
check('All four nodes share authored environment prefab source', len({x['definition']['sourcePrefabHash'] for x in rows}) == 1)

assessment = {
    'status': 'PASS_STATIC_DEFAULT_WORLD_ENVIRONMENT_OWNERSHIP',
    'scope': 'Independent read-only BA1 absolute target and security environment trace',
    'checks_passed': len(checks),
    'checks': checks,
    'sector': sector,
    'archive_census_count': census['archives'],
    'mod_overrides': 0,
    'selected_nodes': rows,
    'default_exterior_descriptor': descriptors['ep1_1_nightcity'],
    'conclusion': 'Both exact target references and the security area/system are authored in a default-world Exterior sector with questPrefabNodeRef=0. The installed base and EP1 copies agree on all four relevant definitions, placement references/positions and block registration. The security system connects this exact area and CE112 community. No additional quest prefab owner is indicated for these dependencies; the isolated native action controller can use the existing streamed world objects.',
    'limits': [
        'Static source ownership is not proof that a specific saved runtime currently has an object streamed, intact or in its authored initial security state.',
        'Authored deviceState ON and security SAFE/RESTRICTED are template defaults, not live save observations.',
        'The placement decoder label quest_ref names the authored QuestPrefabRefHash NodeRef field; its nonzero value is not evidence of quest-only streaming ownership. Default block registration supplies the ownership evidence.',
        'Cooker placement IDs differ between base and EP1 and are excluded from the semantic placement comparison; exact NodeRefs, node indices/types and positions agree.',
        'The earlier raw byte hash scan was non-diagnostic because node setup data is compressed. Only decompressed exact-sector evidence is selected.',
        'BA1 source/native invalid-target cancellation and controller lifecycle are reviewed separately by the native reviewer. This assessment does not claim live shooting or speech recovery.'
    ],
    'game_writes': 0,
    'save_writes': 0,
    'candidate_edits': 0,
    'evidence': [{'path': str(p.relative_to(root)), 'sha256': sha(p)} for p in pins]
}
out.write_text(json.dumps(assessment, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': assessment['status'], 'checks_passed': len(checks), 'assessment': str(out), 'sha256': sha(out)}, indent=2))
