"""Complete the exact version277 component schema; no game/save input or writer."""
from pathlib import Path
import hashlib, json, struct
from decode import Reader, Unsupported, parse, sha

HERE = Path(__file__).resolve().parent


def decode_full(data, keys):
    result = parse(data, keys)
    reader = Reader(data)
    reader.pos = result['decoded_end']
    n_a = reader.u32()
    if n_a > 1000000 or n_a > (len(data)-reader.pos)//80:
        raise ValueError('ListA count outside component bounds')
    total_a_items = 0
    for _ in range(n_a):
        reader.take(8)
        reader.take(64)
        reader.take(4)
        total_a_items += len(reader.ids(12))
    list_b = reader.ids(12)
    n_c = reader.u32()
    if n_c > 1000000 or n_c > (len(data)-reader.pos)//2:
        raise ValueError('ListC count outside component bounds')
    names_c = []
    for _ in range(n_c):
        names_c.append(reader.name())
        reader.take(1)
    list_d = reader.ids(16)
    if reader.pos != len(data):
        raise ValueError('Unexplained component remainder: ' + str(len(data)-reader.pos))
    result.update({'consumed_bytes': reader.pos, 'unparsed_bytes': 0,
                   'footer': {'list_a_count': n_a, 'list_a_nested_count': total_a_items,
                              'list_b_count': len(list_b), 'list_c_count': n_c,
                              'list_c_names': names_c, 'list_d_count': len(list_d)}})
    return result


def controls(data, keys, decoded, target):
    checks = []

    def ck(name, ok):
        checks.append({'name': name, 'pass': bool(ok)})
        assert ok, name

    def refuses(name, thunk):
        try:
            thunk()
        except (ValueError, Unsupported, struct.error):
            ck(name, True)
        else:
            ck(name, False)

    def changed(offset, replacement):
        value = bytearray(data)
        value[offset:offset+len(replacement)] = replacement
        return bytes(value)

    # Controls mutate actual captured bytes and fixed source-bound boundaries,
    # rather than regenerating the current record with this implementation.
    refuses('actual_first_map_count_overflow', lambda: decode_full(changed(0,b'\xff'*4),keys))
    refuses('actual_spawner_map_count_overflow', lambda: decode_full(changed(decoded['second_map_start'],b'\xff'*4),keys))
    refuses('actual_component_truncated', lambda: decode_full(data[:-1],keys))
    refuses('unexplained_appended_bytes', lambda: decode_full(data+b'\x00',keys))
    refuses('actual_first_name_unsupported_unicode', lambda: decode_full(changed(51,b'\x07'),keys))
    refuses('name_negative_zero', lambda: Reader(b'\x80').name())
    refuses('name_noncanonical_continuation', lambda: Reader(b'\xc0\x00').name())
    refuses('name_truncated_payload', lambda: Reader(b'\x87def').name())
    refuses('name_positive_encoding_not_guessed', lambda: Reader(b'\x01a\x00').name())
    refuses('array_truncated_count', lambda: Reader(b'\x00\x00\x00').ids())
    refuses('array_count_bound', lambda: Reader(b'\xff'*4).ids())
    ck('entire_trailing_component_consumed', decoded['consumed_bytes'] == len(data) and decoded['unparsed_bytes'] == 0)
    ck('first_nested_entry_default_is_literal_source_encoding', data[51:59] == b'\x87default')
    index = decoded['second_keys'].index(target)
    key_at = decoded['second_map_keys_start'] + index * 8
    modified = parse(changed(key_at,struct.pack('<Q',0)),keys)
    ck('wrong_native_key_not_silently_treated_as_target', target not in modified['second_rows'])
    row = decoded['second_rows'][target]
    # Active byte follows variable array_00 and raw2, not a guessed constant row offset.
    active_at = row['start_offset'] + 4 + 8*len(row['array_0x00']) + 2
    inactive = decode_full(changed(active_at,b'\x00'),keys)['second_rows'][target]
    ck('native_active_mutation_remains_false_without_liveness_inference', inactive['memory_0x46_u8'] == 0 and inactive['array_0x20'] == row['array_0x20'])
    return checks


def main():
    out = HERE/'decode_02'
    assert not out.exists(), 'Fresh output required'
    captured = json.loads((HERE/'capture_01/capture.json').read_text())
    schema_file = HERE.parent/'community_native/schema_02.json'
    schema = json.loads(schema_file.read_text())
    assert schema['count_encoding'].startswith('fixedU32') or 'fixed' in schema['count_encoding'].lower()
    assert captured['save_version'] == 277, 'Only exact verified version277 is qualified'
    source = Path(captured['trailing_path'])
    assert sha(source) == captured['trailing_sha256']
    data = source.read_bytes()
    keys = list(map(int,captured['unknown_hash_list']))
    assert captured['node']['size'] == 4+4+8*len(keys)+len(data) and captured['node']['trailing_size'] == 0
    decoded = decode_full(data, keys)
    target = int(captured['target_node_id_u64'])
    assert target in decoded['second_rows']
    index = decoded['second_keys'].index(target)
    target_at = decoded['second_map_keys_start']+index*8
    assert captured['target_uninterpreted_byte_offsets'] == [target_at]
    row = decoded['second_rows'][target]
    assert row['memory_0x46_u8'] in (0,1)
    tests = controls(data,keys,decoded,target)
    result = {'status': 'COMPLETE_COMPONENT_STRUCTURAL_DECODE_TARGET_SAVED_ACTIVE_STAGE_UNKNOWN',
              'schema': str(schema_file.resolve()), 'schema_sha256': sha(schema_file),
              'capture': str((HERE/'capture_01/capture.json').resolve()), 'capture_sha256': sha(HERE/'capture_01/capture.json'),
              'input_sha256': sha(source), 'source_save_sha256': captured['source_sha256'], 'save_version': 277,
              'outer_key_count': len(keys), 'first_nested_row_count': decoded['first_nested_rows'],
              'spawner_key_count': len(decoded['second_keys']), 'target_global_node_id_u64': str(target),
              'target_key_byte_offset': target_at,
              'target_record': {k: ([str(v)for v in value] if k.startswith('array_') else value) for k,value in row.items()},
              'saved_active': bool(row['memory_0x46_u8']),
              'saved_active_proof': 'Native pre-save2BD3C30->2BD3CDC->2BCED84 copies the actual object active byte+0x10 to record+0x46. Not a current initialized/owner/setup receipt.',
              'consumed_bytes': decoded['consumed_bytes'], 'unparsed_bytes': decoded['unparsed_bytes'], 'footer': decoded['footer'],
              'checks': tests, 'limits': 'Entity10229047 is a saved associated ID in the reserved/filtered group, not a proven current vehicle, initialized owner, visual-destruction or door completion. Actual loaded JF01/JF02 body remains unbound.',
              'original_save_reads': 0, 'game_calls': 0, 'save_writes': 0}
    out.mkdir()
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'saved_active':result['saved_active'],'target_record':result['target_record'],'consumed_bytes':result['consumed_bytes'],'unparsed_bytes':result['unparsed_bytes'],'checks':len(tests)}))


if __name__ == '__main__':
    main()
