"""Compare the user-identified latest save with the earlier native approach fixture."""
from pathlib import Path
import argparse
import hashlib
import json
import stat
import sys

HERE = Path(__file__).resolve().parent
QR15 = HERE.parent
sys.path.insert(0, str(QR15 / 'lifecycle_01/save_community'))
from decode_full import decode_full

TARGET = 17433794865907239043
CURRENT_BODY = 'AE7331494F242FDCFA9008D86588F9C431B9ABA6092B7E9C845EE78D3D30CE9E'
CURRENT_METADATA = 'BF3131F582656050F4CAE2A860C93548C1CC4B506B6649B6C8B93D78A24A7D5E'
CURRENT_SLOT = Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\AutoSave-8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def pin(path, expected=None):
    path = Path(path)
    with path.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest().upper()
    if expected is not None and digest != expected:
        raise ValueError(f'Hash mismatch for {path}')
    return {'path': str(path.resolve()), 'sha256': digest}


def pin_save(path, expected):
    if any(p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT for p in (path, *path.parents)):
        raise ValueError(f'Linked save input: {path}')
    return pin(path, expected)


def fact_key(name):
    result = 0x811C9DC5
    for byte in name.encode():
        result = ((result ^ byte) * 0x01000193) & 0xFFFFFFFF
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = HERE / args.out
    if out.parent != HERE or out.exists():
        raise ValueError('Use a fresh output directory next to this script')
    current = [pin_save(CURRENT_SLOT / 'sav.dat', CURRENT_BODY), pin_save(CURRENT_SLOT / 'metadata.9.json', CURRENT_METADATA)]
    records_path = QR15 / 'earlier_saves_01/analysis_02/result.json'
    evidence = read(records_path)
    old, = (r for r in evidence['earlier_bodies'] if r['name'] == 'wa1backup16')
    post = evidence['post_ending_comparison']
    if post['body_sha256'] != CURRENT_BODY:
        raise ValueError('Previously decoded comparison belongs to a different body')
    for row in post['pins']:
        pin(row['path'], row['sha256'])
    fact_path = QR15 / 'stores_autosave8_01/facts.json'
    fact_capture = read(fact_path)
    if fact_capture['sha256'] != CURRENT_BODY or fact_capture['metadata_sha256'] != CURRENT_METADATA:
        raise ValueError('Fact capture does not match the identified save')
    named, = (table for table in fact_capture['tables'] if table['physical_child_ordinal'] == 1)
    facts = {int(row['key_u32']): row['value_u32'] for row in named['entries']}
    if len(facts) != len(named['entries']) or facts.get(fact_key('q307_ep1_killed')) != 1:
        raise ValueError('Named fact control failed')
    names = list(old['named_facts']) + [
        'q307_done', 'q307_finished', 'q307_ep1_killed', 'sts_ep1_03_start', 'sts_ep1_03_active',
        'sts_ep1_03_done', 'PTFRU9_sts_ep1_03_ParentEntered', 'PTFRU9_sts_ep1_03_Started',
    ]
    fact_comparison = {name: {'earlier': old['named_facts'].get(name), 'current': facts.get(fact_key(name))}
                       for name in names}

    car_path = HERE / 'car_capture_01/capture.json'
    car = read(car_path)
    if car['source_sha256'] != old['source_sha256'] or car['metadata_sha256'] != old['metadata_sha256'] or car['save_version'] != 277:
        raise ValueError('The earlier car component is from a different fixture or version')
    earlier = [pin_save(Path(car['source']), old['source_sha256']), pin_save(Path(car['metadata']), old['metadata_sha256'])]
    tail = pin(car['trailing_path'], car['trailing_sha256'])
    data = Path(tail['path']).read_bytes()
    keys = list(map(int, car['outer_keys']))
    if car['node_size'] != 8 + 8 * len(keys) + len(data):
        raise ValueError('Earlier community size mismatch')
    decoded = decode_full(data, keys)
    older_row = decoded['second_rows'].get(TARGET)
    if older_row is not None:
        older_row = {k: [str(x) for x in v] if k.startswith('array_') else v for k, v in older_row.items()}
    post_car_path = QR15 / 'lifecycle_01/save_community/decode_02/result.json'
    post_car = read(post_car_path)
    if post_car['source_save_sha256'] != CURRENT_BODY or int(post_car['target_global_node_id_u64']) != TARGET:
        raise ValueError('Post-ending community capture does not match')
    post_ps_path = QR15 / 'identity_01/save_inventory/capture_03/manifest.json'
    post_ps = read(post_ps_path)
    if post_ps['source_sha256'] != CURRENT_BODY:
        raise ValueError('Post-ending PS2 capture does not match')
    post_row = post_car['target_record']
    compare_fields = lambda row: {k: v for k, v in row.items() if k not in ('start_offset', 'end_offset')}

    result = {
        'status': 'USER_SELECTED_LATEST_SAVE_COMPARED_PREPARED_ADAPTER_DEFERRED',
        'selected_save': {'slot': 'AutoSave-8', 'timestamp_from_menu': '2026-11-04 00:30:56', 'inputs': current,
                          'selection': 'User identified the newest in-game save. The current file matches the previously decoded body.'},
        'earlier_comparison': {'slot': 'AutoSave-16', 'timestamp_from_menu': '2026-10-26 16:05:11', 'inputs': earlier},
        'facts': fact_comparison, 'missing_fact_value': 'null denotes no captured record',
        'registrations': {'earlier_jason_slots': old['registered']['jason_descendant_slot_count'],
                          'current_jason_slots': post['registered']['jason_descendant_slot_count'],
                          'earlier_approach': old['registered']['queries']['approach']['saved_slot_ordinals'],
                          'current_approach': post['registered']['queries']['approach']['saved_slot_ordinals']},
        'car': {'global_node_id': str(TARGET), 'earlier_saved_spawner': older_row, 'current_saved_spawner': post_row,
                'same_serialized_spawner_fields': older_row is not None and compare_fields(older_row) == compare_fields(post_row),
                'earlier_component_bytes_decoded': decoded['consumed_bytes'], 'earlier_ps_key_matches': car['matching_rows'],
                'current_ps_key_matches': post_ps['candidate_matches'], 'queried_ps_keys': car['queried_keys']},
        'source_pins': [pin(p) for p in [records_path, fact_path, car_path, post_car_path, post_ps_path]] + [tail],
        'limits': ['Earlier save correlation does not certify exact ancestry or a live JF01/JF02 session identity.',
                   'Retained population rows express saved activation intent and associated IDs. Final actor and door application require positive evidence.',
                   'Absent PS2 entries can have been filtered during saving. Missing keys cannot establish unperformed setup.',
                   'An exact file comparison does not prove a supported native wait rebind.'],
        'runtime_candidate': None, 'save_writes': 0, 'game_calls': 0,
    }
    for row in current + earlier:
        pin_save(Path(row['path']), row['sha256'])
    out.mkdir()
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'registrations': result['registrations'], 'car': result['car']}))


if __name__ == '__main__':
    main()
