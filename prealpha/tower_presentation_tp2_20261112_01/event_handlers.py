"""Read-only event registration inspection against the pinned executable."""
import sys, json, re
from pathlib import Path
from native_types import Image, rip
HERE=Path(__file__).resolve().parent

def main():
    out=HERE/sys.argv[1]; assert out.parent==HERE and not out.exists()
    im=Image(); rows=[]; functions={}
    for name in sys.argv[2:]:
        at=im.data.find(name.encode()+b'\0'); assert at>=0,name
        registrations=[]
        for ref in im.refs_to(im.rva(at)):
            if not ref['container_rva']:continue
            f=im.disasm(int(ref['container_rva'],16)); functions[f['begin_rva']]=f
            for i in f['instructions']:
                if i['mnemonic']!='mov' or not re.match(r'qword ptr \[rip .*\], rdi$',i['operands']):continue
                target=rip(i); refs=im.refs_to(target); candidates=[]
                for r in refs:
                    if not r['container_rva']:continue
                    g=im.disasm(int(r['container_rva'],16)); functions[g['begin_rva']]=g
                    pointers=[]
                    for j in g['instructions']:
                        q=rip(j)
                        if j['mnemonic']=='lea' and q and 0x1000<q<0x3000000:
                            h=im.disasm(q);functions[h['begin_rva']]=h;pointers.append(hex(q))
                    candidates.append({'function':g['begin_rva'],'code_pointers':pointers})
                registrations.append({'global':hex(target),'refs':candidates})
        rows.append({'name':name,'registrations':registrations})
    out.mkdir()
    (out/'readback.json').write_text(json.dumps({'engine_sha256':im.sha,'events':rows,'functions':list(functions.values())},indent=2))
    with (out/'functions.txt').open('w') as stream:
        for f in functions.values():
            stream.write('\nFUNCTION '+f['begin_rva']+'\n')
            for i in f['instructions']:stream.write(i['rva']+' '+i['mnemonic']+' '+i['operands']+'\n')
    print(json.dumps(rows))

if __name__=='__main__':main()
