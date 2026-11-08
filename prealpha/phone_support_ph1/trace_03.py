from model import *
gs=model('research/q307_extracted/json/ep1/quest/ep1.questphase.json')
for gp,g in gs.items():
 for i,n in g['nodes'].items():
  text=str({k:v for k,v in n.items() if k!='phaseGraph'})
  if any(s in text for s in ['holocall','q307_ep1_killed','Terminating','q307_before']):
   print(gp,i,text);print([e for e in g['edges'] if e[0]==i or e[2]==i])
