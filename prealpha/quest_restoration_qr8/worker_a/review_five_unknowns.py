"""Independent QR8 Worker C peer: actual bytes/resources, without importing C checker."""
from inspect_archivexl import *
import collections
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource
C=ROOT/'prealpha/quest_restoration_qr8/worker_c'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def walk(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from walk(x)
 elif isinstance(v,list):
  for x in v:yield from walk(x)
def main():
 out=HERE/'reviews/C_five_01';out.mkdir(parents=True,exist_ok=False);x=Binary(Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/bin/x64/Cyberpunk2077.exe'));tests=[];pins=[];cache={x.path.resolve():((x.stat.st_size,x.stat.st_mtime_ns),x.sha)}
 def sha(p):
  p=Path(p);s=p.stat();k=(s.st_size,s.st_mtime_ns);resolved=p.resolve()
  if resolved not in cache:cache[resolved]=(k,hashlib.sha256(p.read_bytes()).hexdigest().upper())
  assert cache[resolved][0]==k,'changed input '+str(p)
  return cache[resolved][1]
 def ck(n,b,e=None):tests.append({'name':n,'pass':bool(b),'evidence':e});assert b,n
 for pin in read(C/'findings_03/source_pins.json'):
  ck('source pin '+pin['path'],sha(pin['path'])==pin['sha256']);pins.append(pin)
 # Every pinned assembly capture is regenerated independently from the current EXE.
 regenerated=[]
 for pin in pins:
  p=Path(pin['path'])
  if p.suffix!='.asm':continue
  lines=p.read_text().splitlines();parsed=[re.fullmatch(r'([0-9A-Fa-f]{8}): (.*)',line) for line in lines if line.strip()]
  ck('assembly text shape '+p.name,all(parsed) and bool(parsed))
  s=int(parsed[0][1],16);expected=[m[2] for m in parsed];off=x.off(s)
  actual=list(x.md.disasm(x.b[off:off+0x20000],x.base+s,count=len(expected)))
  ck('actual EXE regenerates capture '+str(p),[f'{a.address-x.base:08X}: {a.mnemonic} {a.op_str}' for a in actual]==[m[0] for m in parsed]);regenerated.append(str(p))
 def ins(r,data=None):
  b=x.b if data is None else data;return next(x.md.disasm(b[x.off(r):x.off(r)+15],x.base+r,count=1))
 def op(r,m,s):
  a=ins(r);ck(hex(r)+' '+m+' '+s,a.mnemonic==m and a.op_str==s)
 def rip(r):
  a=ins(r);o=next(o for o in a.operands if o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP);return a.address+a.size+o.mem.disp-x.base
 op(0x1fb2b4,'xor','eax, eax');op(0x1fb2b6,'cmp','eax, dword ptr [rcx]');op(0x1fb2b8,'jne',hex(x.base+0x1fb2bf));op(0x1fb2ba,'cmp','al, byte ptr [rcx + 4]');op(0x1fb2bd,'je',hex(x.base+0x1fb2c6));op(0x1fb2bf,'cmp','dword ptr [rcx + 8], eax');op(0x1fb2c2,'je',hex(x.base+0x1fb2c6));op(0x1fb2c4,'mov','al, 1')
 op(0x21f5e22,'cmp','dword ptr [rbx + 0xa0], 0');op(0x21f5e29,'je',hex(x.base+0x21f5e68));op(0x21f5e2b,'cmp','byte ptr [rbx + 0xa4], 0');op(0x21f5e32,'je',hex(x.base+0x21f5e68));op(0x21f5e60,'call','qword ptr [rax + 0x2f0]');op(0x21f5e89,'mov','r8d, dword ptr [rbx + 0xb4]');op(0x21f5e90,'lea','rdx, [rbx + 0xb0]');op(0x21f5ea0,'call',hex(x.base+0x88cd20));op(0x88cd2d,'cmp','dword ptr [rcx], eax');op(0x88cd2f,'setae','al')
 inv=read(C/'inventory_native_02/manifest.json');cands=[c for c in inv['constructor_candidates'] if any(m['slot']==0xf0 and m['rva']==0xd9631c for m in c['methods'])];ck('actual inventory class final evaluate vtable',len(cands)==1 and struct.unpack_from('<Q',x.b,x.off(cands[0]['instance_vtable'])+0xf0)[0]-x.base==0xd9631c)
 # Exact requested-interface globals, current initialization offsets and registration stores.
 systems=read(C/'context_systems_01/manifest.json')['systems'];labels={'inventory_context_C0':(0x90a5a4,'gameITransactionSystem',0x3c79db,0x3c79e3,0xc0),'inject_context_170':(0xc0c130,'gameIContainerManager',0x3c7c6d,0x3c7c75,0x170),'device_context_58':(0x3c8b8c,'gameIPersistencySystem',0x3c7857,0x3c785f,0x58)}
 for s in systems:
  get,name,call,store,offset=labels[s['context_field']];ck('actual getter requests interface '+name,rip(get)==s['class_global_rva'])
  for f in s['registration_stores']:
   ck('registration writes same requested-class global '+name,rip(f['store_rva'])==s['class_global_rva'])
   ck('registration literal exactly identifies interface '+name,[x.b[x.off(a['rva']):x.off(a['rva'])+len(name)+1] for a in f['strings']]==[name.encode()+b'\0'])
  op(store,'mov',f'qword ptr [rbx + {hex(offset)}], rcx')
 slots=read(C/'container_slots_01/slots.json');ck('concrete ContainerManager slot258 read from actual native vtable',struct.unpack_from('<Q',x.b,x.off(slots['instance_vtable_rva'])+0x258)[0]-x.base==0x1527428)
 op(0x152747a,'call',hex(x.base+0x7af278));op(0x7af2b9,'cmp','qword ptr [rcx + 0x30], rbx');op(0x7af2cc,'call',hex(x.base+0x2b3a064));op(0x7af331,'call',hex(x.base+0x7af3ac));op(0x7af364,'call',hex(x.base+0x7af4b4));op(0x2b3a073,'mov','ebx, dword ptr [rcx + 0xc]');op(0x2b3a07c,'inc','ebx');op(0x2b3a09d,'mov','dword ptr [rdi + 0xc], ebx');op(0x2b3a0ab,'call',hex(x.base+0x7af90c))
 op(0x10738c4,'mov','rbx, r9');op(0x10738c7,'mov','rsi, qword ptr [rdx + 0x58]');op(0x1073903,'mov','rdx, rbx');op(0x1073906,'call','qword ptr [rax + 0x10]');op(0x1073925,'mov','r10, qword ptr [rcx + 0x1b0]');op(0x107392f,'call','r10');op(0x10739cf,'call','qword ptr [rax + 0x1c0]')
 # Independent mutation oracle: these actual bytes must preserve the known numeric branch meanings.
 for rel,r,m in [('mutant_itemid_jne.bin',0x1fb2b8,'jne'),('mutant_quantity_seta.bin',0x88cd2f,'setae'),('mutant_inventory_je.bin',0x21f5e29,'je')]:
  start={'mutant_itemid_jne.bin':0x1fb2b4,'mutant_quantity_seta.bin':0x88cd20,'mutant_inventory_je.bin':0x21f5e22}[rel];b=(C/'findings_03'/rel).read_bytes();decoded=next(x.md.disasm(b[r-start:],x.base+r,count=1));ck('independent actual mutant violates branch contract '+rel,decoded.mnemonic!=m)
 cap=read(C/'capture_01/manifest.json');rows={r['depot']:r for r in cap['resources']};typed={d:read(r['json']) for d,r in rows.items()};cuck=next(d for d in rows if d.endswith('sts_std_rcr_02_dixon.scene'));preds=[n for n in walk(typed[cuck]) if n.get('$type')=='questInventory_ConditionType' and n['itemID'].get('$value')=='114327022403'];ck('actual Dixon numeric source predicate bound',len(preds)==1 and preds[0]['quantity']==1 and preds[0]['comparisonType']=='GreaterOrEqual')
 num=114327022403;ck('actual raw record takes observed CRC-and-length branch',(num&0xffffffff)!=0 and ((num>>32)&255)!=0)
 nulls=read(C/'findings_03/cuckoo_numeric_and_nulls.json')['native_nulls'];ck('four native serialized-null recipients remain explicitly unresolved',{r['node'] for r in nulls}=={'11','13','15','2'} and all(r['source'] is None for r in nulls))
 vd=next(d for d in rows if d.endswith('quest_02032d862a5c14c8.streamingsector'));sector=typed[vd]['Data']['RootChunk'];ck('actual exact Voodoo prefab only supplies one native area trigger',len(sector['nodes'])==1 and sector['nodes'][0]['Data']['$type']=='worldTriggerAreaNode' and sector['persistentNodes']==[])
 spatial=read(C/'findings_03/voodoo_spatial_and_native.json');ck('exact descriptor names the actual one-trigger sector',spatial['descriptor']['descriptor_index']==1809 and spatial['descriptor']['descriptor']['data']['DepotPath']['$value']==vd)
 opaque=read(C/'exterior_capture_01/manifest.json');ck('three exterior candidates retained opaque not ownership proof',len(opaque['resources'])==3 and all(r['status']=='OPAQUE' and 'DynamicBaseClass' in r['error'] for r in opaque['resources']))
 career=read(C/'findings_03/career_owner_bound.json');ck('Career search explicitly bounded to three carriers and derivative',len(career['carrier_candidates'])==3 and not any(r['hits'] for r in career['carrier_candidates']) and career['script_hits']==[])
 updates=read(C/'findings_03/contract_updates.json');ck('all five original exact contracts retain UNKNOWN and named missing evidence',len(updates)==5 and all(r['status']=='UNKNOWN' and len(r['remaining'])>=2 for r in updates))
 ck('no runtime repair is smuggled into dispositions',all(r.get('runtime_changes')==[] for r in updates))
 # Applicability to actual selected QR8 epoch, without a broad catalogue pass.
 ep=read(ROOT/'prealpha/quest_restoration_qr8/source_epoch_00.json');targeted=read(C/'baseline_01/baseline.json')['targeted_sources']
 for r in targeted:
  dep=str(Path(r['path']).relative_to(Path(ep['candidate'])/'archive_source')).replace('/','\\');ck('actual selected epoch target bytes '+dep,sha(r['path'])==r['sha256']==ep['source_resources'][dep])
 result={'status':'APPROVE_BOUNDED_FIVE_UNKNOWN_DISPOSITIONS_AND_CORRECTED_CONTAINER_BINDING','checks':len(tests),'regenerated_actual_assembly_captures':len(regenerated),'source_pins_checked':len(pins),'actual_byte_mutants_independently_rejected':3,'contracts':5,'UNKNOWN_retained':5,'new_runtime_defects_confirmed':[],'repair_approved':False,'input':x.freshness(),'scope_findings':['Cuckoo ItemID validity is (CRC nonzero OR encoded length nonzero) AND seed nonzero; raw-ID quantity dispatch separately requires both CRC and length. The actual114327022403 satisfies that dispatcher. No current TDB definition lookup is present in these bounded predicates; inventory contents/provider remain unobserved.','Inject phase-context170 positively requests gameIContainerManager. Concrete258 dispatch appends a descriptor to a loaded container or pending entity queue. The QR7 TransactionSystem candidate chain is superseded for this executing boundary; downstream consumer/merge/one-time behavior remains unknown.','Device controllerClass is an actual RTTI/PersistencySystem input, so TerminalControllerPS versus DoorControllerPS cannot be dismissed. Exact entity/component ownership remains unobserved.','The exact Voodoo quest descriptor contains one trigger, not a door/container. Three opaque exterior candidates do not prove absence or exhaustive ownership.','Career carrier/script literal absences are bounded and do not retire the original early owner or certify saved concurrency.'],'remaining':['Exact original provenance/implicit activation of Cuckoo four NULL-source entries and historical item/provider/inventory.','Actual Voodoo door/container resources, persistent IDs/components; source-realizable prior claim history; hub12, container consumer/merge and saved ownership lifecycle.','Career original early notification executing-owner registration and Tower retirement/saved transition.'],'limitations':['Independent review reads actual native bytecode/resources and regenerates captured disassembly. It does not execute the game, simulate a save or approve broad native equivalence.','Current source epoch applicability is checked only for the eight C-targeted staged resources. Root owns full package/source preservation.'],'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest().upper(),'candidate_or_runtime_writes':0}
 for n,v in [('review.json',result),('checks.json',tests),('input_pins.json',pins)]: (out/n).write_text(json.dumps(v,indent=2),encoding='utf8')
 print({'status':result['status'],'checks':len(tests),'regenerated':len(regenerated),'pins':len(pins),'out':str(out)})
if __name__=='__main__':main()
