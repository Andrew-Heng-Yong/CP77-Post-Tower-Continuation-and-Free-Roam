"""Verify the combined resource delta and ArchiveXL registration before packing."""

from binascii import crc_hqx
from pathlib import Path
import re
import sys

from prepare import (
    AMBIENT, ARCHIVE, AUDIT, BASE, BASELINE, BASE_MANIFEST, ENTRY, HERE, INSTALLED,
    LIPMAP, OUT, QP1, QP1_PROOF, TRUCK, XL, baseline, checked, inventory, module, plain, read, sha, write,
)
from resources import Resource

VERIFY = HERE / 'verification.json'
PACK_PLAN = HERE / 'pack_inputs.json'
COMPILE = HERE / 'compile_01/result.json'


def normalized(doc):
    model = Resource(doc).normalize()
    assert not model['errors'], model['errors']
    return model


def entry_check(plan, base):
    evidence = OUT / 'entry_readback'
    result = read(evidence / 'result.json')
    assert result['status'] == 'COOKED_QP2_ENTRY' and result['owner'] == 50
    assert result['before'] == base['source_resources'][ENTRY] == plan['entry']['before']
    assert result['donor'] == plan['entry']['donor_sha256']
    checked(OUT / 'archive_source' / ENTRY, result['after'])
    original, donor, merged = [
        normalized(read(checked(evidence / (name + '.json'), result[name + '_json'])))
        for name in ('before', 'donor', 'after')
    ]
    a, b, c = (m['graphs']['root']['nodes']['50'] for m in (original, donor, merged))
    field = 'phaseInstancePrefabs'
    assert a['prefabs'] == [] and c['prefabs'] == b['prefabs'] == [result['prefab']]
    assert a['payload'][field] == [] and c['payload'][field] == b['payload'][field]
    assert {k for k in a if a[k] != c[k]} == {'payload', 'payload_sha256', 'prefabs', 'node_refs'}
    assert c['payload'] | {field: []} == a['payload']
    assert set(c['node_refs']) == set(a['node_refs']) | {result['prefab']}
    merged['graphs']['root']['nodes']['50'] = a
    assert merged == original
    graph = original['graphs']['root/50']
    assert ('9', 'Out1', '2', 'In') in map(tuple, graph['edges'])
    assert graph['nodes']['2']['node_refs'] == ['#sts_ep1_06_tr_init']
    assert graph['nodes']['4']['refs'] == [r'towercontinued\johnny_batch6\sts_ep1_06\sts_ep1_06_zembinsky.questphase']
    return {'depot': ENTRY, 'before': result['before'], 'after': result['after'], 'lease': result['prefab'],
            'preserved_nested_caller': graph['nodes']['4']['refs'][0], 'normalized_delta': 'ONE_PHASE_INSTANCE_PREFAB'}


def scene_checks(plan, qp1):
    sys.path.insert(0, str(QP1.parent))
    checks = module('qp1_source_checks', QP1.parent / 'verify.py',
                    'B35ED00DD6259E847CD0ECD2075A6F61486003AC0A02342FE74A326A6F469CEC')
    saved = read(checked(QP1_PROOF, qp1['verification_sha256']))
    truck_json = QP1 / 'truck/scene.json'
    cases = read(checked(QP1 / 'truck/fixtures.json', qp1['truck_fixtures_sha256']))
    checked(truck_json, cases['cooked_scene_json_sha256'])
    checked(OUT / 'archive_source' / TRUCK, plan['copied_resources'][TRUCK])
    truck = checks.truck_scene(read(QP1 / 'inputs.json'))
    assert truck == saved['small_man'] and len(cases['cases']) == 5
    heavy = checks.heavy_hearts()
    assert heavy == saved['heavy_hearts']

    def johnny_events(model, active):
        return [e for node in active for e in model['events'][node]
                if any('johnny' in a.casefold() or 'silverhand' in a.casefold()
                       for a in [*e['actors'], *e['targets']])]
    scene = checks.scene(read(truck_json))
    reached, _ = checks.active_nodes(scene, 'Start 0')
    assert not johnny_events(scene, reached)
    assert all('voiceset' not in e['type'].casefold() for node in reached for e in scene['events'][node])

    captures = AUDIT / 'encounter_audit/capture_01'
    providers = read(checked(captures / 'providers.json', 'D2196CCF63FCC7545696AFE4B9073A7613A2F8B2FDCAD669FB8C2964C79BA34F'))
    for route in heavy['ambient_callers']:
        d = route['scene']
        row, = (r for r in providers['providers'] if r['depot'] == d and r['json'])
        expected = next(p['archives'] for p in plan['providers'] if p['depot'] == d)
        assert expected == {row['archive']: row['sha256']}
        model = checks.scene(read(checked(captures / row['json'], row['json_sha256'])))
        reached, _ = checks.active_nodes(model, route['input'])
        assert not johnny_events(model, reached)
        assert all('voiceset' not in e['type'].casefold() for node in reached for e in model['events'][node])
    return checks, {'small_man': truck, 'small_man_fixtures': len(cases['cases']),
                    'heavy_hearts': heavy, 'new_johnny_scene_events': 0}


