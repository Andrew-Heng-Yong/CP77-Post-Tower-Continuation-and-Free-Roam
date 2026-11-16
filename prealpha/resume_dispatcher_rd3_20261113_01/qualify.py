"""Verify the native journal handoff, saved owners and preserved scan graph."""
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
TAG = 'PTFRS22_SQ025'
PREFIXES = {
    'base_quest': (0, 2, 82, 5, 48),
    'base_phone': (0, 2, 82, 3, 34, 51),
    'persistent_return_archer': (0, 2, 82, 3, 17, 151, 6, 35),
    'hospital_phone': (1, 0, 9, 12, 23, 32, 100, 2),
    'cabride_phone': (1, 0, 9, 12, 24, 21),
}
BEFORE = ROOT / 'prealpha/handler_preservation_hp1_20261112_01/saves_01'
RD2 = ROOT / 'prealpha/resume_dispatcher_rd2_20261112_01'


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


def graph_delta(archive, label):
    before_path = archive / f'before_{label}.questphase.json'
    after_path = archive / f'after_{label}.questphase.json'
    before, after = model(before_path), model(after_path)
    assert before.keys() == after.keys()
    assert all(before[g] == after[g] for g in before if g != 'root')
    for key in ('phasePrefabs', 'cookingPlatform'):
        assert read(before_path)['Data']['RootChunk'][key] == read(after_path)['Data']['RootChunk'][key]
    old, new = before['root'], after['root']
    assert {i for i in old['nodes'] if new['nodes'][i] != old['nodes'][i]} == {1002, 1003}
    extra = {1020, 1021, 1022, 1023, 1024} if label == 'owner' else set()
    assert new['nodes'].keys() - old['nodes'].keys() == extra
    for i in (1002, 1003):
        condition = new['nodes'][i]['condition']
        assert condition['operation'] == 'OR' and condition['conditions'][0] == old['nodes'][i]['condition']
    edges = set(map(tuple, old['edges']))
    if extra:
        edges.remove((1014, 'Out', 1006, 'In'))
        edges.update([(1014, 'Out', 1020, 'In'), (1020, 'False', 1006, 'In'),
                      (1020, 'True', 1021, 'Active'), (1021, 'Out', 1022, 'Active'),
                      (1022, 'Out', 1023, 'Active'), (1023, 'Out', 1024, 'In'),
                      (1024, 'Out', 1006, 'In')])
    assert set(map(tuple, new['edges'])) == edges
    return new


def check_admission(contract, graph, states, facts, is_support):
    facts = facts | {TAG + '_SupportIssued': 0 if is_support else 1}
    for i in (1002, 1003):
        guard = graph['nodes'][i]['condition']
        legacy, earned = guard['conditions']
        assert not native_condition(legacy, states, facts)
        assert native_condition(earned, states, facts)
        for row in contract['journals']:
            for other in {-1, 1, 2, 3, 4} - set(row['live']):
                assert not native_condition(earned, states | {row['path']: other}, facts), row['path']
        for name, val in (contract['fixed_facts'] | dict.fromkeys(
                contract['own_receipts'] + contract['other_owner_receipts'], 0)).items():
            assert not native_condition(earned, states, facts | {name: val + 1}), name
        for name in ('q307_finished', TAG + '_Permit', TAG + '_SupportIssued', 'holo_interrupt_call'):
            assert not native_condition(guard, states, facts | {name: 1 - facts[name]}), name
        # Legacy entry uses its own earlier Inactive journal state and prior intro.
        old_states = states | {row['path']: row['live'][0] for row in contract['journals']}
        for row in contract['journals']:
            if row['path'].endswith(('sq025_delamain', 'sq025c05_scared')):
                old_states[row['path']] = 1
        assert native_condition(legacy, old_states, facts | {'sq025_scan_scared_intro_done': 1})


