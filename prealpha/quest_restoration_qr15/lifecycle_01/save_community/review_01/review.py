"""Independent cursor parser for captured bytes and source-bound native schema.

Does not import the decoder under review or read an original game save.
"""
from pathlib import Path
import collections, hashlib, json, struct

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
NATIVE = BASE.parent / 'community_native'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()

class Cursor:
    def __init__(self, data):
        self.b, self.at = data, 0
    def raw(self, n):
        if n < 0 or self.at + n > len(self.b):
            raise ValueError('Bounds')
        old = self.at
        self.at += n
        return self.b[old:self.at]
    def scalar(self, fmt):
        return struct.unpack('<'+fmt, self.raw(struct.calcsize('<'+fmt)))[0]
    def block(self, size=8):
        n = self.scalar('I')
        raw = self.raw(n*size)
        return list(struct.unpack('<'+'Q'*n, raw)) if size == 8 else (n, raw)
    def row(self):
        start = self.at
        a = self.block()
        count42, active = self.scalar('H'), self.scalar('B')
        b = self.block()
        count40, count44 = self.scalar('H'), self.scalar('H')
        c = self.block()
        d = self.block(16)
        return {'array_0x00':a, 'memory_0x42_u16':count42, 'memory_0x46_u8':active,
                'array_0x10':b, 'memory_0x40_u16':count40, 'memory_0x44_u16':count44,
                'array_0x20':c, 'array_0x30_hex16':[d[1][i:i+16].hex() for i in range(0,len(d[1]),16)],
                'start_offset':start,'end_offset':self.at}
    def name(self):
        start = self.at
        first = self.scalar('B')
        sign = bool(first & 128)
        magnitude = first & 63
        more = bool(first & 64)
        for shift in (6,13,20,27):
            if not more:
                break
            byte = self.scalar('B')
            magnitude += (byte & 127) << shift
            more = bool(byte & 128)
        if more or magnitude > 0x7fffffff:
            raise ValueError('VLQ overflow')
        # Independently regenerate the native writer's canonical prefix.
        pieces = [magnitude & 63]
        rest = magnitude >> 6
        if rest:
            pieces[0] |= 64
            while rest:
                pieces.append((rest & 127) | (128 if rest >> 7 else 0))
                rest >>= 7
        if sign:
            pieces[0] |= 128
        if bytes(pieces) != self.b[start:self.at] or sign and not magnitude:
            raise ValueError('Noncanonical')
        if magnitude and not sign:
            raise ValueError('Unqualified Unicode')
        name = self.raw(magnitude)
        if any(x > 127 for x in name):
            raise ValueError('Unqualified nonASCII')
        return name.decode('ascii')

def independent(data, outer_keys):
    c = Cursor(data)
    nested = 0
    all_names = collections.Counter()
    first_name_at = None
    for outer in outer_keys:
        inner = c.block()
        if len(inner) != len(set(inner)):
            raise ValueError('Inner duplicate')
        for key in inner:
            row = c.row()
            first_name_at = c.at if first_name_at is None else first_name_at
            all_names[c.name()] += 1
            nested += 1
    second_start = c.at
    spawner_keys = c.block()
    if len(spawner_keys) != len(set(spawner_keys)):
        raise ValueError('Spawner duplicate')
    rows = {key:c.row() for key in spawner_keys}
    footer_start = c.at
    n_a = c.scalar('I')
    nested_a = 0
    for _ in range(n_a):
        c.raw(8+64+4)
        n, _ = c.block(12)
        nested_a += n
    n_b, _ = c.block(12)
    n_c = c.scalar('I')
    footer_names = []
    for _ in range(n_c):
        footer_names.append(c.name())
        c.raw(1)
    n_d, _ = c.block(16)
    if c.at != len(data):
        raise ValueError('Remainder')
    return {'nested':nested, 'names':all_names, 'first_name_at':first_name_at,
            'second_start':second_start,'spawner_keys':spawner_keys,'rows':rows,
            'footer_start':footer_start,'consumed':c.at,
            'footer':{'list_a_count':n_a,'list_a_nested_count':nested_a,'list_b_count':n_b,
                      'list_c_count':n_c,'list_c_names':footer_names,'list_d_count':n_d}}

