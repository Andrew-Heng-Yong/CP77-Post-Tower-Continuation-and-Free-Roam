"""Verify cooked PE1 predicates, protected source scope and full payload delta."""
from pathlib import Path
from collections import Counter, defaultdict
from itertools import product
import copy
import json
import re
import sys
from prepare import HERE, WS, BASE, OUT, ARCHIVE, HISTORY, ACTIVITY, read, sha, write, class_span
from inventory import function_bodies, script_tables
sys.path.insert(0, str(WS/'tools/parity_audit'))
from model import Resource, compare_graph
from trace_prefixes import Models


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def normal(path):
    model = Resource(read(path)).normalize()
    assert not model['errors'], model['errors']
    return model


def atom(condition):
    """Finite-domain interpretation of the actual normalized guard leaves."""
    kind = condition['$type']
    t = condition['type']
    if kind == 'questFactsDBCondition':
        assert t['$type'] == 'questVarComparison_ConditionType'
        op, rhs = t['comparisonType'], t['value']
        def test(value):
            return {'Equal': value == rhs, 'Greater': value > rhs,
                    'GreaterOrEqual': value >= rhs, 'Less': value < rhs,
                    'LessOrEqual': value <= rhs}[op]
        return ('fact', t['factName']), test
    if kind == 'questJournalCondition':
        assert t['$type'] == 'questJournalEntryState_ConditionType' and t['inverted'] == 0
        wanted = {'Inactive': 1, 'Active': 2, 'Succeeded': 3, 'Failed': 4}[t['state']]
        return ('journal', t['path']['realPath']), lambda value: value == wanted
    assert kind == 'questVehicleCondition' and t['$type'] == 'questVehicleAvailable_ConditionType'
    return ('vehicle', t['vehicleName']), bool


def evaluate(condition, assignment):
    if condition['$type'] == 'questLogicalCondition':
        values = [evaluate(c, assignment) for c in condition['conditions']]
        if condition['operation'] == 'AND':
            return all(values)
        assert condition['operation'] == 'OR'
        return any(values)
    key, test = atom(condition)
    return test(assignment[key])


def solutions(condition, domains):
    """Find consistent witnesses; OR branches retain their original semantics."""
    if condition['$type'] != 'questLogicalCondition':
        key, test = atom(condition)
        values = {v for v in domains[key] if test(v)}
        if values:
            yield domains | {key: values}
        return
    if condition['operation'] == 'OR':
        for child in condition['conditions']:
            yield from solutions(child, domains)
        return
    assert condition['operation'] == 'AND'
    def sequence(children, state):
        if not children:
            yield state
            return
        for candidate in solutions(children[0], state):
            yield from sequence(children[1:], candidate)
    yield from sequence(condition['conditions'], domains)


def expected_payload(value, flags):
    # This operates on a normalized payload, independently of handle cloning/cooking.
    if isinstance(value, list):
        return [expected_payload(child, flags) for child in value]
    if not isinstance(value, dict):
        return value
    if value.get('$type') == 'questFactsDBCondition' and value['type'].get('factName') in flags:
        t = value['type']
        assert t['comparisonType'] == 'Equal' and t['value'] == 0
        one = copy.deepcopy(value)
        one['type']['value'] = 1
        return {'$type': 'questLogicalCondition', 'operation': 'OR', 'conditions': [copy.deepcopy(value), one]}
    return {k: expected_payload(v, flags) for k, v in value.items()}


def classes(text):
    return re.findall(r'(?m)^(?:public |private )?(?:abstract )?class\s+(\w+)', text)


def mask_body(text, name, body):
    # Repeated data-array literals can occur in different methods. Anchor the
    # masking to this method's declaration rather than replacing a shared literal.
    match = re.search(r'\bfunc\s+'+re.escape(name)+r'\s*\([^\n]*?\)[^{\n]*\{', text)
    assert match and text[match.end():match.end()+len(body)] == body, name
    return text[:match.end()]+'<PE1_VERIFIED_FUNCTION_BODY>'+text[match.end()+len(body):]


