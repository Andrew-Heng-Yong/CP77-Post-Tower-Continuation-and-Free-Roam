"""Read-only concise native graph/capture inspection for the S23 base-B family."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'prealpha/sidejobs_s23'))
from audit import graphs,walk,value

if __name__=='__main__':
 p=Path(sys.argv[1]); wanted=sys.argv[2] if len(sys.argv)>2 else 'root'
 for g in graphs(p):
  if g['path']!=wanted:continue
  print('GRAPH',g['path'])
  for n in g['nodes']:
   facts=[o for o in walk(n) if o.get('$type','') in ('questVarComparison_ConditionType','questVarVsVarComparison_ConditionType','questSetVar_NodeType')]
   journals=[o['realPath'] for o in walk(n) if 'realPath' in o]
   refs=[str(value(o['DepotPath'])) for o in walk(n) if 'DepotPath' in o]
   details={k:v for k,v in n.items() if k not in ('id','$type','phaseGraph')}
   print(n['id'],n['$type'],'F',json.dumps(facts,separators=(',',':')),'J',journals,'R',refs,'OUT',[e for e in g['edges'] if e[0]==n['id']])
   if '--full' in sys.argv:print(json.dumps(details,separators=(',',':')))
