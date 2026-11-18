"""Read-only, exact-binary native evidence. No process access or game API calls."""
import argparse
import json
import struct
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT/'prealpha/quest_restoration_qr15/saved_graph_state_01'))
from inspect_native import Image

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',required=True)
    for name in ('rva','refs','calls','pointers','qwords'):
        p.add_argument('--'+name,action='append',default=[],type=lambda v:int(v,0))
    p.add_argument('--strings',action='append',default=[])
    args=p.parse_args()
    assert args.out.replace('_','').isalnum()
    out=HERE/'work'/(args.out+'.json')
    assert not out.exists()
    out.parent.mkdir(exist_ok=True)
    im=Image()
    result={'exe_sha256':im.sha,'functions':[im.disasm(r) for r in args.rva],
            'refs':{hex(r):im.refs_to(r) for r in args.refs},
            'calls':{hex(r):im.calls_to(r) for r in args.calls},
            'pointers':{hex(r):im.pointers_to(r) for r in args.pointers},
            'qwords':{hex(r):[(hex(r+i*8),hex(struct.unpack_from('<Q',im.data,im.off(r)+i*8)[0])) for i in range(64)] for r in args.qwords},
            'strings':{},'game_calls':0,'runtime_writes':0}
    for value in args.strings:
        offset=0;hits=[]
        while True:
            offset=im.data.find(value.encode(),offset)
            if offset<0:break
            try:
                rva=im.rva(offset)
                hits.append({'rva':hex(rva),'refs':im.refs_to(rva),'pointers':im.pointers_to(rva)})
            except StopIteration:pass
            offset+=1
        result['strings'][value]=hits
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('functions','qwords')},separators=(',',':')))
    for f in result['functions']:
        print('FUNCTION',f['begin_rva'],f['end_rva'],len(f['instructions']))
        for i in f['instructions']:
            print(i['rva'],i['mnemonic'],i['operands'])

if __name__=='__main__':main()
