"""Independent Wellsprings source review; no peer-verifier imports."""
import sys,copy
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource
from verify import ext,path
def run():
 O=H/'reviews/G02_evidence_02';assert not O.exists();P=H.parent/'G02';results=read(P/'results.json');ids=read(I.W/'prealpha/quest_restoration_qr5/progress.json')['groups']['G02']['ids'];M={};pins=[];tests=[];mut=[]
 def ck(name,ok,e):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':e});assert ok,name
 ck('reported_inputs_and_core_frozen',sha(results['tests'])==results['tests_sha256']and sha(results['source_pins'])==results['source_pins_sha256']and sha(results['shared_core'])==results['shared_core_sha256'],{'results':str(P/'results.json'),'sha256':sha(P/'results.json')})
 recipes=[r for r in I.U['recipes']if r['id']in ids]
 shared=['base\\quest\\holocalls\\padre\\padre_holocall.questphase','base\\quest\\holocalls\\padre\\padre_holocall.scene','base\\quest\\holocalls\\rogue\\rogue_holocall.questphase','base\\quest\\holocalls\\rogue\\rogue_holocall.scene','towercontinued\\gig_phone_u9\\fixer_initializer.questphase','towercontinued\\gig_phone_u9\\fixer_cleanup.questphase']
 for d in sorted({r['depot']for r in recipes}|{'recipe:'+r['raw']for r in recipes}|{d for d,r in I.IDX.items()if r.get('graphs')and any(q in d for q in ids)}|set(shared)|{I.LOOP}):M[d],p=I.load(d);pins.append(p);ck('independent_pin_and_parse '+d,not M[d]['errors'],p)
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,i,p='root'):return g(d,p)['nodes'][str(i)]
 def e(d,a,s,b,t,p='root'):return [str(a),s,str(b),t]in g(d,p)['edges']
 def find(q,t):return next(d for d in M if q in d and d.endswith(t))
 for r in recipes:
  for ni in r['ids']:
   if ni:ck('original_recipe_payload '+r['depot']+str(ni),n(r['depot'],ni)['payload']==ext(n('recipe:'+r['raw'],ni,r['graph'])['payload']),{'original':r['raw'],'graph':r['graph'],'node':ni})
  ck('original_recipe_edges '+r['depot'],g(r['depot'])['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]),r['edges'])
 init=shared[4];cl=shared[5]
 for ix,contact,ci,si in [(79,'padre',336,1),(86,'rogue',344,3)]:
  ck('actual_contact_owner '+contact,n(init,ix)['refs']==[shared[si-1]]and e(init,25,'Out1',ix,'In1'),{'node':ix,'contact':contact});ck('actual_contact_cleanup '+contact,any(contact+'_cleanup.questphase'in r for r in n(cl,ci)['refs']),ci)
  for ni,kind in [(41,'start'),(42,'end')]:ck('actual_real_ACK '+contact+kind,any(w.get('factName')=='holo_'+contact+'_calls_v_'+kind+'_done'and w.get('value')==1 for w in n(shared[si],ni,'scene')['writes']),ni)
 spr01=find('sts_hey_spr_01','openworld_phase.questphase');spr06=find('sts_hey_spr_06','openworld.questphase');spr03=find('sts_hey_spr_03','_ow.questphase')
 # Contact distinction is proved from native producers/callers, not geographical grouping.
 for q,contact in [('sts_hey_spr_01','padre'),('sts_hey_spr_06','rogue'),('sts_hey_spr_03','padre')]:
  producers=[{'depot':d,'graph':gp,'node':ni,'fact':w['factName']}for d,m in M.items()if q in d and not d.startswith(('recipe:','tower'))for gp,gr in m['graphs'].items()for ni,nd in gr['nodes'].items()for w in nd['writes']if w['value']==1 and w['factName'].endswith('_activate')and w['factName'].startswith('holo_')];ck('actual_native_contact '+q,bool(producers)and all(p['fact'].startswith(('holo_'+contact+'_calls_v_','holo_v_calls_'+contact+'_'))for p in producers),producers)
 physical=find('sts_hey_spr_01','padre_fixer_conversation.scene');actor=next(a for a in M[physical]['metadata']['actors']if a.get('actorName')=='padre');ck('Padre_outcome_is_outgoing_holo_scene',actor['acquisitionPlan']=='spawnSet'and actor['spawnSetParams']['entryName']['$value']=='padre_holo'and actor['spawnSetParams']['reference']['$value']=='#padre_holo',actor)
 for writer,wait,clear in [(556,587,550),(557,551,552),(577,574,575)]:ck('Padre_outcome_actual_request_wait_clear '+str(writer),bool(path(g(physical,'scene'),writer,wait))and bool(path(g(physical,'scene'),wait,clear)),{'producer':writer,'wait':wait,'clear':clear})
 for ni,f in [(43,'holo_v_calls_padre_start_done'),(44,'holo_v_calls_padre_end_done')]:ck('Padre_outgoing_real_ACK '+str(ni),any(w.get('factName')==f and w.get('value')==1 for w in n(shared[1],ni,'scene')['writes']),{'node':ni,'fact':f})
 write(O/'SPR01_outgoing_correction.json',{'scene':physical,'actor':actor,'start_wait_clear':[556,587,550],'end_wait_clears':[[557,551,552],[577,574,575]],'retry_request':606,'correction':'Scene is outgoing Padre hologram via padre_holo, not a physical Padre visit. Generic report that only prebrief uses holocall is incomplete; actual outgoing request/wait/ACK/cleanup must be covered.','runtime_change_needed':False})
 ck('HotMerchandise_native_credit_waiter_is_disconnected',any(x.get('factName')=='sts_hey_spr_06_finished'for x in n(I.LOOP,14,'root/2/4')['reads'])and not any(ed[0]=='14'for ed in g(I.LOOP,'root/2/4')['edges'])and not any(r['id']=='sts_hey_spr_06'and r['kind']=='credit'for r in recipes),'native waiter14 exists but has no edge to hey counter3; rejected patch hypothesis is correct')
 ck('HotMerchandise_native_nonlethal_and_death_listeners',e(spr06,0,'Out',5,'In','root/3/175')and e(spr06,0,'Out',6,'In','root/3/175'),'actual authored Rebeca listeners armed by current native body, not original bugfix only')
 ck('LordGiveth_destruct_listener_is_reachable',bool(path(g(spr03,'root/3'),0,271))and e(spr03,271,'Out',277,'In','root/3'),'native connected vehicle listener, unlike ARR12 dead fallback223')
 ck('LordGiveth_perfect_nonperfect_preserved',e(spr03,268,'True',278,'In','root/3')and e(spr03,268,'False',279,'In','root/3'),'exact original outcome branch, no forced success')
 # Negative control: add a fabricated native credit edge to an actual model copy.
 false_credit=copy.deepcopy(g(I.LOOP,'root/2/4'));false_credit['edges'].append(['14','Out','3','In']);caught=any(ed[0]=='14'for ed in false_credit['edges']);ck('rejected_credit_hypothesis_mutation',caught,'Independent original-absence oracle rejects fabricated waiter14→counter3; no runtime copy serialized');mut.append({'fault':'fabricated SPR06 credit edge','caught':caught,'kind':'normalized graph copy; primary G02 has fourteen raw controls separately'})
 for q in ids:
  sp=I.W/'prealpha/quest_restoration_qr5/shared/tdb_applicability_02'/str(q+'.json');s=read(sp);pins.append({'path':str(sp),'sha256':sha(sp)});ck('stock_limits_kept '+q,bool(s['limits']),'record existence is separate from runtime economic child closure')
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'mutation.json',mut);r={'status':'PASS_STATIC_PARITY_WITH_DOCUMENTATION_CORRECTION_REQUIRED','group':'G02','quest_ids':ids,'checks':len(tests),'tests':str(O/'tests.json'),'tests_sha256':sha(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'source_pins_sha256':sha(O/'source_pins.json'),'reviewed_results_sha256':sha(P/'results.json'),'findings':['Exact original selected payload/edge checks pass for all three entries and companion native map/credit slices.','SPR01 and SPR03 actual phone is Padre; SPR06 phone is Rogue despite Padre map context. SPR01 outcome uses outgoing Padre hologram spawnSet #padre_holo; report descriptions of a physical visit and only prebrief phone protocol require a fresh correction addendum. Original outgoing real ACK and wait/clear controls pass here.','SPR06 original lifecycle waiter14 has zero outgoing edges; missing private credit hypothesis was correctly rejected. Actual current native Rebeca nonlethal/death and SPR03 destruction/perfect/nonperfect routes are present.'],'remaining':['Padre holographic spawnSet/studio acquisition, saved owners, native phone scheduling and transport/cleanup require live fixtures; no new owner or physical visit is approved.','Source-pinned stock record presence does not certify economic descendants/runtime overrides.','Review is bounded source parity, not gameplay success or a full blanket quest PASS.'],'runtime_changes':[]};write(H/'reviews/G02.json',r);print({'checks':len(tests),'review':str(H/'reviews/G02.json'),'sha256':sha(H/'reviews/G02.json')})
if __name__=='__main__':run()
