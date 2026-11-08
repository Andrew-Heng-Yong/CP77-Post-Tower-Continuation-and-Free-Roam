"""Bind exact native PhaseNode RTTI registration to its virtual methods."""
import json, struct
from inspect_lock import Image,HERE

def main():
    out=HERE/'phase_type_01.json';assert not out.exists()
    im=Image();reg=im.disasm(0x15b5014)
    def dest(row):
        b=bytes.fromhex(row['bytes']);return int(row['rva'],16)+len(b)+struct.unpack('<i',b[-4:])[0]
    globals_=[dest(r) for r in reg['instructions'] if r['mnemonic']=='mov' and r['operands'].startswith('qword ptr [rip') and r['operands'].endswith(', rdi')]
    assert len(globals_)==1
    global_=globals_[0];refs=im.refs_to(global_)
    getters=[]
    for ref in refs:
        rva=int(ref['candidate_reference_rva'],16);f=im.disasm(rva)
        rows=f['instructions']
        if len(rows)==2 and rows[0]['mnemonic']=='mov' and rows[0]['operands'].startswith('rax, qword ptr [rip') and rows[1]['mnemonic']=='ret':
            getters.append(f)
    assert len(getters)==1
    getter=int(getters[0]['begin_rva'],16)
    vrefs=[int(s,16) for s in im.pointers_to(getter)];assert len(vrefs)==2 and max(vrefs)-min(vrefs)==8
    vtable=min(vrefs)
    methods={hex(slot):im.disasm(struct.unpack_from('<Q',im.data,im.off(vtable+slot))[0]-im.base) for slot in [0x150,0x158,0x160,0x168,0x170,0x178,0x180,0x188,0x190]}
    result={'exe_sha256':im.sha,'class':'questPhaseNodeDefinition','registration':reg,'type_global_rva':hex(global_),
            'getter':getters[0],'vtable_rva':hex(vtable),'methods':methods,'source_writes':0,'game_api_calls':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({k:v for k,v in result.items() if k not in ['registration','getter','methods']})
    for slot,f in methods.items():
        print('\nSlot',slot,'function',f['begin_rva'])
        for r in f['instructions']:print(r['rva'],r['mnemonic'],r['operands'])

if __name__=='__main__':main()
