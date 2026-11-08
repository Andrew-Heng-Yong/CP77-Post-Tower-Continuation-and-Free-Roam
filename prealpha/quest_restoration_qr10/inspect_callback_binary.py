"""Offline PE/disassembly evidence only; never load the game/CET modules."""
from pathlib import Path
import hashlib, json, struct, sys
H=Path(__file__).resolve().parent
W=H.parents[1]
sys.path.insert(0,str(W/'research/finalboards_dismissal/tooling/python'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

def inspect(p, needles):
    b=p.read_bytes(); pe=struct.unpack_from('<I',b,0x3c)[0]
    count=struct.unpack_from('<H',b,pe+6)[0]; opt=pe+24
    image=struct.unpack_from('<Q',b,opt+24)[0]
    sh=opt+struct.unpack_from('<H',b,pe+20)[0]
    sections=[]
    for i in range(count):
        at=sh+40*i; name=b[at:at+8].rstrip(b'\0').decode()
        vs,va,sz,raw=struct.unpack_from('<IIII',b,at+8)
        sections.append((name,va,vs,raw,sz))
    def addr(off):
        for _,va,_,raw,sz in sections:
            if raw<=off<raw+sz:return image+va+off-raw
        raise ValueError(off)
    md=Cs(CS_ARCH_X86,CS_MODE_64); rows=[]
    for needle in needles:
        target=b.index(needle.encode()); literal=b.rfind(b'\0',0,target)+1; target_va=addr(literal); refs=[]
        for name,va,_,raw,sz in sections:
            if name!='.text':continue
            code=b[raw:raw+sz]
            # Exact RIP-relative LEA string xrefs, independently decoded below.
            for at in range(len(code)-7):
                if code[at] in (0x48,0x4c) and code[at+1]==0x8d and code[at+2]&0xc7==0x05:
                    dest=image+va+at+7+struct.unpack_from('<i',code,at+3)[0]
                    if target_va-16<=dest<=target_va:
                        lo=max(0,at-128); hi=min(len(code),at+192)
                        # A fixed aligned starting point can misdecode a prefix; retain raw bytes.
                        refs.append({'file_offset':hex(raw+at),'va':hex(image+va+at),'points_before_text':target_va-dest,
                            'window_offset':hex(raw+lo),'raw_hex':code[lo:hi].hex(),
                            'disassembly':[(hex(x.address),x.mnemonic,x.op_str)for x in md.disasm(code[lo:hi],image+va+lo)]})
        absolute=[]; needleptr=struct.pack('<Q',target_va)
        pos=0
        while True:
            pos=b.find(needleptr,pos)
            if pos<0:break
            absolute.append(hex(pos));pos+=1
        rows.append({'text':needle,'offset':hex(target),'literal_offset':hex(literal),'literal':b[literal:b.index(b'\0',target)].decode(errors='replace'),'va':hex(target_va),'lea_xrefs':refs,'absolute_pointer_offsets':absolute})
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest().upper(),'bytes':len(b),
        'image_base':hex(image),'sections':sections,'strings':rows,
        'method':'Offline raw PE read + RIP-relative LEA enumeration + existing Capstone. No LoadLibrary/game/API execution.'}

def main():
    p=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe')
    result=inspect(p,['RegisterListener() called with non-scripted object.',
        'RegisterListener() requires object and a function name.',
        'RegisterListener(): Can\'t find function'])
    dest=H/'evidence/installed_callback_binary_03.json'
    assert not dest.exists()
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
