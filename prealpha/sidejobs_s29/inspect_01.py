"""Compact current native graph evidence for entry and follow-up review."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,walk,value
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten,references

def graphs(path):
    r=SafeResource(read(path)); return flatten(r,r.obj['Data']['RootChunk'])
def compact(n):
    v={k:v for k,v in n.items() if k not in ['phaseInstancePrefabs','unfreezingTriggerNodeRef','saveLock']}
    return json.dumps(v,ensure_ascii=False,separators=(',',':'))
def main():
    folder=ROOT/'research/sidejobs_s29/native_01'
    suffix=sys.argv[1] if len(sys.argv)>1 else '01'
    out=ROOT/f'research/sidejobs_s29/graphs_{suffix}'
    out.mkdir(parents=True,exist_ok=False)
    rows=[]
    for p in sorted(folder.glob('*/json/**/*.questphase.json')):
        depot=str(p).split('json\\',1)[-1].removesuffix('.json')
        gs=graphs(p); filename=p.parent.name+'__'+p.name.removesuffix('.questphase.json')
        q=out/(filename+'.json'); q.write_text(json.dumps(gs,indent=2)+'\n',encoding='utf-8')
        lines=[]
        for g in gs:
            lines.append(g['path'])
            for n in g['nodes']:
                lines.append(compact(n))
                lines.append(' -> '+str([e[1:] for e in g['edges'] if e[0]==n['id']]))
        (out/(filename+'.txt')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
        rows.append(dict(source=str(p.relative_to(ROOT)).replace('\\','/'),depot=depot,graphs=len(gs),file=filename))
    (out/'index.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    print('Flattened',len(rows),'resources into',out)
if __name__=='__main__':main()
