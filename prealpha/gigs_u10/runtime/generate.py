"""Generate bounded U10 admission from reviewed contracts; no game writes."""
import argparse
import hashlib
import json
import re
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
POLICY = ROOT / 'research/gig_restoration/lore_whitelists_v6_1_dependencies.json'
TEMPLATE = HERE / 'GigsU10.template.reds'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def q(value):
    return json.dumps(value, ensure_ascii=True)


def normalize(paths):
    selected = {r['id']: r for r in read(POLICY)['decision_registry']
                if r['category'] == 'gigs' and r['change'] == 'ADDED_TO_R6'}
    assert len(selected) == 8
    rows = []
    for path in paths:
        doc = read(path)
        for owner in doc.get('owners', doc.get('contracts', [doc])):
            ident = owner['id']; assert ident in selected
            assert owner['tag'] == 'PTFRU10_' + ident
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
                    assert ident == 'sts_wbr_hil_06' and j == {'path': 'quests/main_quest/act_01/q103_warhead', 'class': 'gameJournalQuest', 'states': [3]}
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
            terminal = owner['map_facts_zero']
            assert terminal and len(set(terminal)) == len(terminal)
            assert all(equal.get(f) == 0 for f in terminal)
            service = owner.get('service_facts_equal', {})
            allowed_services = {'PTFRU9_Retaliation_Issued': 1, 'PTFRU9_Retaliation_Fault': 0}
            gang = {'sts_hey_rey_02': 'valentinos', 'sts_wbr_jpn_12': 'tygerclaws'}.get(ident)
            if gang:
                allowed_services.update({f'PTFRU9_Retaliation_{gang}_Issued': 1, f'PTFRU9_Retaliation_{gang}_Fault': 0})
                assert service == allowed_services
            else:
                assert service == {}
            assert not set(service) & set(equal)
            items = owner['inventory_zero']
            expected_items = {
                'sts_hey_gle_03': ['Items.sts_hey_gle_03_guitar'],
                'sts_hey_gle_05': ['Items.sts_hey_gle_05_scandium_cores'],
                'sts_wat_nid_07': ['Items.sts_wat_nid_07_recording'],
                'sts_wbr_hil_06': ['Items.sts_wbr_hil_06_bootleg', 'Items.sts_wbr_hil_06_keys'],
                'sts_wbr_jpn_12': ['Items.sts_wbr_jpn_12_corpo_cracker'],
            }.get(ident, [])
            assert [item['record'] for item in items] == expected_items
            for item in items:
                encoded = item['record'].encode('ascii')
                assert item['hash'] == str((len(encoded) << 32) | zlib.crc32(encoded))
            rows.append({'id': ident, 'title': selected[ident]['title'], 'tag': owner['tag'],
                         'journals': journals, 'facts': facts, 'map_facts_zero': terminal, 'service_facts_equal': service,
                         'inventory_zero': items,
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
            'MapFactsZero': row['map_facts_zero'],
            'ServiceNames': list(row['service_facts_equal']),
            'ServiceValues': list(row['service_facts_equal'].values()),
            'ItemNames': [item['record'] for item in row['inventory_zero']]}


def data_source(rows):
    lines = ['public abstract class GigDataU10 {',
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
        typ = 'String' if method in ['Paths', 'Classes', 'FactNames', 'MapFactsZero', 'ServiceNames', 'ItemNames'] else 'Int32'
        lines.append(f'  public static func {method}(i: Int32) -> array<{typ}> {{')
        for i in range(len(rows)):
            lines.append(f'    if i == {i} {{ return GigDataU10.{method}{i}(); }}')
        lines.append(f'    let empty: array<{typ}>; return empty;\n  }}')
        for i, row in enumerate(rows):
            lines.append(f'  public static func {method}{i}() -> array<{typ}> {{ return {q(arrays(row)[method])}; }}')
    return '\n'.join(lines + ['}']) + '\n'


def template():
    text = TEMPLATE.read_text(encoding='utf-8')
    replacements = {
        'let wanted = GigDataU10.FactValues(i);': 'let minimum = GigDataU10.FactMin(i); let maximum = GigDataU10.FactMax(i);',
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
    target = output / 'GigsU10.reds'
    target.write_text(template().replace('// GENERATED_DATA', data_source(rows)), encoding='utf-8')
    pins = {p.relative_to(ROOT).as_posix(): sha(p) for p in [*paths, POLICY, TEMPLATE, Path(__file__)]}
    manifest = {'status': 'GENERATED_NOT_INSTALLED', 'source_pins': pins, 'rows': rows,
                'files': {'GigsU10.reds': sha(target)},
                'policy': 'Original beginnings; completed and existing owners/progress preserved. Unsupported continuation defers. No reset, replay or invented pre-ending certificate.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return {'output': str(output), 'entries': len(rows), 'sha256': sha(target)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('contracts', type=Path, nargs='+')
    args = parser.parse_args()
    print(json.dumps(generate([p.resolve() for p in args.contracts], args.out.resolve())))
