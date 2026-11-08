"""Independent current-code dispatch and exact Career graph applicability review."""
from pathlib import Path
import sys,struct,hashlib,copy
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'research/finalboards_dismissal/tooling/python'));import pefile,capstone
sys.path.insert(0,str(W/'tools/parity_audit'));from common import read,write,sha,value,walk
from model import Resource
C=W/'prealpha/quest_restoration_qr7/worker_c/journal_proof_02'
def run(o):
 assert not o.exists();e=read(C/'result.json');p=Path(e['input']);cksum=sha(p);assert cksum==e['input_sha256'];b=p.read_bytes();pe=pefile.PE(data=b,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True;T=[]
 def ck(n,v,x=None):T.append({'name':n,'pass':bool(v),'evidence':x});assert v,n
 def raw(a,n):q=pe.get_offset_from_rva(a);return b[q:q+n]
 def ins(a,n):return list(md.disasm(raw(a,n),base+a))
 def qword(a):return struct.unpack('<Q',raw(a,8))[0]-base
 def op(a,n,m,s):return any(x.mnemonic==m and x.op_str==s for x in ins(a,n))
 def call(a,n,target):return any(x.mnemonic=='call'and x.operands[0].type==capstone.x86.X86_OP_IMM and x.operands[0].imm==base+target for x in ins(a,n))
 for f in e['function_files']:
  ck('saved disassembly actual machine-byte pin '+hex(f['bounds'][0]),hashlib.sha256(raw(f['bounds'][0],f['bounds'][1]-f['bounds'][0])).hexdigest().upper()==f['bytes_sha256'])
 ck('actual journal instance vtable dispatch slot290',qword(0x3679e48+0x290)==0x565dfc);ck('actual journal instance vtable dispatch slot268',qword(0x3679e48+0x268)==0x6c1a48);ck('actual journal state getter slot2B0',qword(0x3679e48+0x2b0)==0x6549f8)
 ck('actual graph journal operation vtable process method',qword(0x369e7a8+0x108)==0x56455c);ck('actual graph node delegates state to journal slot290',op(0x56455c,0x270,'call','qword ptr [r10 + 0x290]'));ck('path conversion delegates same state to268',op(0x565dfc,0x10c,'call','qword ptr [rax + 0x268]'));ck('Active2 dispatch and argument preservation',op(0x6c1a48,0xba,'mov','edi, r8d')and op(0x6c1a48,0xba,'mov','r8d, 2')and op(0x6c1a48,0xba,'cmp','edi, r8d')and call(0x6c1a48,0xba,0x6543ec));ck('active state processing calls common',call(0x6543ec,0x126,0x654c0c));ck('common forwards old getter result and new state to guard',op(0x654c0c,0x74,'call','qword ptr [rax + 0x2b0]')and op(0x654c0c,0x74,'mov','r9d, r15d')and op(0x654c0c,0x74,'mov','r8d, eax')and call(0x654c0c,0x74,0x6545d0))
 guard=raw(0x6545d0,16);gi=ins(0x6545d0,16);summary=[(x.mnemonic,x.op_str)for x in gi];ck('exact equality returns zero before guard can reach other state paths',summary[:5]==[('sub','rsp, 0x28'),('cmp','r8d, r9d'),('jne','0x1406545e0'),('xor','al, al'),('add','rsp, 0x28')]and gi[5].mnemonic=='ret',summary)
 early=ins(0x654c61,31);ck('common false guard path exits before write/notification block',[(x.mnemonic,x.op_str)for x in early[:2]]==[('test','al, al'),('jne','0x140654c80')]and early[-1].mnemonic=='ret'and not any(x.mnemonic=='call'for x in early))
 rows=[r for r in e['source_pins']if 'depot'in r];mods={}
 for r in rows:ck('exact raw/typed Career source '+r['depot'],sha(Path(r['raw']))==r['raw_sha256']and sha(Path(r['json']))==r['json_sha256']);mods[r['depot']]=Resource(read(Path(r['json']))).normalize()
 native=mods[r'base\open_world\mini_world_stories\watson\mws_wat_08\mws_wat_08.questphase']['graphs']['root'];rest=mods[r'towercontinued\sidejobs_s30\native\base\open_world\mini_world_stories\watson\mws_wat_08\mws_wat_08.questphase']['graphs']['root']
 for i in ['7','56']:
  n=native['nodes'][i];ck('actual Active socket invokes same JournalQuestEntry type '+i,n['payload']==rest['nodes'][i]['payload']and n['payload']['type']['$type']=='questJournalQuestEntry_NodeType'and n['payload']['type']['trackQuest']==0 and any(x[2:]==[i,'Active']for x in native['edges']));ck('exact native message journal identity '+i,n['payload']['type']['path']['className']['$value']=='gameJournalPhoneMessage'and n['payload']['type']['sendNotification']==1)
 # A graph write still executes code after the state delegate. The specific
 # trackQuest=false field is carried as argument5; do not claim whole-node no-op.
 ck('graph forwards trackQuest byte51 as fifth argument',op(0x56455c,0x270,'mov','al, byte ptr [rdi + 0x51]')and op(0x56455c,0x270,'mov','byte ptr [rsp + 0x20], al'));ck('delegating slot290 skips its separate tracked-entry callback for arg5false',op(0x565dfc,0x10c,'cmp','byte ptr [rbp + 0x40], 0')and op(0x565dfc,0x10c,'je','0x140565e72'))
 mutant=bytearray(guard);jne=next(x for x in gi if x.mnemonic=='jne');mutant[jne.address-base-0x6545d0]=0x74;mi=list(md.disasm(bytes(mutant),base+0x6545d0));ck('independent actual byte mutant reverses equality bypass',next(x for x in mi if x.mnemonic in ['je','jne']).mnemonic=='je');(o/'guard_mutant.bin').parent.mkdir(parents=True);(o/'guard_mutant.bin').write_bytes(mutant)
 ck('native executable preserved after read',sha(p)==cksum);write(o/'tests.json',T);write(o/'review.json',{'status':'APPROVE_NARROW_SAME_ACTIVE_JOURNAL_STATE_AND_NOTIFICATION_IDEMPOTENCE_PROOF','checks':len(T),'reviewed_result':str(C/'result.json'),'reviewed_result_sha256':sha(C/'result.json'),'exe_sha256':cksum,'new_independent_observation':'Exact graph operation passes trackQuest byte0x51 as fifth argument to290; its Active post-delegate tracked-entry branch at565ECF is skipped for the actual Career trackQuest0 writes. Main state transition false guard returns before its notification/write block. Other later graph properties are not asserted no-op.','applicability':'Career nodes7/56 target the same native phone-message identities through Active sockets and identical JournalQuestEntry payloads. A repeated Active→Active state request under this exact executable is rejected before state/listener notification; no fake replay guard or patch is justified for this narrow property.','status_boundary':'May resolve the missing same-state message-state/notification static evidence. Keep saved original-owner retirement, non-Active entry/ancestor histories, rewards, graph post-processing and engine interleavings distinct; do not mark the entire communications or persistence contract unconditional PASS unless all their other evidence already resolves them.','runtime_changes':[]});print({'checks':len(T),'review':str(o/'review.json')})
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);run(Path(a.parse_args().output))