def main():
    output = HERE/'verification.json'
    assert not output.exists()
    plan_path = HERE/'input_02/plan.json'
    plan = read(plan_path)
    cooked_path = HERE/'readback_01/manifest.json'
    cooked = read(cooked_path)
    assert cooked['status'] == 'PE1_PRIVATE_ENTRIES_COOKED_AND_READ_BACK'
    assert cooked['plan_sha256'] == sha(plan_path)
    check_count = 0
    groups = Counter()
    def check(group, label, result):
        nonlocal check_count
        assert result, (group, label)
        check_count += 1
        groups[group] += 1
    models = Models()
    readbacks = {r['depot']: r for r in cooked['resources']}
    all_diffs = []
    witnesses = []
    for row in plan['resources']:
        rb = readbacks[row['depot']]
        check('pins', row['depot'], sha(row['source_json']) == row['source_json_sha256'] and sha(row['edited_json']) == row['edited_json_sha256'] and sha(rb['raw']) == rb['sha256'] and sha(rb['json']) == rb['json_sha256'])
        old, new = normal(row['source_json']), normal(rb['json'])
        check('source', row['depot']+' exact pinned current model', not compare_graph(models.get(row['depot']), old))
        diffs = compare_graph(old, new)
        allowed = {('NODE_PAYLOAD_CHANGED', g['graph'], g['node']) for g in row['guards']}
        check('structure', row['depot'], len(diffs) == len(allowed) and {(d['kind'], d['graph'], d.get('node')) for d in diffs} == allowed)
        all_diffs.extend(dict(d, depot=row['depot']) for d in diffs)
        for guard in row['guards']:
            flags = set(guard['flags'])
            a = old['graphs'][guard['graph']]['nodes'][guard['node']]['payload']
            b = new['graphs'][guard['graph']]['nodes'][guard['node']]['payload']
            tag = row['id']+'/'+guard['node']
            check('structure', tag+' independent exact payload', b == expected_payload(a, flags))
            before, after = a['condition'], b['condition']
            domains = {}
            for leaf in walk(before):
                if leaf.get('$type') not in ('questFactsDBCondition', 'questJournalCondition', 'questVehicleCondition'):
                    continue
                key, _ = atom(leaf)
                if key[0] == 'fact':
                    rhs = leaf['type']['value']
                    domains.setdefault(key, {-2, -1, 0, 1, 2, 3, 4}).update([rhs-1, rhs, rhs+1])
                else:
                    domains[key] = {1, 2, 3, 4} if key[0] == 'journal' else {False, True}
            zero_domains = domains | {('fact', f): {0} for f in flags}
            solution = next(solutions(before, zero_domains), None)
            check('witness', tag+' original guard satisfiable', solution is not None)
            witness = {key: min(values, key=lambda v: (abs(v), v)) for key, values in solution.items()}
            check('witness', tag+' actual original witness', evaluate(before, witness))
            for values in product([0, 1], repeat=len(flags)):
                assignment = witness | {('fact', f): v for f, v in zip(sorted(flags), values)}
                check('prepared', tag+' Boolean combinations '+str(values), evaluate(after, assignment))
                check('prepared', tag+' old guard rejects prepared '+str(values), evaluate(before, assignment) == all(v == 0 for v in values))
            prepared = witness | {('fact', f): 1 for f in flags}
            for flag in flags:
                for value in [-2, -1, 2, 3]:
                    check('invalid', tag+'/'+flag+'='+str(value), not evaluate(after, prepared | {('fact', flag): value}))
            # Vary every protected fact, journal and vehicle condition across its
            # boundary values. The old guard is the oracle after substituting
            # only the selected Boolean setup fields back to their former zero.
            for key, values in domains.items():
                if key in {('fact', f) for f in flags}:
                    continue
                for value in values:
                    candidate = prepared | {key: value}
                    oracle = candidate | {('fact', f): 0 for f in flags}
                    check('protected', tag+'/'+str(key)+'='+str(value), evaluate(after, candidate) == evaluate(before, oracle))
            witnesses.append({'id': row['id'], 'node': guard['node'], 'facts': {k[1]: v for k, v in witness.items() if k[0] == 'fact'}, 'journals': {k[1]: v for k, v in witness.items() if k[0] == 'journal'}, 'vehicle_availability': {k[1]: v for k, v in witness.items() if k[0] == 'vehicle'}})
    expected_functions = defaultdict(set)
    for rule in plan['rules']:
        if rule['family'] == 'SIDE':
            expected_functions[(rule['script'], rule['class'])].add('FactMax'+str(rule['index']))
            expected_functions[(rule['script'], rule['class'].replace('SideJobData', 'SideJobs'))].add('Read')
    expected_functions[(ACTIVITY, 'NativeGigsU9')] = {'EntrySafe'}
    expected_functions[(HISTORY, 'SnapshotStateHS1')] = {'FreshU9'}
    script_changes = []
    for row in plan['scripts']:
        rel = row['path']
        old_bytes, new_bytes = (BASE/'package'/rel).read_bytes(), (OUT/'package'/rel).read_bytes()
        check('scripts', rel+' exact hashes', sha(BASE/'package'/rel) == row['before'] and sha(OUT/'package'/rel) == row['after'])
        old, new = old_bytes.decode('utf-8'), new_bytes.decode('utf-8')
        if rel == HISTORY:
            marker = '// PE1: source-reviewed Boolean setup receipts.'
            check('scripts', 'one nonpersistent helper', new.count(marker) == 1)
            new = new.split(marker, 1)[0].rstrip() + '\r\n' if old.endswith('\r\n') else new.split(marker, 1)[0].rstrip() + '\n'
        check('scripts', rel+' persistent fields unchanged', re.findall(r'(?m)^.*persistent.*$', old) == re.findall(r'(?m)^.*persistent.*$', new))
        check('scripts', rel+' existing classes retained', classes(old) == classes(new))
        for cls in classes(old):
            start, end = class_span(old, cls); a = old[start:end]
            start, end = class_span(new, cls); b = new[start:end]
            fa, fb = function_bodies(a), function_bodies(b)
            check('scripts', cls+' function inventory', set(fa) == set(fb))
            changed = {f for f in fa if fa[f] != fb[f]}
            check('scripts', cls+' exact function scope', changed == expected_functions[(rel, cls)])
            for name in changed:
                a = mask_body(a, name, fa[name])
                b = mask_body(b, name, fb[name])
            check('scripts', cls+' declarations and untouched bodies', a.rstrip() == b.rstrip())
            if changed:
                script_changes.append({'path': rel, 'class': cls, 'functions': sorted(changed)})
        if 'SideJobs' in Path(rel).name:
            original_tables = {t['class']: t for t in script_tables(BASE/'package'/rel)}
            actual_tables = {t['class']: t for t in script_tables(OUT/'package'/rel)}
            for cls, table in original_tables.items():
                expected = copy.deepcopy(table)
                for rule in plan['rules']:
                    if rule['family'] != 'SIDE' or rule['class'] != cls:
                        continue
                    target = next(r for r in expected['rows'] if r['index'] == rule['index'])
                    for flag in rule['flags']:
                        at = target['FactNames'].index(flag)
                        check('tables', rule['id']+'/'+flag+' starts at zero', target['FactMin'][at] == target['FactMax'][at] == 0)
                        target['FactMax'][at] = 1
                # File-level source pins belong to the containing script, not table semantics.
                actual = copy.deepcopy(actual_tables[cls])
                for data in [expected, actual]:
                    for key in ['path', 'script', 'sha256', 'file', 'file_sha256']:
                        data.pop(key, None)
                check('tables', cls+' only selected maxima changed', actual == expected)
    history = (OUT/'package'/HISTORY).read_text(encoding='utf-8-sig')
    a, b = class_span(history, 'PreparedEntryPolicyPE1'); helper = history[a:b]
    check('helper', 'nonpersistent and read only', not re.search(r'\b(?:let|persistent)\b', helper.split('public static func Facts', 1)[0]) and not re.search(r'\b(?:SetFact\w*|SetEntryState|SetNodeState|Request\w*|Reactivate|ResetKillCount)\s*\(', helper))
    for method, field in [('Facts', 'flags'), ('BaselineIDs', 'baseline_ids')]:
        body = function_bodies(helper)[method]
        mapping = {json.loads(m.group(1)): json.loads(m.group(2)) for m in re.finditer(r'if Equals\(id,("[^"]+")\) \{ return (\[[^\n]*?\]); \}', body)}
        check('helper', method+' exact per-ID mapping', mapping == {r['id']: r[field] for r in plan['rules']})
    check('helper', 'no shared-flag catalogue spillover', 'sq_q001_wilson' not in helper and 'mq011_wilson' in helper)
    baseline = read(plan['baseline_package'])
    members = {str(p.relative_to(OUT/'archive_source')).replace('/', '\\'): sha(p) for p in (OUT/'archive_source').rglob('*') if p.is_file()}
    check('inventory', 'same 1581 depots', len(members) == 1581 and set(members) == set(baseline['source_resources']))
    changed_depots = sorted(d for d, h in members.items() if h != baseline['source_resources'][d])
    check('inventory', 'only twelve entry resources changed', changed_depots == sorted(r['depot'] for r in plan['resources']))
    files = {p.relative_to(OUT/'package').as_posix(): sha(p) for p in (OUT/'package').rglob('*') if p.is_file()}
    originals = {r['path']: r['sha256'] for r in baseline['files']}
    check('inventory', 'fifty staged paths, archive pending', set(files) == set(originals)-{ARCHIVE})
    check('inventory', 'only six scripts changed', sorted(r for r, h in files.items() if h != originals[r]) == sorted(r['path'] for r in plan['scripts']))
    xl = 'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
    check('namespaces', 'XL bytes and phase registrations retained', files[xl] == originals[xl])
    compile_path = HERE/'compile_01/result.json'
    compilation = read(compile_path)
    check('compile', 'all148 registered sources passed', compilation['status'] == 'PASS_CURRENT_REGISTERED_SOURCE_COMPILE' and compilation['source_count'] == 148 and len(compilation['input_pins']) == 151 and compilation['installed_inputs_unchanged'])
    check('compile', 'all six exact overlays', {r['path']: r['sha256'] for r in compilation['overlays']} == {r['path']: r['after'] for r in plan['scripts']})
    providers = read(plan['providers'])
    check('providers', 'all current resource/provider checks passed', sha(plan['providers']) == plan['providers_sha256'] and providers['status'] == 'PASS_CURRENT_PHASE_AND_NATIVE_PREFIX_PROVIDERS' and not providers['issues'])
    write(output, {'status': 'PASS_PE1_COOKED_GUARDS_AND_COMPLETE_DELTA', 'plan_sha256': sha(plan_path), 'cooked_sha256': sha(cooked_path), 'compile_result_sha256': sha(compile_path), 'checks': check_count, 'check_groups': dict(groups), 'changes': all_diffs, 'script_changes': script_changes, 'guard_witnesses': witnesses, 'changed_depots': changed_depots, 'archive_members': len(members), 'retained_archive_members': len(members)-len(changed_depots), 'new_depots': 0, 'new_ArchiveXL_phase_ids': 0, 'namespace_evidence': 'Same depots, node IDs, graph edges and byte-identical XL; pinned current providers.', 'limits': 'Cooked-predicate boundary evaluation, exact source and byte delta, and offline compile. No engine scheduling, saved-owner execution or gameplay pass.', 'game_writes': 0, 'save_writes': 0})
    print(json.dumps({'status': 'PASS', 'checks': check_count, 'guard_nodes': len(all_diffs), 'changed_resources': len(changed_depots), 'changed_scripts': len(plan['scripts'])}))


if __name__ == '__main__':
    main()
