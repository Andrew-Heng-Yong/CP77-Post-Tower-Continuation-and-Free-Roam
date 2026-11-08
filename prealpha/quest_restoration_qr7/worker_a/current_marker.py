"""Pin and independently locate the native Hands static marker in fresh providers."""
from pathlib import Path
import sys,json,copy,struct
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,value,walk
P=W/'prealpha/quest_restoration_qr7/shared/marker_providers_01'
TARGET='mr_sm_hands_combat_zone_default';PREFAB='mr_hands_combat_zone_default_prefabPY55PSI'
def extract(doc,packed=False):
 r=doc['Data']['RootChunk'];found=[]
 for i,h in enumerate(r['nodes']):
  n=h.get('Data',{})
  if value(n.get('debugName'))!=TARGET:continue
  for j,d in enumerate(r['nodeData']['Data']):
   idx=struct.unpack('<I',struct.pack('<f',d['MaxStreamingDistance']))[0]&0x7ffff if packed else d['NodeIndex']
   if idx==i:found.append({'node_index':i,'data_index':j,'node':h,'placement':d})
 return found
def run(o):
 assert not o.exists();manifest=read(P/'manifest.json');pin=next(x for x in manifest['providers']if x['raw'].endswith('provider_2.streamingsector'));bp=next(x for x in manifest['providers']if x['raw'].endswith('provider_1.streamingblock'))
 for x in [pin,bp]:assert sha(Path(x['raw']))==x['raw_sha256']and sha(Path(x['json']))==x['json_sha256']
 f=extract(read(Path(pin['json'])),True);old=extract(read(Path(pin['old_json'])));assert len(f)==len(old)==1
 s=read(Path(pin['json']))['Data']['RootChunk'];b=read(Path(bp['json']))['Data']['RootChunk'];rows=[]
 for i,d in enumerate(b['descriptors']):
  text=json.dumps(d)
  if PREFAB in text or 'always_loaded_0.streamingsector' in text:rows.append({'index':i,'descriptor':d})
 m=f[0];n=m['node']['Data'];refs=[x for x in walk(n)if x.get('$type')in ['NodeRef','ResourcePath']and value(x)not in ['0',0,'None','']]
 dt=m['placement'];decoded={'NodeIndex':struct.unpack('<I',struct.pack('<f',dt['MaxStreamingDistance']))[0]&0x7ffff,'secondary_ref_distance':struct.unpack('<f',struct.pack('<HH',dt['NodeIndex'],dt['Uk10']))[0],'streaming_distance':struct.unpack('<f',struct.pack('<HH',dt['Uk11'],dt['Uk12']))[0]}
 layout=W/'research/framework_pr63_01/archivexl/src/Red/StreamingSector.hpp'
 out={'scope':'Exact fresh provider placement correlated by current2.5 packed19bit layout, not WK9.1 old NodeIndex; root separately resolves precedence','manifest_path':str(P/'manifest.json'),'manifest_sha256':sha(P/'manifest.json'),'layout_source':str(layout),'layout_sha256':sha(layout),'decoded_layout':decoded,'source_pins':[pin,bp],'current':m,'historical':old[0],'typed_target_equal':m['node']['Data']==old[0]['node']['Data'],'placement_equal':m['placement']==old[0]['placement'],'stable_placement_fields_equal':all(dt[k]==old[0]['placement'][k]for k in ['Position','Orientation','Scale','Pivot','Bounds','QuestPrefabRefHash','UkHash1','CookedPrefabData']),'external_marker_refs':refs,'related_descriptors':rows,'all_sector_nodes_with_same_source_prefab_hash':[(i,value(h['Data'].get('debugName')),h['Data']['$type'])for i,h in enumerate(s['nodes'])if h['Data'].get('sourcePrefabHash')==n['sourcePrefabHash']],'sector_variant_indices':s['variantIndices'],'sector_variant_nodes':s['variantNodes']}
 write(o/'evidence.json',out);print(json.dumps({k:v for k,v in out.items()if k not in ['current','historical','related_descriptors','source_pins']},indent=2));print('current node/data',m['node_index'],m['data_index'],'descriptor matches',[(x['index'],list(x['descriptor']))for x in rows])
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);run(Path(a.parse_args().output))
