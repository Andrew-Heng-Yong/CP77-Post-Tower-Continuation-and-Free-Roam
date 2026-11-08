"""Bind captured save registrations to authored Jason nodes, without opening a save."""
from collections import defaultdict
from pathlib import Path
import argparse
import base64
import hashlib
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
QR15 = HERE.parent
WORK = HERE.parents[2]
sys.path[:0] = [str(WORK / 'tools/parity_audit'), str(QR15 / 'event_stage_01'),
                str(QR15 / 'saved_graph_state_01/inspector_review_01')]
from model import Resource
from analyze_components import decode_paths, phase_hash
from analyze_native_layout import cname, native_records
from validate_root_array import decode as decode_resource_array
from inspect_native import Image

ROOT_DEPOT = 'ep1\\quest\\ep1.quest'
ANCESTRY = (0, 10, 5, 2, 50, 19)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def pin(path, expected=None):
    actual = hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()
    if expected is not None and expected != actual:
        raise ValueError(f'Hash mismatch: {path}')
    return {'path': str(Path(path).resolve()), 'sha256': actual}


def source_bindings():
    manifests = [QR15 / 'root_binding_providers_01/manifest.json', QR15 / 'providers_01/manifest.json']
    resources = {r['depot']: r for p in manifests for r in read(p)['resources']}
    models = {}
    sources = []
    history_roots = [WORK / 'research/gig_restoration/rollout_r2/native_sources/raw',
                     WORK / 'research/sidejobs_s29/native_01/ep1_2_gamedata/raw']

    def model(depot):
        if depot not in models:
            row = resources[depot]
            raw = pin(row['raw'], row['sha256'])
            export = pin(row['json'], row['json_sha256'])
            model = Resource(read(row['json'])).normalize()
            if model['errors']:
                raise ValueError(model['errors'])
            models[depot] = model
            older = []
            for folder in history_roots:
                source = folder / depot
                if source.is_file():
                    saved = pin(source)
                    older.append({**saved, 'matches_current': saved['sha256'] == raw['sha256']})
            sources.append({'depot': depot, 'raw': raw, 'export': export, 'retained_donors': older})
        return models[depot]

    def trace(hops):
        depot, graph, path = ROOT_DEPOT, 'root', (1,)
        steps = []
        for index in hops:
            parent = model(depot)
            node = parent['graphs'][graph]['nodes'][str(index)]
            if node['type'] != 'questPhaseNodeDefinition':
                raise ValueError('Authored phase ancestry changed')
            steps.append({'depot': depot, 'graph': graph, 'path': path, 'node': index,
                          'type': node['type'], 'saved_type': node['type']})
            path += (index,)
            inline = graph + f'/{index}'
            external = node['refs']
            if len(external) == 1 and inline not in parent['graphs']:
                depot, graph = external[0], 'root'
            elif not external and inline in parent['graphs']:
                graph = inline
            else:
                raise ValueError('Ambiguous inline/external phase binding')
        return steps, depot, graph, path

    queries = {}
    for label, hops, target_nodes in [('openworld', ANCESTRY + (6, 2), {'approach': 3, 'courier': 14}),
                                       ('gameplay', ANCESTRY + (5, 1), {'vehicle': 102})]:
        steps, depot, graph, path = trace(hops)
        if not depot.endswith(f'03_{label}.questphase'):
            raise ValueError('Unexpected Jason leaf phase')
        for step in steps:
            key = f"owner:{'/'.join(map(str, step['path']))}:{step['node']}"
            queries[key] = step
        for role, index in target_nodes.items():
            node = model(depot)['graphs'][graph]['nodes'][str(index)]
            if node['type'] != 'questPauseConditionNodeDefinition':
                raise ValueError('Authored wait changed')
            condition = node['payload']['condition']
            expected = {'approach': 'questLogicalCondition', 'courier': 'questTriggerCondition',
                        'vehicle': 'questVehicleCondition'}[role]
            if condition['$type'] != expected:
                raise ValueError('Wait has a different condition type')
            # VehicleCondition further delegates the CName to its selected subtype.
            saved_type = condition['type']['$type'] if role == 'vehicle' else expected
            if role == 'vehicle' and saved_type != 'questVehicleSpawned_ConditionType':
                raise ValueError('Unexpected vehicle subtype')
            queries[role] = {'depot': depot, 'graph': graph, 'path': path, 'node': index,
                             'type': node['type'], 'saved_type': saved_type}
    contexts = {}
    for suffix in ((), (5,), (5, 1), (6,), (6, 2)):
        _, depot, graph, path = trace(ANCESTRY + suffix)
        contexts[path] = (depot, graph, model(depot)['graphs'][graph]['nodes'])
    expected_roots = [int(resources[depot]['key']) for depot in ['base\\quest\\cyberpunk2077.quest', ROOT_DEPOT]]
    return queries, contexts, sources, expected_roots


