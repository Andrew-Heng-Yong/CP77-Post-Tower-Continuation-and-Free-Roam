"""Independent normalized graph/data delta and admission regression verification."""
import copy, hashlib, itertools, json, re, sys
from pathlib import Path
from prepare import ROOT, HERE, read, sha, graphs, walk, array, lib


def evaluate(c, facts, journals, external=True):
    if c['$type']=='questLogicalCondition':
        values=[evaluate(x,facts,journals,external) for x in c['conditions']]
        return all(values) if c['operation']=='AND' else any(values)
    # Structural equality proves these untouched world/inventory guards are the
    # same engine predicates. Model both pass/fail, not fabricated live state.
    if c['$type'] in ('questTriggerCondition','questObjectCondition'): return external
    return lib.evaluate(c,facts,journals)


def equal_fact(name):
    return {'$type': 'questFactsDBCondition', 'type': {'$type': 'questVarComparison_ConditionType',
            'comparisonType': 'Equal', 'factName': name, 'value': 0}}


def inactive_root(path):
    return {'$type': 'questJournalCondition', 'type': {'$type': 'questJournalEntryState_ConditionType',
            'inverted': 0, 'path': {'$type': 'gameJournalPath', 'className': {'$type': 'CName', '$storage': 'string',
            '$value': 'gameJournalQuest'}, 'editorPath': '', 'fileEntryIndex': 2, 'realPath': path}, 'state': 'Inactive'}}


def expected_condition(old, delta):
    result = copy.deepcopy(old); changed = []
    for obj in walk(result):
        if obj.get('$type') == 'questJournalEntryState_ConditionType' and obj['path']['className']['$value'] == 'gameJournalQuest' and obj['state'] == 'Failed':
            assert obj['path']['realPath'] in delta['narrowed_roots']
            obj['state'] = 'Inactive'; changed.append(obj['path']['realPath'])
    assert sorted(changed) == sorted(delta['narrowed_roots'])
    result['conditions'].extend(equal_fact(name) for name in delta['exclusion_facts'])
    if 'added_root' in delta: result['conditions'].append(inactive_root(delta['added_root']))
    return result


def seed(condition):
    facts = {}; journals = {}; constraints = {}
    for obj in walk(condition):
        if obj.get('$type') == 'questVarComparison_ConditionType':
            constraints.setdefault(obj['factName'], []).append((obj['comparisonType'], obj['value']))
        if obj.get('$type') == 'questVarVsVarComparison_ConditionType':
            facts.setdefault(obj['factName1'], 0); facts.setdefault(obj['factName2'], 0)
        if obj.get('$type') == 'questJournalEntryState_ConditionType':
            path = obj['path']['realPath']
            journals.setdefault(path, obj['state'])
            if obj['state'] == 'Inactive': journals[path] = 'Inactive'
    for name, checks in constraints.items():
        candidates = sorted({0, 1} | {value + offset for _, value in checks for offset in (-1,0,1)})
        candidates = [v for v in candidates if all({'Equal':v==want, 'Greater':v>want, 'GreaterOrEqual':v>=want, 'Less':v<want, 'LessOrEqual':v<=want}[op] for op,want in checks)]
        assert candidates, (name, checks)
        facts[name] = candidates[0]
    assert evaluate(condition, facts, journals), 'Seed must be a true native positive witness'
    return facts, journals


def methods(text):
    """Extract method bodies with balanced braces, independently from build regex."""
    result = {}
    for match in re.finditer(r'\bfunc\s+(\w+)\([^\n]*?\)\s*->[^\n{]+\{', text):
        start = match.start(); cursor = match.end(); depth = 1
        while depth:
            if text[cursor] == '{': depth += 1
            elif text[cursor] == '}': depth -= 1
            cursor += 1
        assert match[1] not in result, match[1]
        result[match[1]] = text[start:cursor]
    return result


