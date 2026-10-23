"""Read-only scene control-flow and persistent fact audit."""
import json,sys,collections
from pathlib import Path
from audit import load,walk

def inspect(path):
 r=load(Path(path))['Data']['RootChunk'];handles={}
 for v in walk(r):
  if 'HandleId' in v and 'Data' in v:handles[v['HandleId']]=v['Data']
 def resolve(v):return v.get('Data',handles.get(v.get('HandleRefId'),v))
 g=resolve(r['sceneGraph']);nodes={resolve(h)['nodeId']['id']:resolve(h) for h in g['graph']};edges={}
 for i,n in nodes.items():
  edges[i]=[(o['stamp'],d['nodeId']['id']) for o in n.get('outputSockets',[]) for d in o['destinations']]
  facts=[v for v in walk(n) if v.get('$type') in ('questSetVar_NodeType','questVarComparison_ConditionType')]
  if '--all' in sys.argv or facts or n['$type'] in ('scnStartNode','scnEndNode','scnQuestNode','scnChoiceNode'):
   print(json.dumps({'id':i,'type':n['$type'],'facts':facts,'choices':[v.get('caption') for v in n.get('options',[])],'edges':edges[i]},separators=(',',':')))
 print('entry',json.dumps(r['entryPoints'],separators=(',',':')));print('exit',json.dumps(r['exitPoints'],separators=(',',':')))
 return r,nodes,edges

if __name__=='__main__':inspect(sys.argv[1])
