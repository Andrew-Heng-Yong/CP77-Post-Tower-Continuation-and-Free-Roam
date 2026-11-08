from model import *
g=model('research/q307_extracted/json/ep1/quest/ep1.questphase.json')['root/10']
for i in [3,4,5]:print(i,{k:v for k,v in g['nodes'][i].items() if k!='phaseGraph'})
