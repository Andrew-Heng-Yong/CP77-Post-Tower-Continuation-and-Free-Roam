"""Targeted named-fact/actor-provider lookup, not a quest catalogue re-audit."""
from pathlib import Path
import sys,json,gzip
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
FACTS={'mr_hands_default_on','mr_hands_default_ep1','q307_ep1_killed'}
REFS={'#mr_hands_combat_zone','#mr_hands_holo'}
def run(o):
 assert not o.exists();mi_path=W/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json';mi=read(mi_path);hits=[];pins=[]
 for depot,pin in mi.items():
  raw=Path(pin['normalized_model']).read_bytes();m=json.loads(gzip.decompress(raw));own=[]
  for gp,g in m['graphs'].items():
   for i,n in g['nodes'].items():
    writes=[x for x in n['writes']if x.get('factName')in FACTS];refs=[x for x in n['node_refs']if x in REFS]
    if not writes and not refs:continue
    own.append({'depot':depot,'graph':gp,'node':i,'writes':writes,'node_refs':refs,'payload':n['payload'],'incoming':[e for e in g['edges']if e[2]==i],'outgoing':[e for e in g['edges']if e[0]==i]})
  if own:
   assert sha(Path(pin['normalized_model']))==pin['normalized_sha256'];hits+=own;pins.append({'depot':depot,**pin})
 write(o/'evidence.json',{'scope':'Only three named facts/two actor NodeRefs; historical normalized-model lookup with source pins for exact follow-up','inventory':str(mi_path),'inventory_sha256':sha(mi_path),'models_consulted':len(mi),'hits':hits,'pins':pins});print({'hits':len(hits),'resources':len(pins)});print([(x['depot'],x['graph'],x['node'],[a['factName']for a in x['writes']],x['node_refs'])for x in hits])
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);run(Path(a.parse_args().output))
