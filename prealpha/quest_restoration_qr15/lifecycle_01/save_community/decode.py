"""Decode the two source-traced community maps, retaining the later footer as opaque.

Reads captured component bytes only. No original save, Game API or writer.
Schema: exact2.5 native Save2BD3A48/record2BD3E84; SaveVersion277.
"""
from pathlib import Path
import hashlib, json, struct

HERE = Path(__file__).resolve().parent


class Unsupported(ValueError):
    pass


class Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def take(self, size):
        if size < 0 or size > len(self.data) - self.pos:
            raise ValueError('Truncated component at ' + str(self.pos))
        start = self.pos
        self.pos += size
        return self.data[start:self.pos]

    def u32(self):
        return struct.unpack('<I', self.take(4))[0]

    def ids(self, stride=8):
        count = self.u32()
        if count > 1000000 or count > (len(self.data) - self.pos) // stride:
            raise ValueError('Array count outside component bounds')
        raw = self.take(count * stride)
        if stride == 8:
            return [x[0] for x in struct.iter_unpack('<Q', raw)]
        return [raw[i:i+stride].hex() for i in range(0, len(raw), stride)]

    def record(self):
        start = self.pos
        row = {'array_0x00': self.ids()}
        row['memory_0x42_u16'] = struct.unpack('<H', self.take(2))[0]
        row['memory_0x46_u8'] = self.take(1)[0]
        row['array_0x10'] = self.ids()
        row['memory_0x40_u16'] = struct.unpack('<H', self.take(2))[0]
        row['memory_0x44_u16'] = struct.unpack('<H', self.take(2))[0]
        row['array_0x20'] = self.ids()
        row['array_0x30_hex16'] = self.ids(16)
        row.update({'start_offset': start, 'end_offset': self.pos})
        return row

    def name(self):
        # Exact non-dictionary CName branch; negative signedVLQ length is bytes.
        start = self.pos
        first = self.take(1)[0]
        negative = bool(first & 0x80)
        length = first & 0x3f
        continuation = bool(first & 0x40)
        shift = 6
        while continuation:
            if shift > 27:
                raise ValueError('Name length overflow')
            byte = self.take(1)[0]
            length |= (byte & 0x7f) << shift
            continuation = bool(byte & 0x80)
            shift += 7
        used = self.pos - start
        if length > 0x7fffffff or used > 1 and length < (1 << (6 + 7*(used-2))):
            raise ValueError('Noncanonical name length')
        if negative and length == 0:
            raise ValueError('Negative zero name length')
        if not negative and length:
            raise Unsupported('Positive/unicode CName encoding needs its native schema; do not guess')
        if length > 65536:
            raise ValueError('Unbounded name')
        raw = self.take(length)
        if any(x >= 128 for x in raw):
            raise Unsupported('NonASCII CName needs explicit encoding evidence')
        return raw.decode('ascii')


def parse(data, outer_keys):
    reader = Reader(data)
    first_count = 0
    names = set()
    for outer in outer_keys:
        keys = reader.ids()
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate first-map inner key')
        for key in keys:
            reader.record()
            names.add(reader.name())
            first_count += 1
    second_start = reader.pos
    keys = reader.ids()
    key_start = second_start + 4
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate second-map key')
    rows = {}
    for key in keys:
        rows[key] = reader.record()
    return {'first_nested_rows': first_count, 'names': sorted(names), 'second_map_start': second_start,
            'second_map_keys_start': key_start, 'second_keys': keys, 'second_rows': rows,
            'decoded_end': reader.pos, 'opaque_footer_bytes': len(data)-reader.pos}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def main():
    out = HERE/'decode_01'
    assert not out.exists(), 'Fresh output required'
    capture = json.loads((HERE/'capture_01/capture.json').read_text())
    source = Path(capture['trailing_path'])
    assert sha(source) == capture['trailing_sha256']
    assert capture['save_version'] == 277 and capture['source_unchanged']
    data = source.read_bytes()
    keys = [int(v) for v in capture['unknown_hash_list']]
    assert len(keys) == capture['unknown_hash_list_count'] and len(set(keys)) == len(keys)
    decoded = parse(data, keys)
    target = int(capture['target_node_id_u64'])
    assert target in decoded['second_rows'], 'Typed spawner not present in the fully traversed second-map prefix'
    index = decoded['second_keys'].index(target)
    key_offset = decoded['second_map_keys_start'] + index * 8
    assert struct.unpack_from('<Q', data, key_offset)[0] == target
    assert capture['target_uninterpreted_byte_offsets'] == [key_offset], 'Candidate signature did not bind uniquely'
    row = decoded['second_rows'][target]
    output_row = {k: ([str(v) for v in values] if k.startswith('array_') and isinstance(values,list) else values) for k,values in row.items()}
    result = {'status': 'TWO_NATIVE_MAPS_DECODED_FOOTER_OPAQUE_NOT_OWNER_PROOF',
              'capture_path': str(HERE/'capture_01/capture.json'), 'capture_sha256': sha(HERE/'capture_01/capture.json'),
              'input_sha256': sha(source), 'source_save_sha256': capture['source_sha256'], 'save_version': capture['save_version'],
              'first_outer_keys': len(keys), 'first_nested_rows': decoded['first_nested_rows'],
              'name_encoding': 'Non-dictionary signedVLQ negative-length ASCII branch; all actual names validated',
              'distinct_names': decoded['names'], 'second_map_start': decoded['second_map_start'],
              'second_map_key_count': len(decoded['second_keys']), 'target_key_index': index, 'target_key_byte_offset': key_offset,
              'target_key_u64': str(target), 'target_record': output_row, 'decoded_prefix_end': decoded['decoded_end'],
              'opaque_footer_bytes': decoded['opaque_footer_bytes'], 'decoded_prefix_sha256': hashlib.sha256(data[:decoded['decoded_end']]).hexdigest().upper(),
              'limits': 'Saved record fields retained by native memory offsets. Semantic labels require native copy/restore proof. No field is a visual/door completion receipt or current liveness. Later footer remains opaque.',
              'game_calls': 0, 'original_save_reads': 0, 'save_writes': 0}
    out.mkdir()
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status': result['status'], 'first_nested_rows': decoded['first_nested_rows'], 'spawner_keys': len(decoded['second_keys']), 'target_record': output_row, 'opaque_footer_bytes': decoded['opaque_footer_bytes']}))


if __name__ == '__main__':
    main()
