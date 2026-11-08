"""Independent B review of A's frozen QR8 installed-DLL and namespace evidence.

No A verifier/reader or root checker imports. PE bytes are only read/disassembled.
"""
from lib import *
import argparse,struct,re,binascii,copy,collections
sys.path.insert(0,str(W/'research/finalboards_dismissal/tooling/python'))
import pefile,capstone
A=W/'prealpha/quest_restoration_qr8/worker_a'
def decode(n):
 if n['kind']=='scalar':return n.get('value')
 if n['kind']=='sequence':return [decode(x)for x in n['items']]
 if n['kind']=='mapping':
  pairs=[(decode(x['key']),decode(x['value']))for x in n['entries']]
  if not all(isinstance(k,str)for k,v in pairs)or len({k for k,v in pairs})!=len(pairs):raise ValueError('Duplicate/non-string mapping key')
  return dict(pairs)
 raise ValueError('Unsupported AST node')
def crc(s):
 v=65535
 for c in s.encode():
  v^=c<<8
  for _ in range(8):v=((v<<1)^0x1021)&65535 if v&0x8000 else(v<<1)&65535
 return v
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=H/'reviews/A_integration'/a.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True);checks=[];pins=[];mutants=[]
 def ck(n,v,**ev):checks.append({'name':n,'pass':bool(v),**ev})
 def pin(f,expected=None):
  f=Path(f);h=sha(f);pins.append({'path':str(f.resolve()),'sha256':h,'size':f.stat().st_size,'mtime_ns':f.stat().st_mtime_ns})
  if expected:ck('pin:'+str(f),h==expected)
  return h
 be=read(A/'binary_verification_01/evidence.json');ns=read(A/'namespace_verification_01/result.json');ix=read(A/'evidence_index.json')
 pin(A/'evidence_index.json')
 for q in ix['primary_results']:pin(q['path'],q['sha256'])
 for q in be['source_pins']:pin(q['path'],q['sha256'])
 dll=Path(be['input']['path']);pin(dll,be['input']['sha256']);b=dll.read_bytes();pe=pefile.PE(data=b);base=pe.OPTIONAL_HEADER.ImageBase;md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
 def off(r):return pe.get_offset_from_rva(r)
 def ins(data,r):return next(md.disasm(data[off(r):off(r)+16],base+r,count=1))
 def rip(data,r):
  i=ins(data,r);v=[o.mem.disp for o in i.operands if o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP]
  if len(v)!=1:return None
  return i.address+i.size+v[0]-base
 def op(data,r,m,s):i=ins(data,r);return i.mnemonic==m and i.op_str==s
 # Critical observations derived from actual official source semantics and disassembled dataflow.
 def critical(data):
  e=[]
  def need(x,n):
   if not x:e.append(n)
  literal=rip(data,0xf4de0);need(literal is not None and data[off(literal):off(literal)+11]==b'QuestPhase\0','literal-QuestPhase')
  refs=[m.start()for m in re.finditer(re.escape(struct.pack('<Q',base+0xf4de0)),data)];need(len(refs)==1 and struct.unpack_from('<Q',data,refs[0]+8)[0]==base+0xf4ea0,'unique-vtable-next-Load')
  for label,aid,movr,leacb,store,callr,wrapr,leaorig,jmporig in [('preload',0x2f1f26cc,0xf4f1e,0xf4ecb,0xf4ed2,0xf4e18,0xf4eed,0xf4f5b,0xf4e36),('restore',0x7a20106e,0xf5025,0xf4fd2,0xf4fd9,0xf4e89,0xf4ff4,0xf5062,0xf4e97),('root',0x2f8e2179,0xf512c,0xf50d9,0xf50e0,0xf4e58,0xf50fb,0xf5169,0xf4e76)]:
   cb={'preload':0xf5f40,'restore':0xf5a10,'root':0xf6160}[label];wrapper={'preload':0xf4e00,'restore':0xf4e80,'root':0xf4e40}[label]
   need(op(data,movr,'mov','edx, '+hex(aid)),label+'-address-ID');need(rip(data,leacb)==cb,label+'-actual-callback')
   need(rip(data,store)==rip(data,callr)and ins(data,callr).mnemonic=='call',label+'-same-callback-slot');need(rip(data,wrapr)==wrapper,label+'-hook-wrapper-argument');need(rip(data,leaorig)==rip(data,jmporig)and ins(data,jmporig).mnemonic=='jmp',label+'-native-after-callback')
  for r,m,s in [(0xf5ac5,'mov','ecx, dword ptr [r9 + 0xb4]'),(0xf5ad0,'mov','rdx, qword ptr [r9 + 0xa8]'),(0xf5ae3,'cmp','qword ptr [rdx + rax*8], r8'),(0xf5cc6,'call','qword ptr [rax + 0x10]'),(0xf5cc9,'test','eax, eax'),(0xf5ccb,'jne',hex(base+0xf5e1b)),(0xf5da2,'mov','r9, qword ptr [rax + 0x240]'),(0xf5db5,'call','r9'),(0xf5dc2,'mov','r9d, 1'),(0xf5dcc,'mov','edx, r9d'),(0xf5dcf,'call','qword ptr [rax + 0x18]'),(0xf6378,'call','qword ptr [rax + 0x18]')]:need(op(data,r,m,s),'actual-'+hex(r)+'-'+m+s)
  r=rip(data,0xf5cd1);need(r is not None and data[off(r):off(r)+4]==b'In1\0','exact-literal-In1')
  need(op(data,0x130a1e,'movabs','rbx, 0x611101b4bb2a5e9c'),'main-world-key');need(op(data,0x130a60,'call',hex(base+0x122630)),'configured-block-to-RegisterPatch')
  need(op(data,0x12269d,'call',hex(base+0x122440)),'RegisterPatch-overload');need(op(data,0x1205b5,'call',hex(base+0x120bb0)),'world-dispatch-merge')
  need(op(data,0x1204f8,'jne',hex(base+0x1206dc)),'world-RTTI-nonmatch-rejected');need(op(data,0x120d26,'call',hex(base+0x106ec0)),'blockRefs-array-append')
  return e
 errors=critical(b);ck('own-critical-binary-source-dataflow',not errors,errors=errors)
 # Own byte-level counterfactuals; no A mutation checker is used.
 for name,r,change in [('inverse-receipt-branch',0xf5ccb,b'\x0f\x84'),('wrong-virtual-start-slot',0xf5da2,bytes.fromhex('4c8b8848020000')),('zero-private-receipt',0xf5dc2,bytes.fromhex('41b900000000')),('wrong-world-key',0x130a20,b'\x00')]:
  z=bytearray(b);z[off(r):off(r)+len(change)]=change;e=critical(z);mutants.append({'fault':name,'detected':bool(e),'errors':e});ck('own-actual-DLL-mutant:'+name,bool(e))
 # Independent fresh function listings preserve evidence of full surrounding control flow.
 for begin,end in[(0xf4ea0,0xf51b0),(0xf5a10,0xf5ed0),(0xf6160,0xf63a0),(0x130a00,0x130aa0),(0x120bb0,0x120e20)]:
  (out/(hex(begin)+'.asm')).write_text('\n'.join(f'{i.address-base:08X} {i.bytes.hex()} {i.mnemonic} {i.op_str}'for i in md.disasm(b[off(begin):off(begin)+end-begin],base+begin))+'\n',encoding='utf-8')
 capture=Path(ns['source_capture']);pin(capture,ns['source_capture_sha256']);I=read(capture);docs={};rows=[];target=r'ep1\quest\ep1.quest';targetrows=[]
 for f in I['xl_configs']:
  pin(f['path'],f['sha256']);ck('single-supported-YAML-document:'+f['path'],f['parse_status']=='PARSED'and len(f['documents'])<=1)
  d=decode(f['documents'][0])if f['documents']else{};d={}if d is None else d;docs[f['path']]=d
  for p in d.get('quest',{}).get('phases',[]):
   r={'source':f['path'],'candidate':f['candidate'],**p};rows.append(r)
   if p.get('parent')==target:targetrows.append(r)
 ck('direct-literal-parent-count-no-alias-expansion-needed',len(targetrows)==1651 and len(rows)==1728)
 c=next(f for f in I['xl_configs']if f['candidate']);old=next(f for f in I['xl_configs']if not f['candidate']and f['path'].endswith('zzzz_PTFR_Combined.archive.xl'));effective=[r for r in targetrows if r['candidate']or r['source']!=old['path']]
 ck('effective-counterpart-replacement-is826',len(effective)==826)
 ids=[]
 for r in effective:
  input=r.get('input',r.get('connection',[]));node=input.get('node',[])if isinstance(input,dict)else input
  ck('actual-root-input:'+r['path'],node in([],['1']));key=r['path']+':1';n=crc(key);ck('independent-CRC-polynomial:'+r['path'],n==binascii.crc_hqx(key.encode(),65535));ids.append(n)
 owner=NEWS;oi=next(i for i,r in enumerate(effective)if r['path']==owner);ck('new-root-generated-id-unique19913',len(ids)==len(set(ids))and ids[oi]==19913)
 ep=next(p for p in I['matching_providers']if p['depot']==target);pin(ep['raw'],ep['raw_sha256']);pin(ep['json'],ep['json_sha256']);em=Resource(read(ep['json'])).normalize();native=set(map(int,em['graphs']['root']['nodes']));ck('all-generated-IDs-clear-native-parent',native=={0,1,2,12,27}and not native.intersection(ids))
 ck('root1-Out-real-native-start',em['graphs']['root']['nodes']['1']['type']=='questStartNodeDefinition'and {'name':'Out','type':'Output'}in em['graphs']['root']['nodes']['1']['sockets'])
 oldcapture=read(W/'prealpha/quest_restoration_qr7/worker_a/ronald_namespace_inputs_01/manifest.json');oldcand=next(f for f in oldcapture['xl_configs']if f['candidate']);expected=decode(oldcand['documents'][0]);expected=copy.deepcopy(expected);expected['quest']['phases'].append({'path':owner,'parent':target,'input':{'node':['1'],'socket':'Out'}});expected['streaming']['blocks'].append(r'towercontinued\quest_restoration_qr7\ronald_news_markers.streamingblock');ck('entire-XL-tree-only-approved-two-appends',expected==docs[c['path']])
 for ar in I['archive_index_inventory']:
  st=Path(ar['path']).stat();ck('archive-index-current-metadata:'+ar['path'],ar['read_status']=='NoError'and st.st_size==ar['bytes']and st.st_mtime_ns//100+621355968000000000==ar['mtime_utc_ticks'])
 ck('actual-expanded-input-superset185archives76XL',len(I['archive_index_inventory'])==185 and len(I['xl_configs'])==76 and any('ArchiveXL\\Bundle' in x['path']for x in I['archive_index_inventory'])and any('mod_settings' in x['path']for x in I['archive_index_inventory']))
 for d in I['depots'][:-1]:
  providers=[p for p in I['matching_providers']if p['depot']==d];ck('only-staged-provider:'+d,len(providers)==1 and providers[0]['candidate']);v=providers[0];pin(v['raw'],v['raw_sha256']);raw=W/'prealpha/quest_restoration_qr7/candidate_01/archive_source'/d;pin(raw,v['raw_sha256'])
 ck('namespace-counterfactual-duplicate-rejected',len(ids+[ids[oi]])!=len(set(ids+[ids[oi]])))
 bad={'kind':'mapping','entries':[{'key':{'kind':'scalar','value':'a'},'value':{'kind':'scalar','value':1}},{'key':{'kind':'scalar','value':'a'},'value':{'kind':'scalar','value':2}}]}
 try:decode(bad);rejected=False
 except ValueError:rejected=True
 ck('own-YAML-duplicate-not-silently-overwritten',rejected)
 ck('DLL-metadata-stable-after-independent-disassembly',(dll.stat().st_size,dll.stat().st_mtime_ns)==(be['input']['size'],be['input']['mtime_ns']))
 manual=[{'finding':'Bounded method correspondence is supported','disposition':'APPROVE','evidence':'Unique GetName/vtable Load anchor, actual hook address IDs, same callback slots/wrappers, source and full instruction listings, receipt branch and dispatch dataflow. FileVersion alone was not used as proof.'},{'finding':'Receipt is not successful-owner ACK','disposition':'LIMIT','evidence':'Actual SetFact follows the void slot0x240 dispatch with no success-result branch. A retained receipt proves dispatch was attempted, not marker lease acquisition or listener execution. Silent runtime failure cannot be retried automatically without a separately reviewed mechanism.'},{'finding':'World merge does not grant quest ownership','disposition':'LIMIT','evidence':'Actual mainworld/RegisterPatch/type dispatch/blockRefs append corresponds to released source; closed-engine descriptor and PIP lifecycle remain LIVE_ONLY.'},{'finding':'Scope aliases do not affect effective EP1 set','disposition':'APPROVE','evidence':'All1651 captured target rows have literal ep1 parent (installed825+candidate826), so826 effective IDs need no recursive ResourceMeta equivalence assumption.'},{'finding':'Namespace scope is bounded','disposition':'LIMIT','evidence':'185 archive indexes and76 XL files are a conservative on-disk superset. Targeted extracted hashes and stable metadata are checked, not full runtime ResourceDepot registration, all world globals or all named-fact hashes.'}]
 result={'status':'APPROVE_BOUNDED_ACTUAL_DLL_AND_TARGET_NAMESPACE_WITH_LIVE_LIMITS'if all(x['pass']for x in checks)else'FAIL','checks':checks,'check_count':len(checks),'own_DLL_mutations':mutants,'reviewed_input_pins':pins,'manual_adversarial_findings':manual,'primary_A_results':{'binary_assertions':91,'binary_controls':6,'namespace_assertions':920,'namespace_controls':2},'no_A_or_root_checker_import':True,'no_DLL_load_or_runtime_execution':True,'runtime_writes':0,'scope':'Review of frozen QR7:04 candidate/installed ArchiveXL. A later QR8 successor must update payload hash applicability independently; same namespace only if depot names/XL registrations are unchanged.'}
 save(out/'review.json',result);save(out/'hash_observations.json',list(OBS.values()));print(result['status'],len(checks),'own assertions',len(mutants),'own DLL mutants')
 if result['status']=='FAIL':raise SystemExit(1)
if __name__=='__main__':main()