def registration_check(installed, plan, parse):
    game = Path(installed['game_root'])
    old = (game / XL).read_bytes()
    new = checked(OUT / 'package' / XL, plan['xl_after']).read_bytes()
    newline = b'\r\n' if b'\r\n' in old else b'\n'
    addition = newline.join(x.encode() for x in (
        f'    - path: {AMBIENT}', r'      parent: ep1\quest\ep1.quest',
        '      input:', '        node: [1]', '        socket: Out', '',
    ))
    anchor = b'streaming:' + newline
    assert old.count(anchor) == 1 and addition not in old
    assert new == old.replace(anchor, addition + anchor)
    controls = read(checked(AUDIT / 'audit_controls.json',
                            'FA6391937F30A10B5C3FFB5863E96B86DCF702C6B28AE41EB690C3551E48663A'))
    native = set(controls['native_parent_ids'])
    paths = sorted((game / 'archive/pc').rglob('*.xl'))
    before, after = [], []
    for p in paths:
        plain(p)
        text = p.read_text(encoding='utf-8-sig')
        assert not re.search(r'(?i)sq030_msg_left_0[123]\.questphase', text), p
        before.extend(parse(text))
        after.extend(parse(new.decode('utf-8-sig')) if p == game / XL else parse(text))
    assert [d for d in after if d != AMBIENT] == before and after.count(AMBIENT) == 1
    ids = {crc_hqx((d + ':1').encode(), 65535) for d in after}
    assert len(ids) == len(after) and ids.isdisjoint(native)
    added_id = crc_hqx((AMBIENT + ':1').encode(), 65535)
    assert added_id == 60197
    return {'generated_node_id': added_id, 'xl_files': len(paths), 'phase_bindings': len(after),
            'native_parent_ids': sorted(native), 'xl_sha256': sha(OUT / 'package' / XL)}


def main():
    assert not VERIFY.exists() and not PACK_PLAN.exists()
    installed, base = baseline()
    plan = read(BASELINE)
    assert plan['installed_manifest_sha256'] == sha(INSTALLED)
    assert plan['baseline_package_sha256'] == sha(BASE_MANIFEST)
    qp1 = read(checked(QP1 / 'package_manifest.json', '69A61611FC9B5B04B7FC78EC38530E381CFA0626F628C373F90BD44CBE644FD8'))
    entry = entry_check(plan, base)
    verifier, scenes = scene_checks(plan, qp1)
    registration = registration_check(installed, plan, verifier.registrations)
    for p, digest in plan['proofs'].items():
        checked(p, digest)
    sources = base['source_resources']
    replacements = plan['copied_resources'] | {ENTRY: entry['after']}
    members = sources | replacements
    assert inventory(OUT / 'archive_source', '\\') == members and len(members) == 1729
    assert members.keys() - sources.keys() == set(plan['new_depots'])
    assert {d for d in sources if sources[d] != members[d]} == {r for r in replacements if r in sources}
    assert len(replacements) == 9 and members[LIPMAP] == sources[LIPMAP]
    compiled = read(COMPILE)
    assert compiled['status'] == 'PASS_QP2_COMPLETE_SOURCE_COMPILE' and compiled['exit_code'] == 0
    assert len(compiled['sources']) == compiled['source_count'] == 148 and len(compiled['input_pins']) == 151
    assert compiled['overlays'] == plan['scripts']
    for p, h in compiled['input_pins'].items():
        checked(p, h)
    write(VERIFY, {
        'status': 'PASS_QP2_MERGED_RESOURCES_AND_SCRIPTS', 'baseline_sha256': sha(BASELINE),
        'entry': entry, **scenes, 'registration': registration,
        'native_judy_overrides': plan['native_overrides'], 'retained_monk_map_sha256': members[LIPMAP],
        'compile_sha256': sha(COMPILE), 'compiled_sources': compiled['source_count'],
        'component_proofs': plan['proofs'], 'script_checks': plan['script_checks'],
    })
    write(PACK_PLAN, {
        'candidate': str(OUT), 'game_root': plan['game_root'], 'before_archive': plan['before_archive'],
        'providers': plan['providers'], 'members': members, 'verification_sha256': sha(VERIFY),
    })
    print(f"Verified the merged entry, quest routes and ArchiveXL ID {registration['generated_node_id']}.")


if __name__ == '__main__':
    main()
