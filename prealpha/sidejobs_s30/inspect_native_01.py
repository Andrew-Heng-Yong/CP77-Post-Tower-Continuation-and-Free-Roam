"""Compact inspection of native quest entry graphs; read only."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCES={
 'pony':ROOT/'research/whitelist_outside_review_20261026/shape_pony_native_01/json/base/open_world/mini_world_stories/badlands/se5/mws_se5_07/mws_se5_07.questphase.json',
 'career':ROOT/'research/whitelist_outside_review_20261026/career_native_01/json/base/open_world/mini_world_stories/watson/mws_wat_08/mws_wat_08.questphase.json',
 'coaster':ROOT/'research/b0_world_interactions/extended/json/base/quest/minor_quests/mq006/mq006.questphase.json',
}

def val(x):
 if isinstance(x,dict):
  if '$value' in x:return x['$value']
  if 'realPath' in x:return x['realPath']
  if 'HandleRefId' in x:return '#'+x['HandleRefId']
  return {k:val(v) for k,v in x.items() if k not in ('sockets','connections','sceneGraph','nodes','debugSymbols','parameters','graph','phaseGraph','data','Data','workspots')}
 if isinstance(x,list):return [val(v) for v in x]
 return x

def inspect(label,path):
 doc=json.loads(path.read_text(encoding='utf-8'))
 graph=doc['Data']['RootChunk']['graph']['Data']
 refs={x['HandleId']:x['Data'] for x in walk(doc) if 'HandleId' in x and 'Data' in x}
 print('\n',label,len(graph['nodes']))
 for w in graph['nodes']:
  n=w.get('Data',{})
  typ=n.get('$type','').replace('quest','')
  data={k:val(refs.get(v.get('HandleId'),v) if isinstance(v,dict) else v) for k,v in n.items() if k not in ('id','sockets','phaseGraph','debugName')}
  descendants=[x for x in walk(n) if isinstance(x,dict)]
  keys=('factName','realPath','DepotPath','rewardName','rewardID','rewardId','socketName')
  markers=[str(val(x[k])) for x in descendants for k in keys if k in x]
  print(n.get('id'),typ,' '.join(dict.fromkeys(markers))[:500],json.dumps(data,ensure_ascii=False)[:180])
  if label=='coaster' and n.get('id') in (15,50,51,52,53,55):
   pg=n.get('phaseGraph',{}).get('Data',{})
   print('  EMBED',len(pg.get('nodes',[])),{v for x in walk(pg) for v in [x.get('factName')] if v})

def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)

if __name__=='__main__':
 for label,path in SOURCES.items():inspect(label,path)
