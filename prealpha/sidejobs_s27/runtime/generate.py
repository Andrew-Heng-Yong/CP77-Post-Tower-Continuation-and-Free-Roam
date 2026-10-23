"""S27 fresh-family admission tables, with no quest reset or gameplay writes.

Original S22 protocol is a pinned source reference. S27 owns only its Permit
facts; family native adapters retain every gameplay/service/reward operation.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'prealpha/sidejobs_s22/runtime_v2/SideJobsS22.template.reds'
INVENTORY = ROOT / 'research/sidejobs_s21_failed/inventory_02.json'
STATE = {'Inactive': 1, 'Active': 2, 'Succeeded': 3, 'Failed': 4}
COMMON = {'PostTowerFreeRoamActive': 1, 'PTFRP0_DR13': 1, 'PTFRPA2_Finished': 1,
          'PTFRPA2_Fault': 0, 'q307_done': 1, 'q307_finished': 1, 'q307_2079': 1,
          'q307_main_game_killed': 1, 'q307_ep1_killed': 1, 'q307_active': 0,
          'q307_debug_reset': 0, 'q115_point_of_no_return': 0,
          'q305_johnny_scene_active': 0, 'PTFRU9_Support_Issued': 1, 'PTFRU9_Support_Fault': 0}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def normalize(paths):
    whitelist = {j['id']: j for j in load(INVENTORY)['jobs']}
    rows = []
    for path in paths:
        source = load(path)
        if isinstance(source, dict) and 'common_equal' in source:
            assert source['common_equal'] == COMMON, 'Native/runtime common guard mismatch'
        specs = source if isinstance(source, list) else source.get('contracts', source.get('owners', [source]))
        for spec in specs:
            ids = spec.get('ids', [spec['id']])
            assert ids and spec['id'] in ids and len(set(ids)) == len(ids)
            assert all(value in whitelist for value in ids), ids
            assert re.fullmatch(r'PTFRS27_[A-Z0-9_]+', spec['tag']), spec['tag']
            journals = []
            for journal in spec.get('journals', spec.get('journal_guards', [])):
                states = [STATE.get(v, v) for v in journal.get('states', journal.get('allowed_states', []))]
                assert 1 <= len(states) <= 2 and set(states) <= {1, 2, 3, 4}, states
                assert all(isinstance(v, int) and not isinstance(v, bool) for v in states)
                journals.append({'path': journal['path'], 'class': journal['class'], 'states': states})
            assert journals and journals[0]['class'] == 'gameJournalQuest'
            assert journals[0]['states'] == [1], 'New family begins only from actual Inactive root'
            assert all(j['states'] == [1] for j in journals if j['class'] == 'gameJournalQuest'), 'Completed/active roots protected'
            assert len({j['path'] for j in journals}) == len(journals)
            assert {j['path'] for j in journals if j['class'] == 'gameJournalQuest'} == {
                whitelist[value]['journal_path'] for value in ids
            }, 'Every admitted family root must have its exact whitelist journal guard'
            equal = spec.get('facts_equal', spec.get('fact_equal', {}))
            ranges = spec.get('fact_ranges', {})
            assert not (set(equal) & set(ranges)), 'Ambiguous fact predicate'
            facts = []
            for name, value in equal.items():
                assert isinstance(value, int) and not isinstance(value, bool)
                facts.append({'name': name, 'min': value, 'max': value})
            for name, bounds in ranges.items():
                assert set(bounds) == {'min', 'max'}
                assert all(isinstance(v, int) and not isinstance(v, bool) for v in bounds.values())
                assert -2147483646 <= bounds['min'] <= bounds['max'] <= 2147483647
                facts.append({'name': name, **bounds})
            assert len({f['name'] for f in facts}) == len(facts)
            assert all(not f['name'].endswith('_Permit') for f in facts), 'Circular permit'
            assert all(not f['name'].startswith('PTFRS27_PHONE_') for f in facts), 'Circular service gate'
            rows.append({'id': spec['id'], 'ids': ids, 'title': spec.get('title', whitelist[spec['id']]['title']),
                         'tag': spec['tag'], 'journals': journals, 'facts': facts,
                         'source': path.relative_to(ROOT).as_posix(), 'source_sha256': sha(path)})
    assert rows and len({r['tag'] for r in rows}) == len(rows), 'Duplicate owner'
    aliases = [value for row in rows for value in row['ids']]
    assert len(set(aliases)) == len(aliases), 'Family alias overlaps another owner'
    return rows


def q(value):
    return json.dumps(value, ensure_ascii=False)


def arrays(row):
    return {'Paths': [j['path'] for j in row['journals']], 'Classes': [j['class'] for j in row['journals']],
            'StatesA': [j['states'][0] for j in row['journals']], 'StatesB': [j['states'][-1] for j in row['journals']],
            'FactNames': [f['name'] for f in row['facts']], 'FactMin': [f['min'] for f in row['facts']],
            'FactMax': [f['max'] for f in row['facts']]}


def data_source(rows):
    text = 'public abstract class SideJobDataS27 {\n'
    text += f'  public static func Count() -> Int32 {{ return {len(rows)}; }}\n'
    for name, key in [('ID', 'id'), ('Title', 'title'), ('Tag', 'tag')]:
        text += f'  public static func {name}(i: Int32) -> String {{\n'
        for i, row in enumerate(rows):
            text += f'    if i == {i} {{ return {q(row[key])}; }}\n'
        text += '    return "";\n  }\n'
    text += '  public static func Index(id: String) -> Int32 {\n'
    for i, row in enumerate(rows):
        checks = ' || '.join(f'Equals(id, {q(value)})' for value in row['ids'] + [row['tag']])
        text += f'    if {checks} {{ return {i}; }}\n'
    text += '    return -1;\n  }\n'
    for name in arrays(rows[0]):
        typ = 'String' if name in ['Paths', 'Classes', 'FactNames'] else 'Int32'
        text += f'  public static func {name}(i: Int32) -> array<{typ}> {{\n'
        for i in range(len(rows)):
            text += f'    if i == {i} {{ return SideJobDataS27.{name}{i}(); }}\n'
        text += f'    let empty: array<{typ}>; return empty;\n  }}\n'
        for i, row in enumerate(rows):
            text += f'  public static func {name}{i}() -> array<{typ}> {{ return {q(arrays(row)[name])}; }}\n'
    return text + '}\n'


def template():
    text = BASE.read_text(encoding='utf-8').replace('S22', 'S27')
    changes = {
        'let wanted = SideJobDataS27.FactValues(i);': 'let minimum = SideJobDataS27.FactMin(i); let maximum = SideJobDataS27.FactMax(i);',
        'ArraySize(names) != ArraySize(wanted)': 'ArraySize(names) != ArraySize(minimum) || ArraySize(names) != ArraySize(maximum)',
        'actual != wanted[k]': 'actual < minimum[k] || actual > maximum[k]',
        'ToString(wanted[k])': 'ToString(minimum[k]) + ".." + ToString(maximum[k])',
        'Current Failed/Inactive policy; progress retained; not certified pre-ending history.':
        'Fresh family entries only; unfinished-job restart migration remains separate; not certified pre-ending history.',
        'Native progress matches the bounded resume seam.': 'Native state matches the bounded original beginning.',
        'boundedAdapters=': 'freshFamilies=',
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
    target = output / 'SideJobsS27.reds'
    target.write_text(template().replace('// GENERATED_DATA', data_source(rows)), encoding='utf-8')
    pins = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths + [BASE, Path(__file__), INVENTORY]}
    manifest = {'status': 'GENERATED_NOT_COMPILED_OR_INSTALLED', 'source_pins': pins, 'rows': rows,
                'files': {'SideJobsS27.reds': sha(target)},
                'policy': 'Only new bounded original beginnings. Completed roots protected. Existing restorations unchanged; no unfinished-job restart implementation.'}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return {'output': str(output), 'adapters': len(rows), 'sha256': sha(target)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('contracts', type=Path, nargs='+')
    args = parser.parse_args()
    print(json.dumps(generate([p.resolve() for p in args.contracts], args.out.resolve())))
