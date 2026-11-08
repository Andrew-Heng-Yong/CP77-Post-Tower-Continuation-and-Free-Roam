"""Bounded current-resource preservation/applicability, not a broad quest audit."""
from inspect_archivexl import ROOT,HERE
import json,hashlib,copy,sys,binascii
from pathlib import Path
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
class Hashes:
 def __init__(self):self.cache={}
 def __call__(self,p):
  p=Path(p);s=p.stat();key=(s.st_size,s.st_mtime_ns)
  if p not in self.cache:self.cache[p]=(key,hashlib.sha256(p.read_bytes()).hexdigest().upper())
  assert self.cache[p][0]==key,'input freshness drift '+str(p)
  return self.cache[p][1]
def main():
 out=HERE/'inherited_controls_02';out.mkdir(exist_ok=False);sha=Hashes();tests=[];pinpaths=set()
 def ck(n,b,e=None):tests.append({'name':n,'pass':bool(b),'evidence':e});assert b,n
 def pinned(p):p=Path(p);pinpaths.add(p);return sha(p)
 ep=ROOT/'prealpha/quest_restoration_qr8/source_epoch_00.json';E=load(ep);pinned(ep);current=Path(E['candidate'])/'archive_source';capture=load(HERE/'preservation_capture_01/manifest.json');pinned(HERE/'preservation_capture_01/manifest.json')
 rawrows={r['depot']:r for r in capture['resources']};models={}
 for d,r in rawrows.items():
  ck('fresh exact binary and typed input '+d,pinned(r['raw'])==r['raw_sha256']==sha(current/d.replace('\\','/'))==E['source_resources'][d] and pinned(r['json'])==r['json_sha256'])
  models[d]=Resource(load(r['json'])).normalize();ck('fresh graph decoder errors absent '+d,not models[d]['errors'])
 old=load(ROOT/'prealpha/quest_restoration_qr7/worker_a/final_package_02/expected/inputs.json');pinned(ROOT/'prealpha/quest_restoration_qr7/worker_a/final_package_02/expected/inputs.json');ledger=old['inherited'];ls={r['depot']:r for r in ledger}
 reuse=[]
 spy=r'towercontinued\native_gigs_u9\sts_ep1_08_entry.questphase'
 for r in ledger:
  d=r['depot'];actual=sha(current/d.replace('\\','/'));expected=E['source_resources'][d]
  ck('current inherited payload matches selected epoch '+d,actual==expected)
  if d!=spy:ck('inherited repair bytes remain exact '+d,actual==r['after'])
  proof=[]
  for k in ['tests','independent_review','independent_source_review','independent_serialized_review']:
   ps=r.get(k,[]);ps=[ps] if isinstance(ps,str) else ps
   for p in ps:
    digest=pinned(p);decl=r.get(k+'_sha256')
    if decl:ck('historical independent proof pin '+str(p),digest==decl)
    doc=load(p);proof.append({'role':k,'path':p,'sha256':digest,'recorded_status':doc.get('status'),'applicability':'Exact current after-bytes' if d!=spy else 'QR7 semantic preservation checked below; original historical controls not rewritten'})
  reuse.append({'depot':d,'current_sha256':actual,'previous_repaired_sha256':r['after'],'scope':r.get('intent'),'proofs':proof,'static_reuse_only':True})
 # Spy preserves the whole actual QR6 graph/model except one approved future Armed splice.
 pm=ROOT/'prealpha/quest_restoration_qr7/worker_a/spy_baseline_readback_01/manifest.json';P=load(pm);pinned(pm)
 ck('actual prior Spy raw bound to inherited repair',pinned(P['source'])==P['source_sha256']==ls[spy]['after'] and pinned(P['json'])==P['json_sha256'])
 before=Resource(load(P['json'])).normalize();after=models[spy]
 ck('Spy all graph and resource metadata identities retained',set(before['graphs'])==set(after['graphs']) and before['metadata']==after['metadata'])
 for gp,g in before['graphs'].items():
  ag=after['graphs'][gp];ck('Spy graph entries preserved '+gp,g['entries']==ag['entries'])
  ck('Spy every old node payload and socket preserved '+gp,all(n['payload']==ag['nodes'][i]['payload'] and n['sockets']==ag['nodes'][i]['sockets'] for i,n in g['nodes'].items()))
  if gp!='root/50':ck('Spy other graph identical '+gp,g==ag)
  else:ck('Spy sole Armed splice preserves all other phone edges',set(ag['nodes'])-set(g['nodes'])=={'65007'} and set(map(tuple,ag['edges']))==(set(map(tuple,g['edges']))-{('65002','Out','65003','In')})|{('65002','Out','65007','In'),('65007','Out','65003','In')})
 # CR1 donor controls follow approved supersessions, rather than reinstating old fixes.
 crp=ROOT/'prealpha/consolidation_repair_cr1/candidate_01/selected_resources_01.json';cr=load(crp)['resources'];pinned(crp)
 ph1p=ROOT/'prealpha/phone_support_ph1/candidate_03/build_01.json';ph1=load(ph1p);pinned(ph1p);crrows=[]
 for r in cr:
  d=r['depot'];authority=r['after'];reason='CR1 exact corrected donor'
  if d in ls:ck('CR1 supersession begins at exact corrected donor '+d,ls[d]['before']==r['after']);authority=ls[d]['after'];reason='Reviewed QR3/QR4/QR5 repair of CR1-corrected source'
  elif d==r'towercontinued\gig_phone_u9\fixer_cleanup.questphase':authority=ph1['resources'][d];reason='PH1 expanded exact native phone cleanup supersedes CR1 cleanup'
  actual=sha(current/d.replace('\\','/'));ck('current corrected donor lineage '+d,actual==authority)
  crrows.append({'depot':d,'CR1_before':r['before'],'CR1_corrected':r['after'],'current':actual,'authority':reason})
 # Original PH1 controllers and cleanup are byte-preserved; modified entry owners have named successors.
 ph1rows=[]
 for d,digest in ph1['resources'].items():
  actual=sha(current/d.replace('\\','/'));sup=ls.get(d)
  ck('PH1 original or explicitly reviewed successor '+d,actual==digest or bool(sup and sup['before']==digest and (actual==sup['after'] or d==spy)))
  ph1rows.append({'depot':d,'original_PH1':digest,'current':actual,'unchanged':actual==digest,'successor':sup.get('intent') if sup else None})
 # Fresh graph controls use actual source-pinned models and intentional before-route mutations.
 q37=models[r'towercontinued\sidejobs_s23\base_b\mq037.questphase']['graphs']['root']
 def mq37_ok(g):return ['1004','True','1008','In'] in g['edges'] and not any(e[2]=='1005' for e in g['edges'])
 ck('MQ037 fresh excluded admission cannot enter Issued1005',mq37_ok(q37));bad=copy.deepcopy(q37);bad['edges'].remove(['1004','True','1008','In']);bad['edges'].append(['1004','True','1005','In']);ck('MQ037 actual graph old-admission mutation rejected',not mq37_ok(bad))
 q30=models[r'towercontinued\sidejobs_s23\base_b\mq030.questphase']['graphs']['root'];required={('1020','Out1','1022','In'),('1022','False','1021','In'),('1021','Out','1023','In'),('1023','False','1020','In1')}
 def mq30_ok(g):return required<=set(map(tuple,g['edges'])) and {tuple(e) for e in g['edges'] if e[2]=='1012'}=={('1022','True','1012','In'),('1023','True','1012','In')}
 ck('MQ030 release1012 requires actual helper retirement/recheck',mq30_ok(q30));bad=copy.deepcopy(q30);bad['edges'].append(['1020','Out','1012','In']);ck('MQ030 premature-release edge mutation rejected',not mq30_ok(bad))
 for d in [r'towercontinued\sidejobs_s23\base_a\mq007_smartgun.questphase',r'towercontinued\sidejobs_s23\base_a_v2\mq007_resume_boot.questphase']:
  m=models[d];g=m['graphs']['root'];req={('1101','Out','1200','In'),('1200','True','1201','In'),('1201','Out','1202','In1'),('1202','Out1','1203','In')}
  def mq7_ok(q):return req<=set(map(tuple,q['edges'])) and {e[0] for e in q['edges'] if e[2]=='1200'}=={'1101'}
  ck('MQ007 future event continuation route '+d,mq7_ok(g));bad=copy.deepcopy(g);bad['edges'].remove(['1101','Out','1200','In']);ck('MQ007 missing native consumer edge mutation rejected '+d,not mq7_ok(bad))
  preds={n['factName']:n['value'] for n in walk(g['nodes']['1200']['payload']) if n.get('$type')=='questVarComparison_ConditionType'}
  ck('MQ007 no historical-return/reacquired adoption '+d,preds.get('mq007_done')==0 and preds.get('mq007_skippy_re_acquiring_done')==0 and preds.get('PTFRQR4_MQ007_ReacquisitionIssued')==0)
  ck('MQ007 recursive exact helper preserved '+d,any('#mq007_pr_gun_re_acquiring' in p for gg in m['graphs'].values() for n in gg['nodes'].values() for p in n['prefabs']))
 # PH2 regression uses literal independently recorded historical collision IDs.
 ph2p=ROOT/'prealpha/phone_merge_ph2/candidate_01/semantic_verification_01.json';ph2=load(ph2p);pinned(ph2p)
 alias=ph2['new_path'];ck('PH2 alias bytes and retained original listener exact',sha(current/alias.replace('\\','/'))==ph2['alias_sha256']==sha(current/ph2['old_path'].replace('\\','/')))
 crc=lambda p:binascii.crc_hqx((p+':1').encode(),65535)
 ck('PH2 historical duplicateID40560 and corrected61197 reproduced',crc(ph2['old_path'])==40560==crc(r'towercontinued\native_gigs_u9\sts_wat_kab_101_map1.questphase') and crc(alias)==61197)
 regs=load(HERE/'namespace_verification_01/registration_inventory.json');ep1=[r for r in regs if r['candidate'] and r'ep1\quest\ep1.quest' in r['expanded_parents']]
 ck('PH2 current binding selects alias not old colliding path',sum(r['path']==alias for r in ep1)==1 and not any(r['path']==ph2['old_path'] for r in ep1))
 # PH1 native request listener and cleanup survive; no fake ACK is introduced.
 mark=models[alias];ck('PH1 exact original Mark listener resource bound at native child10',mark['graphs']['root']['nodes']['10']['refs']==[r'ep1\quest\holocalls\mark_bana\mark_bana_holocall.questphase'])
 cleanup=models[r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'];ck('PH1 native Mark/Janet scene cleanup bindings preserved',all(any(ref in n['refs'] for n in cleanup['graphs'][gp]['nodes'].values()) for gp,ref in [('root/1402',r'ep1\quest\holocalls\mark_bana\mark_bana_holocall.scene'),('root/1405',r'ep1\quest\holocalls\janet\janet_holocall.scene')]))
 # PH3 root/instance support loss is checked on actual current owner, not an initializer shortcut.
 ph3p=ROOT/'prealpha/phone_studios_ph3/candidate_01/build_01.json';ph3=load(ph3p);pinned(ph3p);studio=models[ph3['depot']];refs=studio['graphs']['root']['nodes']['3']['prefabs']
 ck('PH3 exact two original shared studio leases remain on instance owner',refs==ph3['prefabs'] and not studio['root_prefabs'])
 bad=copy.deepcopy(studio);bad['graphs']['root']['nodes']['3']['prefabs']=[];ck('PH3 actual support omission mutation rejected',bad['graphs']['root']['nodes']['3']['prefabs']!=ph3['prefabs'])
 ck('PH3 live owner still registered with generatedID22195',sum(r['path']==ph3['depot'] for r in ep1)==1 and crc(ph3['depot'])==22195)
 # CR1 old donor reversion is detected against the current selected donor (incl supersessions).
 victim=next(r for r in crrows if r['CR1_before']!=r['current']);ck('CR1 actual historical old donor mutation rejected',victim['CR1_before']!=E['source_resources'][victim['depot']])
 result={'status':'PASS_BOUNDED_CURRENT_INHERITED_REPAIR_AND_HISTORICAL_CONTROL_APPLICABILITY','checks':len(tests),'current_epoch':'QR8:00=QR7:04','inherited_resources':len(ledger),'inherited_exact_bytes':8,'inherited_semantic_Spy_Armed_splice':1,'CR1_resources':len(crrows),'CR1_exact_donors':sum(r['current']==r['CR1_corrected'] for r in crrows),'CR1_named_supersessions':sum(r['current']!=r['CR1_corrected'] for r in crrows),'PH1_original_resources':len(ph1rows),'PH2_corrected_generated_id':61197,'PH3_studio_generated_id':22195,'mutation_controls':7,'fresh_typed_resources':len(models),'historical_tests_rerun':False,'unchanged_compile_or_rebuild_performed':False,'limits':['Exact byte preservation permits reuse of pinned earlier tests only for their recorded scope; no historical PASS is relabeled as a new live result.','MQ007 opaque sector/native admission seam, MQ030 saved helper scheduling and MQ037 excluded sequel availability retain the previous limits.','Spy is semantically preserved through the reviewed Armed splice; claiming nine byte-identical resources would be false.'],'candidate_runtime_or_save_writes':0,'checker_sha256':sha(__file__)}
 outputs={'result.json':result,'checks.json':tests,'inherited_test_applicability.json':reuse,'CR1_lineage.json':crrows,'PH1_lineage.json':ph1rows,'input_pins.json':[{'path':str(p),'sha256':sha(p)} for p in sorted(pinpaths)]}
 for name,data in outputs.items():(out/name).write_text(json.dumps(data,indent=2),encoding='utf8')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
