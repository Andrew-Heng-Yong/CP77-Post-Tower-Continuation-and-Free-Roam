"""Independent G07 raw-source review. Does not import any G07 verifier."""
import sys,copy,json,zlib
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource
from verify import ext,path
def canon(x):
 if isinstance(x,list):return [canon(v)for v in x]
 if isinstance(x,dict):
  o={k:canon(v)for k,v in x.items()if k not in ['payload_sha256','metadata_sha256']}
  if o.get('$type')=='TweakDBID':
   v=o['$value'];o['$value']=str((len(v.encode('utf8'))<<32)|zlib.crc32(v.encode('utf8')))if o['$storage']=='string'else str(int(v));o['$storage']='uint64'
  return o
 return x
def run():
 O=H/'reviews/G07_evidence_01';assert not O.exists();P=H.parent/'G07';tests=[];pins=[];M={}
 def ck(name,ok,e):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':e});assert ok,name
 ids=read(I.W/'prealpha/quest_restoration_qr5/progress.json')['groups']['G07']['ids'];recipes=[r for r in I.U['recipes']if r['id']in ids];core=read(P/'shared_core.json');cp=P/'shared_core.json';rp=P/'results.json';ck('reported_group_and_core_frozen',sha(cp)==read(rp)['shared_core_sha256']and sha(cp)=='9F659DCAE5B009EB46952236A067981FD56D8271B906D7F536F67A04E72D6BE2',{'path':str(cp),'sha256':sha(cp),'results_sha256':sha(rp)})
 for d in sorted({r['depot']for r in recipes}|{'recipe:'+r['raw']for r in recipes}|{d for d in I.IDX if any(q in d for q in ids)and I.IDX[d].get('graphs')}|{'base\\quest\\holocalls\\reggie\\reggie_holocall.questphase','base\\quest\\holocalls\\reggie\\reggie_holocall.scene','towercontinued\\gig_phone_u9\\fixer_initializer.questphase','towercontinued\\gig_phone_u9\\fixer_cleanup.questphase','towercontinued\\phone_studios_ph3\\studio_support.questphase'}):M[d],p=I.load(d);pins.append(p);ck('independent_pin_and_raw_graph '+d,not M[d]['errors'],p)
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,k,p='root'):return g(d,p)['nodes'][str(k)]
 def e(d,a,s,b,t,p='root'):return [str(a),s,str(b),t]in g(d,p)['edges']
 for r in recipes:
  for ni in r['ids']:
   if ni==0:continue
   ck('original_selected_node '+r['depot']+str(ni),n(r['depot'],ni)['payload']==ext(n('recipe:'+r['raw'],ni,r['graph'])['payload']),{'native_graph':r['graph'],'node':ni})
  ck('original_selected_edges '+r['depot'],g(r['depot'])['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]),r['edges'])
 # Independently verify all eleven actual raw readback exports and hash/storage boundary.
 for x in read(P/'raw_exports_01/manifest.json'):
  ck('actual_binary_export_pin '+x['depot'],sha(x['raw'])==x['raw_sha256']and sha(x['json'])==x['json_sha256'],x)
  if x['depot']not in M:M[x['depot']],p=I.load(x['depot']);pins.append(p)
  fresh=Resource(read(x['json'])).normalize();ck('actual_binary_redecode_model '+x['depot'],canon(fresh)==canon(M[x['depot']]),{'export':x['json'],'only_encoding':'TweakDBID CRC32+UTF8 length→uint64; derived hashes removed, no graph/payload differences suppressed'})
 init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';cl='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase';hc='base\\quest\\holocalls\\reggie\\reggie_holocall.questphase';hs='base\\quest\\holocalls\\reggie\\reggie_holocall.scene';studio='towercontinued\\phone_studios_ph3\\studio_support.questphase';ck('Regina_actual_U9_owner',hc in n(init,84)['refs']and e(init,25,'Out1',84,'In1'),'current owner84');ck('Regina_actual_cleanup_owner',any('reggie_cleanup.questphase'in r for r in n(cl,342)['refs']),'current cleanup342');ck('Regina_real_start_end_ack',all(any(w.get('factName')==f and w.get('value')==1 for w in n(hs,ni,'scene')['writes'])for ni,f in [(396,'holo_reggie_calls_v_start_done'),(398,'holo_reggie_calls_v_end_done')]),'native scene396/398, no synthetic actor ACK');ck('shared_studio_both_prefabs',len(n(studio,3)['prefabs'])==2,n(studio,3)['prefabs'])
 def find(q,t):return next(d for d in M if q in d and d.endswith(t))
 c101=find('sts_wat_kab_101','openworld.questphase');c107=find('sts_wat_kab_107','openworld.questphase');c102=find('sts_wat_kab_102','openworld.questphase');c07=find('sts_wat_kab_07','openworld.questphase')
 for d,p,edges in [(c101,'root/5',[(0,'Out',53,'In2'),(10,'Out',52,'In1')]),(c107,'root/4',[(49,'End 0',39,'In'),(50,'End 0',40,'In')]),(c102,'root/4',[(34,'False',72,'Succeeded'),(34,'True',68,'In')]),(c07,'root/3/182',[(2,'Out',10,'In'),(10,'Out',5,'Succeeded')])]:
  for edge in edges:ck('independent_native_branch '+d+p+str(edge),e(d,*edge,p),edge)
 # Outcome and prestate distinctions are explicit, not classed by generic family.
 pre107=find('sts_wat_kab_107','prestate_control.questphase');pre102=find('sts_wat_kab_102','prestate_control.questphase');ck('Troublesome_prestate_is_native_empty',sum(len(gr['nodes'])for gr in M[pre107]['graphs'].values())==2,'original prestate two-node passthrough');ck('Welcome_prestate_is_nonempty',sum(len(gr['nodes'])for gr in M[pre102]['graphs'].values())>2,'native security/community/document prestate must remain scoped, no new owner inferred')
 for q in ids:
  p=I.W/'prealpha/quest_restoration_qr5/shared/tdb_applicability_02'/str(q+'.json');data=read(p);pins.append({'path':str(p),'sha256':sha(p)});ck('stock_capture_has_bounded_limits '+q,bool(data['limits'])and bool(data['capture']),'stock records are pinned; depth1 descendants/runtime overrides not certified')
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);review={'status':'PASS_INDEPENDENT_SOURCE_REVIEW_WITH_EXPLICIT_LIMITS','group':'G07','quest_ids':ids,'checks':len(tests),'tests':str(O/'tests.json'),'tests_sha256':sha(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'source_pins_sha256':sha(O/'source_pins.json'),'reviewed_results_sha256':sha(rp),'reviewed_core_sha256':sha(cp),'findings':['Independent original selected payload/socket/edge comparisons pass. Eleven fresh WKit export files match actual pinned binary hashes and independently normalized models after exact TDBID CRC32+length storage canonicalization.','Regina current initializer/cleanup, real native ACKs and both shared studio prefabs are present. Four native outcome branch controls and distinct empty/nonempty prestate obligations pass.','No new restoration defect established in this bounded peer review; reported static conditional/opaque and old owner gaps remain appropriate.'],'limits':['Review does not claim all world placement, runtime TweakXL/CET effects, stock descendant semantics, saved owners or engine phone scheduling are verified.','Monster generic Tyger signal remains without a dedicated Monster selector; no custom retaliation outcome is assumed.','Welcome prestate_triggered remains an exact omitted admission provenance gap; no speculative reset or new owner approved.'],'runtime_changes':[]};write(H/'reviews/G07.json',review);print({'checks':len(tests),'review':str(H/'reviews/G07.json'),'sha256':sha(H/'reviews/G07.json')})
if __name__=='__main__':run()
