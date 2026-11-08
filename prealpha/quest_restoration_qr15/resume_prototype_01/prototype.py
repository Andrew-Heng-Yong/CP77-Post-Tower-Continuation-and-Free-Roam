"""Read-only model of Jason's preparation-to-briefing seam.

The cursor cases are synthetic. This tool cannot read or resume a running quest.
"""
from dataclasses import dataclass
from pathlib import Path
import argparse
import base64
import hashlib
import json
import math
import struct
import sys


HERE = Path(__file__).resolve().parent
QR15 = HERE.parent
WORK = HERE.parents[2]
sys.path.insert(0, str(WORK / 'tools/parity_audit'))
sys.path.insert(0, str(QR15 / 'saved_graph_state_01'))
from model import Resource
from inspect_native import Image

PREPARATION = 'sts_ep1_03_start_community'
COURIER = 'sa_ep1_114_toggledoff_force'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def pin(path, expected=None):
    actual = sha(path)
    if expected is not None and actual != expected:
        raise ValueError(f'Source hash mismatch: {path}')
    return {'path': str(Path(path).resolve()), 'sha256': actual}


def graph_inputs():
    manifest = QR15 / 'providers_01/manifest.json'
    pins = [pin(manifest)]
    models = {}
    for role in ('phase', 'gameplay', 'openworld'):
        row, = (r for r in read(manifest)['resources'] if r['depot'].endswith(f'03_{role}.questphase'))
        pins.extend([pin(row['raw'], row['sha256']), pin(row['json'], row['json_sha256'])])
        model = Resource(read(row['json'])).normalize()
        if model['errors']:
            raise ValueError(model['errors'])
        models[role] = model
    return models, pins


def bind_seam(models):
    """Reject altered wiring before using the small transition model."""
    world = models['openworld']['graphs']
    start = world['root/2']
    native_edges = [
        ['0', 'Out', '13', 'In'], ['13', 'Out', '3', 'In'],
        ['13', 'Out', '12', 'In'], ['13', 'Out', '14', 'In'],
        ['3', 'Out', '4', 'In'], ['12', 'Out', '4', 'In'],
        ['14', 'Out', '15', 'In'], ['4', 'Out', '1', 'In'],
    ]
    if sorted(start['edges']) != sorted(native_edges):
        raise ValueError('Unexpected preparation-phase wiring')
    if start['nodes']['1']['payload']['type'] != 'Terminating':
        raise ValueError('The approach output no longer terminates its wait scope')
    if start['nodes']['15']['writes'] != [
        {'$type': 'questSetVar_NodeType', 'factName': COURIER, 'value': 1, 'setExactValue': 0}
    ]:
        raise ValueError('Courier writer no longer performs its authored increment')
    if start['nodes']['13']['writes'] != [
        {'$type': 'questSetVar_NodeType', 'factName': PREPARATION, 'value': 1, 'setExactValue': 1}
    ]:
        raise ValueError('Unexpected preparation writer')
    if start['nodes']['4']['payload']['type']['phase'] != 'DiscoveredPhase':
        raise ValueError('Unexpected approach marker transition')
    condition = start['nodes']['3']['payload']['condition']
    terms = condition['conditions']
    if condition['operation'] != 'AND' or len(terms) != 6:
        raise ValueError('Unexpected approach predicate')
    if terms[0]['type'] != 'IsInside' or terms[0]['isPlayerActivator'] != 1:
        raise ValueError('Unexpected player approach trigger')
    for term, state in zip(terms[1:3], ('Driving', 'Passenger'), strict=True):
        state_check = term['type']['subType']
        if (state_check['vehicleComparisonType'], state_check['vehicleState']) != ('NotEqual', state):
            raise ValueError('Unexpected vehicle prerequisite')
    effects = [term['type'] for term in terms[3:]]
    if [e['statusEffectID'] for e in effects] != [
        'GameplayRestriction.VehicleScene', 'GameplayRestriction.VehicleSceneFpp',
        'GameplayRestriction.VehicleSceneFppOnlyForward',
    ] or any(e['inverted'] != 1 or e['isPlayer'] != 1 for e in effects):
        raise ValueError('Unexpected status-effect prerequisite')
    courier_condition = start['nodes']['14']['payload']['condition']
    if courier_condition['type'] != 'IsInside' or courier_condition['isPlayerActivator'] != 1:
        raise ValueError('Unexpected courier trigger')

    for graph, edges in (
        (world['root'], [['2', 'Out1', '3', 'In1'], ['2', 'Out1', '4', 'In1']]),
        (world['root/4'], [['0', 'Out', '153', 'In'], ['153', 'False', '154', 'In'],
                           ['154', 'True', '129', 'Start 0'], ['154', 'False', '45', 'Active'],
                           ['153', 'True', '155', 'In1'], ['155', 'Out1', '45', 'Active']]),
        (models['gameplay']['graphs']['root/1'], [['101', 'Out', '102', 'In'],
                                                ['102', 'Out', '103', 'In'], ['103', 'Out', '104', 'In']]),
    ):
        if any(edge not in graph['edges'] for edge in edges):
            raise ValueError('A native continuation edge is missing')
    briefing = world['root/4']['nodes']
    if briefing['153']['payload']['condition']['type']['groupName']['$value'] != 'fixer_briefs_and_debriefs':
        raise ValueError('Unexpected phone mute group')
    if briefing['154']['payload']['condition']['type']['isContentBlocked'] != 0:
        raise ValueError('Unexpected content gate')
    scene, = briefing['129']['refs']
    if not scene.endswith('sts_ep1_03_holocal_prebrief.scene'):
        raise ValueError('Unexpected prebrief scene')
    if briefing['45']['journal_paths'] != ['contacts/mr_hands/sts_ep1_03/brief']:
        raise ValueError('Unexpected brief journal path')
    return {
        'approach_ref': terms[0]['triggerAreaRef']['$value'],
        'courier_ref': courier_condition['triggerAreaRef']['$value'],
        'required_prefabs': models['phase']['root_prefabs'],
        'prebrief_scene': scene,
        'prebrief_marker': briefing['129']['node_refs'],
        'marker_notification': start['nodes']['4']['payload']['type']['notifyUI'],
        'brief_message': briefing['45']['journal_paths'][0],
    }


