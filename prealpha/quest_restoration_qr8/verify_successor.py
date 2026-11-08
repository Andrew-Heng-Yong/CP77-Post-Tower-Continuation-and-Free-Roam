"""Whole actual successor equality, exact four-guard diff and input allowlist."""
from pathlib import Path
import sys,copy,itertools,zlib
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_01';D=C/'repair_late_future_01'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
assert not(O/'source_epoch_01.json').exists()
p=read(D/'promotion.json');m=read(D/'readback_01/manifest.json');plan=read(p['plan']);checks=[]
def ck(n,b,ev=None):checks.append({'name':n,'pass':bool(b),'evidence':ev});assert b,n
def canonical(v):
 if isinstance(v,dict):
  if v.get('$type')=='TweakDBID':
   s=str(v['$value']);v=copy.deepcopy(v);v['$storage']='uint64';v['$value']=str(int(s))if s.isdigit()else str((len(s.encode())<<32)|zlib.crc32(s.encode()))
  return{k:canonical(x)for k,x in v.items()if k not in ['payload_sha256','metadata_sha256']}
 if isinstance(v,list):return[canonical(x)for x in v]
 return v
before=Resource(read(m['before_json'])).normalize();after=Resource(read(m['after_json'])).normalize();approved=Resource(read(p['approved_json'])).normalize()
ck('actual integrated raw pin',sha(C/'archive_source'/p['depot'])==p['after'])
ck('actual readback manifest pins',sha(m['before_json'])==m['before_json_sha256']and sha(m['after_json'])==m['after_json_sha256']and m['promotion_sha256']==sha(D/'promotion.json'))
ck('entire actual integrated model equals independently approved proposal',canonical(after)==canonical(approved))
ck('all resource graph errors absent',not before['errors']and not after['errors'],after['errors'])
ck('all graph identities preserved',set(before['graphs'])==set(after['graphs']))
changed=[]
for gp,bg in before['graphs'].items():
 ag=after['graphs'][gp];ck('all saved node identities and edges '+gp,set(bg['nodes'])==set(ag['nodes'])and bg['edges']==ag['edges'])
 for ident,bn in bg['nodes'].items():
  an=copy.deepcopy(ag['nodes'][ident]);old=copy.deepcopy(bn)
  if gp=='root/202'and ident in ['200','201','202','203']:
   bc=old['payload']['condition'];ac=an['payload']['condition'];case=next(x for x in plan['private_source']['changes']if str(x['node'])==ident)
   ck('top-level guard AND preserved '+ident,bc['operation']==ac['operation']=='AND')
   nc=ac['conditions'][0];ck('exact done0 OR actual private Armed1 '+ident,nc['operation']=='OR'and canonical(nc['conditions'][0])==canonical(bc['conditions'][0])and nc['conditions'][1]=={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRQR7_RonaldNews_Armed_'+case['quest_id'],'value':1}})
   ck('all other original sent/parent guard terms '+ident,canonical(ac['conditions'][1:])==canonical(bc['conditions'][1:]))
   ac['conditions'][0]=bc['conditions'][0]
   for k in ['reads','conditions','refs','node_refs','journal_paths']:an[k]=old[k]
   changed.append({'quest_id':case['quest_id'],'graph':gp,'node':ident})
  ck('all old node semantics except approved first term '+gp+':'+ident,canonical(an)==canonical(old))
ck('metadata/root prefabs/external refs/embedded files preserved',canonical({k:v for k,v in before.items()if k!='graphs'})==canonical({k:v for k,v in after.items()if k!='graphs'}))
base=read(O/'source_epoch_00.json');expected=base['source_resources'].copy();expected[p['depot']]=p['after'];actual={str(f.relative_to(C/'archive_source')):sha(f)for f in(C/'archive_source').rglob('*')if f.is_file()}
ck('all source payloads exact with one approved replacement',actual==expected,{'resources':len(actual),'changed':p['depot']})
ck('all copied package inputs still exact pending rebuild',all(sha(C/'package'/x['path'])==x['sha256']for x in base['package_files']))
write(D/'verification.json',{'status':'PASS_ACTUAL_SUCCESSOR_EXACT_DELTA_AND_ALL_PRIOR_PAYLOADS_PRESERVED','checks':checks,'changed_gates':changed,'old_payloads_unchanged':len(actual)-1,'new_resources':0,'scope':p['source_scope'],'limits':p['limits'],'whole_model':str(D/'readback_01/manifest.json')})
change={'id':'QR8-RONALD-LATE-FUTURE-FIRST-EVALUATION','depot':p['depot'],'before':p['before'],'after':p['after'],'intent':'Permit a genuine QR7 future-entry receipt with done1/sent0 at first case evaluation after an authored helper hold; preserve all old historical guards, timers, nodes and registration identities.','source_plan':p['plan'],'source_plan_sha256':p['plan_sha256'],'independent_review':p['source_review'],'independent_review_sha256':p['source_review_sha256'],'actual_readback':str(D/'readback_01/manifest.json'),'actual_readback_sha256':sha(D/'readback_01/manifest.json'),'actual_verification':str(D/'verification.json'),'actual_verification_sha256':sha(D/'verification.json'),'scope':p['source_scope'],'limits':p['limits']}
ap=O/'approved_changes_01.json';write(ap,{'status':'ONE_APPROVED_SERIALIZED_RUNTIME_REPAIR_ARCHIVE_REBUILD_PENDING','relative_to':'QR7:04','resources':[change],'new_namespaces':0,'registration_changed':False})
e=copy.deepcopy(base);e.update(epoch=1,epoch_key='QR8:01',candidate=str(C),source_resources=actual,changes=[change],predecessor_epoch_path=str(O/'source_epoch_00.json'),predecessor_epoch_sha256=sha(O/'source_epoch_00.json'),approved_changes_sha256=sha(ap),scope='One approved four-guard resource correction; all other QR7 payloads and previous repairs exact. Package explicitly awaits rebuild.',package_state='SOURCE_VERIFIED_ARCHIVE_PENDING_REBUILD')
e['predecessor_archive_sha256']=e.pop('archive_sha256');e.pop('package_manifest_sha256',None);e['predecessor_zip']=e.pop('zip');e['predecessor_zip_sha256']=e.pop('zip_sha256');write(O/'source_epoch_01.json',e)
q=read(O/'queue.json');q.update(source_epoch=1,source_epoch_manifest=str(O/'source_epoch_01.json'),working_candidate=str(C),QR8_changes=[change],QR8_status='ONE_APPROVED_SOURCE_REPAIR_REBUILD_PENDING');write(O/'queue.json',q)
cp=read(O/'checkpoint.json');cp.update(canonical_epoch=str(O/'source_epoch_01.json'),candidate=str(C),new_runtime_changes=1,state='QR8_APPROVED_SOURCE_REPAIR_PROMOTED_PACKAGE_PENDING',next_action='Rebuild and fully read back fresh consolidated archive; package and independently review.');write(O/'checkpoint.json',cp)
print({'status':'PASS_SOURCE_FROZEN_QR8_01','checks':len(checks),'payloads':len(actual),'changed_resources':1,'changed_first_guard_terms':len(changed)})
