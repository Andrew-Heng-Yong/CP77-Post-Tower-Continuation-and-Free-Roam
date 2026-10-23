"""Plan bounded inactive-only admission deltas against immutable winning owners."""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('native', ROOT / 'prealpha/sidejobs_s22/delamain_v2/test.py')
lib = importlib.util.module_from_spec(spec); spec.loader.exec_module(lib)
read, sha, graphs = lib.read, lib.sha, lib.graphs


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values(): yield from walk(child)
    elif isinstance(value, list):
        for child in value: yield from walk(child)


def array(text, name):
    pattern = rf'(public static func {name}\(\) -> array<\w+> \{{ return )(\[[^\r\n]*\])(; \}})'
    hit = re.search(pattern, text)
    assert hit, name
    return json.loads(hit[2]), pattern


def scalar(text, name, index):
    body = re.search(rf'public static func {name}\(i: Int32\) -> String \{{(.*?)\n  \}}', text, re.S)[1]
    return re.search(rf'if i == {index} \{{ return "([^"]+)";', body)[1]


def main():
    output = HERE / 'plan02.json'
    assert not output.exists(), 'Use successor plan filename after review'
    pins = {}
    scripts = []
    roots = {}
    guards = {'PTFRS22_MQ025': 'PTFRS25_MQ025_FRESH_Issued',
              'PTFRS22_SQ025': 'PTFRS25_SQ025_FRESH_Issued',
              'PTFRS23_MQ026': 'PTFRS25_MQ026_FRESH_Issued'}
    for version, source in [('S22', 'prealpha/sidejobs_s22b/build/s22_03/SideJobsS22.reds'),
                            ('S23', 'prealpha/sidejobs_s23/build/s23_02/SideJobsS23.reds')]:
        text = (ROOT / source).read_text(encoding='utf-8-sig')
        count = int(re.search(r'func Count\(\) -> Int32 \{ return (\d+);', text)[1])
        rows = []
        for i in range(count):
            paths, _ = array(text, f'Paths{i}'); classes, _ = array(text, f'Classes{i}')
            first, _ = array(text, f'StatesA{i}'); second, _ = array(text, f'StatesB{i}')
            tag, job = scalar(text, 'Tag', i), scalar(text, 'ID', i)
            narrowed = []
            for k, (path, cls, a, b) in enumerate(zip(paths, classes, first, second)):
                if cls == 'gameJournalQuest' and 1 in (a, b):
                    roots[path] = True
                    if 4 in (a, b): narrowed.append({'index': k, 'path': path, 'before': [a, b], 'after': [1, 1]})
            rows.append({'index': i, 'id': job, 'tag': tag, 'narrowed': narrowed,
                         'exclusion_fact': guards.get(tag)})
        pins[source] = sha(ROOT / source)
        scripts.append({'version': version, 'source': source, 'relative': f'r6/scripts/TowerContinued_SideJobs_{version}/SideJobs{version}.reds', 'rows': rows})
    resources = []
    manifests = ['prealpha/sidejobs_s221/build/s221_01/build.json', 'prealpha/sidejobs_s23/build/s23_02/build.json']
    for rel in manifests:
        manifest = read(ROOT / rel); pins[rel] = sha(ROOT / rel); folder = (ROOT / rel).parent
        for depot, digest in manifest['resources'].items():
            if not depot.startswith(('towercontinued\\sidejobs_s22\\', 'towercontinued\\sidejobs_s23\\')): continue
            raw = folder / 'source' / depot
            jsonpath = folder / 'readback' / (depot.replace('\\', '_') + '.json')
            assert sha(raw) == digest
            changes = []
            for path, graph in graphs(jsonpath).items():
                for node in graph['nodes']:
                    if 'condition' not in node: continue
                    # Only unused-owner preflight is editable, never gameplay conditions.
                    facts = {o['factName']: o.get('value') for o in walk(node['condition']) if o.get('$type') == 'questVarComparison_ConditionType' and o.get('comparisonType') == 'Equal'}
                    unused = [k[:-7] for k, v in facts.items() if k.endswith('_Issued') and v == 0 and k.startswith(('PTFRS22_', 'PTFRS23_'))]
                    if not unused: continue
                    changed = []
                    for obj in walk(node['condition']):
                        if obj.get('$type') == 'questJournalEntryState_ConditionType' and obj.get('state') == 'Failed':
                            ref = obj['path']; cls = ref['className'].get('$value')
                            if cls == 'gameJournalQuest':
                                assert ref['realPath'] in roots, (depot, path, node['id'], ref)
                                changed.append(ref['realPath'])
                    additions = sorted({guards[tag] for tag in unused if tag in guards})
                    if changed or additions:
                        assert node['condition']['$type'] == 'questLogicalCondition' and node['condition']['operation'] == 'AND'
                        changes.append({'graph': path, 'node': node['id'], 'narrowed_roots': sorted(changed), 'exclusion_facts': additions, 'unused_tags': unused})
            if changes:
                rawrel, jsonrel = raw.relative_to(ROOT).as_posix(), jsonpath.relative_to(ROOT).as_posix()
                pins[rawrel], pins[jsonrel] = sha(raw), sha(jsonpath)
                resources.append({'depot': depot, 'source': rawrel, 'json': jsonrel, 'source_sha256': digest, 'changes': changes})
    assert resources
    all_native_roots = {p for r in resources for c in r['changes'] for p in c['narrowed_roots']}
    all_script_roots = {c['path'] for s in scripts for r in s['rows'] for c in r['narrowed']}
    assert all_native_roots == all_script_roots, (all_native_roots-all_script_roots, all_script_roots-all_native_roots)
    for s in scripts:
        for row in s['rows']:
            if row['exclusion_fact']:
                assert any(row['exclusion_fact'] in c['exclusion_facts'] for r in resources for c in r['changes']), row
    s1source = 'prealpha/build/20261013T021845834Z/source/towercontinued/side_job_pilot_s1/owner.questphase'
    pins[s1source] = sha(ROOT / s1source)
    resources.append({'depot': 'towercontinued\\side_job_pilot_s1\\owner.questphase', 'source': s1source,
                      'json': None, 'source_sha256': pins[s1source], 'changes': [{
                          'graph': 'root', 'node': 402, 'narrowed_roots': [], 'exclusion_facts': [],
                          'unused_tags': ['PTFRS1'], 'added_root': 'quests/minor_quest/mq005_alley'}]})
    result = {'status': 'PLANNED_INACTIVE_ONLY_POLICY_NOT_INSTALLED', 'scripts': scripts, 'resources': resources, 'source_pins': pins,
              'policy': 'Only NEW gameJournalQuest roots accepting Inactive/Failed are narrowed to Inactive. Completed child roots, all non-root state requirements, Issued owners, IDs, edges, gameplay and rewards remain unchanged.',
              'mod_overrides': [r['depot'] for r in resources], 'boots': [], 'new_owner_exclusions': guards}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'resources': len(resources), 'native_preflights': sum(len(r['changes']) for r in resources), 'script_rows': sum(bool(r['narrowed'] or r['exclusion_fact']) for s in scripts for r in s['rows']), 'narrowed_root_paths': len(all_script_roots), 'plan': str(output)}))


if __name__ == '__main__': main()
