"""Source-bound permission tests. Models do not claim native gameplay proof."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import generate

spec = importlib.util.spec_from_file_location('s22_model', ROOT / 'prealpha/sidejobs_s22/runtime_v2/test.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)


def observe(row, states=None, facts=None, available=True, settled=True):
    states = states if states is not None else [j['states'][0] for j in row['journals']]
    facts = facts if facts is not None else [f['min'] for f in row['facts']]
    valid = available and settled and len(states) == len(row['journals']) and len(facts) == len(row['facts'])
    valid = valid and all(s in j['states'] for s, j in zip(states, row['journals']))
    valid = valid and all(isinstance(v, int) and f['min'] <= v <= f['max'] for v, f in zip(facts, row['facts']))
    return {'states': list(states), 'facts': list(facts), 'valid': valid}


def verify(folder):
    output = folder / 'tests.json'
    assert not output.exists(), 'Immutable test receipt'
    m = generate.load(folder / 'manifest.json')
    for p, h in m['source_pins'].items():
        assert generate.sha(ROOT / p) == h, p
    rows = m['rows']
    source = (folder / 'SideJobsS24.reds').read_text(encoding='utf-8')
    assert source == generate.template().replace('// GENERATED_DATA', generate.data_source(rows))
    assert source.count('.SetFactStr(') == 1
    assert 'Tag(i) + "_Permit"' in prior.method(source, 'Permit')
    assert 'this.Own(i, "Issued") != 0' in prior.method(source, 'Permit')
    for forbidden in ['ChangeEntryState', 'GiveReward', 'GiveItem', 'ModLog(', 'LogChannel', 'persistent let']:
        assert forbidden not in source, forbidden
    for token in ['ArraySize(names) != ArraySize(minimum)', 'ArraySize(names) != ArraySize(maximum)',
                  'actual < minimum[k] || actual > maximum[k]', 'sample.valid = false',
                  'EnumInt(jm.GetEntryState(entry)) : -1']:
        assert token in prior.method(source, 'Read'), token
    assert prior.method(source, 'Read').count('jm.HasAnyDelayedStateChanges()') == 2
    assert 'this.Same(this.previous[i], current) && this.Ready(i)' in prior.method(source, 'Poll')
    assert 'epoch != this.epoch' in prior.method(source, 'Poll')
    assert 'profile.PTFRPAComplete() && !profile.PTFRPAFaulted()' in prior.method(source, 'Common')
    assert 'BodyPolicy.Safe(player)' in prior.method(source, 'Safe')
    cases = arrays = 0
    for i, row in enumerate(rows):
        assert set(row['journals'][0]['states']) == {1}
        for name, values in generate.arrays(row).items():
            body = prior.method(source, name + str(i))
            actual = json.loads(body[body.index('return ') + 7:body.rindex(';')])
            assert actual == values
            arrays += 1
        baseline = observe(row)
        assert baseline['valid']; cases += 1
        for n, journal in enumerate(row['journals']):
            for state in [None, -1, 0, 1, 2, 3, 4, 5, 999]:
                states = baseline['states'].copy(); states[n] = state
                assert observe(row, states=states)['valid'] == (state in journal['states'])
                cases += 1
        for n, fact in enumerate(row['facts']):
            for value in [None, -2147483647, -1, 0, 1, 2, 999, fact['min'] - 1, fact['min'], fact['max'], fact['max'] + 1]:
                facts = baseline['facts'].copy(); facts[n] = value
                wanted = isinstance(value, int) and fact['min'] <= value <= fact['max']
                assert observe(row, facts=facts)['valid'] == wanted, (row['id'], fact, value)
                cases += 1
        for available, settled in [(False, True), (True, False), (False, False)]:
            assert not observe(row, available=available, settled=settled)['valid']; cases += 1
        assert not observe(row, states=[])['valid']; cases += 1
        if row['facts']:
            assert not observe(row, facts=[])['valid']; cases += 1
        p = prior.Protocol(); p.tick(baseline); assert p.permit == 0
        p.tick(baseline); assert p.permit == 1; cases += 2
        invalid = observe(row, states=[3] + baseline['states'][1:])
        p.tick(invalid); assert p.permit == 0; cases += 1
        for guard in ['common', 'safe', 'final_safe']:
            p = prior.Protocol(); p.tick(baseline); p.tick(baseline)
            p.tick(baseline, **{guard: False}); assert p.permit == 0; cases += 1
        for field, value in [('ready', 0), ('finished', 1), ('fault', 1), ('warmup', 3)]:
            p = prior.Protocol(); p.tick(baseline); p.tick(baseline)
            setattr(p, field, value); p.tick(baseline)
            assert p.permit == 0 and p.previous is None; cases += 1
        p = prior.Protocol(); p.tick(baseline); p.tick(baseline); p.issued = 1
        old = copy.deepcopy(p.writes); p.tick(invalid); p.restore()
        assert p.issued == 1 and old == p.writes; cases += 1
        p = prior.Protocol(); p.tick(baseline); p.tick(baseline); p.restore()
        assert p.permit == 0 and p.previous is None and p.warmup == 3; cases += 1
        p.tick(baseline, epoch=p.epoch-1); assert p.warmup == 3; cases += 1
        for tick in range(1, 5):
            p.tick(baseline); assert p.permit == int(tick == 4); cases += 1
    report = {'status': 'PASS_OFFLINE_NOT_LIVE', 'manifest_sha256': generate.sha(folder / 'manifest.json'),
              'test_sha256': generate.sha(Path(__file__)), 'policy_cases': cases, 'arrays': arrays,
              'adapters': len(rows), 'owned_permit_only': True,
              'existing_restoration_owners_not_called_or_changed': True, 'source_pins': m['source_pins']}
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return {k: v for k, v in report.items() if k != 'source_pins'}


if __name__ == '__main__':
    print(json.dumps(verify(Path(sys.argv[1]))))

