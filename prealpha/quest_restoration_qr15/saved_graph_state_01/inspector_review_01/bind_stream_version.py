"""Identify exact SaveVersion getter by reviewed header offsets; no binary execution."""
import json,struct
from inspect_lock import Image,HERE

def main():
    out=HERE/'stream_version_binding_01.json';assert not out.exists()
    im=Image();patterns=[bytes.fromhex(s) for s in ['488b81e00000008b8098020000c3','488b81200100008b8098020000c3']]
    found=[]
    for needle in patterns:
        at=0
        while True:
            at=im.data.find(needle,at)
            if at<0:break
            rva=im.rva(at)
            pointers=[int(s,16) for s in im.pointers_to(rva)]
            found.append({'getter_rva':hex(rva),'bytes':needle.hex(),'instructions':im.disasm(rva),
                'pointer_refs':[hex(p) for p in pointers],
                'candidate_vtables_at_virtual48':[{'vtable_rva':hex(p-0x48),'qwords':[(hex(p-0x48+i*8),hex(struct.unpack_from('<Q',im.data,im.off(p-0x48)+i*8)[0])) for i in range(20)]} for p in pointers]})
            at+=1
    result={'exe_sha256':im.sha,'result':'EXACT_REVIEWED_HEADER_OFFSET_GETTER_CANDIDATES','candidates':found,'save_reads':0,'game_api_calls':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
