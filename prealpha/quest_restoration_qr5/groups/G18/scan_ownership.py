"""Read-only G18 owner/prefab/journal census over pinned normalized sources."""
from lib import *
import argparse
from common import fnv
def run(O):
 assert not O.exists();O.mkdir(parents=True);I=W/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json';mi=read(I)
 targets=['ep1\\quest\\main_quests\\q304\\phases\\q304_slider_stash.questphase','ep1\\quest\\main_quests\\q304\\phases\\q304_car_retrieval.questphase','ep1\\quest\\ep1_persistent_content.questphase','ep1\\quest\\ep1_additional_game_elements.questphase']
 prefabs=['#q304_pr_car_retrieval','#q304_pr_slider_stash_quest'];facts=['q304_05_slider_stash_info_downloaded','q304_car_retrieval_done','q304_car_retrieval_finished','q304_car_retrieval_accepted'];fa={a:f for f in facts for a in[f,fnv(f)]};refs=[];owners=[];js=[];fs=[];pins=[]
 needles=[json.dumps(t)[1:-1].encode()for t in targets]+[fnv(t).encode()for t in targets]+[x.encode()for x in prefabs]+[fnv(x).encode()for x in prefabs]+[b'q304_splinter_stash']+[x.encode()for x in fa]
 for d,row in mi.items():
  data=Path(row['normalized_model']).read_bytes();assert sha(row['normalized_model'])==row['normalized_sha256'];blob=gzip.decompress(data)
  if not any(x in blob for x in needles):continue
  m=json.loads(blob);pins.append({'depot':d,'model':row['normalized_model'],'sha256':row['normalized_sha256']})
  for p in prefabs:
   if any(x==p or x==fnv(p)for x in m['root_prefabs']):owners.append({'depot':d,'scope':'root_phase_prefab','prefab':p,'source_value':m['root_prefabs']})
  for gp,g in m['graphs'].items():
   for i,n in g['nodes'].items():
    for t in targets:
     if t in n['refs']or fnv(t)in n['refs']:refs.append({'depot':d,'graph':gp,'node':i,'target':t,'payload':n['payload'],'incoming':[e for e in g['edges']if e[2]==i],'outgoing':[e for e in g['edges']if e[0]==i]})
    for p in prefabs:
     if any(x==p or x==fnv(p)for x in n['prefabs']):owners.append({'depot':d,'scope':gp+'/'+i,'prefab':p,'payload':n['payload']})
    if any('q304_splinter_stash'in x for x in n['journal_paths']):js.append({'depot':d,'graph':gp,'node':i,'type':n['type'],'payload':n['payload'],'incoming':[e for e in g['edges']if e[2]==i],'outgoing':[e for e in g['edges']if e[0]==i]})
    for kind in['reads','writes']:
     for f in n.get(kind,[]):
      if f.get('factName')in fa:fs.append({'depot':d,'graph':gp,'node':i,'kind':kind,'canonical_fact':fa[f['factName']],'fact':f})
 out={'status':'COMPLETE_PINNED_SOURCE_UNIVERSE_CENSUS_NOT_ENGINE_OWNER_PROOF','models':len(mi),'inventory':str(I),'inventory_sha256':sha(I),'all_actual_gzip_hashes_checked':True,'resource_targets':targets,'prefab_targets':prefabs,'reverse_refs':refs,'prefab_owners':owners,'stash_journal_handlers':js,'fact_handlers':fs,'matched_model_pins':pins,'limits':['Named and FNV-encoded references checked; other opaque engine aliases and dynamic external providers not certified.','All source files refer to frozen QR5epoch00; affected G18 source hashes independently compared with canonical05.','Journal writes and prefab presence are not proof of actual saved owner retirement or placement.']};save(O/'census.json',out);print(json.dumps({'models':len(mi),'prefab_owners':owners,'stash_handlers':len(js),'fact_handlers':len(fs),'review_sha256':sha(O/'census.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(Path(a.output).resolve())
