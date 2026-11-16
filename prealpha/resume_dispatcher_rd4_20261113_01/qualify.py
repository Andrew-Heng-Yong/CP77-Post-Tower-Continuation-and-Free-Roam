"""Verify boxing admission, saved-owner retirement and preserved native progression."""
from collections import Counter
from pathlib import Path
import shutil
import struct
import sys

from capture import HERE, ROOT, BASELINE_SHA, baseline, read, sha, write
sys.path.insert(0, str(ROOT / 'prealpha/handler_preservation_hp1_20261112_01'))
from analyze import framed, freezer, paths, phase_hash
sys.path.insert(0, str(ROOT / 'prealpha/phone_support_ph1'))
sys.modules.pop('model', None)
from model import model, walk

ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
HS1 = 'r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds'
S22 = 'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS22.reds'
STATE = {'Inactive': 1, 'Active': 2, 'Succeeded': 3, 'Failed': 4}
TAG = 'PTFRS22_MQ025'
PREFIXES = {
    'base_quest': (0, 2, 82, 6, 28),
    'journal_companion': (0, 2, 82, 4, 9, 3, 44),
    'encounter_companion': (0, 2, 82, 4, 12, 5, 14),
    'cinematic_companion': (0, 2, 82, 4, 10, 3, 27),
}
BEFORE = ROOT / 'prealpha/handler_preservation_hp1_20261112_01/saves_01'
RD3 = ROOT / 'prealpha/resume_dispatcher_rd3_20261113_01'


def saved_owners(directory):
    manifest = read(directory / 'manifest.json')
    assert manifest['root_gap_hex'] == '026B577A51814903CAE118A84B9942C8C4'
    data = {}
    for row in manifest['nodes']:
        path = Path(row['path'])
        assert sha(path) == row['sha256']
        data[row['name']] = (path.read_bytes(), row['id'])
    catalogue = paths(*data['customArray'])
    collisions = Counter(phase_hash(path) for path in catalogue)
    events = [(h, node) for token, h, node in struct.iter_unpack(
        '<QII', framed(*data['eventManager'], 16)) if token and node != 0xffff]
    frozen = freezer(*data['questPhaseFreezer'])
    result = {}
    for name, prefix in PREFIXES.items():
        selected = [p for p in catalogue if p[:len(prefix)] == prefix]
        keys = {phase_hash(p): p for p in selected}
        boundaries = [(phase_hash(prefix[:i]), prefix[i]) for i in range(1, len(prefix))]
        assert all(collisions[key] == 1 for key in keys)
        assert all(collisions[key] <= 1 for key, _ in boundaries)
        owned = [[list(keys[h]), n] for h, n in events if h in keys]
        ancestor_nodes = [n for h, n in boundaries if (h, n) in events]
        frozen_count = sum(group['owner'][0] in keys or tuple(group['owner']) in boundaries
                           or any(member['key'][0] in keys for member in group['members'])
                           for group in frozen)
        result[name] = {'cached_paths': len(selected), 'handlers': owned,
                        'ancestor_nodes': ancestor_nodes, 'freezer_groups': frozen_count}
    return result


def native_condition(condition, states, facts):
    kind = condition['$type']
    if kind == 'questLogicalCondition':
        assert condition['operation'] in ('AND', 'OR')
        fn = all if condition['operation'] == 'AND' else any
        return fn(native_condition(c, states, facts) for c in condition['conditions'])
    data = condition['type']
    if kind == 'questFactsDBCondition':
        assert data['comparisonType'] == 'Equal'
        return facts.get(data['factName']) == data['value']
    assert kind == 'questJournalCondition' and not data['inverted']
    return states.get(data['path']['realPath']) == STATE[data['state']]


def snapshot(game, filename, expected, quest):
    p = game / 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1' / filename
    assert sha(p) == expected
    row = next(r for r in read(p)['rows'] if r['definition']['id'] == quest)
    assert row['stable']
    data = row['definition']
    journals = [j[0] for j in data['journals']]
    return dict(zip(journals, row['states'])), dict(zip(journals, row['counters'])), dict(zip(data['fact_names'], row['facts']))


