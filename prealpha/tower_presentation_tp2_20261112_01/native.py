"""Read-only matched-engine inspection. Fresh evidence outputs only."""
from pathlib import Path
import sys,argparse,json,struct
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

def main():
    p=argparse.ArgumentParser();p.add_argument('out');p.add_argument('--string',action='append',default=[]);p.add_argument('--rva',action='append',default=[],type=lambda x:int(x,0));p.add_argument('--refs',action='append',default=[],type=lambda x:int(x,0));p.add_argument('--callers',action='append',default=[],type=lambda x:int(x,0));p.add_argument('--ptr',action='append',default=[],type=lambda x:int(x,0));p.add_argument('--hash',action='append',default=[],type=lambda x:int(x,0));p.add_argument('--table',action='append',default=[],nargs=3,type=lambda x:int(x,0));a=p.parse_args()
    out=HERE/a.out;assert out.parent==HERE and not out.exists();im=Image();funcs=set(a.rva);strings={};refs={};tables={}
    for value in a.string:
        pos=0;hits=[]
        while True:
            pos=im.data.find(value.encode()+b'\0',pos)
            if pos<0:break
            hits.append(im.rva(pos));pos+=1
        strings[value]=[hex(h) for h in hits]
        a.refs+=hits
    for r in a.refs:refs[hex(r)]=im.refs_to(r)
    callers={hex(r):im.calls_to(r) for r in a.callers}
    for row in list(refs.values())+list(callers.values()):
        for hit in row:
            if hit['container_rva']:funcs.add(int(hit['container_rva'],16))
    for r,start,end in a.table:
        rows=[]
        for off in range(start,end,8):
            v=struct.unpack_from('<Q',im.data,im.off(r+off))[0]-im.base;rows.append([hex(off),hex(v)])
            if im.function(v):funcs.add(v)
        tables[hex(r)]=rows
    hashes={}
    for value in a.hash:
        pos=0;hits=[]
        while True:
            pos=im.data.find(struct.pack('<Q',value),pos)
            if pos<0:break
            r=im.rva(pos);f=im.function(r);hits.append([hex(r),hex(f[0]) if f else None]);pos+=1
            if f:funcs.add(f[0])
        hashes[hex(value)]=hits
    data={'engine_sha256':im.sha,'strings':strings,'refs':refs,'callers':callers,'hashes':hashes,'pointers':{hex(r):im.pointers_to(r) for r in a.ptr},'tables':tables,'functions':[im.disasm(r) for r in sorted(funcs)],'game_writes':0,'save_writes':0}
    out.mkdir();(out/'readback.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    with (out/'functions.txt').open('w',encoding='utf-8') as f:
        for row in data['functions']:
            f.write('\nFUNCTION '+row['begin_rva']+'\n')
            for i in row['instructions']:f.write(i['rva']+' '+i['mnemonic']+' '+i['operands']+'\n')
    print(json.dumps({k:v for k,v in data.items() if k!='functions'}));print('Functions:',[(f['begin_rva'],len(f['instructions'])) for f in data['functions']])

if __name__=='__main__':main()
