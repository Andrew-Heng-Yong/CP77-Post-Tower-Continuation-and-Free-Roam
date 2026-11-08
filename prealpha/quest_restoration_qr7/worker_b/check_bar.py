"""Read-only current-layout Ronald placement checker, independent of WK's old index field.

Run: python -X utf8 -B prealpha/quest_restoration_qr7/worker_b/check_bar.py --out bar_check_01
No resource writer or builder is imported. A fresh result directory is required.
"""
from lib import *
import argparse,math,struct,copy,re

LAYOUT=W/'research/framework_pr63_01/archivexl/src/Red/StreamingSector.hpp'
NODEREF=W/'research/framework_pr63_01/archivexl/vendor/RED4ext.SDK/include/RED4ext/NodeRef.hpp'
def fnv(s):
 h=0xcbf29ce484222325
 s=re.sub(r';[^/]*','',s).replace('#','')
 for c in s.encode('utf-8'):h=((h^c)*0x100000001b3)&0xffffffffffffffff
 return 0 if h==0xcbf29ce484222325 else h

def inspect(raw,root):
 rr=Resource({'Data':{'RootChunk':root}});nodes=[rr.d(z)for z in root['nodes']]
 typed=root['nodeData']['Data'];errors=[];rows=[]
 if len(raw)%0x90:errors.append('setup-buffer-length-not-multiple-144')
 if len(raw)//0x90!=len(typed):errors.append('typed-raw-count-mismatch')
 for i in range(len(raw)//0x90):
  b=raw[i*0x90:(i+1)*0x90];packed=struct.unpack_from('<Q',b,0x70)[0];ix=packed&0x7ffff
  ref=struct.unpack_from('<Q',b,0x58)[0];proxy=struct.unpack_from('<Q',b,0x60)[0]
  distance,stream=struct.unpack_from('<ff',b,0x78)
  if ix>=len(nodes):errors.append(f'node-index-out-of-range:{i}:{ix}');continue
  t=typed[i];text=val(t['QuestPrefabRefHash']);expected=int(text)if str(text).isdigit()else fnv(text)
  if ref!=expected:errors.append(f'global-reference-differs:{i}')
  if int(t['NodeIndex'])!=struct.unpack_from('<H',b,0x78)[0]:errors.append(f'old-typed-index-layout-not-reproduced:{i}')
  if not(math.isfinite(distance)and math.isfinite(stream)):errors.append(f'non-finite-distances:{i}')
  rows.append({'setup':i,'node_index':ix,'packed_70':f'{packed:016X}','global_node_id':str(ref),'proxy_node_id':str(proxy),
   'reference':text,'type':nodes[ix]['$type'],'debug_name':val(nodes[ix].get('debugName')),
   'position':dict(zip('xyz',struct.unpack_from('<fff',b,0))),
   'secondary_reference_distance':distance,'streaming_distance':stream,'old_WK_NodeIndex':t['NodeIndex'],
   'node_payload_sha256':hashlib.sha256(json.dumps(nodes[ix],sort_keys=True).encode()).hexdigest().upper()})
 for suffix in ['#q302_tr_ronald_area_02','#q302_tr_ronald_area_02_closer']:
  found=[r for r in rows if str(r['reference']).endswith('/'+suffix)]
  if len(found)!=1:errors.append('required-marker-count:'+suffix+':'+str(len(found)))
  elif found[0]['type']!='worldTriggerAreaNode':errors.append('required-marker-type:'+suffix)
 return rows,errors

def main():
 a=argparse.ArgumentParser();a.add_argument('--out',required=True);args=a.parse_args();out=H/args.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir()
 provider=read(H/'bar_provider_02/manifest.json')['providers'][0];bp=read(H/'bar_buffer_01/manifest.json')
 checks=[]
 def ck(name,ok,**detail):checks.append({'name':name,'pass':bool(ok),**detail})
 for p,h in [(provider['raw'],provider['raw_sha256']),(provider['json'],provider['json_sha256']),(bp['buffer'],bp['buffer_sha256'])]:ck('pin:'+str(p),sha(p)==h)
 raw=Path(bp['buffer']).read_bytes();root=Resource(read(provider['json'])).root
 rows,errors=inspect(raw,root);ck('raw-current-layout-75-placement-bindings',not errors,errors=errors)
 required=[r for r in rows if str(r['reference']).endswith(('/#q302_tr_ronald_area_02','/#q302_tr_ronald_area_02_closer'))]
 ck('exact-two-marker-nonzero-native-bar-prefab-identities',len(required)==2 and all(r['global_node_id']!='0'and '/#q302_pr_bar/#q302_05_bar/'in r['reference']for r in required))
 ck('all-native-sector-descriptor-indices-covered',sorted(r['node_index']for r in rows)==list(range(75)))
 ck('typed-old-index-is-invalid-for-all75',all(r['old_WK_NodeIndex']>=75 for r in rows))
 mutants=[]
 raw2=bytearray(raw);p=required[0]['setup']*0x90;word=struct.unpack_from('<Q',raw2,p+0x70)[0];struct.pack_into('<Q',raw2,p+0x70,(word&~0x7ffff)|99999)
 _,err=inspect(raw2,root);mutants.append({'fault':'out-of-range-packed-node-index','detected':bool(err),'errors':err})
 raw2=bytearray(raw);raw2[p+0x58]^=1
 _,err=inspect(raw2,root);mutants.append({'fault':'changed-native-global-marker-identity','detected':bool(err),'errors':err})
 raw2=bytearray(raw);p=required[1]['setup']*0x90;word=struct.unpack_from('<Q',raw2,p+0x70)[0];struct.pack_into('<Q',raw2,p+0x70,(word&~0x7ffff)|0)
 _,err=inspect(raw2,root);mutants.append({'fault':'marker-bound-to-workspot-instead-of-trigger','detected':bool(err),'errors':err})
 for m in mutants:ck('mutation:'+m['fault'],m['detected'])
 report={'status':'PASS'if all(c['pass']for c in checks)else'FAIL','scope':'Current native packed placement and exact marker membership; no lease/runtime/shape occupancy claim.',
 'source_epoch':{'path':str(W/'prealpha/quest_restoration_qr6/source_epoch_00.json'),'sha256':sha(W/'prealpha/quest_restoration_qr6/source_epoch_00.json')},
 'provider':provider,'buffer_pin':bp,'layout_source':{'path':str(LAYOUT),'sha256':sha(LAYOUT),'field_evidence':'CompiledNodeInstanceSetupInfo: size0x90, 19-bit nodeIndex+0x70, globalNodeID+0x58, floats+0x78/+0x7C'},
 'node_reference_hash_source':{'path':str(NODEREF),'sha256':sha(NODEREF),'algorithm':'RED4ext NodeRef::Hash skips # and ;... through next / before FNV-1a; empty is0'},
 'checks':checks,'mutations':mutants,'placements':rows,'required_markers':required,'type_counts':dict(collections.Counter(r['type']for r in rows)),
 'lease_conclusion':'Both selected conditions bind quest-sector triggers with nonzero native-bar prefab identity. This capture provides no marker-only acquisition/release or executing saved-owner proof. No full-bar owner copy is authorized.',
 'historical_hash_mismatch':{'historical':read(H/'bar_provider_02/manifest.json')['historical_expected'],'current':provider['raw_sha256'],'conclusion':'Different bytes; the old placement coordinates/name-index binding is not reused as current proof. Asset movement is not inferred.'},
 'runtime_changes':0,'serialized_resources':0}
 save(out/'evidence.json',report);print(report['status'],len(checks),'checks',len(rows),'placements',len(mutants),'raw-byte mutants')
 if report['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