def verify_native(archive, contract, states, saved_facts, pins):
    old = model(archive / 'before.questphase.json')
    new = model(archive / 'after.questphase.json')
    assert old.keys() == new.keys()
    assert all(old[g] == new[g] for g in old if g != 'root')
    assert read(archive / 'before.questphase.json')['Data']['RootChunk']['phasePrefabs'] == read(
        archive / 'after.questphase.json')['Data']['RootChunk']['phasePrefabs']
    before, after = old['root'], new['root']
    assert before['edges'] == after['edges'] and before['nodes'].keys() == after['nodes'].keys()
    assert {i for i in before['nodes'] if before['nodes'][i] != after['nodes'][i]} == {1001, 1002}
    facts = {k: v if v is not None else 0 for k, v in saved_facts.items()}
    facts[TAG + '_Permit'] = 1
    tests = 0
    for i in (1001, 1002):
        guard = after['nodes'][i]['condition']
        assert guard['operation'] == 'OR'
        legacy, earned = guard['conditions']
        assert legacy == before['nodes'][i]['condition']
        assert not native_condition(legacy, states, facts)
        assert native_condition(guard, states, facts)
        for row in contract['journals']:
            for bad in {-1, 1, 2, 3, 4} - set(row['live']):
                assert not native_condition(earned, states | {row['path']: bad}, facts), row['path']
                tests += 1
        for name, val in (contract['fixed_facts'] | dict.fromkeys(
                contract['own_receipts'] + contract['other_owner_receipts'], 0)).items():
            assert not native_condition(guard, states, facts | {name: val + 1}), name
            tests += 1
        for name in ('q307_done', 'q307_finished', TAG + '_Permit'):
            assert not native_condition(guard, states, facts | {name: 0})
            tests += 1
        # Reconstruct the previous Inactive-root admission using the same facts.
        assert native_condition(legacy, states | {contract['journals'][0]['path']: 1}, facts)

    claim = after['nodes'][1003]['type']
    assert claim['factName'] == TAG + '_Issued' and claim['value'] == 1 and claim['setExactValue'] == 1
    issued = facts | {TAG + '_Issued': 1}
    active = states | {j['path']: 2 for j in contract['journals'][:2]}
    edges = set(map(tuple, after['edges']))
    assert {(1002,'True',1003,'In'), (1003,'Out',1006,'Active'), (1006,'Out',1007,'Active'),
            (1007,'Out',1008,'In'), (1008,'Out',1009,'In'), (1009,'True',55,'In1')} <= edges
    for node, journal in zip((1006, 1007), contract['journals']):
        assert after['nodes'][node]['type']['path']['realPath'] == journal['path']
    for node in (1008, 1009):
        check = after['nodes'][node]['condition']
        assert native_condition(check, active, issued)
        assert not native_condition(check, states, issued)
        assert not native_condition(check, active, facts)
        assert not native_condition(check, active | {contract['journals'][2]['path']: 3}, issued)
    assert not native_condition(after['nodes'][1001]['condition'], states, issued)
    assert {(55,'Out1',3,'In1'), (55,'Out1',12,'In'), (12,'Out',5,'In1'),
            (12,'Out',7,'In1'), (12,'Out',9,'In1'), (10,'Out1',11,'In1'),
            (55,'Out1',24,'In'), (8,'Cleanup',25,'In2'), (11,'Out1',25,'In1')} <= edges
    assert after['nodes'][11]['phaseResource']['DepotPath']['$value'] == pins[15352]['depot']
    for slot, parent, rid, native_input, marker in (
            (1, 3, 5885, 0, 120), (2, 5, 9776, 26, 99),
            (3, 7, 5149, 0, 89), (4, 9, 9458, 0, 69)):
        assert (parent, 'Out1', 10, f'In{slot}') in edges
        source = Path(pins[rid]['export_path'])
        root = model(source)['root']
        assert after['nodes'][parent]['phaseResource']['DepotPath']['$value'] == pins[rid]['depot']
        assert root['nodes'][native_input]['socketName']['$value'] == 'In1'
        todo = [native_input]
        seen = set()
        while todo:
            node = todo.pop()
            if node in seen or node == marker:
                continue
            seen.add(node)
            assert root['nodes'][node]['$type'] in (
                'questInputNodeDefinition', 'questFactsDBManagerNodeDefinition', 'questDeletionMarkerNodeDefinition')
            for e in root['edges']:
                if e[0] == node and e[2] == marker:
                    assert e[3] == 'Active'
                if e[0] == node:
                    todo.append(e[2])
        assert any(e[0] in seen and e[2] == marker for e in root['edges'])
        assert root['nodes'][marker]['type']['path']['realPath'] == contract['journals'][slot + 1]['path']
        assert read(source)['Data']['RootChunk']['phasePrefabs']
    return tests