def verify(build):
    manifest = read(build/'build.json'); plan = read(ROOT/manifest['policy_plan'])
    assert manifest['native_changes'] == plan['resources']
    assert manifest['mod_overrides'] == [row['depot'] for row in plan['resources']]
    assert manifest['boots'] == [] and manifest['native_copies'] == []
    for name,digest in manifest['source_pins'].items(): assert sha(ROOT/name)==digest,name
    native_checks = cases = method_checks = 0
    for row in plan['resources']:
        name = row['depot'].replace('\\','_')+'.json'
        assert sha(ROOT/row['source']) == row['source_sha256']
        assert sha(build/'source'/row['depot']) == manifest['resources'][row['depot']]
        old = graphs(build/'original_readback'/name); new = graphs(build/'readback'/name)
        if row['json']: assert old == graphs(ROOT/row['json']), ('source readback drift', row['depot'])
        assert set(old)==set(new)
        changes = {(d['graph'],d['node']):d for d in row['changes']}
        for path, graph in old.items():
            expected = copy.deepcopy(graph)
            for node in expected['nodes']:
                delta = changes.get((path,node['id']))
                if delta:
                    original = copy.deepcopy(node['condition'])
                    node['condition'] = expected_condition(original, delta)
                    condition = node['condition']; facts,journals = seed(condition)
                    assert evaluate(original,facts,journals)
                    cases += 2
                    # Changes apply only to unused owners, and never remove original gates.
                    unused = [o['factName'] for o in walk(condition) if o.get('$type')=='questVarComparison_ConditionType' and o['comparisonType']=='Equal' and o['value']==0 and (o['factName'].endswith('_Issued') or o['factName']=='PTFRS1_Started') and any(o['factName'].startswith(t+'_') for t in delta['unused_tags'])]
                    assert unused, (row['depot'],node['id'])
                    for key in unused:
                        assert not evaluate(condition,facts|{key:1},journals); cases += 1
                    changed_paths = delta['narrowed_roots'] + ([delta['added_root']] if 'added_root' in delta else [])
                    for key in changed_paths:
                        for state in ('Inactive','Active','Succeeded','Failed','Unknown',None):
                            assert evaluate(condition,facts,journals|{key:state}) == (state=='Inactive'), (row['depot'],key,state)
                            cases += 1
                    for key in delta['exclusion_facts']:
                        for value in (-1,0,1,2):
                            assert evaluate(condition,facts|{key:value},journals) == (value==0); cases += 1
                    # Existing guard regressions. Tightening never admits anything formerly blocked.
                    for key,value in facts.items():
                        for wrong in (-1,0,1,2,7,value+1):
                            f=facts|{key:wrong}; accepted=evaluate(condition,f,journals)
                            assert not accepted or evaluate(original,f,journals)
                            cases += 1
                    # All journal conditions must remain meaningful; completed sibling states persist.
                    for key in journals:
                        for state in ('Inactive','Active','Succeeded','Failed',None):
                            j=journals|{key:state}
                            assert not evaluate(condition,facts,j) or evaluate(original,facts,j)
                            cases += 1
                    assert evaluate(condition,facts,journals,False)==evaluate(original,facts,journals,False);cases+=1
                native_checks += 1
            # Node IDs, sockets, resource refs, gameplay payloads, and graph edges exact.
            assert expected == new[path], ('unplanned graph delta',row['depot'],path)
            native_checks += 1
    assert len(manifest['script_replacements']) == 2
    for spec,replacement in zip(plan['scripts'],manifest['script_replacements']):
        assert replacement['source'] == spec['source'] and replacement['relative']==spec['relative']
        assert replacement['source_sha256']==sha(ROOT/spec['source'])
        assert replacement['sha256']==sha(ROOT/replacement['path'])
        old=(ROOT/spec['source']).read_text(encoding='utf-8-sig'); new=(ROOT/replacement['path']).read_text(encoding='utf-8-sig')
        om=methods(old); nm=methods(new); assert om.keys()==nm.keys()
        allowed={f'{prefix}{r["index"]}' for r in spec['rows'] if r['narrowed'] for prefix in ('StatesA','StatesB')}
        allowed|={f'{prefix}{r["index"]}' for r in spec['rows'] if r['exclusion_fact'] for prefix in (('FactNames','FactValues') if spec['version']=='S22' else ('FactNames','FactMin','FactMax'))}
        if 'Current Failed/Inactive policy' in old: allowed.add('Status')
        for name,body in om.items():
            if name not in allowed: assert body==nm[name],('unexpected method delta',name)
            method_checks += 1
        # Non-method module/class/member declarations remain exact too.
        old_rest=old; new_rest=new
        for name in allowed: old_rest=old_rest.replace(om[name],f'<{name}>');new_rest=new_rest.replace(nm[name],f'<{name}>')
        assert old_rest==new_rest
        if 'Status' in allowed: assert nm['Status']==om['Status'].replace('Current Failed/Inactive policy','New activation Inactive-only; existing issued progress preserved')
        for row in spec['rows']:
            i=row['index']; paths,_=array(old,f'Paths{i}'); classes,_=array(old,f'Classes{i}')
            beforeA,_=array(old,f'StatesA{i}');beforeB,_=array(old,f'StatesB{i}')
            afterA,_=array(new,f'StatesA{i}');afterB,_=array(new,f'StatesB{i}')
            changed={r['index'] for r in row['narrowed']}
            for k,(path,cls,a,b) in enumerate(zip(paths,classes,beforeA,beforeB)):
                expected=(1,1) if k in changed else (a,b)
                assert (afterA[k],afterB[k])==expected
                if cls=='gameJournalQuest': assert 4 not in expected and (1 in expected or expected==(3,3)), (path,expected)
                for state in (-1,0,1,2,3,4,5):
                    actual=state in (afterA[k],afterB[k]); assert actual==(state in expected)
                    assert not actual or state in (a,b)
                    cases+=1
            prefixes=('FactNames','FactValues') if spec['version']=='S22' else ('FactNames','FactMin','FactMax')
            for prefix in prefixes:
                original,_=array(old,f'{prefix}{i}'); actual,_=array(new,f'{prefix}{i}')
                suffix=[row['exclusion_fact'] if prefix=='FactNames' else 0] if row['exclusion_fact'] else []
                assert actual==original+suffix
            # Existing durable-Issued skip paths exactly preserved, including Failed roots.
            for state,issued in itertools.product((-1,1,2,3,4),(0,1)):
                if issued==1:
                    assert 'if this.Own(i, "Issued") == 0 {' in nm['Poll']
                    assert 'this.Own(i, "Issued") != 0 { return; }' in nm['Permit']
                cases+=1
    # Previously Inactive-only controllers need no replacements; pin the audited sources.
    audited={
        'redscript/PTFR_SideJobPilotS1/SideJobPilotS1.reds':'if this.ReadJournalState(paths[i]) != 1',
        'prealpha/sidejobs_s22b/build/s22_03/SideJobsS2.reds':None,
        'prealpha/sidejobs_s24/build/s24_02/SideJobsS24.reds':None,
    }
    audit_pins={name:sha(ROOT/name) for name in audited}
    s1=(ROOT/next(iter(audited))).read_text(encoding='utf-8-sig')
    assert 'Inactive' in s1 and 'UntouchedStage' in s1 and 'PTFRS1_Started' in s1
    s2=(ROOT/'prealpha/sidejobs_s22b/build/s22_03/SideJobsS2.reds').read_text(encoding='utf-8-sig')
    s2methods=methods(s2[:s2.index('public class SideJobTickS2')])
    assert '!= 1' in s2methods['SampleFresh'] and 'Issued' in s2methods['CanPermit']
    s24=(ROOT/'prealpha/sidejobs_s24/build/s24_02/SideJobsS24.reds').read_text(encoding='utf-8-sig')
    for i in range(7):
        paths,_=array(s24,f'Paths{i}');classes,_=array(s24,f'Classes{i}');a,_=array(s24,f'StatesA{i}');b,_=array(s24,f'StatesB{i}')
        for path,cls,first,second in zip(paths,classes,a,b):
            if cls=='gameJournalQuest': assert first==second==1;cases+=1
    result={'status':'PASS_OFFLINE_NOT_LIVE','tester_sha256':sha(Path(__file__)), 'component_sha256':sha(build/'build.json'),
        'build_sha256':sha(build/'build.json'),'native_payload_checks':native_checks,'policy_cases':cases,
        'exact_method_checks':method_checks,'resources':len(manifest['resources']),'preflight_conditions':sum(len(r['changes']) for r in plan['resources']),
        'script_replacements':len(manifest['script_replacements']),'audited_unchanged_source_pins':audit_pins,
        'limitations':'Does not simulate REDengine saved-node rehydration or prove live gameplay. Full native payloads, graph identity, existing issued paths and all non-admission method bodies are unchanged.'}
    return result


if __name__=='__main__':
    build=Path(sys.argv[1]);result=verify(build)
    target=build/'tests.json';assert not target.exists(),'Immutable test receipt exists'
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
