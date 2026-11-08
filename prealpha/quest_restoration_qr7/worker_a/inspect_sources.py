"""Bounded read-only target inspection; all output is private evidence."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,value
from model import Resource
OLD=W/'prealpha/quest_restoration_qr5/groups/G11/reviews/CVI02_EP1'
def run(o):
 assert not o.exists();pins=read(OLD/'verification_03/source_pins.json');out={'pins':[],'graphs':{}}
 for x in pins:
  if 'depot'not in x or not x['depot'].endswith('.questphase'):continue
  p=Path(x['json']);r=Resource(read(p)).normalize();out['pins'].append(x);out['graphs'][x['depot']]=r
 sector=read(W/'research/phase2b_p4/staging_scan/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/ep1/always_loaded_0.streamingsector.json')['Data']['RootChunk']
 out['marker']=sector['nodes'][2577];out['marker_node_data']=sector['nodeData']['Data'][4670];out['node_data_type']=sector['nodeData'].get('$type')
 out['same_prefab_nodes']=[]
 for i,n in enumerate(sector['nodes']):
  if str(n.get('Data',{}).get('sourcePrefabHash',''))=='5807650261310263587':out['same_prefab_nodes'].append({'index':i,'node':n})
 write(o/'sources.json',out);print(json.dumps({'graphs':[(d,[(gp,len(g['nodes']))for gp,g in m['graphs'].items()])for d,m in out['graphs'].items()],'marker':out['marker'],'node_data':out['marker_node_data'],'same_prefab':[(x['index'],x['node']['Data'].get('$type'),value(x['node']['Data'].get('debugName')))for x in out['same_prefab_nodes']]},indent=2))
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output))
