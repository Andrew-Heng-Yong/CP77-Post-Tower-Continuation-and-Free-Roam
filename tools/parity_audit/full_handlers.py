"""Inventory original/restored handlers beyond executing candidates, bounded per model."""
from common import *
from engine import Models
import collections
def inventory(o,reuse=None):
 idx=read(o/'resource_inventory.json');store=Models(o/'models',Models(reuse/'models') if reuse else None);active=read(o/'execution_contexts.json')['nodes'];counts=collections.Counter();rows=0;node_total=0
 columns=['resource','source_json','sha256','ownership','graph','node','type','active_may','stages','sockets','reads','writes','conditions','journal_paths','prefabs','node_refs','references']
 with (o/'all_handlers.jsonl').open('w',encoding='utf-8') as jf,(o/'all_handlers.csv').open('w',encoding='utf-8',newline='') as cf:
  cw=csv.DictWriter(cf,fieldnames=columns);cw.writeheader()
  for d,r in idx.items():
   if not r.get('graphs'):continue
   m=store.get(d);act={tuple(x) for x in active.get(d,[])}
   for gp,g in m['graphs'].items():
    for i,n in g['nodes'].items():
     node_total+=1;st=[];facts=[str(value(x.get('factName',''))) for x in n['reads']+n['writes']]
     if 'InputNode'in n['type'] or 'StartNode'in n['type'] or n['conditions']:st.append('entry_or_branch')
     if any(f.startswith(('holo_','audio_')) for f in facts):st.append('phone')
     if n['sms']:st.append('sms')
     if n['journal_paths'] or n['writes']:st.append('progression_or_state')
     if 'cleanup'in d.lower() or 'OutputNode'in n['type'] or 'EndNode'in n['type']:st.append('cleanup_or_exit')
     if n['reward']:st.append('rewards')
     if n['prefabs'] or n['node_refs'] or n['refs']:st.append('dependencies_or_support')
     if not st:continue
     rec={'resource':d,'source_json':r.get('json'),'sha256':r['sha256'],'ownership':'RESTORED_PRIVATE' if r.get('private') else 'ORIGINAL_OR_SHARED','graph':gp,'node':i,'type':n['type'],'active_may':(gp,i)in act,'stages':st,'sockets':n['sockets']+n.get('embedded_sockets',[]),'reads':n['reads'],'writes':n['writes'],'conditions':n['conditions'],'journal_paths':n['journal_paths'],'prefabs':n['prefabs'],'node_refs':n['node_refs'],'references':n['refs']}
     jf.write(json.dumps(rec,separators=(',',':'),ensure_ascii=False)+'\n');cw.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in rec.items()});rows+=1;counts.update(st)
 write(o/'handler_coverage.json',{'handlers':rows,'decoded_nodes_examined':node_total,'by_stage_tag':dict(counts),'scope':'Every normalized original/private node examined; tagged rows exported. Full models retain remaining node IDs. MAY reachability is not execution. Tags are lexical classification, not independently proven lifecycle ownership.'});print(json.dumps({'handlers':rows,'nodes_examined':node_total}))
if __name__=='__main__':
 import sys
 inventory(Path(sys.argv[1]),Path(sys.argv[2]) if len(sys.argv)>2 else None)
