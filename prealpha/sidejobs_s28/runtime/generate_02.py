"""Generate bounded S28 admission from reviewed contracts; no game writes."""
import argparse
import hashlib
import json
import re
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
POLICY = ROOT / 'research/gig_restoration/lore_whitelists_v6_1_dependencies.json'
TEMPLATE = HERE / 'SideJobsS28.template_02.reds'
NATIVE_PREDICATES = {'highwayman_vehicle': {'class': 'PTFR.SideJobsS28.PTFRS28HighwaymanVehicleUnownedPrereq',
                        'kind': 'vehicle_unowned',
                        'record': 'Vehicle.v_sportbike2_arch_tyger_player',
                        'hash': '167323116460'},
 'hoon_vehicle': {'class': 'PTFR.SideJobsS28.PTFRS28HoonVehicleUnownedPrereq',
                  'kind': 'vehicle_unowned',
                  'record': 'Vehicle.v_sport2_quadra_type66_nomad_tribute',
                  'hash': '189393478117'},
 'hoon_world_key': {'class': 'PTFR.SideJobsS28.PTFRS28HoonWorldKeyAbsentPrereq',
                    'kind': 'loaded_world_inventory_zero',
                    'node_ref': '$/03_night_city/c_watson/northside/loc_mq050_ken_block_tribute_prefabIK2VAKA/loc_mq050_ken_block_tribute_gameplay_prefabJPVRKTI/loc_mq050_ken_block_tribute_loot_prefabPU3FSXA/#mq050_main_loot',
                    'record': 'Keycards.mq050_car_keys',
                    'hash': '99716362400',
                    'unloaded': 'DEFER',
                    'native_target_witness': {'depot': 'base\\quest\\minor_quests\\mq050\\mq050.questphase',
                                              'node': 51,
                                              'reference': '#mq050_main_loot'}}}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def q(value):
    return json.dumps(value, ensure_ascii=True)


def normalize(paths):
    selected = {r['id']: r for r in read(POLICY)['decision_registry']
                if r['id'] in {'mq003_orbitals', 'mq022_ezekiel', 'mq029_tourist', 'mq050_ken_block_tribute'}}
    assert len(selected) == 4
    assert all(r['decision'] == 'INCLUDE' and r['category'] == 'side_and_minor_jobs' for r in selected.values())
    rows = []
    for path in paths:
        doc = read(path)
        owners = doc.get('owners', doc.get('contracts', [doc]))
        if any(o['id'] in {'mq029_tourist', 'mq050_ken_block_tribute'} for o in owners):
            assert doc['native_runtime_predicates'] == NATIVE_PREDICATES
        for owner in doc.get('owners', doc.get('contracts', [doc])):
            ident = owner['id']; assert ident in selected
            assert owner['tag'] == 'PTFRS28_' + ident
            journals = []
            for journal in owner['journals']:
                states = journal['states']
                assert 1 <= len(states) <= 2
                assert all(type(s) is int and s in [1, 2, 3, 4] for s in states)
                journals.append({'path': journal['path'], 'class': journal['class'], 'states': states})
            assert journals[0] == {'path': selected[ident]['journal_path'], 'class': 'gameJournalQuest', 'states': [1]}
            assert len({j['path'] for j in journals}) == len(journals)
            for j in journals[1:]:
                if j['class'] == 'gameJournalQuest':
                    assert j == {'path': 'quests/main_quest/act_01/q101_resurrection', 'class': 'gameJournalQuest', 'states': [3]}
                else:
                    # These adapters implement original beginnings only. A
                    # progressed objective cannot be admitted by broadening its
                    # allowed state in a successor contract.
                    assert j['path'].startswith(selected[ident]['journal_path'] + '/')
                    assert j['class'] in ['gameJournalQuestPhase', 'gameJournalQuestObjective',
                                          'gameJournalQuestDescription', 'gameJournalQuestCodexLink',
                                          'gameJournalQuestMapPin']
                    assert j['states'] == [1]
            facts = []
            equal = owner['facts_equal']; ranges = owner.get('fact_ranges', {})
            assert not set(equal) & set(ranges)
            for name, number in equal.items():
                assert type(number) is int
                facts.append({'name': name, 'min': number, 'max': number})
            for name, bounds in ranges.items():
                assert set(bounds) == {'min', 'max'}
                assert all(type(v) is int for v in bounds.values())
                assert -2147483646 <= bounds['min'] <= bounds['max'] <= 2147483647
                facts.append({'name': name, **bounds})
            assert facts and len({f['name'] for f in facts}) == len(facts)
            assert all(not f['name'].endswith(('_Permit', '_MapPermit', '_PreparePermit')) for f in facts)
            items = owner['inventory_zero']
            vehicles = owner['vehicle_zero']
            if ident in {'mq029_tourist', 'mq050_ken_block_tribute'}:
                key = 'highwayman_vehicle' if ident == 'mq029_tourist' else 'hoon_vehicle'
                expected = NATIVE_PREDICATES[key]
                assert vehicles == [{'record': expected['record'], 'hash': expected['hash']}]
                required = [expected['class']]
                world = []
                if ident == 'mq050_ken_block_tribute':
                    required.append(NATIVE_PREDICATES['hoon_world_key']['class'])
                    world = [NATIVE_PREDICATES['hoon_world_key']]
                assert owner['native_predicates'] == required
                assert owner['native_world_inventory_zero'] == world
            for entries, prefixes in [(items, ('Items.', 'Keycards.')), (vehicles, ('Vehicle.',))]:
                assert len({x['record'] for x in entries}) == len(entries)
                for item in entries:
                    assert any(re.fullmatch(re.escape(prefix) + r'[A-Za-z0-9_]+', item['record']) for prefix in prefixes)
                    encoded = item['record'].encode('ascii')
                    assert item['hash'] == str((len(encoded) << 32) | zlib.crc32(encoded))
            rows.append({'id': ident, 'title': selected[ident]['title'], 'tag': owner['tag'],
                         'journals': journals, 'facts': facts, 
                         'inventory_zero': items, 'vehicle_zero': vehicles,
                         'native_predicates': owner.get('native_predicates', []),
                         'native_world_inventory_zero': owner.get('native_world_inventory_zero', []),
                         'source': path.relative_to(ROOT).as_posix(), 'source_sha256': sha(path)})
    assert len(rows) == len(selected) and {r['id'] for r in rows} == set(selected)
    return rows


