"""Source-bound S22 admission/protocol model tests; not a live game test."""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import generate

PRIOR_PINS = {
    'generate.py':'6E2155CBBBD45BA8F9E29A85DA838AD52A789CA505DAD099413C851E9327675B',
    'SideJobsS22.template.reds':'92D24064A51EAA972FFCB5796FB83D42B8E7B572A0FB1F93462BEFF6F74696FF',
    'test.py':'272A55CF5FCAF14E588FBB28577E1D88BB25AD42387B01DC7A88CE4F1C9F6C6F',
    'SideJobsS2.reds':'58F134FFE6CCD8DF0AF30FCCABBFD161BBBCC8AEF75E25C16D18303992134295',
    'SideJobsS22.reds':'D5AB7605DDC8302693CF227181D3DD131FF18DF3D1BBE715C09AE949BFE5112D',
    'manifest.json':'7635FCBD0E9E03E6F2519275CAD2C3E93957664CC3A7CE31B266046B946F652C',
    'test_result_01.json':'17DD5836E70DC57A266DECBA1C6E154B86C54B6C606F9DC889F6A4F8ECD6C9EC',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def method(text, name):
    match = re.search(r'\bfunc ' + re.escape(name) + r'\(', text)
    assert match, name
    start = text.index('{', match.start())
    level = 1
    pos = start + 1
    while level:
        level += (text[pos] == '{') - (text[pos] == '}')
        pos += 1
    return text[match.start():pos]


def observed(row, states=None, facts=None, available=True, settled=True):
    states = states if states is not None else [j['states'][0] for j in row['journals']]
    facts = facts if facts is not None else list(row['facts_equal'].values())
    valid = available and settled and len(states) == len(row['journals']) and len(facts) == len(row['facts_equal'])
    valid = valid and all(state in journal['states'] for state, journal in zip(states, row['journals']))
    valid = valid and all(value == wanted for value, wanted in zip(facts, row['facts_equal'].values()))
    return {'states': list(states), 'facts': list(facts), 'valid': valid}


def same(a, b):
    return bool(a and b and a['valid'] and b['valid'] and a['states'] == b['states'] and a['facts'] == b['facts'])


class Protocol:
    """Independent state model bound to the source assertions below."""
    def __init__(self):
        self.running = True
        self.epoch = 0
        self.warmup = 0
        self.previous = None
        self.permit = 0
        self.issued = 0
        self.finished = 0
        self.fault = 0
        self.ready = 1
        self.writes = []

    def set_permit(self, value):
        if self.issued == 0 and self.permit != int(value):
            self.permit = int(value)
            self.writes.append(('owned_Permit', self.permit))

    def restore(self):
        self.epoch += 1
        self.warmup = 3
        self.previous = None
        self.set_permit(False)

    def tick(self, sample, common=True, safe=True, epoch=None, final_safe=True):
        if not self.running or (epoch is not None and epoch != self.epoch):
            return
        self.warmup = max(0, self.warmup - 1)
        if self.issued != 0:
            return
        ready = self.warmup == 0 and common and safe and self.ready == 1 and self.finished == 0 and self.fault == 0
        if ready:
            self.set_permit(same(self.previous, sample) and final_safe)
            self.previous = copy.deepcopy(sample)
        else:
            self.set_permit(False)
            self.previous = None


def verify(destination):
    if destination.exists():
        raise RuntimeError('Existing test receipt is immutable')
    manifest = load(HERE/'manifest.json')
    rows = generate.normalize()
    checks = cases = 0
    for path, expected in manifest['source_pins'].items():
        assert sha(ROOT/path) == expected, path
        checks += 1
    assert rows == manifest['rows']
    assert set(manifest['files']) == {'SideJobsS2.reds', 'SideJobsS22.reds'}
    for name, expected in manifest['files'].items():
        assert sha(HERE/name) == expected
        checks += 1
    template = (HERE/'SideJobsS22.template.reds').read_text(encoding='utf-8')
    source = (HERE/'SideJobsS22.reds').read_text(encoding='utf-8')
    s2 = (HERE/'SideJobsS2.reds').read_text(encoding='utf-8')
    old = generate.S21.read_text(encoding='utf-8')
    assert source == template.replace('// GENERATED_DATA', generate.data_source(rows))
    assert s2 == generate.s2_successor()
    assert len(rows) == 4
    checks += 4

    # Successor scope: only the Delamain table gains the source-audited mounted
    # guard. Runtime behavior, S2 successor, other contracts, prior files/proofs
    # and all normalized journal rows remain exact.
    prior = HERE.parent/'runtime'
    for name, expected in PRIOR_PINS.items():
        assert sha(prior/name) == expected, 'Prior pinned file changed: '+name
        checks += 1
    prior_manifest = load(prior/'manifest.json')
    prior_source = (prior/'SideJobsS22.reds').read_text(encoding='utf-8')
    assert (HERE/'SideJobsS2.reds').read_bytes() == (prior/'SideJobsS2.reds').read_bytes()
    assert (HERE/'SideJobsS22.template.reds').read_bytes() == (prior/'SideJobsS22.template.reds').read_bytes()
    data_start = 'public abstract class SideJobDataS22 {'
    assert source[:source.index(data_start)] == prior_source[:prior_source.index(data_start)]
    for i in [0,2,3]:
        assert rows[i] == prior_manifest['rows'][i], rows[i]['id']
        checks += 1
    current_delamain = rows[1]
    prior_delamain = prior_manifest['rows'][1]
    for key in ['id','title','tag','journals']:
        assert current_delamain[key] == prior_delamain[key], key
        checks += 1
    assert 'sq025_sad_mounted' not in prior_delamain['facts_equal']
    assert current_delamain['facts_equal'] == prior_delamain['facts_equal'] | {'sq025_sad_mounted':0}
    assert len(current_delamain['facts_equal']) == 41
    assert current_delamain['source'] == 'prealpha/sidejobs_s22/delamain_v2/admission.json'
    checks += 7

    # Read the generated arrays back independently, with no inference for an
    # omitted FailedDetails child. Explicit native getter state is mandatory.
    sizes = []
    for i, row in enumerate(rows):
        expected = {
            'Paths': [j['path'] for j in row['journals']],
            'Classes': [j['class'] for j in row['journals']],
            'StatesA': [j['states'][0] for j in row['journals']],
            'StatesB': [j['states'][-1] for j in row['journals']],
            'FactNames': list(row['facts_equal']),
            'FactValues': list(row['facts_equal'].values()),
        }
        for field, values in expected.items():
            body = method(source, field + str(i))
            match = re.search(r'return (\[.*\]);', body)
            assert match and json.loads(match.group(1)) == values
            checks += 1
        assert set(row['journals'][0]['states']) == {1, 4}
        assert row['journals'][0]['class'] == 'gameJournalQuest'
        assert row['tag'].startswith('PTFRS22_')
        assert not any(k.startswith('PTFR') for k in row['facts_equal'])
        sizes.append({'id': row['id'], 'journals': len(row['journals']), 'facts': len(row['facts_equal'])})
        checks += 4

    # Exactly one write API, scoped to owned Permit; no gameplay, quest-root,
    # reward, progress, certificate, or durable owner mutation in S22.
    assert source.count('.SetFactStr(') == 1
    assert 'let name = SideJobDataS22.Tag(i) + "_Permit";' in method(source, 'Permit')
    assert 'this.Own(i, "Issued") != 0' in method(source, 'Permit')
    for forbidden in ['ChangeEntryState', 'SetEntryState', 'AddToInventory', 'GiveReward', 'ResetQuest', 'LogChannel', 'ModLog', 'print(', 'persistent let']:
        assert forbidden not in source, forbidden
        checks += 1
    for token in ['this.Common()', 'this.Safe()', 'this.Own(i, "Ready") == 1', 'this.Own(i, "Issued") == 0', 'this.Own(i, "Finished") == 0', 'this.Own(i, "Fault") == 0']:
        assert token in method(source, 'Ready'), token
        checks += 1
    assert 'profile.PTFRPAComplete() && !profile.PTFRPAFaulted()' in method(source, 'Common')
    assert 'BodyPolicy.Safe(player)' in method(source, 'Safe')
    assert '!player.IsDead() && !player.IsReplacer()' in method(source, 'Safe')
    assert method(source, 'Read').count('jm.HasAnyDelayedStateChanges()') == 2
    assert 'EnumInt(jm.GetEntryState(entry)) : -1' in method(source, 'Read')
    assert 'sample.valid = false' in method(source, 'Read')
    assert 'this.Same(this.previous[i], current) && this.Ready(i)' in method(source, 'Poll')
    assert method(source, 'Poll').index('this.Same(this.previous[i], current)') < method(source, 'Poll').index('this.previous[i] = current')
    assert 'epoch != this.epoch' in method(source, 'Poll')
    assert 'if this.Own(i, "Issued") == 0 { this.Permit(i, false); }' in method(source, 'Restored')
    assert 'this.epoch += 1; this.warmup = 3; ArrayClear(this.previous)' in method(source, 'Restored')
    assert 'wrappedMethod(gameInstance)' in method(source, 'OnRestored')
    checks += 12

    # Only the intended S21 automatic current-policy auth and display labels
    # change. All legacy persistence, history, read-only FailedDetails, native
    # freshness, ownership and certificate logic remain byte-for-byte exact.
    old_prefix = old[:old.index('public abstract class SideJobFailureDataS21')]
    new_prefix = s2[:s2.index('public abstract class SideJobFailureDataS21')]
    old_names = re.findall(r'\bfunc (\w+)\(', old_prefix)
    assert len(old_names) == len(set(old_names))
    for name in old_names:
        if name not in {'DevelopmentArmed', 'Status', 'Inspect'}:
            assert method(old_prefix, name) == method(new_prefix, name), name
            checks += 1
    assert old[:old.index('  public static func Catalogue')]==s2[:s2.index('  public static func Catalogue')]
    assert old[old.index('public abstract class SideJobFailureDataS21'):]==s2[s2.index('public abstract class SideJobFailureDataS21'):]
    assert 'return !this.faulted && this.Common();' in method(s2, 'DevelopmentArmed')
    assert 'this.Certified(SideJobDataS2.ID(i)) ? 1 : 2' in method(s2, 'Poll')
    assert 'this.explicitDevelopment = true' in method(s2, 'EnableFreshFixture')
    assert 'currentPostTowerPolicy=' in method(s2, 'Status')
    checks += 6

    # Every exact fact and every observed journal state is tested independently.
    # This models admission, not the native engine/interaction runtime.
    successful_rows = 0
    for row in rows:
        baseline = observed(row)
        assert baseline['valid']; cases += 1
        for index, journal in enumerate(row['journals']):
            for state in [None, -1, 0, 1, 2, 3, 4, 5, 999]:
                states = baseline['states'].copy(); states[index] = state
                actual = observed(row, states=states)
                assert actual['valid'] == (state in journal['states']), (row['id'], journal['path'], state)
                cases += 1
            if journal['states'] == [3]:
                successful_rows += 1
        for index, (name, wanted) in enumerate(row['facts_equal'].items()):
            for value in [None, -1, 0, 1, 2, 999]:
                facts = baseline['facts'].copy(); facts[index] = value
                assert observed(row, facts=facts)['valid'] == (value == wanted), (row['id'], name, value)
                cases += 1
        for available, settled in [(False, True), (True, False), (False, False)]:
            assert not observed(row, available=available, settled=settled)['valid']; cases += 1
        assert not observed(row, states=[])['valid']; cases += 1
        assert not observed(row, facts=[])['valid']; cases += 1

        # Two distinct ticks and unchanged guard values required. Root Failed to
        # Inactive is still allowed, but must be observed stable again.
        p = Protocol(); p.tick(baseline); assert p.permit == 0
        p.tick(baseline); assert p.permit == 1; cases += 2
        alternative = copy.deepcopy(baseline)
        alternative['states'][0] = 1 if baseline['states'][0] == 4 else 4
        p.tick(alternative); assert p.permit == 0
        p.tick(alternative); assert p.permit == 1; cases += 2
        invalid = observed(row, states=[3] + baseline['states'][1:])
        p.tick(invalid); assert p.permit == 0
        p.tick(invalid); assert p.permit == 0; cases += 2
        for guard in ['common', 'safe', 'final_safe']:
            p = Protocol(); p.tick(baseline); p.tick(baseline)
            p.tick(baseline, **{guard:False}); assert p.permit == 0; cases += 1
        for field, value in [('ready',0),('finished',1),('fault',1),('warmup',3)]:
            p = Protocol(); p.tick(baseline); p.tick(baseline)
            setattr(p, field, value); p.tick(baseline)
            assert p.permit == 0 and p.previous is None; cases += 1
        p = Protocol(); p.tick(baseline); p.tick(baseline)
        p.issued = 1; old_writes = list(p.writes); p.tick(invalid); p.restore()
        assert p.permit == 1 and p.issued == 1 and p.writes == old_writes; cases += 1
        p = Protocol(); p.tick(baseline); p.tick(baseline); p.restore()
        assert p.permit == 0 and p.previous is None and p.warmup == 3; cases += 1
        p.tick(baseline, epoch=p.epoch-1); assert p.warmup == 3 and p.previous is None; cases += 1
        for tick in range(1,5):
            p.tick(baseline); assert p.permit == int(tick == 4); cases += 1
        assert all(name == 'owned_Permit' for name,value in p.writes); cases += 1
        p.running = False; before = copy.deepcopy(p.__dict__); p.tick(invalid)
        assert p.__dict__ == before; cases += 1
    assert successful_rows >= 10
    result = {
        'status':'PASS_OFFLINE_NOT_LIVE', 'checks':checks, 'policy_cases':cases,
        'adapter_shapes':sizes, 'required_succeeded_journal_rows_preserved':successful_rows,
        'source_pins':manifest['source_pins'], 'runtime_sha256':manifest['files'],
        'test_sha256':sha(Path(__file__)),
        'prior_runtime_pins':PRIOR_PINS,
        'successor_delta':'Delamain adds exact sq025_sad_mounted==0. Other three contracts, all journal rows, S2 successor and S22 runtime behavior are unchanged. Native watcher cleanup is tested separately by the Delamain builder.',
        'scope':'Source/table/model checks only. Main integration compiler/native graph tests and live gameplay remain separate. No installation or game/save changes.',
        'protected':'Native facts/journals/rewards and Issued owners are never written by S22 runtime; original S2 history/certification/data/FailedDetails remain exact.'
    }
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__ == '__main__':
    print(json.dumps(verify(Path(sys.argv[1]))))
