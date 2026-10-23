"""Source-bound admission, reload and malformed-contract tests; not gameplay."""
import copy
import importlib.util
import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import generate

MODEL = ROOT / 'prealpha/sidejobs_s22/runtime_v2/test.py'
spec = importlib.util.spec_from_file_location('u10_protocol_reference', MODEL)
prior = importlib.util.module_from_spec(spec); spec.loader.exec_module(prior)


def observe(row, states=None, facts=None, inventory=None, inventory_available=True, available=True, settled=True):
    states = states if states is not None else [j['states'][0] for j in row['journals']]
    facts = facts if facts is not None else [f['min'] for f in row['facts']]
    valid = available and settled and len(states) == len(row['journals']) and len(facts) == len(row['facts'])
    valid = valid and all(type(s) is int and s in j['states'] for s, j in zip(states, row['journals']))
    valid = valid and all(type(v) is int and f['min'] <= v <= f['max'] for v, f in zip(facts, row['facts']))
    inventory = inventory if inventory is not None else [0] * len(row['inventory_zero'])
    valid = valid and len(inventory) == len(row['inventory_zero'])
    valid = valid and (not row['inventory_zero'] or inventory_available)
    valid = valid and all(type(v) is int and v == 0 for v in inventory)
    return {'states': list(states), 'facts': list(facts), 'inventory': list(inventory), 'valid': valid}


