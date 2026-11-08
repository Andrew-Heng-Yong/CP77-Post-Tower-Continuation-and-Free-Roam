"""Bounded literal search for native save-header version identity."""
import json
from inspect_lock import Image,HERE

def main():
    out=HERE/'save_header_candidates_01.json';assert not out.exists()
    im=Image();seen=set();literals={}
    for needle in [b'CSAV',b'VASC']:
        off=0;rows=[]
        while True:
            off=im.data.find(needle,off)
            if off<0:break
            try:
                rva=im.rva(off);f=im.function(rva)
                rows.append({'rva':hex(rva),'container_rva':hex(f[0]) if f else None})
                if f:seen.add(f[0])
            except StopIteration:pass
            off+=1
        literals[needle.decode()]=rows
    result={'exe_sha256':im.sha,'literal_candidates':literals,'functions':[im.disasm(r) for r in sorted(seen)],'save_reads':0,'game_api_calls':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({'literals':literals,'function_lengths':[(f['begin_rva'],len(f['instructions'])) for f in result['functions']]})

if __name__=='__main__':main()
