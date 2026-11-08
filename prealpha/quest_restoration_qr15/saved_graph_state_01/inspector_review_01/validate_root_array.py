"""Fresh strict validation of the extracted gap plus meaningful malformed controls."""
import hashlib,json,struct
from pathlib import Path
from inspect_lock import HERE
W=HERE.parents[3]

class InvalidArray(ValueError):pass

def encode_count(value):
    assert 0<=value<=0x7fffffff
    b=[value&0x3f];value>>=6
    if value:b[0]|=0x40
    while value:
        byte=value&0x7f;value>>=7
        b.append(byte|(0x80 if value else 0))
    return bytes(b)

def decode(data,max_count=64):
    if not data:raise InvalidArray('EMPTY')
    first=data[0]
    if first&0x80:raise InvalidArray('NEGATIVE_OR_NEGATIVE_ZERO')
    value=first&0x3f;cursor=1;cont=bool(first&0x40)
    for shift in [6,13,20,27]:
        if not cont:break
        if cursor>=len(data):raise InvalidArray('TRUNCATED_COUNT')
        b=data[cursor];cursor+=1
        value|=(b&0x7f)<<shift;cont=bool(b&0x80)
        if value>0x7fffffff:raise InvalidArray('COUNT_OVERFLOW')
    if cont:raise InvalidArray('COUNT_TOO_LONG')
    if data[:cursor]!=encode_count(value):raise InvalidArray('NONCANONICAL_COUNT')
    if value>max_count:raise InvalidArray('COUNT_BOUND')
    end=cursor+value*8
    if end>len(data):raise InvalidArray('TRUNCATED_ARRAY')
    if end<len(data):raise InvalidArray('UNCONSUMED_BYTES')
    return list(struct.unpack_from('<'+'Q'*value,data,cursor))

def main():
    out=HERE/'root_array_controls_01.json';assert not out.exists()
    base=W/'prealpha/quest_restoration_qr15'
    data=(base/'root_saved_resource_array_01/facts_to_custom_array.bin').read_bytes()
    old=json.loads((HERE/'root_binding_decode_01.json').read_text())
    decoded=decode(data)
    assert [str(v) for v in decoded]==[r['resource_path_u64'] for r in old['members']]
    controls=[]
    malformed=[
        ('empty',b'','EMPTY'),
        ('negative_zero',b'\x80','NEGATIVE_OR_NEGATIVE_ZERO'),
        ('negative_one',b'\x81'+b'\0'*8,'NEGATIVE_OR_NEGATIVE_ZERO'),
        ('overlong_zero',b'\x40\x00','NONCANONICAL_COUNT'),
        ('overlong_two',b'\x42\x00'+data[1:],'NONCANONICAL_COUNT'),
        ('truncated_count',b'\x40','TRUNCATED_COUNT'),
        ('count_overflow',b'\x40\x80\x80\x80\x10','COUNT_OVERFLOW'),
        ('count_too_long',b'\x40\x80\x80\x80\x80','COUNT_TOO_LONG'),
        ('count_bound',encode_count(65)+b'\0'*(65*8),'COUNT_BOUND'),
        ('truncated_array',b'\x03'+data[1:],'TRUNCATED_ARRAY'),
        ('unconsumed_byte',data+b'\0','UNCONSUMED_BYTES')]
    for label,b,expected in malformed:
        try:decode(b)
        except InvalidArray as e:assert str(e)==expected
        else:raise AssertionError(label)
        controls.append({'case':label,'expected':expected,'result':'PASS'})
    for count in [0,1,2,63,64]:
        values=list(range(count));encoded=encode_count(count)+struct.pack('<'+'Q'*count,*values)
        assert decode(encoded)==values
        controls.append({'case':'valid_'+str(count),'result':'PASS'})
    header_path=base/'root_saved_resource_array_01/header.json'
    header=json.loads(header_path.read_text(encoding='utf-8-sig'))
    result={'result':'PASS_STRICT_CURRENT_GAP_AND_MALFORMED_CONTROLS','controls_count':len(controls),
       'controls':controls,'decoded_members':[str(v) for v in decoded],
       'gap_sha256':hashlib.sha256(data).hexdigest().upper(),
       'header_artifact':{'path':str(header_path.relative_to(W)),'sha256':hashlib.sha256(header_path.read_bytes()).hexdigest().upper(),'data':header},
       'limit':'Validates this exact extracted gap and bounded decoder. No pending/owner/lease semantics or current live body certified.',
       'original_save_reads':0,'game_api_calls':0,'runtime_changes':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({'result':result['result'],'controls_count':len(controls),'members':result['decoded_members'],'header':header})

if __name__=='__main__':main()