def verify(folder):
    output = folder / 'tests.json'; assert not output.exists()
    manifest = generate.read(folder / 'manifest.json')
    for p, h in manifest['source_pins'].items(): assert generate.sha(ROOT / p) == h
    paths = list(dict.fromkeys(ROOT / row['source'] for row in manifest['rows']))
    rows = generate.normalize(paths); assert rows == manifest['rows']
    source = (folder / 'GigsU10.reds').read_text(encoding='utf-8')
    assert source == generate.template().replace('// GENERATED_DATA', generate.data_source(rows))
    assert generate.sha(folder / 'GigsU10.reds') == manifest['files']['GigsU10.reds']
    method = lambda name: prior.method(source, name)
    assert source.count('.SetFactStr(') == 3
    assert 'GigDataU10.Tag(i) + "_Permit"' in method('Permit')
    assert 'this.Own(i, "Issued") != 0' in method('Permit')
    assert 'GigDataU10.Tag(i) + "_MapPermit"' in method('MapPermit')
    assert 'GigDataU10.Tag(i) + "_PreparePermit"' in method('PreparePermit')
    assert 'this.Own(i, "Issued") != 0' in method('PreparePermit')
    for forbidden in ['ChangeEntryState', 'GiveReward', 'GiveItem', 'SetFact(', 'ModLog(', 'StartQuest']:
        assert forbidden not in source, forbidden
    for token in ['ArraySize(names) != ArraySize(minimum)', 'ArraySize(names) != ArraySize(maximum)',
                  'actual < minimum[k] || actual > maximum[k]', 'sample.valid = false',
                  'EnumInt(jm.GetEntryState(entry)) : -1']:
        assert token in method('Read'), token
    assert method('Read').count('jm.HasAnyDelayedStateChanges()') == 2
    for token in ['GigDataU10.ItemNames(i)', '!IsDefined(players) || !IsDefined(transaction)',
                  '!IsDefined(player) || player.IsReplacer()',
                  'transaction.GetItemQuantity(player, ItemID.CreateQuery(TDBID.Create(items[k])))',
                  'ArrayPush(sample.inventory, actual)', 'if actual != 0']:
        assert token in method('Read'), token
    assert 'ArraySize(a.inventory) != ArraySize(b.inventory)' in method('Same')
    assert 'a.inventory[i] != b.inventory[i]' in method('Same')
    assert 'ItemID.FromTDBID' not in source
    assert 'this.PreparePermit(i, this.Same(this.previous[i], current) && this.Ready(i))' in method('Poll')
    assert 'this.Permit(i, this.Same(this.previous[i], current) && this.Ready(i) && this.Dependencies(i))' in method('Poll')
    assert 'this.Fact(names[k]) != values[k]' in method('Dependencies')
    assert 'epoch != this.epoch' in method('Poll')
    assert '!player.IsDead() && !player.IsReplacer() && BodyPolicy.Safe(player)' in method('Safe')
    assert 'profile.PTFRPAComplete() && !profile.PTFRPAFaulted()' in method('BaseCommon')
    assert 'this.BaseCommon() && IsDefined(phone) && phone.Supported()' in method('Common')
    assert source.count('phone.Start(') == 1
    for token in ['!this.BaseCommon() || !this.Safe()', 'this.warmup != 0',
                  'this.Fact("PTFRU9_Support_Request") != 0', 'this.Fact("PTFRU9_Support_Issued") != 0',
                  'this.Fact("PTFRU9_Support_Fault") != 0', 'this.FreshOwner(i)', 'sample = this.Read(i)',
                  'if sample.valid { phone.Start("DISPOSABLE_SAVE"); return; }']:
        assert token in method('PrepareSupport'), token
    assert 'Unsupported continuation defers without restart' in method('Status')
    fresh = dict((k, int(v)) for k, v in re.findall(r'this.Own\(i, "([^"]+)"\) == (\d+)', method('FreshOwner')))
    assert fresh == {'Ready': 1, 'Revision': 1, 'Issued': 0, 'Started': 0, 'OwnerFinished': 0, 'Fault': 0, 'CreditEntered': 0, 'CreditDone': 0}
    assert 'this.FreshOwner(i)' in method('Ready')
    assert 'this.HistoryReady(i)' in method('Ready') and 'this.HistoryReady(i)' in method('PrepareSupport')
    assert re.findall(r'private persistent let ([^;]+);', source) == ['familyHistorySchema: Int32', 'familyPreTowerCompleted: Bool']
    assert source.count('this.familyPreTowerCompleted = true') == 1
    assert source.count('this.familyHistorySchema = 1') == 1
    assert 'completed && this.historyPrevious' in method('ObserveHistory')
    assert method('ObserveHistory').count('!this.BeforeTower()') == 2
    assert 'this.familyPreTowerCompleted || this.familyHistorySchema != 0' in method('ObserveHistory')
    assert 'this.ObserveHistory()' in method('Poll')
    assert 'this.historyPrevious = false' in method('Restored')
    mapguard = dict((k, int(v)) for k, v in re.findall(r'this.Own\(i, "([^"]+)"\) != (\d+)', method('MapReady')))
    assert mapguard == {'Revision': 1, 'Issued': 1, 'Started': 1, 'OwnerFinished': 0, 'Fault': 0}
    for token in ['!this.Common() || !this.Safe()', 'EnumInt(jm.GetEntryState(entry)) != 1',
                  'this.Fact(facts[k]) != 0', '!jm.HasAnyDelayedStateChanges()']:
        assert token in method('MapReady'), token
    cases = 0; arrays = 0
    # Exercise the saved-history boundary independently of fresh admission.
    # No after-Tower or unsettled observation may manufacture the witness.
    def history_tick(state, before, after, settled, completed):
        schema, witnessed, previous = state
        if witnessed or schema != 0: return state
        if not before or not after or not settled: return (schema, witnessed, False)
        if completed and previous: return (1, True, True)
        return (schema, witnessed, completed)
    assert history_tick((0, False, False), True, True, True, True) == (0, False, True)
    assert history_tick((0, False, True), True, True, True, True) == (1, True, True)
    for before, after, settled, complete in [(False, False, True, True), (True, False, True, True), (False, True, True, True),
                                             (True, True, False, True), (True, True, True, False)]:
        assert not history_tick((0, False, True), before, after, settled, complete)[1]; cases += 1
    for schema in [-1, 1, 2]:
        assert history_tick((schema, False, True), True, True, True, True) == (schema, False, True); cases += 1
    assert history_tick((1, True, False), False, False, True, True) == (1, True, False); cases += 1
    for guards in [fresh, mapguard]:
        for key, expected in guards.items():
            for value in [-1, 0, 1, 2, 3]:
                sample = guards | {key: value}
                assert all(sample[k] == v for k, v in guards.items()) == (value == expected)
                cases += 1
    original_read = generate.read
    for path in paths:
        original = original_read(path)
        def rejects(mutator):
            changed = copy.deepcopy(original); mutator(changed['owners'][0])
            with patch.object(generate, 'read', side_effect=lambda p: changed if p == path else original_read(p)):
                try: generate.normalize(paths)
                except (AssertionError, ValueError, KeyError, TypeError): return
            raise AssertionError('Unsafe contract accepted')
        for mutation in [lambda r: r.update(tag='PTFRS27_OTHER'), lambda r: r.update(id='q307_tower'),
                         lambda r: r['journals'][0].update(states=[2]), lambda r: r['journals'][0].update(states=[3]),
                         lambda r: r['journals'][0].update(states=[4]), lambda r: r['journals'][0].update(states=[True]),
                         lambda r: r['facts_equal'].update({r['tag'] + '_Permit': 1}),
                         lambda r: r.update(map_facts_zero=[]),
                         lambda r: r.update(inventory_zero=[]),
                         lambda r: r['inventory_zero'][0].update(record='Items.money'),
                         lambda r: r['inventory_zero'][0].update(hash='0'),
                         lambda r: r.setdefault('fact_ranges', {}).update({'test': {'min': 2, 'max': 1}})]:
            rejects(mutation); cases += 1
    for i, row in enumerate(rows):
        for key, value in row['service_facts_equal'].items():
            for actual in [-1, 0, 1, 2]:
                sample = row['service_facts_equal'] | {key: actual}
                assert all(sample[k] == v for k, v in row['service_facts_equal'].items()) == (actual == value); cases += 1
        for name, values in generate.arrays(row).items():
            body = method(name + str(i)); actual = json.loads(body[body.index('return ') + 7:body.rindex(';')])
            assert actual == values; arrays += 1
        baseline = observe(row); assert baseline['valid']; cases += 1
        for n in range(len(row['inventory_zero'])):
            for value in [None, False, True, -1, 0, 1, 2, 2147483647]:
                inventory = baseline['inventory'].copy(); inventory[n] = value
                assert observe(row, inventory=inventory)['valid'] == (type(value) is int and value == 0); cases += 1
            assert not observe(row, inventory_available=False)['valid']; cases += 1
            protocol = prior.Protocol(); protocol.tick(baseline); protocol.tick(baseline)
            inventory = baseline['inventory'].copy(); inventory[n] = 1
            protocol.tick(observe(row, inventory=inventory)); assert protocol.permit == 0; cases += 1
        assert not observe(row, inventory=baseline['inventory'] + [0])['valid']; cases += 1
        for n, journal in enumerate(row['journals']):
            for state in [None, False, True, -1, 0, 1, 2, 3, 4, 5, 999]:
                states = baseline['states'].copy(); states[n] = state
                assert observe(row, states=states)['valid'] == (type(state) is int and state in journal['states']); cases += 1
        for n, fact in enumerate(row['facts']):
            for value in [None, False, True, -2147483647, -1, 0, 1, 2, 999, fact['min'] - 1, fact['max'] + 1]:
                facts = baseline['facts'].copy(); facts[n] = value
                assert observe(row, facts=facts)['valid'] == (type(value) is int and fact['min'] <= value <= fact['max']); cases += 1
        for available, settled in [(False, True), (True, False), (False, False)]:
            assert not observe(row, available=available, settled=settled)['valid']; cases += 1
        protocol = prior.Protocol(); protocol.tick(baseline); assert protocol.permit == 0
        protocol.tick(baseline); assert protocol.permit == 1; cases += 2
        invalid = observe(row, states=[3] + baseline['states'][1:])
        protocol.tick(invalid); assert protocol.permit == 0; cases += 1
        for guard in ['common', 'safe', 'final_safe']:
            protocol = prior.Protocol(); protocol.tick(baseline); protocol.tick(baseline)
            protocol.tick(baseline, **{guard: False}); assert protocol.permit == 0; cases += 1
        protocol = prior.Protocol(); protocol.tick(baseline); protocol.tick(baseline); protocol.issued = 1
        old = copy.deepcopy(protocol.writes); protocol.tick(invalid); protocol.restore()
        assert old == protocol.writes and protocol.issued == 1; cases += 1
        protocol = prior.Protocol(); protocol.restore(); protocol.tick(baseline, epoch=protocol.epoch - 1)
        assert protocol.warmup == 3 and protocol.permit == 0
        for tick in range(1, 5): protocol.tick(baseline); assert protocol.permit == int(tick == 4); cases += 1
    pins = manifest['source_pins'] | {p.relative_to(ROOT).as_posix(): generate.sha(p) for p in [MODEL, Path(__file__)]}
    result = {'status': 'PASS_OFFLINE_NOT_LIVE', 'manifest_sha256': generate.sha(folder / 'manifest.json'),
              'test_sha256': generate.sha(Path(__file__)), 'policy_cases': cases, 'arrays': arrays,
              'source_pins': pins, 'runtime_direct_writes': ['own Permit', 'own PreparePermit', 'own MapPermit'],
              'shared_service': 'Calls existing guarded U9 Start only for an eligible fresh owner; no duplicate native controller.',
              'resume_limit': 'No general continuation engine; unsupported progress remains unchanged.'}
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return {k: v for k, v in result.items() if k != 'source_pins'}


if __name__ == '__main__': print(json.dumps(verify(Path(sys.argv[1]))))
