"""Read-only native FNV1a32 caller search; candidate graph-fact uses only."""
import json
from inspect_native import Image, HERE

def main():
    out=HERE/'native_key_uses_01.json'
    assert not out.exists()
    im=Image()
    calls=im.calls_to(0x1efa14)
    candidates=sorted(set(int(r['container_rva'],16) for r in calls if r['container_rva']))
    matched=[]
    for rva in candidates:
        f=im.disasm(rva);rows=f['instructions']
        if any(r['mnemonic'] in ('call','jmp') and ('+ 0x10]' in r['operands'] or '+ 0x18]' in r['operands']) for r in rows):
            matched.append(f)
    result={'exe_sha256':im.sha,'method':'RawE8 targetFNV1a32 search, containing .pdata function decode, filter virtualslots10/18; registerdataflow still requires review',
            'fnv_caller_candidates':len(candidates),'matching_functions':len(matched),'functions':matched,'source_writes':0,'game_api_calls':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({k:v for k,v in result.items() if k!='functions'})
    for f in matched:
        print(f['begin_rva'], f['end_rva'], len(f['instructions']))

if __name__=='__main__':
    main()
