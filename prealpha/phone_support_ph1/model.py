import json,hashlib
from pathlib import Path
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def model(p):
 o=read(p);handles={x['HandleId']:x['Data'] for x in walk(o) if 'HandleId'in x and 'Data'in x}
 def d(x):return x.get('Data',handles.get(x.get('HandleRefId'),x)) if isinstance(x,dict) else x
 def clean(x,seen=frozenset()):
  if isinstance(x,dict):
   h=x.get('HandleId',x.get('HandleRefId'))
   if h is not None:
    if h in seen:return None
    y=d(x)
    if y is not x:return clean(y,seen|{h})
   return {k:clean(v,seen) for k,v in x.items() if k not in ('sockets','connections')}
  if isinstance(x,list):return [clean(v,seen) for v in x]
  return x
 graphs={}
 def graph(g,path):
  g=d(g);nodes={d(x)['id']:d(x) for x in g['nodes']};sockets={}
  for i,n in nodes.items():
   for s in n.get('sockets',[]):sockets[s.get('HandleId',s.get('HandleRefId'))]=(i,d(s)['name']['$value'])
  edges=set()
  for n in nodes.values():
   for s in n.get('sockets',[]):
    for c in d(s).get('connections',[]):
     c=d(c);a=c['source'];b=c['destination'];a=sockets.get(a.get('HandleId',a.get('HandleRefId')));b=sockets.get(b.get('HandleId',b.get('HandleRefId')))
     assert a and b,(path,a,b)
     edges.add((*a,*b))
  graphs[path]={'nodes':{i:clean(n) for i,n in nodes.items()},'edges':sorted(edges)}
  for i,n in nodes.items():
   if isinstance(d(n.get('phaseGraph')),dict) and 'nodes'in d(n['phaseGraph']):graph(n['phaseGraph'],path+'/'+str(i))
 graph(o['Data']['RootChunk']['graph'],'root');return graphs
