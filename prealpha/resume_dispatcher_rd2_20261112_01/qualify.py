"""Read back the compiled package and replay The Gig's native claim and reward path."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import struct
import sys

from capture import HERE, ROOT, BASELINE_SHA, baseline, read, sha, write
from prepare import ARCHIVE, HS1, S22

REGISTRY = ROOT / 'prealpha/quest_resume_registry_20261112_01'
sys.path.insert(0, str(REGISTRY))
from model import normalize, load_export, walk

STATE = {'Inactive': 1, 'Active': 2, 'Succeeded': 3, 'Failed': 4}
QUEST = 'quests/side_quest/sq_q001_wakako'
PREFIX = (0, 2, 82, 3, 17, 151, 9, 2, 5)

def graph(path):
    m = normalize(load_export(path))
    assert len(m['graphs']) == 1
    g = m['graphs'][0]
    return m['support'], {n['id']: n['parameters'] for n in g['nodes']}, set(map(tuple, g['edges']))

def condition(c, journals, facts, items):
    kind = c['$type']
    if kind == 'questLogicalCondition':
        assert c['operation'] in ('AND', 'OR')
        fn = all if c['operation'] == 'AND' else any
        return fn(condition(k, journals, facts, items) for k in c['conditions'])
    t = c['type']
    if kind == 'questFactsDBCondition':
        assert t['comparisonType'] == 'Equal'
        return facts.get(t['factName']) == t['value']
    if kind == 'questJournalCondition':
        assert not t['inverted']
        return journals.get(t['path']['realPath']) == STATE[t['state']]
    assert kind == 'questObjectCondition' and t['$type'] == 'questInventory_ConditionType'
    assert t['comparisonType'] == 'GreaterOrEqual'
    return items.get(t['itemID']['$value'], 0) >= t['quantity']

def phase_hash(path):
    h = (0x811c9dc5, 0x01800013)[path[0]]
    for byte in struct.pack('<' + 'H' * len(path), *path):
        h = ((h ^ byte) * 0x1000193) & 0xffffffff
    return h

def owner_controls():
    evidence = ROOT / 'prealpha/handler_preservation_hp1_20261112_01/saves_01'
    results = {}
    for slot in ('ManualSave-26', 'AutoSave-10', 'AutoSave-11', 'AutoSave-5'):
        manifest = read(evidence / slot / 'manifest.json')
        assert manifest['root_gap_hex'] == '026B577A51814903CAE118A84B9942C8C4'
        blobs = {}
        for row in manifest['nodes']:
            name = row['name']
            if name not in ('customArray', 'eventManager'):
                continue
            p = Path(row['path'])
            assert sha(p) == row['sha256']
            data = p.read_bytes()
            ident, count = struct.unpack_from('<II', data)
            assert ident == row['id'] and len(data) == 8 + count * (2 if name == 'customArray' else 16)
            blobs[name] = data[8:]
        words = [v[0] for v in struct.iter_unpack('<H', blobs['customArray'])]
        paths = []
        at = 0
        while at < len(words):
            n = words[at]
            assert n and at + 1 + n <= len(words)
            paths.append(tuple(words[at+1:at+1+n]))
            at += 1 + n
        matches = [p for p in paths if p[:len(PREFIX)] == PREFIX]
        assert matches == [PREFIX], (slot, matches)
        key = phase_hash(PREFIX)
        assert [p for p in paths if phase_hash(p) == key] == matches
        events = [(h, n) for token, h, n in struct.iter_unpack('<QII', blobs['eventManager']) if token and n != 0xffff]
        handlers = [n for h,n in events if h == key]
        ancestors = [list(PREFIX[:i+1]) for i in range(1,len(PREFIX)) if (phase_hash(PREFIX[:i]),PREFIX[i]) in events]
        if slot in ('ManualSave-26', 'AutoSave-10'):
            assert handlers == [29] and ancestors
        else:
            assert handlers == [] and ancestors == []
        results[slot] = {'handlers': handlers, 'ancestors': ancestors, 'save_sha256': manifest['source_sha256']}
    return results

def snapshot(game, name, expected):
    p = game / 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1' / name
    assert sha(p).startswith(expected)
    row = next(r for r in read(p)['rows'] if r['definition']['id'] == 'sq_q001_wakako')
    assert row['stable']
    d = row['definition']
    return (dict(zip((j[0] for j in d['journals']), row['states'])),
            dict(zip(d['fact_names'], row['facts'])),
            dict(zip((j[0] for j in d['journals']), row['counters'])), sha(p))

def main():
    m, game = baseline()
    c = read(HERE / 'contract.json')
    a = HERE / 'archive_01'
    package = HERE / 'candidate_01/package'
    compiled = read(HERE / 'compile_01/result.json')
    assert compiled['status'] == 'PASS' and compiled['source_count'] == 148
    assert all(sha(game / path) == pin for path,pin in compiled['input_pins'].items())
    assert all(sha(package / p) == compiled['staged_hashes'][p] for p in (HS1,S22))
    readback = read(a / 'readback.json')
    assert readback['status'] == 'MEMBERS_VERIFIED' and readback['contract_sha256'] == sha(HERE / 'contract.json')
    assert readback['archive_sha256'] == sha(a / 'zzzz_PTFR_Combined.archive')
    donor = read(ROOT / 'prealpha/resume_dispatcher_rd1_20261112_01/archive_04/readback.json')
    old_members = {r['depot']: r['sha256'] for r in donor['members']}
    new_members = {r['depot']: r['sha256'] for r in readback['members']}
    assert old_members.keys() == new_members.keys() and len(new_members) == 1742
    assert {k for k in new_members if new_members[k] != old_members[k]} == {c['depot']}
    support, old, edges = graph(a / 'before.questphase.json')
    next_support, new, next_edges = graph(a / 'after.questphase.json')
    assert support == next_support and edges == next_edges and old.keys() == new.keys()
    assert {n for n in new if new[n] != old[n]} == {1001,1002}
    assert all('RewardManager' not in n['$type'] and 'PhoneManager' not in n['$type'] for n in new.values())

    hj,hf,hc,hp = snapshot(game, 'snapshot_hs1_20261112T193921Z_151_2.json',
                            'C1CFCBB5FF3BFB13D718C4FF0735D5A0E22A6C84C434E791F4F89C6C17BD26BE')
    lj,lf,lc,lp = snapshot(game, 'snapshot_hs1_20261112T171055Z_161_1.json', '849751BD2A07')
    for j in c['journals']:
        p = j['path']
        assert hj[p] in j['history'] and lj[p] in j['live']
        if j['class'] == 'gameJournalQuestObjective':
            assert hc[p] == lc[p] == 0
    assert all(hf[k] == lf[k] == v for k,v in c['fixed_facts'].items())
    # The older compact export did not include every session/service flag.
    # Reconstruct only the known post-Tower startup and explicit test doubles.
    flags = {k: 1 for k in ('PostTowerFreeRoamActive','PTFRP0_DR13','PTFRPA2_Finished','q307_done',
            'q307_finished','q307_2079','q307_main_game_killed','q307_ep1_killed','PTFRU9_Support_Issued',
            'PTFRS22_SQ_Q001_Permit','PTFRB0STCASSIUS_OwnerActive')}
    flags.update({k: 0 for k in ('PTFRPA2_Fault','q307_active','q307_debug_reset','q115_point_of_no_return',
                  'q305_johnny_scene_active','PTFRU9_Support_Fault','PTFRS22_SQ_Q001_Refused',*c['other_owner_receipts'])})
    f = lf | flags
    for n in (1001,1002):
        guard = new[n]['condition']
        assert guard['operation'] == 'OR' and guard['conditions'][0] == old[n]['condition']
        earned = guard['conditions'][1]
        assert not condition(guard['conditions'][0], lj, f, {})
        assert condition(guard, lj, f, {})
        assert condition(guard, lj | {QUEST: 1}, f, {}) == condition(old[n]['condition'], lj | {QUEST: 1}, f, {})
        for j in c['journals']:
            p = j['path']
            for bad in {-1,1,2,3,4} - set(j['live']):
                assert not condition(earned, lj | {p: bad}, f, {}), (n,p,bad)
        for k,v in (c['fixed_facts'] | c['live_only_facts'] |
                    dict.fromkeys(c['own_receipts']+c['other_owner_receipts'],0)).items():
            assert not condition(earned, lj, f | {k: v+1}, {}), (n,k)
        assert not condition(guard, lj, f | {'q307_finished':0}, {})

    # Follow the serialized edges, including the post-claim activation wait.
    expected = [0,1000,1001,1002,1003,25,2,1006,15,1007,1008,30,28,29,18,4,26,27,1004,1]
    journals, facts = deepcopy(lj), deepcopy(f)
    visited = []
    for i, n in enumerate(expected):
        visited.append(n)
        p = new[n]
        kind = p['$type']
        if i == len(expected)-1:
            assert kind == 'questOutputNodeDefinition' and p['type'] == 'Terminating'
            break
        out = 'Out'
        if kind in ('questPauseConditionNodeDefinition', 'questConditionNodeDefinition'):
            if n == 29:
                assert not condition(p['condition'], journals, facts, {})
                for item in ('Items.YakuzaTattoo','Items.AdvancedYakuzaTattoo'):
                    assert condition(p['condition'], journals, facts, {item:1})
                assert facts['sq_q001_done'] == 0
            else:
                assert condition(p['condition'], journals, facts, {}), n
            if kind == 'questConditionNodeDefinition':
                out = 'True'
        elif kind == 'questFactsDBManagerNodeDefinition':
            t = p['type']
            assert t['setExactValue'] == 1
            facts[t['factName']] = t['value']
        elif kind == 'questJournalNodeDefinition':
            incoming = {e[4] for e in edges if e[0] == expected[i-1] and e[3] == n}
            assert len(incoming) == 1
            journals[p['type']['path']['realPath']] = STATE[incoming.pop()]
        outgoing = {e[3] for e in edges if e[0] == n and e[1] == out}
        assert outgoing == {expected[i+1]}, (n,outgoing)
    assert journals[QUEST] == 3 and facts['sq_q001_done'] == facts['PTFRS22_SQ_Q001_Finished'] == 1
    assert facts['q001_wakako_reward_given'] == f['q001_wakako_reward_given']
    assert not condition(new[1001]['condition'], lj, f | {'PTFRS22_SQ_Q001_Issued':1}, {})

    owners = owner_controls()
    dst = package / ARCHIVE
    assert sha(dst) == next(x['sha256'] for x in m['core_files'] if x['path']==ARCHIVE)
    shutil.copyfile(a / 'zzzz_PTFR_Combined.archive', dst)
    rows = [{'path': r['path'], 'sha256': sha(package / r['path'])} for r in m['core_files']]
    changes = {r['path'] for r,b in zip(rows,m['core_files']) if r['sha256'] != b['sha256']}
    assert changes == {ARCHIVE, HS1, S22}
    write(HERE / 'candidate_01/manifest.json', {'baseline_manifest_sha256': BASELINE_SHA, 'files': rows,
        'changed_paths': sorted(changes), 'archive_source': str(a/'archive_source'),
        'qualification': 'PASS_BOUNDED_OFFLINE', 'installed': False})
    write(HERE / 'assessment.json', {'status':'PASS_BOUNDED_OFFLINE', 'stage':c['stage'], 'contract_sha256':sha(HERE/'contract.json'),
        'compiled_sources':148, 'archive_members':1742, 'changed_resources':[c['depot']], 'changed_nodes':[1001,1002],
        'snapshot_sha256':hp, 'post_ending_projection_sha256':lp, 'fixture_doubles':flags, 'native_path':list(PREFIX),
        'saved_owner_controls':owners, 'reward_path_replay':visited, 'gameplay':'PENDING', 'game_writes':0, 'save_writes':0})
    print('PASS: serialized guard diff, paid-to-pending fixture, one-time claim and reward replay, and native retirement controls.')

if __name__ == '__main__':
    main()
