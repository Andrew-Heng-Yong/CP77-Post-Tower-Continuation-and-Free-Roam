"""Read the exact historical typed Hands marker, without assuming provider equivalence."""
from pathlib import Path
import sys,json,collections
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
P=W/'research/phase2b_p4/staging_scan/ep1_1_nightcity'
S=P/'json/base/worlds/03_night_city/_compiled/default/ep1/always_loaded_0.streamingsector.json'
B=P/'json/base/worlds/03_night_city/_compiled/default/ep1/blocks/all.streamingblock.json'
def run(O):
 assert not O.exists();doc=read(S);root=doc['Data']['RootChunk'];target='mr_sm_hands_combat_zone_default';prefab='mr_hands_combat_zone_default_prefabPY55PSI';out={'scope':'Historical typed placement until root confirms current provider bytes','sector_json':str(S),'sector_json_sha256':sha(S),'root_keys':list(root),'root_type':root['$type'],'collections':{k:len(v)for k,v in root.items()if isinstance(v,list)},'marker_nodes':[],'references':[],'prefab_block_records':[]}
 def visit(x,p=''):
  if isinstance(x,dict):
   if x.get('$type')in['worldStaticMarkerNode','worldEntityNode','worldNode']and target in str(value(x.get('debugName',''))):out['marker_nodes'].append({'json_pointer':p,'type':x['$type'],'debugName':value(x.get('debugName')),'isEnabled':x.get('isEnabled'),'sourcePrefabHash':x.get('sourcePrefabHash'),'fields':list(x),'data_type':x.get('data',{}).get('Data',{}).get('$type')})
   if x.get('$type')=='NodeRef'and prefab in str(value(x)):out['references'].append({'pointer':p,'value':value(x)})
   for k,v in x.items():visit(v,p+'/'+k)
  elif isinstance(x,list):
   for i,v in enumerate(x):visit(v,p+'/'+str(i))
 visit(root,'/Data/RootChunk')
 block=read(B)
 def blocks(x,p=''):
  if isinstance(x,dict):
   for k,v in x.items():
    if k in['nodeRef','prefabNodeRef']and prefab in str(value(v)):out['prefab_block_records'].append({'pointer':p,'object':x})
    blocks(v,p+'/'+k)
  elif isinstance(x,list):
   for i,v in enumerate(x):blocks(v,p+'/'+str(i))
 blocks(block);out['block_json']=str(B);out['block_json_sha256']=sha(B);write(O/'marker.json',out)
 print(json.dumps({k:v for k,v in out.items()if k not in ['prefab_block_records','references']},indent=2));print('References',len(out['references']),'blockrecords',len(out['prefab_block_records']))
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output))
