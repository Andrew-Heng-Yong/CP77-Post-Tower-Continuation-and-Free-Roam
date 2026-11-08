"""Verify the actual integrated successor and publish source epoch QR7:03."""
from pathlib import Path
import sys,copy,zlib
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_01';R=C/'repair_ronald_01'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
assert not (O/'source_epoch_03.json').exists()
p=read(R/'promotion.json');m=read(R/'readback_02/manifest.json');checks=[]
def ck(name,ok,evidence):
 checks.append({'name':name,'pass':bool(ok),'evidence':evidence});assert ok,name
def canon(v):
 if isinstance(v,dict):
  if v.get('$type')=='TweakDBID':
   s=str(v['$value']);v=copy.deepcopy(v);v['$storage']='uint64';v['$value']=str(int(s))if s.isdigit()else str((len(s.encode())<<32)|zlib.crc32(s.encode()))
  return{k:canon(x)for k,x in v.items()if k not in ['payload_sha256','metadata_sha256']}
 if isinstance(v,list):return[canon(x)for x in v]
 return v
ck('readback promotion pin',m['promotion_sha256']==sha(R/'promotion.json'),str(R/'promotion.json'))
for x,y in zip(p['rows'],m['rows'],strict=True):
 ck('actual integrated raw '+x['depot'],x['depot']==y['depot']and sha(y['raw'])==y['raw_sha256']==x['after'],y['raw'])
 ck('fresh export pin '+x['depot'],sha(y['json'])==y['json_sha256'],y['json'])
 a,b=read(y['json']),read(x['approved_json'])
 if x['depot'].endswith('.questphase'):
  an,bn=Resource(a).normalize(),Resource(b).normalize()
  ck('graph integrity '+x['depot'],not an['errors'],an['errors'])
  ck('entire approved graph/payload equality '+x['depot'],canon(an)==canon(bn),x['approved_json'])
 else:ck('entire approved typed data equality '+x['depot'],a['Data']==b['Data'],x['approved_json'])
 if 'buffer'in y:ck('exact packed two-trigger bytes',sha(y['buffer'])==read(O/'worker_b/experiments/markers_04/NOT_FOR_INTEGRATION.json')['buffer_sha256'],y['buffer'])
e=read(O/'source_epoch_02.json');a=read(O/'approved_changes_02.json')
for x in p['rows']:
 a['resources'].append({**{k:x[k]for k in ['depot','before','after','intent']},'id':'QR7-RONALD-FUTURE-NEWS','source_serialized_artifact':x['source'],'source_review':p['source_review'],'source_review_sha256':p['source_review_sha256'],'namespace_review':p['namespace_review'],'namespace_review_sha256':p['namespace_review_sha256'],'actual_readback':str(R/'readback_02/manifest.json'),'actual_readback_sha256':sha(R/'readback_02/manifest.json'),'scope':'Prospective positive Armed event and genuine existing enrollment/contact only. Existing entered/sent/pending clocks defer without resets. No native news or contact replay.'})
source={str(f.relative_to(C/'archive_source')):sha(f)for f in (C/'archive_source').rglob('*')if f.is_file()};base=read(O/'source_epoch_00.json')['source_resources']
expected=base.copy()
for x in a['resources']:
 ck('exact approved baseline predecessor '+x['depot'],base.get(x['depot'])==x['before'],x['before']);expected[x['depot']]=x['after']
