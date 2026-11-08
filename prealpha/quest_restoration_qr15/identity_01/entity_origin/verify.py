"""Independent byte/slot controls for the bounded native EntityID dataflow."""
from pathlib import Path
import hashlib,json,struct
from capture import HERE, WORK, Image

def main():
    # Preserve run01: two hand-transcribed rel32 displacement typos.
    # Decode their direct destinations independently in fresh run02.
    out=HERE/'verification_02.json'
    assert not out.exists()
    im=Image();checks=[]
    def ck(name,ok,evidence):checks.append({'name':name,'pass':bool(ok),'evidence':evidence})
    def b(a,h):
        x=bytes.fromhex(h)
        return im.data[im.off(a):im.off(a)+len(x)]==x
    def slot(v,o,t):return struct.unpack_from('<Q',im.data,im.off(v+o))[0]==im.base+t
    def direct(a, opcode, target):
        p=im.off(a)
        return im.data[p]==opcode and a+5+struct.unpack_from('<i',im.data,p+1)[0]==target
    for n,v,o,t in [('stub_construct',0x3330838,0xD8,0xDB3B7C),
                    ('stub_create',0x31083C0,0x1B0,0x2FA044),
                    ('stub_restore',0x31083C0,0x1B8,0x9CF378),
                    ('persistency_classify',0x36343D8,0x1F0,0x4CB220),
                    ('dynamic_construct',0x32F1268,0xD8,0x13EFF30),
                    ('dynamic_high_allocator',0x3213628,0x1B0,0x4FAC20),
                    ('dynamic_low_allocator',0x3213628,0x1B8,0x12EC1A8)]:
        ck(n,slot(v,o,t),hex(t))
    ck('saved_row20_starts_with_reserved98',b(0x2BCEE43,'488d9798000000') and direct(0x2BCEE4D,0xE8,0x2F9DF0),
       '2BCED84 row+20 destination; object+98 source→u64append2F9DF0')
    ck('saved_active_filter_keeps_raw_id',b(0x2BCEEAA,'498bd1') and b(0x2BCEEB0,'ff90f0010000'),
       'R9rawID→RDX; IPersistencySystem.v1F0')
    ck('restore_adds_reserved98',b(0x2606570,'4881c198000000') and direct(0x2606577,0xE9,0x467DEC),
       'rowarray20 copied withoutIDconversion')
    ck('activation_pops_raw64_associated_id',b(0x9CF603,'488b8b98000000') and b(0x9CF60A,'488b14d1'),
       'object+98[index*8]→RDX')
    ck('create_request_preserves_u64',b(0x9CF713,'488bda') and b(0x9CF7A0,'48895d87'),
       'RDX→RBX→requestfirstU64')
    ck('stub_token_preserves_request_id',b(0x2FA3BC,'488b07') and b(0x2FA3C9,'48894308'),
       'request[0]→token+08')
    ck('allocator_counters_native_bounds',b(0x13EFFB2,'b880969800') and b(0x13F0027,'b940548900') and
       b(0x4FAC2D,'b9ffffff00') and b(0x12EC1B5,'b980969800'),
       'constructor10M/9M; generatorcapsFFFFFF/10M')
    ck('fallback_selects_same_allocators',b(0x4FABCE,'ff90b0010000') and b(0x4FABE8,'ff90b8010000'),
       '4FABB8 chooses actualnativev1B0/v1B8')
    row=json.loads((WORK/'prealpha/quest_restoration_qr15/lifecycle_01/save_community/decode_02/result.json').read_text())
    ids=list(map(int,row['target_record']['array_0x20']))
    ck('captured_target_has_one_associated_value',ids==[10229047], 'Captured decode only; no originalsave read')
    ck('target_within_exact_native_high_allocation_interval',all(10000000<=v<0xFFFFFF for v in ids),
       'Interval classification only; no absentPS or unsavableforever inference')
    result={'status':'PASS' if all(c['pass']for c in checks)else'FAIL','checks':checks,
            'pins':{p.name:hashlib.sha256(p.read_bytes()).hexdigest().upper()for p in(HERE/'capture.py',HERE/'evidence_01.json')},
            'original_save_reads':0,'game_calls':0,'save_writes':0,'runtime_changes':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':len(checks),'failures':[x['name']for x in checks if not x['pass']]}))

if __name__=='__main__':main()
