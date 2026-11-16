"""Static RTTI constructor/vtable catalogue from matched engine bytes."""
import sys,json,re,struct,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image
def rip(i):
    m=re.search(r'\[rip ([+-]) (0x[0-9a-f]+)\]',i['operands'])
    return int(i['rva'],16)+len(bytes.fromhex(i['bytes']))+(1 if m[1]=='+' else -1)*int(m[2],16) if m else None
def main():
    p=argparse.ArgumentParser();p.add_argument('out');p.add_argument('names',nargs='+');a=p.parse_args()
    im=Image();out=HERE/a.out;assert not out.exists();rows=[];funcs={}
    for name in a.names:
        at=im.data.find(name.encode()+b'\0');assert at>=0,name
        refs=im.refs_to(im.rva(at));reg=[im.disasm(int(x['container_rva'],16)) for x in refs if x['container_rva']]
        tables=[]
        for f in reg:
            for i in f['instructions']:
                if i['mnemonic']=='lea' and i['operands'].startswith('rax, [rip'):
                    t=rip(i)
                    if t is None:continue
                    try:target=struct.unpack_from('<Q',im.data,im.off(t+0xd8))[0]-im.base
                    except Exception:continue
                    if not 0<target<0x3000000:continue
                    ctor=im.disasm(target);funcs[ctor['begin_rva']]=ctor
                    jump=next((i for i in ctor['instructions'][:3] if i['mnemonic']=='jmp' and i['operands'].startswith('0x')),None)
                    if jump:
                        ctor=im.disasm(int(jump['operands'],16)-im.base);funcs[ctor['begin_rva']]=ctor
                    vt=[]
                    for n,x in enumerate(ctor['instructions']):
                        q=rip(x)
                        if x['mnemonic']=='lea' and q and any(y['mnemonic']=='mov' and re.match(r'qword ptr \[(?:rdx|rbx|rdi|rcx)\], ',y['operands']) for y in ctor['instructions'][n+1:n+4]):
                            vals=[]
                            for offset in range(0,0x280,8):
                                v=struct.unpack_from('<Q',im.data,im.off(q+offset))[0]-im.base
                                if not 0x1000<v<0x3000000:break
                                vals.append([hex(offset),hex(v)])
                                d=im.disasm(v);funcs[d['begin_rva']]=d
                            vt.append({'vtable':hex(q),'entries':vals})
                    tables.append({'rtti':hex(t),'ctor':ctor['begin_rva'],'vtables':vt})
        rows.append({'name':name,'tables':tables})
    out.mkdir();(out/'readback.json').write_text(json.dumps({'engine_sha256':im.sha,'types':rows,'functions':list(funcs.values())},indent=2))
    with (out/'functions.txt').open('w',encoding='utf-8') as f:
        for d in funcs.values():
            f.write('\nFUNCTION '+d['begin_rva']+'\n')
            for i in d['instructions']:f.write(i['rva']+' '+i['mnemonic']+' '+i['operands']+'\n')
    print(json.dumps(rows));print('Functions:',[(f['begin_rva'],len(f['instructions'])) for f in funcs.values()])
if __name__=='__main__':main()
