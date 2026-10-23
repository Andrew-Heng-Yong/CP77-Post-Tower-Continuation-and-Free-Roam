"""Audit cooked Claire phases and prepare an unstarted-only native-entry contract.

phaseResource can retain an editor resource name while phaseGraph contains the
complete cooked implementation. Such names are not unresolved external phases.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'prealpha/ncpd_scanner_n1')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import value, walk


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def graphs(p):
    r = SafeResource(read(p))
    return {g['path']: g for g in flatten(r, r.obj['Data']['RootChunk'])}


def refs(obj):
    return {value(v) for x in walk(obj) for k, v in x.items()
            if k == 'DepotPath' and isinstance(value(v), str)
            and value(v).endswith(('.questphase', '.scene'))}


def catalog(path):
    data = read(path)
    handles = {x['HandleId']: x['Data'] for x in walk(data) if 'HandleId' in x and 'Data' in x}
    out = {}

    def visit(wrapper, parts):
        node = wrapper.get('Data', handles.get(wrapper.get('HandleRefId'), wrapper))
        ident = node.get('id', '')
        parts = parts + ([ident] if ident else [])
        if node.get('$type', '').startswith('gameJournal'):
            out['/'.join(parts)] = node['$type']
        for child in node.get('entries', []):
            visit(child, parts)

    visit(data['Data']['RootChunk']['entry'], [])
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision', default='01')
    args = parser.parse_args()
    destination = HERE / ('contract' + args.revision + '.json')
    evidence_path = ROOT / 'research/sidejobs_s27/claire' / ('dependency_' + args.revision + '.json')
    assert not destination.exists() and not evidence_path.exists(), 'Immutable output exists'

    index = {}
    for folder in sorted((ROOT / 'research/sidejobs_s25/families').glob('native_*')):
        for p in (folder / 'json').rglob('*.json'):
            index[p.relative_to(folder / 'json').as_posix()[:-5].replace('/', '\\')] = p
    main_depot = 'base\\quest\\side_quests\\sq024\\sq024.questphase'
    phone_depot = 'base\\quest\\holocalls\\claire\\claire_holocall.questphase'
    cleanup_depot = 'base\\quest\\holocalls\\claire\\claire_cleanup.questphase'
    queue = [main_depot, phone_depot, cleanup_depot]
    closure, objects, embedded, external = {}, [], [], []
    while queue:
        depot = queue.pop(0)
        if depot in closure:
            continue
        assert depot in index, ('Missing genuine external resource', depot)
        p = index[depot]
        closure[depot] = p
        data = read(p)
        objects.append(data)
        if depot.endswith('.questphase'):
            gs = graphs(p)
            found = set()
            for gp, g in gs.items():
                for n in g['nodes']:
                    local = dict(n)
                    resource = value(n.get('phaseResource', {}).get('DepotPath'))
                    child = gp + '/' + str(n['id'])
                    if n['$type'] == 'questPhaseNodeDefinition' and child in gs:
                        # Some parents also serialize a disconnected two-node
                        # editor placeholder. Always include real external
                        # resources when present; only an absent name backed
                        # by an executable embedded graph is metadata-only.
                        metadata_only = bool(resource and resource not in index and gs[child]['edges'])
                        if metadata_only:
                            local.pop('phaseResource', None)
                        embedded.append({'owner': depot, 'graph': gp, 'node': n['id'],
                                         'metadata_path': resource, 'embedded_graph': child,
                                         'nodes': len(gs[child]['nodes']), 'edges': len(gs[child]['edges']),
                                         'metadata_only_missing_external': metadata_only})
                    found |= refs(local)
            queue.extend(sorted(found))
            external.extend({'owner': depot, 'reference': d} for d in sorted(found))
        else:
            found = refs(data)
            queue.extend(sorted(found))
            external.extend({'owner': depot, 'reference': d} for d in sorted(found))

    journal = ROOT / 'research/sidejobs_s24/ep1/native_02/json/base/journal/cooked_journal.journal.json'
    cat = catalog(journal)
    inventory = ROOT / 'research/sidejobs_s21_failed/inventory_02.json'
    jobs = [j for j in read(inventory)['jobs'] if j['id'].startswith('sq024') or j['id'] == '07_nc_underground']
    ids = [j['id'] for j in jobs]
    assert len(ids) == 5, ids
    journals = []
    for ident in ids:
        roots = [p for p, c in cat.items() if c == 'gameJournalQuest' and p.endswith('/' + ident)]
        assert len(roots) == 1, (ident, roots)
        for p, c in cat.items():
            if p == roots[0] or p.startswith(roots[0] + '/'):
                journals.append({'path': p, 'class': c, 'states': [1]})
    facts, phonepaths, busy = {}, {}, set()
    for obj in objects:
        for x in walk(obj):
            for key in ('factName', 'factName1', 'factName2'):
                name = value(x.get(key))
                if isinstance(name, str) and name.startswith(('sq024_', '#sq024_')):
                    facts[name] = 0
                if isinstance(name, str) and name.startswith(('holo_', 'audio_')) and name.endswith(('_start_activate', '_end_activate', '_active', '_started')):
                    busy.add(name)
            if x.get('$type') == 'gameJournalPath':
                path, cls = x.get('realPath', ''), value(x.get('className'))
                if path.startswith('contacts/') and ('sq024' in path or path.startswith('contacts/marianne/')):
                    phonepaths[path] = cls
    for name in ('holo_setup_active', 'holo_setup_started', 'holo_interrupt_call', 'holo_active_call_interrupted',
                 'holo_reset', 'holo_force_reset', 'holo_reset_soft', 'holo_interrupt_call_manual', 'holo_interrupt_braindance'):
        busy.add(name)
    facts.update({name: 0 for name in sorted(busy)})
    # Existing B0 service legitimately toggles the intro greeting latch. The
    # native family may passively set active=1 before its first earned hook.
    ranges = {'sq024_active': {'min': 0, 'max': 1}, 'sq024_intro_dialogues_done': {'min': 0, 'max': 1},
              'q101_enable_side_content': {'min': 1, 'max': 2147483647}}
    for name in ranges:
        facts.pop(name, None)
    facts.update({'ep1_standalone': 0, 'PTFRB0CLA_Ready': 1, 'PTFRB0CLA_Enabled': 1,
                  'PTFRB0CLA_Excluded': 0, 'PTFRB0CLA_Suspended': 0, 'PTFRBASE_Suspended': 0,
                  'PTFRR1_Issued': 0})
    excluded = []
    for path, cls in sorted(phonepaths.items()):
        if cat.get(path) == cls:
            journals.append({'path': path, 'class': cls, 'states': [1]})
        else:
            excluded.append({'path': path, 'class': cls})
    assert cat['contacts/marianne'] == 'gameJournalContact'
    # Root-first deterministic order matches runtime lookup expectations.
    journals.sort(key=lambda j: (j['class'] != 'gameJournalQuest', j['path']))
    common_source = ROOT / 'prealpha/sidejobs_s24/ep1/contract02.json'
    pins = {}

    def pin(p):
        pins[Path(p).relative_to(ROOT).as_posix()] = sha(p)

    native = {}
    for depot, p in closure.items():
        raw = Path(str(p).replace('\\json\\', '\\raw\\').replace('/json/', '/raw/')[:-5])
        pin(p)
        pin(raw)
        native[depot] = {'json': p.relative_to(ROOT).as_posix(), 'json_sha256': sha(p),
                         'raw': raw.relative_to(ROOT).as_posix(), 'raw_sha256': sha(raw)}
    for p in (Path(__file__), journal, inventory, common_source,
              ROOT / 'prealpha/ncpd_scanner_n1/native_inspect.py', ROOT / 'tools/audit_activity_batches_b1.py',
              ROOT / 'tools/catalog_gig_rollout_r2.py', ROOT / 'tools/test_gig_pilot_r1.py',
              ROOT / 'research/b0_claire/quest_compatibility_audit.json',
              ROOT / 'research/sidejobs_s27/heroes/native_04/raw/base/quest/side_quests/sidequests.questphase',
              ROOT / 'research/sidejobs_s27/heroes/native_04/json/base/quest/side_quests/sidequests.questphase.json'):
        pin(p)
    result = {'schema': 'S27_CLAIRE_FRESH_CONTRACT_1', 'status': 'PREPARED_NOT_LIVE',
              'common_equal': read(common_source)['common_equal'],
              'owners': [{'id': '07_nc_underground', 'ids': ids, 'key': 'SQ024_FRESH',
                          'title': 'The Beast in Me (fresh story-race family)', 'tag': 'PTFRS27_SQ024_FRESH',
                          'depot': 'towercontinued\\sidejobs_s27\\claire\\sq024_fresh.questphase',
                          'entry': 'sq024_in', 'native_depot': main_depot,
                          'native_source': index[main_depot].relative_to(ROOT).as_posix(),
                          'facts_equal': facts, 'fact_ranges': ranges, 'journals': journals,
                          'contact': 'contacts/marianne', 'busy_flags': sorted(busy),
                          'native_dependencies': sorted(closure), 'metadata_invalid_native_refs_excluded': excluded}],
              'phone': {'controller_source': 'research/sidejobs_s25/families/native_01/raw/base/quest/holocalls/holocall_initializers.questphase',
                        'controller_graph': 'root', 'controller_node': 46, 'controller_input': 'In1',
                        'cleanup_source': 'research/sidejobs_s25/families/native_01/raw/base/quest/holocalls/holocall_cleanup.questphase',
                        'cleanup_condition_node': 433, 'cleanup_phase_node': 297, 'cleanup_input': 'In7', 'cleanup_output': 'Out7',
                        'support_fact': 'PTFRS27_PHONE_CLAIRE_Issued', 'controller_owned_by_parent': True,
                        'cleanup_owned_by_parent': True},
              'native_resources': native, 'source_pins': pins,
              'policy_limit': 'Only genuinely unstarted Inactive family. No restart/reset of progressed family, completed child, existing repeatable race or old restoration.'}
    # Phase 55 has a complete embedded implementation even though its editor
    # name has no stand-alone file. Keep both metadata and embedded bytes.
    finding = [r for r in embedded if r['owner'] == main_depot and r['graph'] == 'root/53' and r['node'] == 55]
    assert len(finding) == 1 and finding[0]['nodes'] == 20 and finding[0]['edges'] == 28
    evidence = {'status': 'COOKED_EMBEDDED_DEPENDENCY_RESOLVED_NOT_LIVE', 'native_main': native[main_depot],
                'old_blocker': 'research/sidejobs_s25/families/claire_deferred_01.json',
                'finding': finding[0], 'embedded_phases': embedded, 'external_references': external,
                'external_closure_count': len(closure),
                'decision': 'Retain original metadata AND complete embedded graph. No missing-phase stub, deleted hook, replacement hacking logic or external file required.'}
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'contract': str(destination), 'roots': len(ids), 'facts': len(facts),
                      'journals': len(journals), 'native_resources': len(native), 'embedded': finding[0]}))


if __name__ == '__main__':
    main()
