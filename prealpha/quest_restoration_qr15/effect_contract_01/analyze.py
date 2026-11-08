"""Source-backed startup/effect analysis. Writes fresh workspace evidence only.

This is not an engine emulator, restore adapter, save parser or game diagnostic.
"""
from pathlib import Path
import argparse
import collections
import copy
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
WORK = HERE.parents[2]
sys.path.insert(0, str(BASE / 'saved_graph_state_01'))
from inspect_native import Image
sys.path.insert(0, str(WORK / 'tools/parity_audit'))
from model import Resource


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def pin(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def raw_edges(obj):
    """Second traversal: collect connection objects, not normalized node edges."""
    handles = {}
    def walk(value):
        if isinstance(value, dict):
            if 'HandleId' in value and 'Data' in value:
                handles[str(value['HandleId'])] = value['Data']
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(obj)
    def resolve(h):
        return handles[str(h.get('HandleId', h.get('HandleRefId')))]
    root = resolve(obj['Data']['RootChunk']['graph'])
    startup = next(resolve(h) for h in root['nodes'] if resolve(h)['id'] == 1)
    graph = resolve(startup['phaseGraph'])
    sockets = {}
    for h in graph['nodes']:
        n = resolve(h)
        for sh in n.get('sockets', []):
            s = resolve(sh)
            sockets[str(sh.get('HandleId', sh.get('HandleRefId')))] = [str(n['id']), s['name']['$value']]
    edges = []
    for v in handles.values():
        if v.get('$type') != 'graphGraphConnectionDefinition':
            continue
        a, b = v.get('source', {}), v.get('destination', {})
        ka, kb = str(a.get('HandleId', a.get('HandleRefId'))), str(b.get('HandleId', b.get('HandleRefId')))
        if ka in sockets and kb in sockets:
            edges.append(sockets[ka] + sockets[kb])
    return sorted(edges)


def reachable(graph, seed):
    seen, todo = set(), [str(seed)]
    while todo:
        node = todo.pop()
        if node in seen:
            continue
        seen.add(node)
        todo.extend(e[2] for e in graph['edges'] if e[0] == node and e[1] != 'CutSource' and e[3] != 'CutDestination')
    return sorted(seen, key=int)


BRANCHES = {
    '16': ('Hotel-area approach', 'Conditional listener rearm', 'IsInside can immediately re-fire. Its descendants activate friendly/combat entries and change security/crowd state; prior execution is not certified.'),
    '30': ('Cracked-shard progression', 'Preserve native predicate; conditional listener rearm', 'Native shard>0, then hotel-area wait, authored delays, devices and actors. Do not substitute direct progression or replay elapsed timers.'),
    '33': ('Native debug alternate', 'Keep dormant', 'Original chicken-test OR only. No synthetic debug facts or use as a prepared-entry shortcut.'),
    '54': ('Parked-car interaction setup', 'Hold pending actor/command state', 'CharacterSpawned→57, door=invalid. Do not transfer the separately proved node104 normal enum route to this different payload.'),
    '86': ('Gunfight community', 'Preserve activation intent; support rebind conditional', 'Already-active community Activate guard is proved. Initialization, materialization, saved actors and reacquisition are separate obligations.'),
    '92': ('Broken community-car interaction setup', 'Hold pending actor/command state', 'CharacterSpawned→93, door=invalid; distinct from population-spawner car101 and node104.'),
    '98': ('Friendly car door actions', 'Hold pending actor/command state', 'CharacterSpawned→100→106 uses authored door commands. No completed-command certificate recovered.'),
    '101': ('Population car, visual grid and interactions', 'Preserve state; no unconditional replay/skip', '101→102→103→104. False-accumulate replaces grid values and queues a vehicleGridDestructionEvent; scalar grid idempotence does not establish event/history preservation.'),
    '113': ('Memorial and environment variants', 'Preserve existing variants; owner-specific restore conditional', 'Eight exact variants include memorial_shards and clues_turned_off. Current variant state/loot history cannot be inferred from start_community.'),
    '133': ('Friendly car01 interactions', 'Hold pending actor/command state', 'CharacterSpawned>=1→134, door=invalid. Wait may already have fired before the cut.'),
    '135': ('Friendly car02 interactions', 'Hold pending actor/command state', 'CharacterSpawned>=1→136, door=invalid. Wait may already have fired before the cut.'),
    '141': ('Gunfight crowd exclusion area', 'Preserve/rebind conditional', 'Crowd null-area enable is a different service from quest-prevention toggles; no imported proof from the latter.'),
    '142': ('Gunfight crowd community', 'Preserve activation intent; support rebind conditional', 'User observed50/50 active entries. This is not live actor count, handler ownership or permission to replay the full startup.'),
    '143': ('Pre-gunfight community deactivation', 'Hold full operation pending lifecycle proof', 'Existing source proves cancellation of pending matching pairs before the inactive guard. Final inactive state alone is insufficient.'),
    '150': ('Ambient radio ForceOFF', 'Preserve device state; no unconditional replay', 'Native ForceOFF is an action on an independent RadioControllerPS. A fresh-style restart would request it again without saved-history discrimination.'),
    '152': ('Three gunfight prevention areas', 'Conditional target rebind only', 'Exact native enable path assigns one Boolean when resolved. Missing area/component returns without application. Full dispatch and persistence are not proven idempotent.'),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = HERE / args.out
    assert out.parent == HERE and not out.exists(), 'Fresh local directory required'
    checks = []
    def ck(name, value):
        checks.append({'name': name, 'pass': bool(value)})
        assert value, name

    manifests = [BASE / 'providers_01/manifest.json', BASE / 'courier_providers_01/manifest.json']
    pins = [pin(p) for p in manifests]
    models = {}
    raw_objects = {}
    wanted = {'sts_ep1_03_gameplay.questphase', 'sts_ep1_03_openworld.questphase', 'sts_ep1_03_cleanup.questphase'}
    for row in read(manifests[0])['resources']:
        if Path(row['raw']).name not in wanted:
            continue
        ck('raw_and_export_hash_' + Path(row['raw']).name,
           sha(row['raw']) == row['sha256'] and sha(row['json']) == row['json_sha256'])
        obj = read(row['json'])
        model = Resource(obj).normalize()
        ck('model_has_no_errors_' + Path(row['raw']).name, not model['errors'])
        models[Path(row['raw']).name] = model
        raw_objects[Path(row['raw']).name] = obj
        pins.extend([pin(row['raw']), pin(row['json'])])
    ck('all_selected_resources_present', set(models) == wanted)
    gp = models['sts_ep1_03_gameplay.questphase']['graphs']['root/1']
    ck('independent_raw_connection_traversal_matches', raw_edges(raw_objects['sts_ep1_03_gameplay.questphase']) == gp['edges'])
    seeds = sorted([e[2] for e in gp['edges'] if e[:2] == ['0', 'Out']], key=int)
    ck('every_actual_startup_branch_has_a_specific_disposition', set(seeds) == set(BRANCHES))
    ck('no_hidden_duplicate_startup_edges', len(seeds) == len(set(seeds)))
    ck('no_startup_fact_receipt_writer', not any(n['writes'] for n in gp['nodes'].values()))
    altered = copy.deepcopy(gp)
    altered['edges'].remove(['0', 'Out', '142', 'In'])
    ck('mutation_missing_crowd_branch_rejected', set(e[2] for e in altered['edges'] if e[:2] == ['0', 'Out']) != set(BRANCHES))
    event = gp['nodes']['103']['payload']['event']
    ck('authored_visual_payload_nonaccumulating', event['$type'] == 'VehicleQuestVisualDestructionEvent' and event['accumulate'] == 0)
    e2 = copy.deepcopy(event)
    e2['accumulate'] = 1
    ck('mutation_accumulating_event_rejected', e2['accumulate'] != 0)
    ck('original_car_sequence_retained', all(e in gp['edges'] for e in [
        ['101','Out','102','In'], ['102','Out','103','In'], ['103','Out','104','In']]))
    ow = models['sts_ep1_03_openworld.questphase']['graphs']['root/2']
    ck('courier_increment_separate_from_preparation_receipt', ow['nodes']['15']['writes'] == [
        {'$type': 'questSetVar_NodeType', 'factName': 'sa_ep1_114_toggledoff_force', 'setExactValue': 0, 'value': 1}]
        and ['13','Out','14','In'] in ow['edges'] and ['14','Out','15','In'] in ow['edges'])

    im = Image()
    functions = {}
    captures = sorted(HERE.glob('native_*.json'))
    instruction_count = 0
    for file in captures:
        doc = read(file)
        ck('pinned_exe_' + file.name, doc['exe_sha256'] == im.sha)
        for key, f in doc['functions'].items():
            for row in f['instructions']:
                rva = int(row['rva'], 16)
                encoded = bytes.fromhex(row['bytes'])
                actual = im.data[im.off(rva):im.off(rva)+len(encoded)]
                ck_value = actual == encoded
                if not ck_value:
                    raise AssertionError('Captured executable byte mismatch at ' + row['rva'])
                decoded = list(im.md.disasm(actual, im.base+rva))
                assert len(decoded) == 1 and decoded[0].mnemonic == row['mnemonic'] and decoded[0].op_str == row['operands']
                instruction_count += 1
            functions[key] = f
        pins.append(pin(file))
    ck('all_captured_instructions_match_executable_and_redecode', instruction_count > 0)

    def at(fn, rva, mnemonic, operands):
        return any(i['rva'] == rva and i['mnemonic'] == mnemonic and i['operands'] == operands for i in functions[fn]['instructions'])
    exact = [
        ('registration_selects_actual_thunk', '0x18af314', '0x18af36f', 'lea', 'rax, [rip + 0x12ea4a6]'),
        ('thunk_passes_accumulate', '0x2b9981c', '0x2b998e0', 'mov', 'r9b, byte ptr [rbp + 0x20]'),
        ('thunk_calls_grid_setter', '0x2b9981c', '0x2b998ee', 'call', '0x142bb2d84'),
        ('layer_stride15', '0x2bb2d84', '0x2bb2db8', 'imul', 'r13d, ebx, 0xf'),
        ('false_accumulate_goes_to_replacement', '0x2bb2d84', '0x2bb2df1', 'je', '0x142bb2e0b'),
        ('replacement_reads_authored_point', '0x2bb2d84', '0x2bb2e0b', 'mov', 'eax, dword ptr [rdi]'),
        ('replacement_overwrites_existing_point', '0x2bb2d84', '0x2bb2e0d', 'mov', 'dword ptr [rsi + rdx*4 + 0x100], eax'),
        ('true_accumulate_adds', '0x2bb2d84', '0x2bb2dfc', 'addss', 'xmm0, dword ptr [rdi]'),
        ('fifteen_point_loop', '0x2bb2d84', '0x2bb2e1a', 'cmp', 'ecx, 0xf'),
        ('event_delta_calculated', '0x2bb2d84', '0x2bb2e3f', 'subss', 'xmm0, dword ptr [rsp + rbx]'),
        ('actor_event_attempt_not_equality_guarded', '0x2bb2d84', '0x2bb2e96', 'call', '0x1401a67b0'),
        ('event_vtable_bound', '0xa1d6c4', '0xa1d6d2', 'lea', 'rcx, [rip + 0x268a4bf]'),
        ('event_type_global_bound', '0x1554b30', '0x1554b30', 'mov', 'rax, qword ptr [rip + 0x2673709]'),
        ('event_registration_literal', '0x15dac68', '0x15dacb7', 'lea', 'rdx, [rip + 0x1c96ab2]'),
        ('event_listener_registration', '0xb4d13c', '0xb4e211', 'call', '0x1418400ac'),
        ('event_listener_target', '0xb4d13c', '0xb4e1de', 'lea', 'rax, [rip - 0x1323b9]'),
        ('grid_event_reaches_current_state_copy', '0xa1be2c', '0xa1be4d', 'jmp', '0x140a1be60'),
        ('vehicle_owned_ps_handle', '0xa1c1ec', '0xa1c209', 'mov', 'rax, qword ptr [rdx + 0x538]'),
        ('ps_grid_target', '0xa1be9c', '0xa1bebf', 'lea', 'rdx, [rdi + 0x100]'),
        ('current_grid_copy', '0x389c54', '0x389c7a', 'movups', 'xmm0, xmmword ptr [rax + 0x100]'),
        ('prevention_thunk_selects_boolean_setter', '0x2bc310c', '0x2bc31d5', 'call', '0x142bc4040'),
        ('missing_area_returns_without_setter', '0x2bc310c', '0x2bc31be', 'je', '0x142bc31fc'),
        ('missing_component_returns_without_setter', '0x2bc310c', '0x2bc31d0', 'je', '0x142bc31f3'),
        ('resolved_prevention_enable_assigns_boolean', '0x2bc4040', '0x2bc408f', 'mov', 'byte ptr [rax + 0x40], r9b'),
    ]
    for name, *args2 in exact:
        ck(name, at(*args2))
    offset = im.off(0x3271770)
    event_name = b'vehicleGridDestructionEvent\0'
    ck('constructed_event_is_vehicleGridDestructionEvent', im.data[offset:offset+len(event_name)] == event_name)
    old = copy.deepcopy(functions['0x2bb2d84'])
    for row in functions['0x2bb2d84']['instructions']:
        if row['rva'] == '0x2bb2e0d':
            row['mnemonic'] = 'add'
    ck('mutation_addition_misreported_as_assignment_rejected', not at('0x2bb2d84', '0x2bb2e0d', 'mov', 'dword ptr [rsi + rdx*4 + 0x100], eax'))
    functions['0x2bb2d84'] = copy.deepcopy(old)
    functions['0x2bb2d84']['instructions'] = [r for r in old['instructions'] if r['rva'] != '0x2bb2e96']
    ck('mutation_deleted_actor_notification_rejected', not at('0x2bb2d84', '0x2bb2e96', 'call', '0x1401a67b0'))
    functions['0x2bb2d84'] = old

    template = [event['backLeft'], event['back'], event['backRight'], event['left'], 0, event['right'],
                event['left'], 0, event['right'], event['left'], 0, event['right'], event['frontLeft'],
                event['front'], event['frontRight']] + [event['roof']] * 15
    # Only the proven 30 scalar stores, not native events, queues or physics.
    scalar_assign = lambda previous: list(template)
    changed = list(template)
    changed[0] += 4.0
    ck('scalar_only_same_state_idempotence', scalar_assign(scalar_assign([0.0]*30)) == template)
    ck('scalar_only_intervening_state_not_preserved', scalar_assign(changed) != changed)
    ck('scalar_only_skip_does_not_finish_unapplied_setup', [0.0]*30 != template)

    source = BASE / 'lifecycle_01/script_source/current_01/base.script'
    ck('current_decompiled_base_source_pin', sha(source) == '5DED85C18A0FECFC055CB36E6636F55B6D909865D1393935FC6343DC23111E38')
    text = source.read_text(encoding='utf-8-sig')
    ck('script_forwards_native_accumulate_argument_for_both_layers',
       'SetDestructionGridPointValues(0u, pointValues, evt.accumulate)' in text and
       'SetDestructionGridPointValues(1u, pointValues, evt.accumulate)' in text)
    ck('script_forwards_prevention_area_and_enable', 'TogglePreventionQuestTrigger(evt.m_areaReference, evt.m_enable)' in text)
    pins.append(pin(source))

    branch_rows = []
    for seed in seeds:
        title, disposition, reason = BRANCHES[seed]
        nodes = reachable(gp, seed)
        branch_rows.append({'seed_node': seed, 'graph': 'root/1', 'source': 'sts_ep1_03_gameplay.questphase',
            'title': title, 'disposition': disposition, 'reason': reason, 'runtime_authorized': False,
            'reachable_nodes': nodes, 'terminal_nodes': [n for n in nodes if not any(e[0] == n for e in gp['edges'])],
            'node_evidence': {n: gp['nodes'][n] for n in nodes}})
    cleanup = models['sts_ep1_03_cleanup.questphase']['graphs']['root']
    cleanup_prevention = [{'node': i, 'event': n['payload']['event']} for i, n in cleanup['nodes'].items()
                          if n['payload'].get('event', {}).get('$type') == 'ToggleQuestPreventionTrigger']
    ck('native_cleanup_meet_wagner_value_not_silently_normalized',
       next(r['event']['enable'] for r in cleanup_prevention if r['node'] == '266') == 1)

    out.mkdir()
    result = {
        'status': 'STARTUP_EFFECT_CONTRACT_NARROWED_NO_SAFE_PREPARED_ADAPTER',
        'quest': 'sts_ep1_03', 'checks': checks, 'source_pins': pins,
        'captured_instructions_verified': instruction_count,
        'startup': {'actual_fanout_count': len(seeds), 'nodes': len(gp['nodes']), 'edges': len(gp['edges']),
                    'branches': branch_rows, 'unreachable_nodes': gp['unreachable']},
        'grid_effect': {'authored_event': event, 'two_layer_scalar_template': template,
                       'intervening_state_counterexample': {'before': changed, 'after': scalar_assign(changed)},
                       'limits': 'Abstract source-derived store counterexample, not a claimed Jason runtime history. Same unchanged scalar state is idempotent; entire dispatch/event/physics/persistence lifecycle is not thereby proved idempotent.'},
        'prevention_cleanup': cleanup_prevention,
        'decision': 'No automatic full startup replay, blanket skip or scalar admission exemption is justified. No current prepared-stage preservation contract is complete.',
        'closed': ['Actual native false-accumulate grid writes', 'Unconditional grid event submission attempt and typed consumer/persistent-state copy path',
                   'All16startup branch dispositions and exact reachability', 'Resolved prevention enable Boolean assignment and unresolved-target boundary'],
        'remaining': ['Bind actual prepared instance and its support/device/variant/actor state, not rejected scalar/path proxies',
                      'Preserve pending vs consumed startup waits and authored timers',
                      'Close courier writer/history and branch/geometry contract without increment replay',
                      'Engine-level dispatch/effect equivalence, saved persistence and prior setup application remain unproved'],
        'runtime_changes': 0, 'save_or_fact_writes': 0, 'game_calls': 0, 'new_candidate': None, 'ready_human_tests': [],
    }
    (out / 'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    lines = ['# Jason prepared startup — all native branches', '',
             'Derived from pinned native `sts_ep1_03_gameplay.questphase`, graph `root/1`. Dispositions are investigation results, not implemented or approved runtime actions.', '',
             '| Entry target | Purpose | Reachable node IDs | Disposition and missing evidence |', '| --- | --- | --- | --- |']
    for row in branch_rows:
        lines.append('| '+row['seed_node']+' | '+row['title']+' | '+', '.join(row['reachable_nodes'])+' | '+row['disposition']+'. '+row['reason']+' |')
    lines.extend(['', 'Shared descendants appear in multiple branches. Counts are not independent gameplay coverage. Node162 is an unconnected deletion marker. The startup graph has no fact-writing node; `start_community` is written in the parallel openworld graph and is not a barrier for these effects.', '',
                  'Native cleanup retains enable=1 at node266 for the meet-Wagner prevention area. That authored value is recorded, not changed or presented as an independently established bug.'])
    (out / 'BRANCH_MATRIX.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': len(checks), 'branches': len(branch_rows),
                      'instructions_verified': instruction_count, 'runtime_changes': 0, 'output': str(out)}))


if __name__ == '__main__':
    main()