def main():
    output = HERE/'review.json'
    assert not output.exists()
    capture = json.loads((BASE/'capture_01/capture.json').read_text())
    captured_path = BASE/'capture_01/community_trailing.bin'
    source = captured_path.read_bytes()
    report = json.loads((BASE/'decode_02/result.json').read_text())
    previous = json.loads((BASE/'decode_01/result.json').read_text())
    keys = [int(s) for s in capture['unknown_hash_list']]
    parsed = independent(source, keys)
    target = int(capture['target_node_id_u64'])
    target_at = parsed['second_start']+4+8*parsed['spawner_keys'].index(target)
    row = parsed['rows'][target]
    presented = {k:([str(v) for v in value] if k.startswith('array_') else value)
                 for k,value in row.items()}
    checks=[]
    def ck(name, value):
        checks.append({'name':name,'pass':bool(value)})
    ck('capture_input_digest', sha(captured_path)==capture['trailing_sha256']==report['input_sha256'])
    ck('exact_version277_and_capture_unchanged', capture['save_version']==277 and capture['source_unchanged'])
    ck('outer_count_and_unique_keys',len(keys)==capture['unknown_hash_list_count'] and len(keys)==len(set(keys)))
    ck('schema_digest', sha(NATIVE/'schema_02.json')==report['schema_sha256'])
    ck('independent_nested_rows',parsed['nested']==report['first_nested_row_count']==previous['first_nested_rows'])
    ck('independent_spawner_keys',len(parsed['spawner_keys'])==report['spawner_key_count'])
    ck('independent_target_row',presented==report['target_record']==previous['target_record'])
    ck('target_key_boundary_not_signature_guess',target_at==report['target_key_byte_offset'] and
       struct.unpack_from('<Q',source,target_at)[0]==target and capture['target_uninterpreted_byte_offsets']==[target_at])
    ck('first_actual_name_native_encoding',parsed['first_name_at']==51 and source[51:59]==b'\x87default')
    ck('footer_source_widths_and_complete_consumption',parsed['footer']==report['footer'] and parsed['consumed']==len(source)==report['consumed_bytes'])
    ck('node_length_includes_index_and_outer_map_header',4+4+8*len(keys)+len(source)==capture['node']['size'])
    ck('no_unparsed_footer',report['unparsed_bytes']==0 and previous['opaque_footer_bytes']==len(source)-parsed['footer_start'])
    ck('active_semantic_matches_native_copy_only',row['memory_0x46_u8']==1 and report['saved_active'] is True and
       'not a proven current vehicle' in report['limits'] and 'Not a current initialized/owner/setup receipt' in report['saved_active_proof'])
    ck('producer_controls_all_pass',len(report['checks'])==15 and all(x['pass'] for x in report['checks']))
    malformed = {'overflow5':b'\xff\xff\xff\xff\x08', 'continuation6':b'\xc1\x80\x80\x80\x80\x00',
                 'negative_zero':b'\x80', 'overlong':b'\xc7\x00default', 'truncated':b'\x87def',
                 'positive':b'\x01a\x00'}
    for name, raw in malformed.items():
        try:
            Cursor(raw).name()
        except (ValueError,struct.error):
            ck('independent_malformed_name_'+name,True)
        else:
            ck('independent_malformed_name_'+name,False)
    # Footer protection is independently tested against the captured component.
    for name, changed in [('truncated_footer',source[:-1]),('extra_footer',source+b'\x00')]:
        try:
            independent(changed,keys)
        except (ValueError,struct.error):
            ck('independent_'+name,True)
        else:
            ck('independent_'+name,False)
    result={'status':'PASS' if all(c['pass'] for c in checks) else 'FAIL','checks':checks,
            'method':'Independent implementation from sealed native schema; does not import decoderunderreview',
            'target_key_offset':target_at,'target_record':presented,'consumed_bytes':parsed['consumed'],
            'footer':parsed['footer'],'name_count':parsed['nested'],'distinct_names':len(parsed['names']),
            'qualification':'Saved active=true and saved associated reserved/filteredID10229047 only; no current entity,graph,setup,door,initialized,or owner proof.',
            'pins':{str(p.relative_to(BASE)):sha(p) for p in [BASE/'capture_01/capture.json',captured_path,
                BASE/'decode.py',BASE/'decode_full.py',BASE/'decode_01/result.json',BASE/'decode_02/result.json']},
            'original_save_reads':0,'game_calls':0,'save_writes':0}
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':len(checks),'failures':[x['name'] for x in checks if not x['pass']],
                     'output':str(output),'target':presented}))

if __name__=='__main__':
    main()
