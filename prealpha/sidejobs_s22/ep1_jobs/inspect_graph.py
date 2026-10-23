"""Read-only compact quest graph inspection for this S22 audit."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'tools'))
from analyze_q307 import walk,unwrap,cname,scalar_details
p=Path(sys.argv[1]); d=json.loads(p.read_text(encoding='utf-8-sig'))
h={str(o['HandleId']):o['Data'] for o,_,_ in walk(d) if 'HandleId' in o and isinstance(o.get('Data'),dict)}
for g,path,anc in walk(d):
 if g.get('$type')!='questGraphDefinition':continue
 label='root'+''.join('/'+str(a['id']) for a in anc if a.get('$type')=='questPhaseNodeDefinition')
 if len(sys.argv)>2 and label!=sys.argv[2]:continue
 print('GRAPH',label)
 nodes=dict(unwrap(w,h) for w in g['nodes']); own={sh:k for k,n in nodes.items() for sh,_ in (unwrap(w,h) for w in n.get('sockets',[]))}
 for k,n in nodes.items():
  edges=[]
  for w in n.get('sockets',[]):
   sh,s=unwrap(w,h)
   if s.get('type')!='Output':continue
   for cw in s.get('connections',[]):
    _,c=unwrap(cw,h);dh,ds=unwrap(c['destination'],h)
    edges.append([cname(s['name']),nodes[own[dh]]['id'],cname(ds['name'])])
  detail=scalar_details({key:value for key,value in n.items() if key not in ('sockets','phaseGraph')})
  print(n['id'],n['$type'],json.dumps(edges),json.dumps(detail))
