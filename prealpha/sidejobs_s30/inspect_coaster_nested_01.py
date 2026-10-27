import json
from inspect_native_01 import SOURCES,walk
d=json.loads(SOURCES['coaster'].read_text(encoding='utf-8'))
g=d['Data']['RootChunk']['graph']['Data']
for w in g['nodes']:
 n=w['Data'];nid=n['id']
 if nid not in (15,50,51,52,53,55):continue
 print('\nOUTER',nid)
 for nw in n['phaseGraph']['Data']['nodes']:
  x=nw['Data'];refs=[]
  for y in walk(x):
   for k in ('factName','realPath','DepotPath','rewards'):
    if k in y:refs.append(str(y[k].get('$value',y[k]) if isinstance(y[k],dict) else y[k]))
  print(x['id'],x['$type'],','.join(sorted(set(refs)))[:340])
