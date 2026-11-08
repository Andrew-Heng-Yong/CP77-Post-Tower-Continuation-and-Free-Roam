"""Early reusable Padre/Wakako U9 proof, applicable only under exact byte pins."""
from pathlib import Path
import importlib.util,json,argparse,collections
H=Path(__file__).resolve().parent;s=importlib.util.spec_from_file_location('g01_inputs',H/'source_inputs.py');I=importlib.util.module_from_spec(s);s.loader.exec_module(I)
from common import read,write,sha
def path(g,a,b):
 q=collections.deque([[str(a)]]);seen={str(a)}
 while q:
  p=q.popleft()
  if p[-1]==str(b):return p
  for x,s,y,t in g['edges']:
   if x==p[-1] and s!='CutSource' and t!='CutDestination' and y not in seen:seen.add(y);q.append(p+[y])
 return None
def run(O):
 assert not O.exists();M={};pins=[];checks=[];contacts={}
 def ck(name,ok,e):checks.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,name
 ck('canonical QR4 predecessor pin',sha(I.E['predecessor_epoch_path'])==I.E['predecessor_epoch_sha256'],I.E['predecessor_epoch_path'])
 sentinel=read(I.F/'sentinel.json');ck('handoff sentinel verified exact inputs',sentinel['status']=='PASS_EXACT_QR4_HANDOFF_SENTINEL' and sentinel['canonical_predecessor_epoch_sha256']==I.E['predecessor_epoch_sha256'],dict(path=str(I.F/'sentinel.json'),sha256=sha(I.F/'sentinel.json')))
 old=I.W/'prealpha/quest_restoration_qr4/groups/G09/shared_core.json';core=read(old);ck('frozen U9 PH3 common proof',sha(old)=='BDD1BB748A68160491FE98715951DAD7C79D8CB8233333255C250D2FF060A857' and sha(core['tests'])==core['tests_sha256'] and sha(core['source_pins'])==core['source_pins_sha256'],dict(path=str(old),sha256=sha(old),scope='U9 wrapper/parent/studio only; contact-specific proofs below'))
 for p in core['sources']:
  d=p['depot'];raw=I.C/'archive_source'/d.replace('\\','/') if d in I.E['source_resources'] else Path(p['binary']);ck('current applicability of inherited common '+d,sha(raw)==p['resource_sha256'],str(raw))
 for d in I.COMMON:m,p=I.load(d);M[d]=m;pins.append(p);ck('exact common source and decoding '+d,not m['errors'],p)
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def e(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
 def wr(d,i,f,v,gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(d,i,gp)['writes'])
 ini=r'towercontinued\gig_phone_u9\fixer_initializer.questphase';cle=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';nativeini=r'base\quest\holocalls\holocall_initializers.questphase'
 for contact,initializer,caller,cleanup,slot,nextnode in [('padre',79,468,336,42,474),('rogue',86,476,344,50,488)]:
  hc=f'base\\quest\\holocalls\\{contact}\\{contact}_holocall.questphase';hs=hc.replace('.questphase','.scene');cl=hc.replace('_holocall','_cleanup')
  ck('native initializer body '+contact,n(ini,initializer)['payload']==n(nativeini,initializer)['payload'] and n(ini,initializer)['refs']==[hc] and e(ini,25,'Out1',initializer,'In1'),dict(resource=ini,node=initializer,controller=hc))
  ck('actual native cleanup invocation '+contact,n(cle,cleanup)['refs']==[cl] and e(cle,caller,'True',cleanup,'In'+str(slot)) and e(cle,cleanup,'Out'+str(slot),nextnode,'In'),dict(resource=cle,gate=caller,node=cleanup,slot=slot,next=nextnode))
  ck('native request queue producer '+contact,e(hc,32,'Out',33,'In') and e(hc,33,'Out',34,'In') and e(hc,34,'Out',35,'In1') and wr(hc,33,'holo_'+contact+'_calls_v_start_activate_count',1) and wr(hc,34,'holo_'+contact+'_calls_v_start_activate',0),dict(resource=hc,nodes=[32,33,34,35]))
  ck('native queued request gated consumer '+contact,e(hc,36,'Out',28,'In') and e(hc,28,'False',10,'In') and e(hc,10,'Out',0,'holo_'+contact+'_calls_v_start') and wr(hc,10,'holo_'+contact+'_calls_v_start_activate_count',-1),dict(resource=hc,nodes=[36,28,10,0]))
  ck('native end request consumer '+contact,e(hc,3,'Out',11,'In') and e(hc,11,'Out',0,'holo_'+contact+'_calls_v_end') and wr(hc,11,'holo_'+contact+'_calls_v_end_activate',0),dict(resource=hc,nodes=[3,11,0]))
  acknowledgements=[]
  for suffix,ack in [('start',41),('end',42)]:
   name='holo_'+contact+'_calls_v_'+suffix;entry=g(hs,'scene')['entries'][name];p=path(g(hs,'scene'),entry,ack);ck('real scene acknowledgement '+contact+suffix,wr(hs,ack,name+'_done',1,'scene') and bool(p),dict(scene=hs,entry=entry,ack=ack,path=p));acknowledgements.append(dict(type=suffix,scene_entry=entry,writer=ack,path=p))
  ck('native cleanup end branch '+contact,wr(cl,6,'holo_'+contact+'_calls_v_reset_counter',1) and e(cl,6,'Out',0,'holo_'+contact+'_calls_v_end'),dict(resource=cl,nodes=[6,0]))
  contacts[contact]=dict(controller=hc,scene=hs,cleanup=cl,initializer=dict(resource=ini,node=initializer),shared_cleanup=dict(resource=cle,gate=caller,node=cleanup,slot=slot,next=nextnode),acknowledgements=acknowledgements)
 write(O/'source_pins.json',pins);write(O/'tests.json',dict(status='PASS_SHARED_CONTACT_APPLICABILITY',count=len(checks),checks=checks,runtime_changes=[]))
 out=dict(status='SOURCE_PINNED_SHARED_PADRE_ROGUE_U9_CORE',source_epoch=str(I.F/'source_epoch_00.json'),source_epoch_sha256=sha(I.F/'source_epoch_00.json'),working_candidate=str(I.C),sources=pins,tests=str(O/'tests.json'),tests_sha256=sha(O/'tests.json'),source_pins=str(O/'source_pins.json'),source_pins_sha256=sha(O/'source_pins.json'),checks=len(checks),inherited_common=dict(path=str(old),sha256=sha(old),checks_reused=core['checks'],scope='Exact U9/PH3 common wrappers and studio; Dakota-specific statements are not applied'),contacts=contacts,applicability=dict(padre=['sts_hey_spr_01','sts_hey_spr_03'],rogue=['sts_hey_spr_06']),limits=['SupportIssued/native initializer receipts are source prerequisites, not proof of engine-completed listener startup.','Native scene retry fork/cut behavior and actual call/rejection/cleanup scheduling remain live-dependent.','This proves shared bindings and literal acknowledgement paths, not target world placement, entitlement, current TweakDB balance or saved-owner retirement.'],runtime_changes=[])
 target=H/'shared_core.json';assert not target.exists();write(target,out);return dict(checks=len(checks),sources=len(pins),core=str(target),sha256=sha(target))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(run(Path(a.output).resolve())))
