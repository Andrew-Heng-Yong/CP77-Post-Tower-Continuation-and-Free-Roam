import sys
sys.path.insert(0,'prealpha/sidejobs_s29')
import common
from pathlib import Path

dep=r'base\quest\minor_quests\minorquests.questphase'
root=common.load(dep)['Data']['RootChunk']
h=common.handles(root)
graph=root['graph']['Data']
ids={0,20,54,55,59,62,70,73,80,81,83,84,86,177,178}
for w in graph['nodes']:
 n=common.deref(w,h)
 if n.get('id') in ids:
  refs=[]
  for x in common.walk(n):
   for k in ('factName','realPath','DepotPath'):
    if k in x:refs.append(str(common.value(x[k])))
  print(n['id'],n['$type'],','.join(sorted(set(refs)))[:500])
