"""Read-only exact-engine investigation for the preservation prototype."""
from pathlib import Path
import argparse,json,struct,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--rva',action='append',default=[],type=lambda x:int(x,0));p.add_argument('--callers',action='append',default=[],type=lambda x:int(x,0));p.add_argument('--table',action='append',default=[],nargs=3,type=lambda x:int(x,0))
    p.add_argument('--string',action='append',default=[])
    p.add_argument('--refs',action='append',default=[],type=lambda x:int(x,0))
    p.add_argument('--pointers',action='append',default=[],type=lambda x:int(x,0))
    a=p.parse_args()
    out=HERE/a.out;assert out.parent==HERE and not out.exists();im=Image();functions=set(a.rva);tables={}
    for table,start,end in a.table:
        rows=[]
        for off in range(start,end,8):
            v=struct.unpack_from('<Q',im.data,im.off(table+off))[0]-im.base
            rows.append({'slot':hex(off),'rva':hex(v)})
            if im.function(v):functions.add(v)
        tables[hex(table)]=rows
    callers={hex(r):im.calls_to(r) for r in a.callers}
    strings={}
    for value in a.string:
        hits=[];offset=0;needle=value.encode()+b'\0'
        while True:
            offset=im.data.find(needle,offset)
            if offset<0:break
            hits.append(im.rva(offset));offset+=1
        strings[value]=[hex(r) for r in hits]
    refs={hex(r):im.refs_to(r) for r in a.refs+[int(r,16) for rows in strings.values() for r in rows]}
    pointers={hex(r):im.pointers_to(r) for r in a.pointers}
    for matches in list(callers.values())+list(refs.values()):
        for match in matches:
            if match['container_rva']:functions.add(int(match['container_rva'],16))
    data={'engine_sha256':im.sha,'method':'Static file bytes; no process access or native calls','tables':tables,'strings':strings,'reference_candidates':refs,'pointers':pointers,'call_candidates':callers,'functions':[im.disasm(r) for r in sorted(functions)],'game_writes':0,'save_writes':0}
    out.mkdir();(out/'readback.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'out':a.out,'tables':tables,'strings':strings,'pointers':pointers,'functions':[{'rva':f['requested_rva'],'instructions':len(f['instructions'])} for f in data['functions']]}))

if __name__=='__main__':main()
