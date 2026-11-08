from model import *
for p in ['research/q307_extracted/json/ep1/quest/ep1.quest.json','research/q307_extracted/json/ep1/quest/main_quests/q307/q307.quest.json']:
 print(p)
 g=model(p)['root']
 for i,n in g['nodes'].items():
  if 'phaseGraph' in n:n={k:v for k,v in n.items() if k!='phaseGraph'}
  print(i,str(n)[:600])
 print(g['edges'])
