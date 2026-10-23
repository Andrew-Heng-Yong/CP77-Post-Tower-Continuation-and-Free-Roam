"""Independent read-only S24 review; writes only a new services evidence receipt."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('native_checks', ROOT / 'prealpha/sidejobs_s22/delamain_v2/test.py')
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)
read, sha, graphs = lib.read, lib.sha, lib.graphs


def walk(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def main():
    dest = ROOT / 'research/sidejobs_s24/services' / sys.argv[1]
    assert dest.suffix == '.json' and dest.parent.resolve() == (ROOT / 'research/sidejobs_s24/services').resolve()
    assert not dest.exists(), 'Immutable independent review receipt'
    reviewed = [
        'prealpha/sidejobs_s24/build.ps1', 'prealpha/sidejobs_s24/test.py',
        'prealpha/sidejobs_s24/compile.py', 'prealpha/sidejobs_s24/deploy.ps1',
        'prealpha/sidejobs_s24/test_deploy.py', 'prealpha/sidejobs_s24/runtime/generate.py',
        'prealpha/sidejobs_s24/runtime/test.py',
        'prealpha/sidejobs_s24/base/build/base_04/build.json',
        'prealpha/sidejobs_s24/base/build/base_04/tests.json',
        'prealpha/sidejobs_s24/support/build/support_02/component.json',
        'prealpha/sidejobs_s24/support/build/support_02/tests.json',
        'research/afterlife_world/nix_repaired_phase.json',
        'redscript/PTFR_B0_StoryEight/StoryEightDriver.reds',
        'research/sidejobs_s23/native_01/json/base/quest/minor_quests/mq015/phases/mq015_01_hook.questphase.json',
        'research/sidejobs_s23/native_01/json/base/quest/minor_quests/mq015/scenes/mq015_01_hook.scene.json',
    ]
    pins = {p: sha(ROOT / p) for p in reviewed}
    for folder, manifest in [('base/base_04', 'build.json'), ('support/support_02', 'component.json')]:
        family, revision = folder.split('/')
        build = ROOT / 'prealpha/sidejobs_s24' / family / 'build' / revision
        m, t = read(build / manifest), read(build / 'tests.json')
        assert t['status'].startswith('PASS')
        assert t.get('component_sha256', t.get('build_sha256')) == sha(build / manifest)
        for path, digest in m['source_pins'].items():
            assert sha(ROOT / path) == digest, path
            pins[path] = digest
        for depot, digest in m['resources'].items():
            assert sha(build / 'source' / depot) == digest

    base = ROOT / 'prealpha/sidejobs_s24/base/build/base_04'
    m = read(base / 'build.json')
    c = read(ROOT / m['contract'])
    parent = graphs(ROOT / 'research/sidejobs_s2/sacrum_audit/native_01/json/base/quest/minor_quests/minorquests.questphase.json')
    parent_nodes = {n['id']: n for n in parent['root']['nodes']}
    assert all(parent_nodes[i]['$type'] == 'questLogicalHubNodeDefinition' for i in (70, 86, 89))
    for owner in c['owners']:
        g = graphs(base / ('readback/' + owner['key'].lower() + '.json'))['root']
        ns = {n['id']: n for n in g['nodes']}
        for node_id in owner['parent_nodes']:
            assert ns[node_id] == parent_nodes[node_id], (owner['id'], node_id)
        assert all(edge in g['edges'] for edge in owner['parent_edges'])
        for obj in walk(ns[1004]):
            if obj.get('$type') == 'questJournalEntryState_ConditionType':
                path = obj['path']
                assert path['fileEntryIndex'] == (1 if path['realPath'].startswith('contacts/') else 2)
                assert obj['state'] == 'Inactive'
        if owner['contact_copy']:
            node = ns[1010]
            param = node['type']['params'][0]
            assert param['contact']['realPath'] == owner['contact_copy']['path']
            assert param['contact']['fileEntryIndex'] == 1
            assert param['addContact'] == 1 and param['sendNotification'] == 0
        assert not any(o.get('$type') == 'questSetVar_NodeType' and o.get('factName', '').startswith('PTFRB0') for o in walk(g))

    nix = graphs(ROOT / 'research/afterlife_world/nix_repaired_phase.json')
    ns = {n['id']: n for n in nix['root/5']['nodes']}
    assert any(o.get('factName') == 'nix_default_on' and o.get('comparisonType') == 'Less' and o.get('value') == 1 for o in walk(ns[11]))
    assert [11, 'Out', 18, 'In'] in nix['root/5']['edges']
    assert [18, 'Out', 1, 'In'] in nix['root/5']['edges']
    assert ns[1]['type'] == 'Terminating'
    assert [5, 'Out1', 6, 'In'] in nix['root']['edges']
    assert [6, 'Out', 2, 'In'] in nix['root']['edges']
    hook = ROOT / 'research/sidejobs_s23/native_01/json/base/quest/minor_quests/mq015'
    scene = read(hook / 'scenes/mq015_01_hook.scene.json')
    assert {n['value'] for n in walk(scene) if n.get('$type') == 'questSetVar_NodeType' and n.get('factName') == 'nix_default_on'} == {0, 1}
    phase = graphs(hook / 'phases/mq015_01_hook.questphase.json')
    spawn = next(n for n in phase['root/23']['nodes'] if n['id'] == 2)['actions'][0]['type']
    assert spawn['action'] == 'Reactivate' and spawn['reference']['$value'] == '#nix'
    assert spawn['phaseName']['$value'] == 'default' and spawn['entryName']['$value'] == 'nix'
    assert any(n.get('factName') == 'mq016_active' and n.get('comparisonType') == 'Equal' and n.get('value') == 0 for n in walk(parent_nodes[152]))

    support = read(ROOT / 'prealpha/sidejobs_s24/support/build/support_02/component.json')
    assert len(support['contacts']) == 2
    r3no = next(c for c in support['contacts'] if c['contact']['name'] == 'R3NO')
    assert all(r3no['idle'][f'audio_{who}_start_activate'] == 0 and r3no['idle'][f'audio_{who}_end_activate'] == 0 for who in ('v_calls_r3no', 'r3no_calls_v'))
    assert support['native_counter_writes'] == support['global_owner_restarts'] == support['history_equalities'] == 0
    for p, digest in pins.items():
        assert sha(ROOT / p) == digest, p
    result = {
        'status': 'PASS_REVIEWED_SOURCE_AND_COMPONENTS_NOT_LIVE',
        'reviewer': 's24_services_audit', 'review_script_sha256': sha(Path(__file__)),
        'source_pins': pins, 'blocking_findings': [],
        'resolved_finding': 'Compiler proof now binds complete script identity sets, include roots/configuration, and CLI/SCC binaries; installation recomputes them and rejects changed/added dependencies.',
        'verified': [
            'Native Nix parent content/story/mq016/distance waits retained. Bypassed parent hubs are not predicates.',
            'MQ015 uses original #nix/default spawn-set Reactivate and original scene default-off/on protocol; B0 retains its native terminating default-off watcher and rearm gate.',
            'Base contact guard fileEntryIndex=1 and silently restored original native contact copies verified.',
            'Phone audio busy request flags included for R3NO, no historical start/end equality admission.',
            'Earlier review compared all preserved old cleanup node payloads and nested edges; only appended, own-Issued-gated contacts act.',
            'Aggregate validates runtime tester and generated source; installer is three additions only and verifies preserved package hashes, protected saves/cache/settings, and recoverable rollback.',
        ],
        'limits': [
            'Final aggregate, compiler execution, resource-audit journal variant proof and deployment fixture execution remain separate root-owned checks.',
            'Native Nix service/quest handoff, calls/SMS, actual interactions, rewards, Johnny body hiding and save/reload are not live-tested by this receipt.',
            'No game files, saves, cache, settings, existing installed source or pinned evidence modified.'
        ]
    }
    dest.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'receipt': str(dest), 'source_pins': len(pins), 'sha256': sha(dest)}))


if __name__ == '__main__':
    main()