ck('complete source allowlist',source==expected,{'baseline':len(base),'current':len(source),'changed_existing':sum(k in base and v!=base[k]for k,v in source.items()),'added':len(set(source)-set(base))})
inherited=[]
for x in a['inherited_repair_resources']:
 if source[x['depot']]==x['after']:
  ck('prior repaired resource byte-preserved '+x['depot'],True,x['after']);inherited.append({'depot':x['depot'],'preservation':'EXACT_BYTES','sha256':x['after']});continue
 # Spy's previously corrected Mark/Ana controller is in a resource receiving
 # the new Armed splice. Prove every existing node and old edge elsewhere.
 ck('only reviewed Spy prior resource changed',x['depot']=='towercontinued\\native_gigs_u9\\sts_ep1_08_entry.questphase'and base[x['depot']]==x['after'],x['depot'])
 old=Resource(read(O/'worker_c/reviews/ronald_01/raw_exports_01/before_sts_ep1_08.json')).normalize()
 nr=next(y for y in m['rows']if y['depot']==x['depot']);new=Resource(read(nr['json'])).normalize()
 ck('all Spy graph identities and metadata preserved',set(old['graphs'])==set(new['graphs'])and canon(old['metadata'])==canon(new['metadata']),nr['json'])
 for gp,bg in old['graphs'].items():
  ag=new['graphs'][gp]
  ck('all Spy existing node payloads preserved '+gp,all(canon(v)==canon(ag['nodes'][k])for k,v in bg['nodes'].items()),len(bg['nodes']))
  if gp=='root/50':
   ck('only future Armed edge splice Spy',set(ag['nodes'])-set(bg['nodes'])=={'65007'}and [v for v in bg['edges']if v not in ag['edges']]==[['65002','Out','65003','In']]and [v for v in ag['edges']if v not in bg['edges']]==[['65002','Out','65007','In'],['65007','Out','65003','In']],gp)
  else:ck('other Spy edges preserved '+gp,bg['edges']==ag['edges']and set(bg['nodes'])==set(ag['nodes']),gp)
 inherited.append({'depot':x['depot'],'preservation':'ALL_EXISTING_NODES_AND_PHONE_FIXES_PRESERVED_ONLY_FUTURE_ARM_SPLICE','before':x['after'],'after':source[x['depot']],'readback':nr['json']})
a['status']='THREE_APPROVED_REPAIRS_NINE_RESOURCE_DELTAS_PACKAGE_PENDING';a['registration_change']={k:p[k]for k in ['xl_before_sha256','xl_after_sha256','registration_id','registration_parent','input','append_only','prior_registrations','prior_blocks']};a['unique_new_repairs']=3
write(R/'verification.json',{'status':'PASS_ACTUAL_INTEGRATED_MODELS_SOURCE_ALLOWLIST_AND_PRIOR_REPAIRS','checks':checks,'inherited_preservation':inherited,'promotion':str(R/'promotion.json'),'fresh_manifest':str(R/'readback_02/manifest.json'),'before_readback_failure':'readback_01 exported resources but manifest failed due PowerShell variable case collision; no runtime/resource writes occurred; readback_02 is authoritative','prepromotion_failed_attempts':['missing optional PyYAML dependency before any mutation; dependency removed in favor of exact byte-preserving insertion','namespace check count treated as list before mutation; schema corrected'],'scope':'Exact serialized bytes/model equality with independently reviewed source. No gameplay proof.'})
a['integrated_verification']=str(R/'verification.json');a['integrated_verification_sha256']=sha(R/'verification.json');write(O/'approved_changes_03.json',a)
e.update(epoch=3,epoch_key='QR7:03',source_resources=source,xl_sha256=p['xl_after_sha256'],changes=a['resources'],approved_changes_sha256=sha(O/'approved_changes_03.json'),predecessor_epoch_path=str(O/'source_epoch_02.json'),predecessor_epoch_sha256=sha(O/'source_epoch_02.json'),scope='Three accepted repairs: Nitro entry, CVI alternate phone lifecycle, future-only four-gig Ronald news; six existing resources changed and three new resources. Eight prior repaired resources byte-identical; all old Spy nodes including its Mark/Ana fixes preserved with only a future Armed edge splice. Archive explicitly awaits rebuild.',package_state='SOURCE_FROZEN_ARCHIVE_PENDING_REBUILD')
write(O/'source_epoch_03.json',e)
q=read(O/'queue.json');q.update(source_epoch=3,source_epoch_manifest=str(O/'source_epoch_03.json'),QR7_changes=a['resources'],package_verification='SOURCE_FROZEN_ARCHIVE_REBUILD_PENDING');write(O/'queue.json',q)
print({'status':'PASS_SOURCE_FROZEN_QR7_03','payloads':len(source),'checks':len(checks),'changed_existing':6,'added':3})
