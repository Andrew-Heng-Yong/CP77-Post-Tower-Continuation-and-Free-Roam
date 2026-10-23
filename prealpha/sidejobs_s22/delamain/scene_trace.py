from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools'))
from inspect_scene_nodes import pick
from analyze_q307 import walk
p=Path(sys.argv[1]); start=int(sys.argv[2]); depth=int(sys.argv[3]) if len(sys.argv)>3 else 8
r=json.loads(p.read_text(encoding='utf-8-sig'))['Data']['RootChunk']; ns={w['Data']['nodeId']['id']:w['Data'] for w in r['sceneGraph']['Data']['graph']}
q=[(start,0)];seen=set()
while q:
    i,d=q.pop(0)
    if i in seen or d>depth:continue
    seen.add(i);n=ns[i];out=[(s.get('stamp'),t['nodeId']['id'],t['isockStamp']) for s in n.get('outputSockets',[]) for t in s.get('destinations',[])]
    details=[]
    for o,_,_ in walk(n):
        if o.get('$type','').endswith('_ConditionType') or o.get('$type','').endswith('_NodeType'): details.append(o)
    print(d,i,n['$type'],'OUT',[(x[0].get('ordinal'),x[1]) for x in out],json.dumps(details,separators=(',',':')))
    q.extend((x[1],d+1) for x in out)