def check_native_wait_tokens():
    image = Image()
    slot_links = [(0x32B6010, 0xD8, 0x3524C0), (0x30476E8, 0x180, 0x35110C),
                  (0x32B2830, 0xD8, 0x1C2B88), (0x302C360, 0x118, 0x35187C),
                  (0x3695350, 0xD8, 0x1C21B8), (0x302BC80, 0x118, 0x35187C),
                  (0x3692680, 0xD8, 0xEE2A1C), (0x31376F8, 0x118, 0x35112C),
                  (0x31376F8, 0x170, 0x350D50)]
    for table, offset, expected in slot_links:
        pointer, = struct.unpack_from('<Q', image.data, image.off(table) + offset)
        if pointer - image.base != expected:
            raise ValueError('Native wait class slot changed')
    operations = {
        0x35110C: [(0x351112, 'mov', 'rcx, qword ptr [rcx + 0x48]'),
                   (0x35111C, 'call', 'qword ptr [rax + 0x118]')],
        0x35187C: [(0x351888, 'call', 'qword ptr [rax + 8]'), (0x35188B, 'mov', 'rcx, qword ptr [rax + 0x18]')],
        0x35112C: [(0x35113D, 'call', 'qword ptr [rax + 0x170]'), (0x351150, 'call', 'qword ptr [rax + 8]'),
                   (0x351153, 'mov', 'rcx, qword ptr [rax + 0x18]')],
        0x350D50: [(0x350D50, 'mov', 'rax, qword ptr [rcx + 0x30]')],
    }
    evidence = []
    for function, assertions in operations.items():
        instructions = {int(i['rva'], 16): i for i in image.disasm(function)['instructions']}
        for rva, mnemonic, operands in assertions:
            row = instructions[rva]
            if (row['mnemonic'], row['operands']) != (mnemonic, operands):
                raise ValueError(f'Native wait token contract changed at {rva:#x}')
            evidence.append(row)
    # Bind class registration literals and final concrete instance tables.
    constructors = [('questPauseConditionNodeDefinition', 0x32B5FE8, 0x3524C0, 0x352507, 0x30476E8),
                    ('questLogicalCondition', 0x32B2818, 0x1C2A9C, 0x1C2AE0, 0x302C360),
                    ('questTriggerCondition', 0x3270230, 0x1C21C0, 0x1C21EF, 0x302BC80),
                    ('questVehicleCondition', 0x3270480, 0xEE2A1C, 0xEE2A4B, 0x31376F8)]
    for name, string_rva, constructor, lea_rva, instance_table in constructors:
        literal = name.encode() + b'\0'
        offset = image.off(string_rva)
        if image.data[offset:offset + len(literal)] != literal:
            raise ValueError('Native class literal changed')
        item, = (i for i in image.disasm(constructor)['instructions'] if int(i['rva'], 16) == lea_rva)
        encoded = bytes.fromhex(item['bytes'])
        if encoded[:3] != b'\x48\x8d\x05' or lea_rva + len(encoded) + struct.unpack('<i', encoded[3:])[0] != instance_table:
            raise ValueError('Native constructor does not bind the expected instance table')
        evidence.append(item)
    return {'exe_sha256': image.sha, 'slot_links': slot_links, 'instructions': evidence,
            'classes': [name for name, *_ in constructors]}