def main():
    baseline_manifest, game = baseline()
    contract = read(HERE / 'contract.json')
    archive = HERE / 'archive_01'
    package = HERE / 'candidate_01/package'
    compiled = read(HERE / 'compile_01/result.json')
    assert compiled['status'] == 'PASS' and compiled['source_count'] == 148
    assert all(sha(game / p) == h for p, h in compiled['input_pins'].items())
    assert all(sha(package / p) == compiled['staged_hashes'][p] for p in (HS1, S22))
    proof = read(archive / 'readback.json')
    old_members = {r['depot']: r['sha256'] for r in read(RD3 / 'archive_01/readback.json')['members']}
    new_members = {r['depot']: r['sha256'] for r in proof['members']}
    assert proof['status'] == 'MEMBERS_VERIFIED' and proof['contract_sha256'] == sha(HERE / 'contract.json')
    assert proof['archive_sha256'] == sha(archive / 'zzzz_PTFR_Combined.archive')
    assert len(old_members) == len(new_members) == 1742 and old_members.keys() == new_members.keys()
    assert {d for d in old_members if old_members[d] != new_members[d]} == set(contract['depots'])
    pins = {r['rid']: r for r in read(HERE / 'evidence_01/sources.json')}
    assert all(sha(r['export_path']) == r['export_sha256'] for r in pins.values())
    prior, prior_counters, prior_facts = snapshot(game, 'snapshot_hs1_20261112T193921Z_151_2.json',
        'C1CFCBB5FF3BFB13D718C4FF0735D5A0E22A6C84C434E791F4F89C6C17BD26BE', contract['id'])
    post, post_counters, post_facts = snapshot(game, 'snapshot_hs1_20261112T171055Z_161_1.json',
        '849751BD2A07EFA27D1BE09D5EB38403F59B7D7F07BDB1948CAF8C38A1BFEF6D', contract['id'])
    fixture = HERE / 'saves_01/AutoSave-3'
    save = read(fixture / 'manifest.json')
    saved_journals = {r['path']: r['state_u32'] for r in save['journals']}
    for row in contract['journals']:
        path = row['path']
        assert prior[path] in row['history'] and post[path] in row['live']
        if path in saved_journals:
            assert saved_journals[path] == post[path]
        else:
            assert post[path] == 1
        if row['class'] == 'gameJournalQuestObjective':
            assert prior_counters[path] == post_counters[path] == 0
    assert all(prior_facts[k] == post_facts[k] == v for k,v in contract['fixed_facts'].items())
    assert all((save['facts'][k] or 0) == v for k,v in contract['fixed_facts'].items())
    assert all(save['facts']['PTFRB0STFRED_' + name] == 1 for name in ('Ready', 'Enabled', 'OwnerActive'))
    rejected = verify_native(archive, contract, post, save['facts'], pins)

    controls = {}
    for directory in (BEFORE/'ManualSave-26', BEFORE/'AutoSave-10', BEFORE/'AutoSave-11', BEFORE/'AutoSave-5', fixture):
        rows = saved_owners(directory)
        if directory.name in ('ManualSave-26', 'AutoSave-10'):
            assert len(rows['base_quest']['handlers']) == 21
            assert all(rows[name]['handlers'] for name in PREFIXES)
        else:
            assert all(not r['handlers'] and not r['ancestor_nodes'] and not r['freezer_groups'] for r in rows.values())
        controls[directory.name] = rows
    destination = package / ARCHIVE
    assert sha(destination) == baseline_manifest['archive_sha256']
    shutil.copyfile(archive / 'zzzz_PTFR_Combined.archive', destination)
    files = [{'path': r['path'], 'sha256': sha(package / r['path'])} for r in baseline_manifest['core_files']]
    changes = {r['path'] for r,b in zip(files,baseline_manifest['core_files']) if r['sha256'] != b['sha256']}
    assert changes == {ARCHIVE, HS1, S22}
    write(HERE/'candidate_01/manifest.json', {'baseline_manifest_sha256': BASELINE_SHA, 'files': files,
        'changed_paths': sorted(changes), 'archive_source': str(archive/'archive_source'),
        'qualification':'PASS_BOUNDED_OFFLINE', 'installed':False})
    write(HERE/'assessment.json', {'status':'PASS_BOUNDED_OFFLINE', 'stage':contract['stage'],
        'contract_sha256':sha(HERE/'contract.json'), 'compiled_sources':148, 'archive_members':1742,
        'changed_resources':contract['depots'], 'changed_nodes':[1001,1002],
        'native_rejection_controls':rejected, 'saved_owner_controls':controls,
        'post_tower_fixture_sha256':save['source_sha256'], 'gameplay':'PENDING', 'game_writes':0, 'save_writes':0})
    print(f'Verified boxing admission, four native marker writers, preserved combat graph, and {rejected} rejection controls.')


if __name__ == '__main__':
    main()
