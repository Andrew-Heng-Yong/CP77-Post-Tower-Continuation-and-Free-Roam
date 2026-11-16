"""Read back native admission and prove the old and earned branches are exclusive."""
from verify_entrance import HERE, BATCH, graph, load_export, normalize, read, sha, value, write


def leaves(group):
    facts, journals = {}, {}
    for condition in group['conditions']:
        t = condition['type']
        if condition['$type'] == 'questFactsDBCondition':
            assert t['comparisonType'] == 'Equal' and t['factName'] not in facts
            facts[t['factName']] = t['value']
        else:
            assert condition['$type'] == 'questJournalCondition' and not t['inverted']
            p = t['path']
            assert p['realPath'] not in journals
            journals[p['realPath']] = (value(p['className']), t['state'])
    return facts, journals


def admit(group, facts, journal):
    needed_facts, needed_journal = leaves(group)
    return all(facts.get(k) == v for k, v in needed_facts.items()) and all(
        journal.get(k) == v for k, v in needed_journal.items())


def main():
    out = HERE / 'graph_06'
    output = out / 'entry.questphase'
    assert sha(output) == read(out / 'readback.json')['raw_sha256']
    guard = read(HERE / 'evidence_01/admission.json')
    route = read(BATCH / 'evidence_02/rite_route.json')
    pin = next(p for p in route['providers'] if p['rid'] == 15359)
    assert sha(out / 'entry.before.questphase') == pin['sha256']
    assert sha(pin['export_path']) == pin['export_sha256']
    old = normalize(load_export(pin['export_path']))
    new = normalize(load_export(output.with_suffix('.questphase.json')))
    assert new['support'] == old['support']
    assert new['graphs'][1:] == old['graphs'][1:]
    before, earlier_edges = graph(old, 'root')
    after, edges = graph(new, 'root')
    assert {i for i in before if before[i] != after[i]} == {65002}
    assert after.keys() - before.keys() == set(range(65010, 65016))
    removed = {(65003, 'Out', 'Output', 2, 'In1', 'Input')}
    added = {(a, b, 'Output', c, d, 'Input') for a, b, c, d in (
        (65003, 'Out', 65010, 'In'), (65010, 'False', 2, 'In1'),
        (65010, 'True', 65013, 'Active'), (65013, 'Out', 65014, 'Active'),
        (65014, 'Out', 65015, 'In'), (65015, 'Out', 65011, 'In'),
        (65011, 'Out', 65012, 'ResumeGetToClinic'), (65012, 'OUT', 65005, 'In'))}
    assert set(earlier_edges) - set(edges) == removed and set(edges) - set(earlier_edges) == added
    assert after[65002]['condition']['operation'] == 'OR'
    fresh, resume = after[65002]['condition']['conditions']
    assert fresh['operation'] == resume['operation'] == 'AND'
    assert fresh['conditions'][:-1] == before[65002]['condition']['conditions']
    tag = guard['tag']
    assert leaves(fresh)[0] == route['existing_entry_condition'] | {tag+'ResumeRequested': 0}
    assert after[65010]['condition']['type']['factName'] == tag+'ResumeRequested'
    assert after[65011]['type']['factName'] == tag+'Started'
    assert value(after[65012]['phaseResource']['DepotPath']).endswith('sts_wat_nid_05_main.questphase')
    enum = {1: 'Inactive', 2: 'Active', 4: 'Failed'}
    journal = {j['path']: (j['class'], enum[j['live']]) for j in guard['journals']}
    journal.update({p: ('gameJournalPhoneMessage', enum[s]) for p, s in guard['live_phone'].items()})
    facts = guard['native_facts']
    assert leaves(resume) == (facts, journal)
    assert admit(resume, facts, journal) and not admit(fresh, facts, journal)
    assert admit(fresh, leaves(fresh)[0], {}) and not admit(resume, leaves(fresh)[0], journal)
    for node, j in zip((65013, 65014), guard['journals'][:2], strict=True):
        assert after[node]['type']['path']['realPath'] == j['path']
        assert value(after[node]['type']['path']['className']) == j['class']
        assert not after[node]['type']['trackQuest'] and not after[node]['type']['sendNotification']
    assert leaves(after[65015]['condition']) == ({}, {j['path']: (j['class'], 'Active') for j in guard['journals'][:2]})
    rejected = 0
    for name, required in facts.items():
        assert not admit(resume, facts | {name: required + 1}, journal)
        rejected += 1
    for path, (cls, state) in journal.items():
        for variant in ('Undefined', 'Inactive', 'Active', 'Succeeded', 'Failed'):
            if variant != state:
                assert not admit(resume, facts, journal | {path: (cls, variant)})
                rejected += 1
    write(HERE / 'evidence_01/wrapper_assessment.json', {
        'status': 'PASS_UNPACKED_NATIVE_WRAPPER', 'raw_sha256': sha(output),
        'rejected_native_mutations': rejected, 'shared_parent_claim': 65003,
        'existing_credit_depot_unchanged': True, 'registered': False,
    })
    print(f'Checked fresh and earned paths and rejected {rejected} mutated native inputs.')


if __name__ == '__main__':
    main()