def check_scan(scan, scene, history_states, facts):
    root = scan['root']
    edges = set(map(tuple, root['edges']))
    assert all((1000 + i, 'True', 198, f'In{i}') in edges for i in range(1, 8))
    assert [i for i in range(1, 8) if native_condition(
        root['nodes'][1000 + i]['condition'], history_states, facts)] == [2, 3, 7]
    chain = (1005, 264, 397, 412, 404, 304, 193)
    assert all(any(e[0] == a and e[2] == b for e in edges) for a, b in zip(chain, chain[1:]))
    assert any(x.get('$value') == '#sq025_pr_scared' for x in walk(root['nodes'][193]['phaseInstancePrefabs']))
    assert any(x.get('$value') == '#sq025_tr_scared' for x in walk(root['nodes'][404]['condition']))
    assert any(x.get('$value') == '#sq025_pr_03_street_find_delamain' for x in walk(
        read(scene['scan'])['Data']['RootChunk']['phasePrefabs']))
    assert {(193, 'Out1', 198, 'In5'), (193, 'reward_out', 267, 'In1')} <= edges
    assert {(23, 'Out2', 22, 'scared_in_talk'), (23, 'Out3', 12, 'scared_in')} <= set(map(tuple, scan['root/193']['edges']))
    scene_data = read(scene['scan_scene'])['Data']['RootChunk']
    nodes = {n['nodeId']['id']: n for n in walk(scene_data['sceneGraph']) if 'nodeId' in n and 'outputSockets' in n}
    assert not any('johnny' in str(a).lower() for a in scene_data['actors'])
    once = next(x for x in walk(nodes[8728]) if x.get('factName') == 'sq025_scan_scared_intro_once')
    assert once['comparisonType'] == 'Less' and once['value'] == facts['sq025_scan_scared_intro_once'] == 1
    assert any(dest['nodeId']['id'] == 3810 for port in nodes[939]['outputSockets'] for dest in port['destinations'])
    increment = next(x for x in walk(nodes[3810]) if x.get('factName') == 'sq025_scans_done')
    assert increment['value'] == 1 and increment['setExactValue'] == 0


