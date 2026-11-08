"""Independent whole QR8 package gate; no coordinator/proposal checker imports."""
from inspect_archivexl import ROOT,HERE
from pathlib import Path,PurePosixPath
import argparse,json,hashlib,zipfile,zlib,copy,itertools,binascii
import sys
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def fnv(s):
 h=0xcbf29ce484222325
 for c in s.encode():h=((h^c)*0x100000001b3)&0xffffffffffffffff
 return str(h)
def predicate(c,f):
 if c['$type']=='questLogicalCondition':
  vs=[predicate(x,f) for x in c['conditions']]
  assert c['operation'] in ['AND','OR'];return all(vs) if c['operation']=='AND' else any(vs)
 assert c['$type']=='questFactsDBCondition';t=c['type'];assert t['$type']=='questVarComparison_ConditionType' and t['comparisonType']=='Equal';return f[t['factName']]==t['value']
def prune(m):
 q=copy.deepcopy(m);q.pop('metadata_sha256',None)
 for g in q['graphs'].values():
  for n in g['nodes'].values():
   for k in ['payload_sha256','reads','conditions']:n.pop(k,None)
 return q
def main(a):
 out=Path(a.output).resolve();out.relative_to(HERE);out.mkdir(parents=True,exist_ok=False);I=read(a.inputs);E=read(I['epoch']);B=read(I['baseline']);A=read(a.capture);P=read(I['package_manifest']);checks=[];cache={}
 def sha(p):
  p=Path(p).resolve();st=p.stat();state=(st.st_size,st.st_mtime_ns)
  if p not in cache:
   digest=hashlib.sha256(p.read_bytes()).hexdigest().upper();st2=p.stat();assert state==(st2.st_size,st2.st_mtime_ns),'input changed during hash';cache[p]=(state,digest)
  assert cache[p][0]==state,'input changed after hash';return cache[p][1]
 def ck(n,b,e=None):checks.append({'name':n,'pass':bool(b),'evidence':e});assert b,n
 for field in ['epoch','baseline','approved','package_manifest','prototype_plan','independent_source_approval','native_namespace_capture','namespace_result','prior_inherited_gate']:
  ck('frozen input '+field,sha(I[field])==I[field+'_sha256'])
 ck('fresh extraction bound to these independent input pins',A['input_sha256']==sha(a.inputs) and A['archive_sha256']==I['archive_sha256'])
 ck('actual final archive and ZIP equal frozen epoch',sha(I['archive'])==E['archive_sha256']==I['archive_sha256'] and sha(I['zip'])==E['zip_sha256']==I['zip_sha256'])
 def inventory(folder):
  rows={}
  for p in Path(folder).rglob('*'):
   st=p.lstat();ck('no linked source/package path '+str(p),not p.is_symlink() and not getattr(st,'st_file_attributes',0)&0x400)
   if p.is_file():rows[p.relative_to(folder).as_posix()]={'sha256':sha(p),'bytes':st.st_size}
  return rows
 source=inventory(I['source']);canon={p.replace('/','\\'):r['sha256'] for p,r in source.items()};ck('all actual source paths/hashes equal canonical epoch',canon==E['source_resources']==I['canonical_resources'])
 ck('all depot hashes unique',len({fnv(p) for p in canon})==len(canon))
 rows=A['members'];ck('every actual archive member resolves uniquely to canonical source',len(rows)==len(canon) and len({r['fnv64'] for r in rows})==len(rows) and all(r['canonical_key'] for r in rows) and {r['depot'] for r in rows}==set(canon));members={r['depot']:r for r in rows};actual={}
 for d,r in members.items():
  ck('extracted payload matches canonical source '+d,sha(r['raw'])==r['raw_sha256']==canon[d] and fnv(d)==r['fnv64']);actual[d]=r['raw_sha256']
 old=B['source_resources'];changed=sorted(d for d in set(old)&set(actual) if old[d]!=actual[d]);ck('only approved single resource changed; no additions/deletions',changed==I['changed'] and set(actual)==set(old) and len(changed)==1)
 ck('every other QR7 payload byte-preserved',all(actual[d]==old[d] for d in old if d not in changed))
 d=changed[0];proto=I['prototype'];r=members[d];ck('actual packaged changed member equals approved private binary',sha(proto['raw'])==proto['raw_sha256']==actual[d]);ck('fresh actual member typed readback is pinned',r.get('typed_status')=='FRESH_ACTUAL_FINAL_ARCHIVE_MEMBER' and sha(r['json'])==r['json_sha256'] and sha(proto['json'])==proto['json_sha256'])
 final=Resource(read(r['json'])).normalize();approved=Resource(read(proto['json'])).normalize();ck('whole actual graph/node/socket/reference/metadata tree equals approved proposal',final==approved and not final['errors'])
 originalrow=proto['source'];ck('old source model is bound to actual QR7 bytes',sha(originalrow['raw'])==originalrow['raw_sha256']==old[d] and sha(originalrow['json'])==originalrow['json_sha256']);before=Resource(read(originalrow['json'])).normalize();expected=copy.deepcopy(before)
 cases=[('12','200'),('08','201'),('03','202'),('01','203')]
 for code,node in cases:
  p=expected['graphs']['root/202']['nodes'][node]['payload']['condition'];p['conditions'][0]={'$type':'questLogicalCondition','conditions':[p['conditions'][0],{'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRQR7_RonaldNews_Armed_sts_ep1_'+code,'value':1}}],'operation':'OR'}
 ck('entire semantic difference is exactly four reviewed first-case predicates',prune(expected)==prune(final))
 ck('root issuance and all graphs/edges/nodeIDs/sockets/prefabs preserved',before['graphs']['root']==final['graphs']['root'] and before['metadata']==final['metadata'] and all(g['entries']==final['graphs'][gp]['entries'] and g['edges']==final['graphs'][gp]['edges'] and set(g['nodes'])==set(final['graphs'][gp]['nodes']) and all(n['sockets']==final['graphs'][gp]['nodes'][i]['sockets'] and n['prefabs']==final['graphs'][gp]['nodes'][i]['prefabs'] for i,n in g['nodes'].items()) for gp,g in before['graphs'].items()))
 spec=read(ROOT/'prealpha/quest_restoration_qr7/worker_b/future_protocol_spec_01.json');nativeids=set(map(str,spec['kept_native_ids']));ck('all native protocol nodes and timers retain exact models',all(before['graphs']['root/202']['nodes'][i]==final['graphs']['root/202']['nodes'][i] for i in nativeids))
 fixtures=[]
 for code,node in cases:
  q='sts_ep1_'+code;arm='PTFRQR7_RonaldNews_Armed_'+q;sent='q302_msg_ronald_'+q;parent='PTFRU9_'+q+'_ParentEntered';g=final['graphs']['root/202']['nodes'][node]['payload']['condition'];og=before['graphs']['root/202']['nodes'][node]['payload']['condition']
  for done,seen,earned,entered in itertools.product([0,1],repeat=4):
   f={q+'_done':done,sent:seen,arm:earned,parent:entered};got=predicate(g,f);was=predicate(og,f);want=not seen and (not entered or earned) and (not done or earned)
   ck('actual final predicate case '+q+str((done,seen,earned,entered)),got==bool(want) and (got==was or done==1 and seen==0 and earned==1));fixtures.append({'quest':q,'done':done,'sent':seen,'Armed':earned,'ParentEntered':entered,'before':was,'after':got,'abstract_source_predicate_only':True})
 # Actual semantic before-state and a real edited guard are independent failure controls.
 ck('defective packaged QR7 route fails intended late future contract',all(not predicate(before['graphs']['root/202']['nodes'][node]['payload']['condition'],{'sts_ep1_'+code+'_done':1,'q302_msg_ronald_sts_ep1_'+code:0,'PTFRQR7_RonaldNews_Armed_sts_ep1_'+code:1,'PTFRU9_sts_ep1_'+code+'_ParentEntered':1}) for code,node in cases))
 bad=copy.deepcopy(final);bad['graphs']['root/202']['nodes']['200']['payload']['condition']['conditions'].pop(1);ck('actual final guard sent-history deletion is rejected',prune(expected)!=prune(bad))
 # Every older correction remains bound to the independent QR8-start gate.
 prior=read(I['prior_inherited_gate']);ck('bounded inherited gate remains applicable to nine exact QR7 resources',prior['inherited_resources']==len(I['inherited']) and all(actual[r['depot']]==old[r['depot']] for r in I['inherited']))
 ck('inherited eight exact repair bytes and Spy semantic successor preserved',sum(actual[r['depot']]==r['after'] for r in I['inherited'])==8 and next(r for r in I['inherited'] if actual[r['depot']]!=r['after'])['depot']==r'towercontinued\native_gigs_u9\sts_ep1_08_entry.questphase')
 package=inventory(I['package']);oldpkg={r['path']:r for r in B['package_files']};epkg={r['path']:{'sha256':r['sha256'],'bytes':r['bytes']} for r in E['package_files']};mpkg={r['path']:{'sha256':r['sha256'],'bytes':r['bytes']} for r in P['files']}
 ck('exact package paths/hashes/sizes equal frozen epoch and package manifest',package==epkg==mpkg and set(package)==set(oldpkg));pdiff=sorted(p for p in oldpkg if oldpkg[p]['sha256']!=package[p]['sha256']);ck('only consolidated archive package file changed',pdiff==['archive/pc/mod/zzzz_PTFR_Combined.archive'])
 ziprows=[]
 with zipfile.ZipFile(I['zip']) as z:
  infos=[i for i in z.infolist() if not i.is_dir()];names=[i.filename for i in infos];ck('ZIP exact package path inventory with no duplicates',set(names)==set(package) and len(names)==len(set(names))==len(package) and len({n.casefold() for n in names})==len(names));ck('ZIP all paths contained and CRC test succeeds',all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names) and z.testzip() is None)
  for info in infos:
   data=z.read(info);h=hashlib.sha256(data).hexdigest().upper();ck('ZIP member CRC/SHA/size '+info.filename,h==package[info.filename]['sha256'] and len(data)==package[info.filename]['bytes']==info.file_size and zlib.crc32(data)&0xffffffff==info.CRC);ziprows.append({'path':info.filename,'sha256':h,'CRC32':f'{info.CRC:08X}','bytes':len(data)})
 # Exact unchanged XL preserves registered paths/order/CRC IDs and prior provider gate.
 xl=Path(I['package'])/'archive/pc/mod/zzzz_PTFR_Combined.archive.xl';oldxl=Path(B['candidate'])/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl';ck('entire XL bytes unchanged including all old order and IDs',sha(xl)==sha(oldxl)==E['xl_sha256']==B['xl_sha256'])
 capture=read(I['native_namespace_capture']);game=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077');oldarchives=[v for v in capture['archive_index_inventory'] if v['classification']!='QR7_STAGED_NOT_INSTALLED'];ck('no new on-disk game archive provider since bounded namespace capture',{str(p).replace('\\','/').lower() for p in game.rglob('*.archive')}=={str(Path(v['path'])).replace('\\','/').lower() for v in oldarchives})
 for ar in oldarchives:
  st=Path(ar['path']).stat();ticks=st.st_mtime_ns//100+621355968000000000;ck('namespace provider metadata stable '+ar['path'],st.st_size==ar['bytes'] and ticks==ar['mtime_utc_ticks'])
 xlgame=[v for v in capture['xl_configs'] if not v['candidate']];ck('no new on-disk XL provider since bounded namespace capture',{str(p).replace('\\','/').lower() for p in game.rglob('*.xl')}=={str(Path(v['path'])).replace('\\','/').lower() for v in xlgame})
 for f in xlgame:ck('namespace configuration bytes unchanged '+f['path'],sha(f['path'])==f['sha256'])
 nk=read(I['namespace_result']);ck('namespace proofs apply to unchanged depot keys and registered owner',nk['new_generated_id']==19913 and nk['effective_target_root_registrations']==826 and set(canon)==set(old) and not read(I['approved'])['registration_changed'])
 cr=read(P['compile_reuse']);ck('exact unchanged REDscript compile evidence remains pinned',sha(P['compile_reuse'])==P['compile_reuse_sha256'] and cr['status']=='PASS_EXACT_UNCHANGED_FULL_COMPILE_INPUTS_AND_SUCCESSOR_REDS' and all(package[p]['sha256']==oldpkg[p]['sha256'] for p in package if p.endswith('.reds')))
 for p,(state,h) in cache.items():
  st=p.stat();assert state==(st.st_size,st.st_mtime_ns),'input changed before final report '+str(p)
 result={'status':'PASS_INDEPENDENT_WHOLE_QR8_ARCHIVE_ZIP_SOURCE_DELTA_AND_PRESERVATION','checks':len(checks),'source_epoch':'QR8:02','archive_sha256':I['archive_sha256'],'ZIP_sha256':I['zip_sha256'],'archive_payloads':len(actual),'package_paths':len(package),'changed_existing_resources':changed,'new_resources':0,'unchanged_QR7_payloads':len(old)-len(changed),'whole_proposal_model_parity':True,'four_gate_scalar_cases':len(fixtures),'native_protocol_nodes_preserved':len(nativeids),'inherited_exact_repair_bytes':8,'inherited_Spy_semantic_successor_retained':True,'XL_byte_unchanged':True,'registration_id_preserved':19913,'namespace_scope':'Earlier185-index/76-XL conservative provider gate remains applicable by unchanged keys/XL/current provider metadata and no new provider files. No stock archive rehash or new full world-global census.','prior_compile_reused':True,'limitations':['Static artifact/source parity only; no deployment, game execution, save/fact edits or live SMS/streaming success is established.','Repair applies only at unchanged first case evaluation with real future Armed1 and native sent0; processed branches, old timers, missing enrollment/contact or ambiguous prior owners are not adopted.','Saved-handler resource-predicate refresh, actual timing and private marker acquisition/release remain LIVE_ONLY; five original UNKNOWN contracts remain outside this package PASS.'],'input_manifest':str(Path(a.inputs).resolve()),'input_manifest_sha256':sha(a.inputs),'readback_manifest':str(Path(a.capture).resolve()),'readback_manifest_sha256':sha(a.capture),'checker_sha256':sha(__file__),'candidate_runtime_or_save_writes':0}
 for name,data in [('result.json',result),('checks.json',checks),('payload_hashes.json',actual),('zip_members.json',ziprows),('scalar_cases.json',fixtures)]: (out/name).write_text(json.dumps(data,indent=2),encoding='utf8')
 print(json.dumps(result,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inputs',required=True);p.add_argument('--capture',required=True);p.add_argument('--output',required=True);main(p.parse_args())