def address_matches(records, path, node, kind):
    return [(i, row) for i, row in enumerate(records) if row == (cname(kind), phase_hash(path), node)]


def analyze_blocks(paths, records, queries, contexts):
    registered = defaultdict(set)
    for path in paths:
        if path:
            registered[phase_hash(path)].add(path)
    hits = {}
    for role, target in queries.items():
        path = target['path']
        context = phase_hash(path)
        if registered[context] - {path}:
            raise ValueError(f'Collision or unexpected phase path for {role}')
        address_rows = [(i, row) for i, row in enumerate(records) if row[1:] == (context, target['node'])]
        typed_rows = address_matches(records, path, target['node'], target['saved_type'])
        if address_rows != typed_rows or len(typed_rows) > 1 or (typed_rows and path not in registered[context]):
            raise ValueError(f'Unbound or type-mismatched registration for {role}')
        hits[role] = {'path_in_catalog': path in registered[context],
                      'phase_hash_u32': context, 'saved_slot_ordinals': [i for i, _ in typed_rows]}
    descendant_paths = sorted(p for p in set(paths) if p[:7] == (1,) + ANCESTRY)
    descendant_hashes = {phase_hash(p) for p in descendant_paths}
    if any(len(registered[key]) != 1 for key in descendant_hashes):
        raise ValueError('A Jason descendant hash is ambiguous')
    descendants = []
    for ordinal, (token, key, index) in enumerate(records):
        if key not in descendant_hashes:
            continue
        path, = registered[key]
        depot, graph, nodes = contexts[path]
        node = nodes[str(index)]
        saved_type = node['type']
        if saved_type == 'questPauseConditionNodeDefinition':
            condition = node['payload']['condition']
            saved_type = condition['$type']
            if saved_type in ('questVehicleCondition', 'questCharacterCondition', 'questFactsDBCondition'):
                saved_type = condition['type']['$type']
        if token != cname(saved_type):
            raise ValueError(f'Unexpected descendant token at {depot}:{graph}:{index}')
        descendants.append({'slot': ordinal, 'path': path, 'depot': depot, 'graph': graph, 'node': index,
                            'definition': node['type'], 'saved_type': saved_type,
                            'saved_token': hex(token), 'node_refs': node['node_refs'], 'reads': node['reads']})
    return {'paths': len(paths), 'slots': len(records), 'queries': hits,
            'jason_interned_paths': descendant_paths,
            'jason_descendant_slot_count': len(descendants), 'jason_descendant_slots': descendants}