def verify_native():
    """Keep the inspected slices and check the opcodes the model depends on."""
    image = Image()
    checks = {
        # Instance serializer reads four bytes, 16 per point, then the height.
        0x45E9F0: [(0x45EA10, 'mov', 'r8d, 4'), (0x45EA43, 'mov', 'r8d, 0x10'),
                   (0x45EA73, 'movss', 'dword ptr [rax + rcx*4 + 8], xmm2'),
                   (0x45EA81, 'lea', 'rdx, [r14 + 0x40]'), (0x45EA85, 'mov', 'r8d, 4')],
        0x70D15C: [(0x70D1C5, 'add', 'rax, 0xc'), (0x70D1C9, 'movss', 'xmm0, dword ptr [rcx + 0x40]'),
                   (0x70D1DE, 'addps', 'xmm4, xmm3')],
        # The typed output path returns zero for Terminating, 2 for NonTerminating.
        0x2B393C: [(0x2B3A1A, 'call', '0x140cf95a0'), (0x2B3A8B, 'cmp', 'byte ptr [rsi + 0x50], bl'),
                   (0x2B3A90, 'xor', 'bl, bl'), (0x2B3A97, 'mov', 'bl, 2')],
        0x352984: [(0x352A10, 'call', '0x1402b393c'), (0x352A17, 'je', '0x140352a50'),
                   (0x352A73, 'mov', 'al, bl')],
        0x3528A4: [(0x35294F, 'call', '0x140352984')],
        0xBEBFCC: [(0xBEC064, 'call', '0x1403528a4'), (0xBEC069, 'mov', 'bl, al')],
        0xBEBEB8: [(0xBEBF50, 'call', '0x140bebfcc'), (0xBEBF57, 'je', '0x140bebf78'),
                   (0xBEBF95, 'call', '0x140bec890')],
        0xBEC890: [(0xBEC8A6, 'call', '0x1402b1d30'), (0xBEC8E7, 'call', '0x1401cafc4')],
    }
    slices = {}
    for address, expected in checks.items():
        actual = {int(i['rva'], 16): i for i in image.disasm(address)['instructions']}
        for rva, mnemonic, operands in expected:
            item = actual.get(rva)
            if item is None or (item['mnemonic'], item['operands']) != (mnemonic, operands):
                raise ValueError(f'Native instruction no longer matches at {rva:#x}')
        slices[hex(address)] = [actual[rva] for rva, _, _ in expected]
    serializer = struct.unpack_from('<Q', image.data, image.off(0x3058148) + 0x40)[0] - image.base
    if serializer != 0x45E9F0:
        raise ValueError('AreaShapeOutline instance serializer mismatch')
    for address, expected in ((0x315F408, b'AreaShapeOutline\0'), (0x326FE10, b'questOutputNodeDefinition\0')):
        offset = image.off(address)
        if image.data[offset:offset + len(expected)] != expected:
            raise ValueError('Native class name mismatch')
    return {'exe_sha256': image.sha, 'outline_serialize_slot': hex(serializer), 'instruction_slices': slices}


