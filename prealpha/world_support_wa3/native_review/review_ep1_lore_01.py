import json,collections
from pathlib import Path
R=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
rows=[]
for h in read(R/'ep1_lore_native_01/report_01.json')['hits']:
 j=read(h['copy']+'.json');nn=list(walk(j));types=collections.Counter(n.get('$type','') for n in nn);ops=[n for n in nn if n.get('$type') in ['questSetVar_NodeType','questCharacterManagerCombat_Kill','questCharacterManagerParameters_SetStatusEffect','questSpawnManagerNodeDefinition'] or ('Kill' in n.get('$type','') and 'Condition' not in n.get('$type',''))];rows.append({'depot':h['depot'],'binary':h['copy'],'sha256':h['sha256'],'types':{t:n for t,n in types.items() if t.startswith('quest')},'stateful_operations':ops})
assert len(rows)==3 and all(r['types'].get('questFactsDBManagerNodeDefinition',0)>0 for r in rows)
(R/'ep1_lore_exclusion_assessment_01.json').write_text(json.dumps({'status':'PASS_STATEFUL_NATIVE_DEPENDENCIES_FILTERED','scenes':rows,'disposition':'HighPeak removals omit scene and paired attractor nodes; remaining passive612 EP1 spots retained across four sectors. These are one-off stateful lore actions, not ordinary pure ambient speech.'},indent=2)+'\n',newline='\n')
print([(r['depot'],r['types'].get('questFactsDBManagerNodeDefinition',0),len(r['stateful_operations'])) for r in rows])