def decode_blocks(capture):
    path = capture['components']['customArray']
    event = capture['components']['eventManager']
    _, paths = decode_paths(base64.b64decode(path['base64'], validate=True), path['id'])
    events = native_records(base64.b64decode(event['base64'], validate=True), event['id'])
    return paths, events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = HERE / args.out
    if out.parent != HERE or out.exists():
        raise ValueError('Use a fresh output directory alongside this script')
    queries, contexts, sources, roots = source_bindings()
    native_wait_types = check_native_wait_tokens()
    earlier = []
    captures = sorted((HERE / 'capture_01').glob('*.json')) + sorted((HERE / 'capture_02').glob('*.json'))
    if len(captures) != 7:
        raise ValueError('Expected the seven exact captured bodies')
    for path in captures:
        row = read(path)
        if not row['unchanged'] or row['offset_id_checks'] != 14:
            raise ValueError('Incomplete capture provenance')
        if decode_resource_array(base64.b64decode(row['resource_array_base64'], validate=True)) != roots:
            raise ValueError('This save uses a different resource root index binding')
        paths, records = decode_blocks(row)
        earlier.append({**{k: v for k, v in row.items() if k not in ('components', 'resource_array_base64')},
                        'capture': pin(path), 'registered': analyze_blocks(paths, records, queries, contexts)})

    comparison_folder = QR15 / 'event_stage_01/components_01'
    comparison = read(comparison_folder / 'manifest.json')
    gap = QR15 / 'root_saved_resource_array_01/facts_to_custom_array.bin'
    if decode_resource_array(gap.read_bytes()) != roots:
        raise ValueError('Historical comparison root binding changed')
    components = {r['name']: r for r in comparison['nodes']}
    comparison_data = {}
    comparison_pins = [pin(gap), pin(comparison_folder / 'manifest.json')]
    for key, decoder in [('customArray', decode_paths), ('eventManager', native_records)]:
        row = components[key]
        comparison_pins.append(pin(row['path'], row['sha256']))
        comparison_data[key] = decoder(Path(row['path']).read_bytes(), row['id'])
    post = analyze_blocks(comparison_data['customArray'][1], comparison_data['eventManager'], queries, contexts)

    # Exercise exact-width and type discrimination on a positive saved upstream owner.
    first = read(HERE / 'capture_01/manual09.json')
    _, records = decode_blocks(first)
    target = queries['owner:1:0']
    match, = address_matches(records, target['path'], target['node'], target['type'])
    ordinal, (kind, key, node) = match
    damaged = list(records)
    damaged[ordinal] = (kind, key, node | 0x10000)
    if address_matches(damaged, target['path'], target['node'], target['type']):
        raise AssertionError('Upper half alias was accepted')
    damaged[ordinal] = (kind ^ 1, key, node)
    if address_matches(damaged, target['path'], target['node'], target['type']):
        raise AssertionError('Wrong definition type was accepted')

    positive = [{k: r[k] for k in ('name', 'slot', 'timestamp', 'source_sha256')}
                for r in earlier if any(r['registered']['queries'][role]['saved_slot_ordinals']
                                        for role in ('approach', 'courier', 'vehicle'))]
    queue_path = HERE / 'capture_03/wa1backup16.json'
    queue_capture = read(queue_path)
    matched, = (r for r in earlier if r['name'] == 'wa1backup16')
    captured = read(matched['capture']['path'])
    if queue_capture['save_version'] != 277 or queue_capture['offset_id_checks'] != 15 or not queue_capture['unchanged']:
        raise ValueError('Unsupported QueuedData capture')
    for field in ('source_sha256', 'metadata_sha256', 'named_facts', 'resource_array_base64'):
        if queue_capture[field] != captured[field]:
            raise ValueError(f'Positive re-read does not match: {field}')
    for name in ('customArray', 'eventManager'):
        if queue_capture['components'][name] != captured['components'][name]:
            raise ValueError(f'Positive re-read does not match: {name}')
    queue = queue_capture['components']['QueuedData']
    queue_bytes = base64.b64decode(queue['base64'], validate=True)
    if queue_bytes != struct.pack('<IBI', queue['id'], 0, 0):
        raise ValueError('Nonempty quest queue requires a separate decoder')
    status = 'RETAINED_JASON_WAIT_REGISTRATIONS_FOUND' if positive else 'OLDER_SAVES_HAVE_NO_RETAINED_JASON_WAIT_REGISTRATIONS'
    result = {
        'status': status, 'earlier_bodies': earlier, 'positive_wait_bodies': positive,
        'native_query_bindings': queries, 'source_bindings': sources, 'native_wait_token_contract': native_wait_types,
        'root_resource_hashes': [str(i) for i in roots],
        'positive_body_quest_queue': {'capture': pin(queue_path), 'source_sha256': queue_capture['source_sha256'],
                                      'raw_hex': queue_bytes.hex(), 'resource_requests': 0, 'handler_notifications': 0},
        'post_ending_comparison': {'body_sha256': comparison['source_sha256'], 'pins': comparison_pins, 'registered': post},
        'controls': ['Full-width node ID rejects upper-half alias', 'Definition type rejects a wrong typed row'],
        'limits': ['Comparison is to the retained historical body. The exact blocked live save is still unbound.',
                   'Matching a retained typed registration identifies a restoration record. Its delivery and final actor effects are separate.',
                   'An absent registration is compatible with more than one past stage.',
                   'Older retained graph donor matches do not identify every provider mounted when a save was made.'],
        'runtime_candidate': None, 'save_writes': 0, 'game_calls': 0,
    }
    out.mkdir()
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': status, 'earlier_bodies': len(earlier), 'positive_wait_bodies': positive, 'output': str(out)}))


if __name__ == '__main__':
    main()