def main():
    baseline_manifest, game = baseline()
    contract = read(HERE / 'contract.json')
    archive = HERE / 'archive_01'
    package = HERE / 'candidate_01/package'
    compiled = read(HERE / 'compile_01/result.json')
    assert compiled['status'] == 'PASS' and compiled['source_count'] == 148
    assert all(sha(game / p) == h for p, h in compiled['input_pins'].items())
    assert all(sha(package / p) == compiled['staged_hashes'][p] for p in (HS1, S22))
    readback = read(archive / 'readback.json')
    old_members = {r['depot']: r['sha256'] for r in read(RD2 / 'archive_01/readback.json')['members']}
    new_members = {r['depot']: r['sha256'] for r in readback['members']}
    assert readback['status'] == 'MEMBERS_VERIFIED'
    assert readback['contract_sha256'] == sha(HERE / 'contract.json')
    assert readback['archive_sha256'] == sha(archive / 'zzzz_PTFR_Combined.archive')
    assert len(old_members) == len(new_members) == 1742 and old_members.keys() == new_members.keys()
    assert {d for d in old_members if old_members[d] != new_members[d]} == set(contract['depots'])
    support = graph_delta(archive, 'support')
    owner = graph_delta(archive, 'owner')
    history, past_counters, past_facts = snapshot(game, 'snapshot_hs1_20261112T193921Z_151_2.json',
        'C1CFCBB5FF3BFB13D718C4FF0735D5A0E22A6C84C434E791F4F89C6C17BD26BE', contract['id'])
    states, counters, post_facts = snapshot(game, 'snapshot_hs1_20261112T171055Z_161_1.json',
        '849751BD2A07EFA27D1BE09D5EB38403F59B7D7F07BDB1948CAF8C38A1BFEF6D', contract['id'])
    for row in contract['journals']:
        path = row['path']
        assert history[path] in row['history'] and states[path] in row['live']
        if row['class'] == 'gameJournalQuestObjective':
            assert past_counters[path] == counters[path] == row.get('counter', 0)
    assert all(past_facts[k] == post_facts[k] == v for k, v in contract['fixed_facts'].items())

    control = HERE / 'saves_02/AutoSave-16'
    saved = read(control / 'manifest.json')
    for row in saved['journals']:
        assert states[row['path']] == row['state_u32']
    actual_facts = {k: v if v is not None else 0 for k, v in saved['facts'].items()}
    assert all(actual_facts[k] == v for k, v in contract['fixed_facts'].items())
    # Test the native predicate using the serialized condition and an issued
    # script permit. Absent facts in the save are evaluated with GetFact's zero default.
    old_guard = support['nodes'][1002]['condition']['conditions'][0]
    required = {x['factName'] for x in walk(old_guard) if 'factName' in x}
    assert required <= actual_facts.keys()
    facts = actual_facts | {TAG + '_Permit': 1}
    for native, is_support in ((support, True), (owner, False)):
        check_admission(contract, native, states, facts, is_support)
    for i, path in zip((1021, 1022, 1023), contract['restore_journals']):
        node = owner['nodes'][i]
        assert node['$type'] == 'questJournalNodeDefinition' and node['type']['path']['realPath'] == path
    entry = owner['nodes'][1020]['condition']
    claimed = facts | {TAG + '_Issued': 1}
    assert native_condition(entry, states, claimed)
    assert not native_condition(entry, states | {contract['restore_journals'][0]: 3}, claimed)
    ack = owner['nodes'][1024]['condition']
    assert not native_condition(ack, states, claimed)
    active = states | dict.fromkeys(contract['restore_journals'], 2)
    assert native_condition(ack, active, claimed)
    assert not native_condition(ack, active, facts)

    pins = {r['rid']: r for r in read(HERE / 'evidence_01/sources.json')}
    source_paths = {k: pins[rid]['export_path'] for k, rid in (('scan', 14929), ('scan_scene', 11747))}
    check_scan(model(source_paths['scan']), source_paths, history, facts)
    owners = {}
    for directory in (BEFORE / 'ManualSave-26', BEFORE / 'AutoSave-10', BEFORE / 'AutoSave-11',
                      HERE / 'saves_02/AutoSave-15', control, HERE / 'saves_01/AutoSave-17'):
        rows = saved_owners(directory)
        if directory in (BEFORE / 'ManualSave-26', BEFORE / 'AutoSave-10'):
            assert rows['base_quest']['handlers'] and rows['base_phone']['handlers']
        else:
            for key, row in rows.items():
                assert not row['handlers'] and not row['freezer_groups'], (directory, key, row)
                if key.startswith('base_') or key == 'persistent_return_archer':
                    assert not row['ancestor_nodes']
                else:
                    assert not (set(row['ancestor_nodes']) & {2, 21, 32, 100})
        owners[directory.name] = rows

    destination = package / ARCHIVE
    assert sha(destination) == baseline_manifest['archive_sha256']
    shutil.copyfile(archive / 'zzzz_PTFR_Combined.archive', destination)
    rows = [{'path': r['path'], 'sha256': sha(package / r['path'])} for r in baseline_manifest['core_files']]
    changes = {r['path'] for r, b in zip(rows, baseline_manifest['core_files']) if r['sha256'] != b['sha256']}
    assert changes == {ARCHIVE, HS1, S22}
    write(HERE / 'candidate_01/manifest.json', {'baseline_manifest_sha256': BASELINE_SHA, 'files': rows,
        'changed_paths': sorted(changes), 'archive_source': str(archive/'archive_source'),
        'qualification': 'PASS_BOUNDED_OFFLINE', 'installed': False})
    write(HERE / 'assessment.json', {'status': 'PASS_BOUNDED_OFFLINE', 'stage': contract['stage'],
        'contract_sha256': sha(HERE / 'contract.json'), 'archive_members': len(new_members),
        'changed_resources': contract['depots'], 'compiled_sources': 148,
        'saved_owner_controls': owners, 'tested_native_gate_save': saved['source_sha256'],
        'gameplay': 'PENDING', 'save_writes': 0, 'game_writes': 0})
    print('Verified four native guard changes, Northside journal acknowledgement and saved owner retirement.')


if __name__ == '__main__':
    main()
