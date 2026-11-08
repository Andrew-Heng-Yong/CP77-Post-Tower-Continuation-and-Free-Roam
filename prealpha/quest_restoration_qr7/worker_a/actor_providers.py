"""Targeted actor definitions and registry memberships; pin before current use."""
from pathlib import Path
import sys,json,struct
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,value,walk,depots
S=W/'research/phase2b_p4/staging_scan/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/always_loaded_1.streamingsector.json'
def run(o,source=S,packed=False):
 assert not o.exists();r=read(source)['Data']['RootChunk'];nodes=[];entries=[]
 for i,h in enumerate(r['nodes']):
  n=h['Data'];dn=str(value(n.get('debugName')))
  if dn in ['SpawnSet_#mr_hands_combat_zone','SpawnSet_#mr_hands_holo']:
   ds=[]
   for j,d in enumerate(r['nodeData']['Data']):
    idx=struct.unpack('<I',struct.pack('<f',d['MaxStreamingDistance']))[0]&0x7ffff if packed else d['NodeIndex']
    if idx==i:ds.append({'index':j,'placement':d})
   nodes.append({'node_index':i,'node':h,'placements':ds,'refs':depots(n)})
  if n['$type']=='worldCommunityRegistryNode':
   for j,c in enumerate(n.get('communitiesData',[])):
    if any(str(value(x))in ['#mr_hands_combat_zone','#mr_hands_holo','mr_hands_combat_zone','mr_hands_holo']for x in walk(c)):entries.append({'node_index':i,'community_index':j,'entry':c,'registry_header':{k:v for k,v in n.items()if k in ['$type','debugName','sourcePrefabHash']},'refs':depots(c)})
 out={'scope':'Current provider typed definitions and packed placement correlation'if packed else'Historical typed lookup only pending exact current provider equality','source':str(source),'source_sha256':sha(source),'nodes':nodes,'registry_entries':entries};write(o/'evidence.json',out);print(json.dumps({'nodes':[(x['node_index'],value(x['node']['Data'].get('debugName')),x['node']['Data']['$type'],[d['index']for d in x['placements']],x['refs'])for x in nodes],'entries':[(x['node_index'],x['community_index'],list(x['entry']),x['refs'])for x in entries]},indent=2))
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--source');a.add_argument('--packed',action='store_true');z=a.parse_args();run(Path(z.output),Path(z.source)if z.source else S,z.packed)
