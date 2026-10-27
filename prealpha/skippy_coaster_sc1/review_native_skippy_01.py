import json
from pathlib import Path

p=Path(__file__).resolve().parents[2]/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq007/mq007.questphase.json'
r=json.loads(p.read_text())['Data']['RootChunk']['graph']['Data']
n=next(h['Data'] for h in r['nodes'] if h.get('Data',{}).get('id')==3)
print('node type',n['$type'],'keys',list(n))
print('socket names',[(x['Data'].get('name'),x['Data'].get('type'),len(x['Data'].get('connections',[]))) for x in n.get('sockets',[]) if x.get('Data')])
print('native node phase',n.get('phaseGraph',{}).get('Data',{}).keys())
print('prefabs',n.get('phaseInstancePrefabs'))
g=n.get('phaseGraph',{}).get('Data',{})
if g:
 for h in g.get('nodes',[]):
  d=h.get('Data',{})
  print('inner node',d.get('id'),d.get('$type'))
  if d.get('condition'):
   print(' condition',json.dumps(d['condition'])[:1200])
  if d.get('$type')=='questOutputNodeDefinition': print(' output',json.dumps(d)[:800])
  if d.get('phaseResource'):
   print(' phase resource',d['phaseResource'])
  for socket in d.get('sockets',[]):
   sd=socket.get('Data',{})
   edges=[]
   for conn in sd.get('connections',[]):
    cd=conn.get('Data',{})
    edges.append(json.dumps(cd)[:250])
   if edges: print(' socket',sd.get('name'),edges)