def decode_outline(buffer):
    raw = base64.b64decode(buffer, validate=True)
    count, = struct.unpack_from('<I', raw)
    if count < 3 or len(raw) != 8 + count * 16:
        raise ValueError('Invalid cooked AreaShapeOutline size')
    points = list(struct.iter_unpack('<4f', raw[4:-4]))
    height, = struct.unpack_from('<f', raw, len(raw) - 4)
    if not math.isfinite(height) or height <= 0:
        raise ValueError('Invalid cooked AreaShapeOutline height')
    if not all(all(math.isfinite(v) for v in p) and p[3] == 1 for p in points):
        raise ValueError('Unexpected cooked point layout')
    return [p[:3] for p in points], height


def load_volumes(seam):
    folder = QR15 / 'runtime_probe_01/car_binding_review_01'
    evidence_path = folder / 'binding_evidence.json'
    evidence = read(evidence_path)
    source = evidence['sector']
    pins = [pin(evidence_path), pin(source['raw'], source['sha256']), pin(source['json'], source['json_sha256'])]
    for key in ('actual_setup_bytes', 'layout_source'):
        row = evidence[key]
        pins.append(pin(row['path'], row['sha256']))
    binding_path = folder / 'binding_02/result.json'
    bindings = read(binding_path)
    pins.append(pin(binding_path))
    sector = read(source['json'])['Data']['RootChunk']
    setup = Path(evidence['actual_setup_bytes']['path']).read_bytes()
    prefab = evidence['descriptor']['descriptor']['questPrefabNodeRef']['$value']
    volumes = {}
    for role in ('approach', 'courier'):
        alias = seam[f'{role}_ref']
        full_ref = f'{prefab}/{alias}'
        item, = (b for b in bindings['setups'] if b['full_ref'] == full_ref)
        off = item['datum'] * 0x90
        index = struct.unpack_from('<Q', setup, off + 0x70)[0] & 0x7FFFF
        identity, = struct.unpack_from('<Q', setup, off + 0x58)
        if index != item['actual_node_index'] or str(identity) != item['globalNodeID']:
            raise ValueError('Trigger setup identity mismatch')
        node = sector['nodes'][index]['Data']
        if node['$type'] != 'worldTriggerAreaNode' or node['debugName']['$value'] != '{' + alias[1:] + '}':
            raise ValueError('Trigger type or binding mismatch')
        outline = node['outline']['Data']
        if outline['$type'] != 'AreaShapeOutline':
            raise ValueError('Unexpected outline type')
        points, height = decode_outline(outline['buffer'])
        position = struct.unpack_from('<3f', setup, off)
        rotation = struct.unpack_from('<4f', setup, off + 0x10)
        scale = struct.unpack_from('<3f', setup, off + 0x20)
        if rotation[:2] != (0, 0) or scale != (1, 1, 1) or not math.isclose(math.hypot(*rotation), 1, abs_tol=1e-6):
            raise ValueError('The yaw-invariant bound requires unit scale and no tilt')
        volumes[role] = {'full_ref': full_ref, 'node': index, 'global_id': str(identity), 'position': position,
                         'rotation': rotation, 'scale': scale, 'points': points, 'height': height,
                         'outline_buffer': outline['buffer']}
    return volumes, pins


def enclosure(volumes):
    """Use an inner disk and an outer disk, so yaw conventions cannot affect inclusion."""
    outer, inner = volumes['courier'], volumes['approach']
    polygon = outer['points']
    distances = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1], strict=True):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length == 0 or any(dx * (p[1] - a[1]) - dy * (p[0] - a[0]) < -1e-6 for p in polygon):
            raise ValueError('Courier outline must be convex and counterclockwise')
        distances.append((dy * a[0] - dx * a[1]) / length)
    courier_radius = min(distances)
    approach_radius = max(math.hypot(p[0], p[1]) for p in inner['points'])
    offset = math.dist(outer['position'][:2], inner['position'][:2])
    z_ranges = {}
    for role, volume in volumes.items():
        levels = {p[2] for p in volume['points']}
        if len(levels) != 1:
            raise ValueError('Expected planar trigger outline')
        low = volume['position'][2] + levels.pop()
        z_ranges[role] = (low, low + volume['height'])
    lo, hi = z_ranges['approach']
    outer_lo, outer_hi = z_ranges['courier']
    margin = courier_radius - approach_radius - offset
    return {'courier_inner_disk': courier_radius, 'approach_outer_disk': approach_radius,
            'origin_distance_xy': offset, 'minimum_horizontal_clearance': margin,
            'z_ranges': z_ranges, 'strict_enclosure': margin > 0 and outer_lo < lo < hi < outer_hi}


