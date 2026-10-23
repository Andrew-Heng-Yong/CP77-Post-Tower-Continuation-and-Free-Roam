"""Build S25 permission tables from independently audited per-family contracts.

The S22 runtime is a pinned implementation reference, never an edit target.
Only owned Permit facts are written. Native components retain gameplay ownership.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'prealpha/sidejobs_s22/runtime_v2/SideJobsS22.template.reds'
STATE = {'Inactive': 1, 'Active': 2, 'Succeeded': 3, 'Failed': 4}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def normalize(paths):
    whitelist = {j['id'] for j in load(ROOT / 'research/sidejobs_s21_failed/inventory_02.json')['jobs']}
    rows = []
    for path in paths:
        source = load(path)
        specs = source if isinstance(source, list) else source.get('contracts', source.get('owners', [source]))
        for spec in specs:
            assert spec['id'] in whitelist, spec['id']
            assert re.fullmatch(r'PTFRS25_[A-Z0-9_]+', spec['tag']), spec['tag']
            journals = []
            for j in spec.get('journals', spec.get('journal_guards', [])):
                states = [STATE.get(v, v) for v in j.get('states', j.get('allowed_states', []))]
                assert 1 <= len(states) <= 2 and set(states) <= {1, 2, 3, 4}
                journals.append({'path': j['path'], 'class': j['class'], 'states': states})
            assert journals and journals[0]['class'] == 'gameJournalQuest'
            assert set(journals[0]['states']) == {1}, 'Active/completed root must be protected'
            assert len({j['path'] for j in journals}) == len(journals)
            assert all(j['states'] == [1] for j in journals if j['class'] == 'gameJournalQuest'), 'Fresh roots only'
            equal = spec.get('facts_equal', spec.get('fact_equal', {}))
            ranges = spec.get('fact_ranges', {})
            assert not (set(equal) & set(ranges))
            facts = []
            for name, value in equal.items():
                assert isinstance(value, int) and not isinstance(value, bool)
                facts.append({'name': name, 'min': value, 'max': value})
            for name, bounds in ranges.items():
                assert set(bounds) == {'min', 'max'}
                assert all(isinstance(v, int) and not isinstance(v, bool) for v in bounds.values())
                assert -2147483646 <= bounds['min'] <= bounds['max'] <= 2147483647
                facts.append({'name': name, **bounds})
            assert all(not f['name'].endswith('_Permit') for f in facts), 'Circular permit'
            assert all(not f['name'].startswith('PTFRS25_PHONE_') for f in facts), 'Circular service gate'
            titles = {j['id']: j['title'] for j in load(ROOT / 'research/sidejobs_s21_failed/inventory_02.json')['jobs']}
            rows.append({'id': spec['id'], 'title': spec.get('title', titles[spec['id']]), 'tag': spec['tag'],
                         'journals': journals, 'facts': facts,
                         'source': path.relative_to(ROOT).as_posix(), 'source_sha256': sha(path)})
    assert rows and len({r['tag'] for r in rows}) == len(rows), 'Duplicate owner'
    return rows


def q(value):
    return json.dumps(value, ensure_ascii=False)


def arrays(row):
    return {'Paths': [j['path'] for j in row['journals']],
            'Classes': [j['class'] for j in row['journals']],
            'StatesA': [j['states'][0] for j in row['journals']],
            'StatesB': [j['states'][-1] for j in row['journals']],
            'FactNames': [f['name'] for f in row['facts']],
            'FactMin': [f['min'] for f in row['facts']],
            'FactMax': [f['max'] for f in row['facts']]}


def data_source(rows):
    text = 'public abstract class SideJobDataS25 {\n'
    text += f'  public static func Count() -> Int32 {{ return {len(rows)}; }}\n'
    for name, key in [('ID', 'id'), ('Title', 'title'), ('Tag', 'tag')]:
        text += f'  public static func {name}(i: Int32) -> String {{\n'
        for i, row in enumerate(rows):
            text += f'    if i == {i} {{ return {q(row[key])}; }}\n'
        text += '    return "";\n  }\n'
    text += '  public static func Index(id: String) -> Int32 {\n'
    for i, row in enumerate(rows):
        text += f'    if Equals(id, {q(row["id"])}) || Equals(id, {q(row["tag"])}) {{ return {i}; }}\n'
    text += '    return -1;\n  }\n'
    for name in arrays(rows[0]):
        typ = 'String' if name in ['Paths', 'Classes', 'FactNames'] else 'Int32'
        text += f'  public static func {name}(i: Int32) -> array<{typ}> {{\n'
        for i in range(len(rows)):
            text += f'    if i == {i} {{ return SideJobDataS25.{name}{i}(); }}\n'
        text += f'    let empty: array<{typ}>; return empty;\n  }}\n'
        for i, row in enumerate(rows):
            text += f'  public static func {name}{i}() -> array<{typ}> {{ return {q(arrays(row)[name])}; }}\n'
    return text + '}\n'


def template():
    text = BASE.read_text(encoding='utf-8').replace('S22', 'S25')
    changes = {
        'let wanted = SideJobDataS25.FactValues(i);':
        'let minimum = SideJobDataS25.FactMin(i); let maximum = SideJobDataS25.FactMax(i);',
        'ArraySize(names) != ArraySize(wanted)':
        'ArraySize(names) != ArraySize(minimum) || ArraySize(names) != ArraySize(maximum)',
        'actual != wanted[k]': 'actual < minimum[k] || actual > maximum[k]',
        'ToString(wanted[k])': 'ToString(minimum[k]) + ".." + ToString(maximum[k])',
        'Current Failed/Inactive policy; progress retained; not certified pre-ending history.':
        'Unstarted whitelist entries only; previous restorations preserved; not certified pre-ending history.',
        'Native progress matches the bounded resume seam.':
        'Native state matches the bounded unstarted entry.',
        'boundedAdapters=': 'freshAdapters=',
        '      if Equals(id, "mq306_dumpster") { return "No Easy Way Out: unsupported progress seam; native stage and item/choice/reward history remain unchanged. No generic restart applied."; }\n': '',
    }
    for before, after in changes.items():
        assert text.count(before) == 1, before
        text = text.replace(before, after)
    return text


def generate(paths, output):
    if output.exists():
        raise ValueError('Immutable output exists; use new revision')
    rows = normalize(paths)
    output.mkdir(parents=True)
    source = template().replace('// GENERATED_DATA', data_source(rows))
    target = output / 'SideJobsS25.reds'
    target.write_text(source, encoding='utf-8')
    pins = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths + [BASE, Path(__file__), ROOT / 'research/sidejobs_s21_failed/inventory_02.json']}
    manifest = {'status': 'GENERATED_NOT_COMPILED_OR_INSTALLED', 'source_pins': pins,
                'rows': rows, 'files': {'SideJobsS25.reds': sha(target)},
                'policy': 'Fresh whitelisted entry only; keep prior restored progress. No pre-ending certification inferred.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return {'output': str(output), 'adapters': len(rows), 'sha256': sha(target)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('contracts', type=Path, nargs='+')
    args = parser.parse_args()
    print(json.dumps(generate([p.resolve() for p in args.contracts], args.out.resolve())))