def arrays(row):
    return {'Paths': [j['path'] for j in row['journals']],
            'Classes': [j['class'] for j in row['journals']],
            'StatesA': [j['states'][0] for j in row['journals']],
            'StatesB': [j['states'][-1] for j in row['journals']],
            'FactNames': [f['name'] for f in row['facts']],
            'FactMin': [f['min'] for f in row['facts']],
            'FactMax': [f['max'] for f in row['facts']],
            'ItemNames': [item['record'] for item in row['inventory_zero']],
            'VehicleNames': [item['record'] for item in row['vehicle_zero']]}


def data_source(rows):
    lines = ['public abstract class SideJobDataS28 {',
             f'  public static func Count() -> Int32 {{ return {len(rows)}; }}']
    for method, field in [('ID', 'id'), ('Title', 'title'), ('Tag', 'tag')]:
        lines.append(f'  public static func {method}(i: Int32) -> String {{')
        for i, row in enumerate(rows):
            lines.append(f'    if i == {i} {{ return {q(row[field])}; }}')
        lines.append('    return "";\n  }')
    lines.append('  public static func Index(id: String) -> Int32 {')
    for i, row in enumerate(rows):
        lines.append(f'    if Equals(id, {q(row["id"])}) || Equals(id, {q(row["tag"])}) {{ return {i}; }}')
    lines.append('    return -1;\n  }')
    for method in arrays(rows[0]):
        typ = 'String' if method in ['Paths', 'Classes', 'FactNames', 'ItemNames', 'VehicleNames'] else 'Int32'
        lines.append(f'  public static func {method}(i: Int32) -> array<{typ}> {{')
        for i in range(len(rows)):
            lines.append(f'    if i == {i} {{ return SideJobDataS28.{method}{i}(); }}')
        lines.append(f'    let empty: array<{typ}>; return empty;\n  }}')
        for i, row in enumerate(rows):
            lines.append(f'  public static func {method}{i}() -> array<{typ}> {{ return {q(arrays(row)[method])}; }}')
    return '\n'.join(lines + ['}']) + '\n'


def template():
    text = TEMPLATE.read_text(encoding='utf-8')
    replacements = {
        'let wanted = SideJobDataS28.FactValues(i);': 'let minimum = SideJobDataS28.FactMin(i); let maximum = SideJobDataS28.FactMax(i);',
        'ArraySize(names) != ArraySize(wanted)': 'ArraySize(names) != ArraySize(minimum) || ArraySize(names) != ArraySize(maximum)',
        'actual != wanted[k]': 'actual < minimum[k] || actual > maximum[k]',
        'ToString(wanted[k])': 'ToString(minimum[k]) + ".." + ToString(maximum[k])',
    }
    for old, new in replacements.items():
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    return text


def generate(paths, output):
    assert not output.exists(), 'Use a new immutable revision'
    rows = normalize(paths)
    output.mkdir(parents=True)
    target = output / 'SideJobsS28.reds'
    target.write_text(template().replace('// GENERATED_DATA', data_source(rows)), encoding='utf-8')
    pins = {p.relative_to(ROOT).as_posix(): sha(p) for p in [*paths, POLICY, TEMPLATE, Path(__file__)]}
    manifest = {'status': 'GENERATED_NOT_INSTALLED', 'source_pins': pins, 'rows': rows,
                'native_runtime_predicates': NATIVE_PREDICATES,
                'files': {'SideJobsS28.reds': sha(target)},
                'policy': 'Original beginnings; completed and existing owners/progress preserved. Unsupported continuation defers. No reset, replay or invented pre-ending certificate.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return {'output': str(output), 'entries': len(rows), 'sha256': sha(target)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('contracts', type=Path, nargs='+')
    args = parser.parse_args()
    print(json.dumps(generate([p.resolve() for p in args.contracts], args.out.resolve())))
