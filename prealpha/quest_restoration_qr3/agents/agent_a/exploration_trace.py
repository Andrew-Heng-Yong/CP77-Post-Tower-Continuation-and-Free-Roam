from pathlib import Path
import json,gzip,sys
W=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';I=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json')
def m(d):return json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()))
def brief(n):
 return {'type':n['type'],'reads':n['reads'],'writes':n['writes'],'refs':n['refs'],'payload':n['payload'] if not n['reads'] else None}
P=r'towercontinued\sidejobs_s27\claire\sq024_fresh.questphase';N=r'base\quest\side_quests\sq024\sq024.questphase'
out={}
for d,gps in [(N,['root/92','root/106','root/22','root/53/55']), (r'base\quest\side_quests\sq024\phases\sq024_00_hook.questphase',['root']), (r'base\quest\holocalls\claire\claire_holocall.questphase',['root']),(r'base\quest\holocalls\claire\claire_cleanup.questphase',['root']), (r'towercontinued\races_r1\main.questphase',['root']), (r'towercontinued\races_r1\owner.questphase',['root'])]:
 x=m(d);out[d]={gp:{'nodes':{i:brief(n) for i,n in x['graphs'][gp]['nodes'].items()},'edges':x['graphs'][gp]['edges'],'entries':x['graphs'][gp]['entries']} for gp in gps if gp in x['graphs']}
write(Path(__file__).parent/'inspection.json',out)
for d,gs in out.items():
 print(d)
 for gp,g in gs.items():
  print(gp, 'nodes',len(g['nodes']),'entries',g['entries'])
  for i,n in g['nodes'].items():
   if n['reads'] or n['writes'] or n['refs']:print(i,n['type'],json.dumps({k:v for k,v in n.items() if k!='payload' and v},ensure_ascii=True)[:900])
  print('edges',g['edges'])