@dataclass(frozen=True)
class Fixture:
    """Stage certificates here are supplied only by synthetic test cases."""
    same_instance: bool = False
    retired_original_owner: bool = False
    support_verified: bool = False
    approach_pending: bool = False
    other_startup_state_verified: bool = False
    car: str = 'unknown'
    courier: str = 'unknown'


def plan(fixture):
    missing = [name for name in ('same_instance', 'retired_original_owner', 'support_verified',
                                'approach_pending', 'other_startup_state_verified') if not getattr(fixture, name)]
    if fixture.car not in ('applied', 'waiting_at_102'):
        missing.append('car_effect_stage')
    if fixture.courier not in ('consumed', 'pending'):
        missing.append('courier_wait_stage')
    if missing:
        return {'status': 'DEFERRED', 'missing': missing, 'cursors': []}
    cursors = ['openworld/root/2:3.In']
    if fixture.courier == 'pending':
        cursors.append('openworld/root/2:14.In')
    if fixture.car == 'waiting_at_102':
        cursors.append('gameplay/root/1:102.In')
    return {'status': 'SYNTHETIC_CURSOR_PLAN', 'missing': [], 'cursors': cursors}


def run_trace(cursors, events, force_before):
    """Project ordered predicate completions through native edges up to first briefing.

    A predicate completion is a model input, never a generated quest receipt.
    The car branch is independent of the approach/courier ordering tested here.
    """
    approach = 'openworld/root/2:3.In' in cursors
    courier = 'openworld/root/2:14.In' in cursors
    car = 'gameplay/root/1:102.In' in cursors
    trace = []
    force = force_before
    for event in events:
        if event == 'courier_inside' and courier:
            trace.extend(['root/2:14.Out', 'root/2:15.increment'])
            force += 1
            courier = False
        elif event == 'vehicle_spawned' and car:
            trace.extend(['gameplay/root/1:102.Out', 'gameplay/root/1:103.dispatch', 'gameplay/root/1:104.dispatch'])
            car = False
        elif event in ('approach_qualified_call', 'approach_qualified_message') and approach:
            trace.extend(['root/2:3.Out', 'root/2:4.DiscoveredPhase', 'root/2:1.Terminating',
                          'root:2.Out1', 'root:3.In1', 'root:4.In1', 'root/4:153'])
            if event.endswith('_call'):
                trace.extend(['root/4:154.True', 'root/4:129.Start 0'])
            else:
                trace.extend(['root/4:154.False', 'root/4:45.Active'])
            approach = courier = False
    return {'force_before': force_before, 'force_after': force, 'ordered_trace': trace,
            'courier_wait_remaining': courier, 'car_wait_remaining': car}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = HERE / args.out
    if out.parent != HERE or out.exists():
        raise ValueError('Choose a fresh output directory alongside the prototype')
    models, pins = graph_inputs()
    seam = bind_seam(models)
    native = verify_native()
    volumes, more_pins = load_volumes(seam)
    geometry = enclosure(volumes)
    if not geometry['strict_enclosure']:
        raise ValueError('Cooked shapes do not meet the enclosure bound')
    snapshot_path = QR15 / 'analysis_01/snapshot.json'
    snapshot = read(snapshot_path)
    row, = (r for r in snapshot['rows'] if r['definition']['id'] == 'sts_ep1_03')
    selected = dict(zip(row['definition']['fact_names'], row['facts'], strict=True))
    if {k: v for k, v in selected.items() if v != 0} != {PREPARATION: 1} or set(row['states']) != {1}:
        raise ValueError('The historical prepared projection has changed')
    from test_prototype import check_cases
    checks, examples = check_cases(models, volumes)
    result = {
        'status': 'OFFLINE_CURSOR_MODEL_PASSES_ACTUAL_FIXTURE_DEFERRED',
        'seam': seam, 'native': native, 'geometry': geometry, 'volumes': volumes,
        'source_pins': pins + more_pins + [pin(snapshot_path), pin(HERE / 'prototype.py'), pin(HERE / 'test_prototype.py')],
        'checks': checks, 'synthetic_examples': examples,
        'historical_projection': {'origin': snapshot['origin'], 'fact_count': len(selected),
                                  'journal_count': len(row['states']), 'courier_in_projection': COURIER in selected,
                                  'plan': plan(Fixture())},
        'limits': ['Only strictly ordered predicate completions are modeled.',
                   'Cooked volume enclosure gives a geometric region, not a navigable gameplay path or delivery order.',
                   'The phone branch ends at the native scene or journal input. Delivery and further progression are outside the model.',
                   'Synthetic cursor inputs assume proof of other startup state. The actual fixture supplies no such proof.',
                   'Model traces are neither save-owner evidence nor executable quest commands.'],
    }
    out.mkdir()
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': len(checks), 'geometry': geometry, 'output': str(out)}))


if __name__ == '__main__':
    main()
