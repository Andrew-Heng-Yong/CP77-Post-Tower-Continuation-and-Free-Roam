"""S27 source/permission protocol tests, not native execution or gameplay proof."""
import copy
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import generate

MODEL = ROOT / 'prealpha/sidejobs_s22/runtime_v2/test.py'
spec = importlib.util.spec_from_file_location('s27_protocol_reference', MODEL)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)


def observe(row, states=None, facts=None, available=True, settled=True):
    states = states if states is not None else [j['states'][0] for j in row['journals']]
    facts = facts if facts is not None else [f['min'] for f in row['facts']]
    valid = available and settled and len(states) == len(row['journals']) and len(facts) == len(row['facts'])
    valid = valid and all(isinstance(s, int) and not isinstance(s, bool) and s in j['states'] for s, j in zip(states, row['journals']))
    valid = valid and all(isinstance(v, int) and not isinstance(v, bool) and f['min'] <= v <= f['max'] for v, f in zip(facts, row['facts']))
    return {'states': list(states), 'facts': list(facts), 'valid': valid}


def verify(folder):
    output = folder / 'tests.json'
    assert not output.exists(), 'Immutable test receipt'
    manifest = generate.load(folder / 'manifest.json')
    for path, digest in manifest['source_pins'].items():
        assert generate.sha(ROOT / path) == digest, path
    paths = list(dict.fromkeys(ROOT / row['source'] for row in manifest['rows']))
    rows = generate.normalize(paths)
    assert rows == manifest['rows'], 'Independent contract normalization differs'
    source = (folder / 'SideJobsS27.reds').read_text(encoding='utf-8')
    assert generate.sha(folder / 'SideJobsS27.reds') == manifest['files']['SideJobsS27.reds']
    assert source == generate.template().replace('// GENERATED_DATA', generate.data_source(rows))
    assert source.count('.SetFactStr(') == 1
    assert 'Tag(i) + "_Permit"' in prior.method(source, 'Permit')
    assert 'this.Own(i, "Issued") != 0' in prior.method(source, 'Permit')
    for forbidden in ['ChangeEntryState', 'GiveReward', 'GiveItem', 'ModLog(', 'LogChannel', 'persistent let', 'SetFactStr("mq', 'SetFactStr("sq']:
        assert forbidden not in source, forbidden
    for token in ['ArraySize(names) != ArraySize(minimum)', 'ArraySize(names) != ArraySize(maximum)',
                  'actual < minimum[k] || actual > maximum[k]', 'sample.valid = false',
                  'EnumInt(jm.GetEntryState(entry)) : -1']:
        assert token in prior.method(source, 'Read'), token
    assert prior.method(source, 'Read').count('jm.HasAnyDelayedStateChanges()') == 2
    assert 'this.Same(this.previous[i], current) && this.Ready(i)' in prior.method(source, 'Poll')
    assert 'epoch != this.epoch' in prior.method(source, 'Poll')
    assert 'profile.PTFRPAComplete() && !profile.PTFRPAFaulted()' in prior.method(source, 'Common')
    assert '!player.IsDead() && !player.IsReplacer() && BodyPolicy.Safe(player)' in prior.method(source, 'Safe')
    assert 'unfinished-job restart migration remains separate' in prior.method(source, 'Status')
    cases = arrays = 0
    common = prior.method(source, 'Common')
    for name, value in generate.COMMON.items():
        assert f'this.Fact("{name}") == {value}' in common
        cases += 1
    # Mutate only in-memory contract fixtures; immutable sources stay untouched.
    original_load = generate.load
    for path in paths:
        contract = original_load(path)
        owner_key = 'contracts' if 'contracts' in contract else 'owners'
        def rejects(mutator):
            mutated = copy.deepcopy(contract)
            mutator(mutated[owner_key][0])
            def fixture_load(candidate):
                return mutated if candidate == path else original_load(candidate)
            try:
                with patch.object(generate, 'load', side_effect=fixture_load):
                    generate.normalize([path])
            except (AssertionError, KeyError, TypeError, ValueError):
                return
            raise AssertionError('Unsafe contract mutation was accepted')
        rejects(lambda owner: owner.update(tag='PTFRS25_OLD_OWNER')); cases += 1
        rejects(lambda owner: owner.update(id='q307_tower', ids=['q307_tower'])); cases += 1
        rejects(lambda owner: owner['journals'][0].update(states=[3])); cases += 1
        rejects(lambda owner: owner['journals'][0].update(states=[2])); cases += 1
        rejects(lambda owner: owner['journals'][0].update(states=[4])); cases += 1
        rejects(lambda owner: owner['journals'][0].update(states=[True])); cases += 1
        rejects(lambda owner: owner['journals'][0].update(path='quests/side_quest/not_the_declared_root')); cases += 1
        rejects(lambda owner: owner['facts_equal'].update({owner['tag'] + '_Permit': 1})); cases += 1
        rejects(lambda owner: owner['facts_equal'].update({'PTFRS27_PHONE_FAKE_Issued': 1})); cases += 1
        rejects(lambda owner: owner.setdefault('fact_ranges', {}).update({'invalid_range': {'min': 2, 'max': 1}})); cases += 1
    for i, row in enumerate(rows):
        assert row['journals'][0]['states'] == [1]
        assert all(j['states'] == [1] for j in row['journals'] if j['class'] == 'gameJournalQuest')
        for alias in row['ids'] + [row['tag']]:
            assert f'Equals(id, {generate.q(alias)})' in prior.method(source, 'Index')
            cases += 1
        for name, values in generate.arrays(row).items():
            body = prior.method(source, name + str(i))
            actual = json.loads(body[body.index('return ') + 7:body.rindex(';')])
            assert actual == values
            arrays += 1
        baseline = observe(row)
        assert baseline['valid']; cases += 1
        for n, journal in enumerate(row['journals']):
            for state in [None, False, True, -1, 0, 1, 2, 3, 4, 5, 999]:
                states = baseline['states'].copy(); states[n] = state
                expected = isinstance(state, int) and not isinstance(state, bool) and state in journal['states']
                assert observe(row, states=states)['valid'] == expected
                cases += 1
        for n, fact in enumerate(row['facts']):
            for value in [None, False, True, -2147483647, -1, 0, 1, 2, 999, fact['min'] - 1, fact['min'], fact['max'], fact['max'] + 1]:
                facts = baseline['facts'].copy(); facts[n] = value
                expected = isinstance(value, int) and not isinstance(value, bool) and fact['min'] <= value <= fact['max']
                assert observe(row, facts=facts)['valid'] == expected, (row['id'], fact, value)
                cases += 1
        for available, settled in [(False, True), (True, False), (False, False)]:
            assert not observe(row, available=available, settled=settled)['valid']; cases += 1
        assert not observe(row, states=[])['valid']; cases += 1
        if row['facts']:
            assert not observe(row, facts=[])['valid']; cases += 1
        protocol = prior.Protocol(); protocol.tick(baseline); assert protocol.permit == 0
        protocol.tick(baseline); assert protocol.permit == 1; cases += 2
        invalid = observe(row, states=[3] + baseline['states'][1:])
        protocol.tick(invalid); assert protocol.permit == 0; cases += 1
        for guard in ['common', 'safe', 'final_safe']:
            protocol = prior.Protocol(); protocol.tick(baseline); protocol.tick(baseline)
            protocol.tick(baseline, **{guard: False}); assert protocol.permit == 0; cases += 1
        for field, value in [('ready', 0), ('finished', 1), ('fault', 1), ('warmup', 3)]:
            protocol = prior.Protocol(); protocol.tick(baseline); protocol.tick(baseline)
            setattr(protocol, field, value); protocol.tick(baseline)
            assert protocol.permit == 0 and protocol.previous is None; cases += 1
        protocol = prior.Protocol(); protocol.tick(baseline); protocol.tick(baseline); protocol.issued = 1
        old = copy.deepcopy(protocol.writes); protocol.tick(invalid); protocol.restore()
        assert protocol.issued == 1 and old == protocol.writes; cases += 1
        protocol = prior.Protocol(); protocol.tick(baseline); protocol.tick(baseline); protocol.restore()
        assert protocol.permit == 0 and protocol.previous is None and protocol.warmup == 3; cases += 1
        protocol.tick(baseline, epoch=protocol.epoch - 1); assert protocol.warmup == 3; cases += 1
        for tick in range(1, 5):
            protocol.tick(baseline); assert protocol.permit == int(tick == 4); cases += 1
    pins = dict(manifest['source_pins'])
    pins[MODEL.relative_to(ROOT).as_posix()] = generate.sha(MODEL)
    pins[Path(__file__).relative_to(ROOT).as_posix()] = generate.sha(Path(__file__))
    report = {'status': 'PASS_OFFLINE_NOT_LIVE', 'manifest_sha256': generate.sha(folder / 'manifest.json'),
              'test_sha256': generate.sha(Path(__file__)), 'policy_cases': cases, 'arrays': arrays,
              'adapters': len(rows), 'owned_permit_only': True, 'source_pins': pins,
              'existing_restoration_owners_not_called_or_changed': True, 'restart_implementation': False}
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return {k: v for k, v in report.items() if k != 'source_pins'}


if __name__ == '__main__':
    print(json.dumps(verify(Path(sys.argv[1]))))
