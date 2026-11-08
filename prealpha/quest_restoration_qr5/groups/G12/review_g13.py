"""Independent Wakako/HIL07 Tyger/raw protocol review, no peer verifier imports."""
import sys,copy,re
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource
from verify import ext,path
def run():
 O=H/'reviews/G13_evidence_01';assert not O.exists();P=H.parent/'G13';res=read(P/'results.json');ids=read(I.W/'prealpha/quest_restoration_qr5/progress.json')['groups']['G13']['ids'];M={};pins=[];tests=[]
 def ck(name,ok,e):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':e});assert ok,name
 ck('frozen_peer_inputs',sha(res['tests'])==res['tests_sha256']and sha(res['source_pins'])==res['source_pins_sha256']and sha(res['shared_core'])==res['shared_core_sha256'],{'results_sha256':sha(P/'results.json')})
 hc='base\\quest\\holocalls\\wakako\\wakako_holocall.questphase';hs='base\\quest\\holocalls\\wakako\\wakako_holocall.scene';cl='base\\quest\\holocalls\\wakako\\wakako_cleanup.questphase';init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';clean='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase';gang='towercontinued\\special_gigs_u9\\gang_retaliation.questphase';rec=[r for r in I.U['recipes']if r['id']in ids]
 catalog={p['depot']:p for p in read(res['source_pins'])if p.get('depot','').startswith('recipe:')}
 for d in sorted({r['depot']for r in rec}|{'recipe:'+r['raw']for r in rec}|{d for d,r in I.IDX.items()if r.get('graphs')and any(q in d for q in ids)}|{hc,hs,cl,init,clean,gang}):
  if d.startswith('recipe:'):
   p=catalog[d];ck('original_recipe_raw_export_pair '+d,sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256']and(p.get('historical_raw_sha256')is None or p['sha256']==p['historical_raw_sha256']),{'input_catalog':res['source_pins'],'pin':p,'limit':'Existing hash-pinned original extraction reused; no new provider scan'});M[d]=Resource(read(p['json'])).normalize()
  else:M[d],p=I.load(d)
  pins.append(p);ck('independent_pin '+d,not M[d]['errors'],p)
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,k,p='root'):return g(d,p)['nodes'][str(k)]
 def e(d,a,s,b,t,p='root'):return [str(a),s,str(b),t]in g(d,p)['edges']
 for r in rec:
  for ni in r['ids']:
   if ni:ck('original_selected_payload '+r['depot']+str(ni),n(r['depot'],ni)['payload']==ext(n('recipe:'+r['raw'],ni,r['graph'])['payload']),{'donor':r['raw'],'graph':r['graph'],'node':ni})
  ck('original_selected_edges '+r['depot'],g(r['depot'])['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]),r['edges'])
 ck('actual_Wakako_initializer',n(init,97)['refs']==[hc]and e(init,25,'Out1',97,'In1'),'all three use actual Wakako owner97');ck('actual_Wakako_cleanup',n(clean,355)['refs']==[cl],'native current cleanup355')
 directions={};rx=re.compile(r'^(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate$')
 for q in ids:
  rows=[]
  for d,m in M.items():
   if q not in d or not d.startswith('base'):continue
   for gp,gr in m['graphs'].items():
    for ni,nd in gr['nodes'].items():
     for w in nd['writes']:
      ma=rx.fullmatch(w['factName'])if w['value']==1 else None
      if not ma:continue
      mode,inc,out,kind=ma.groups();contact=inc or out;ack='holo_'+(contact+'_calls_v'if inc else'v_calls_'+contact)+'_'+kind+'_done';reader=[i for i,nn in g(hc)['nodes'].items()if any(r.get('factName')==w['factName']for r in nn['reads'])];writer=[i for i,nn in g(hs,'scene')['nodes'].items()if any(ww.get('factName')==ack and ww['value']==1 for ww in nn['writes'])];row={'depot':d,'graph':gp,'node':ni,'request':w['factName'],'mode':mode,'direction':'incoming'if inc else'outgoing','contact':contact,'controller_readers':reader,'real_ACK_writers':writer};rows.append(row);ck('all_direction_Wakako_request '+q+gp+ni,contact=='wakako'and bool(reader)and bool(writer),row)
  directions[q]=rows;ck('positive_request_inventory '+q,bool(rows),{'count':len(rows),'outgoing':sum(r['direction']=='outgoing'for r in rows)})
 inert=next(d for d in M if 'sts_wbr_hil_01'in d and 'prestate_control'in d);ck('HIL01_original_prestate_genuinely_inert',len(g(inert)['nodes'])==2 and g(inert)['edges']==[]and not M[inert]['root_prefabs']and not any(nd['prefabs']or nd['writes']for nd in g(inert)['nodes'].values()),'original input0 and unreachable output1, no edges/actions/prefabs; no invented owner needed')
 jpn=next(r for r in rec if r['id']=='sts_wbr_jpn_03'and r['kind']=='entry');ck('JPN03_uppercase_native_input',jpn['main_input']=='IN'and any(ed[3]=='IN'for ed in g(jpn['depot'])['edges']),'retain actual IN socket, not case-normalized In1')
 native=M[jpn['native']];ck('JPN03_uppercase_native_output','OUT'in {nd['payload'].get('socketName',{}).get('$value')for nd in native['graphs']['root']['nodes'].values()if nd['type']=='questOutputNodeDefinition'},'native OUT preserved')
 supplement=read(P/'retaliation_02/evidence.json');ck('Tyger_original_native_pins',sha(supplement['native']['binary'])==supplement['native']['sha256']and sha(supplement['native']['json'])==supplement['native']['json_sha256'],supplement['native']);orig=Resource(read(supplement['native']['json'])).normalize();ck('Tyger_complete_native_helper_body',orig['graphs']['root/37']==g(gang,'root/22/37'),'exact native Tyger child body, not only selector initials')
 for gp,ng in orig['graphs'].items():
  if gp!='root/37'and not gp.startswith('root/37/'):continue
  cg=copy.deepcopy(g(gang,'root/22'+gp[len('root'):]))
  if gp=='root/37/298':
   expected={str(r['node']):r['owner']for r in supplement['actual_adaptations']}
   for ni,owner in expected.items():
    old=ng['nodes'][ni];new=cg['nodes'][ni];cond=new['payload']['condition'];nativecond=old['payload']['condition'];check=copy.deepcopy(new['payload']);check['condition']=nativecond
    ck('Tyger_selector_only_existing_owner_guard '+ni,cond['$type']=='questLogicalCondition'and cond['operation']=='AND'and nativecond in cond['conditions']and any(r.get('factName')==owner and r.get('value')==1 for r in new['reads'])and check==old['payload'],{'graph':gp,'node':ni,'owner':owner,'native_condition':nativecond,'current_condition':cond});cg['nodes'][ni]=copy.deepcopy(old)
  ck('Tyger_recursive_body_except_four_existing_guards '+gp,cg==ng,{'native_graph':gp,'current_graph':'root/22'+gp[len('root'):]})
 hil=next(r['depot']for r in rec if r['id']=='sts_wbr_hil_07'and r['kind']=='entry');ck('HIL07_requires_owned_Tyger_support',any(r.get('factName')=='PTFRU9_Retaliation_tygerclaws_Issued'and r.get('value')==1 for r in n(hil,65002)['reads']),'native gang dependency before story entry')
 ck('HIL07_dedicated_selector_owner_guard',any(r.get('factName')=='PTFRU9_sts_wbr_hil_07_Started'and r.get('value')==1 for r in n(gang,78,'root/22/37/298')['reads']),'current exact HIL07 Started guard; other selectors remain distinct')
 for q in ids:
  p=I.W/'prealpha/quest_restoration_qr5/shared/tdb_applicability_02'/str(q+'.json');s=read(p);pins.append({'path':str(p),'sha256':sha(p)});ck('stock_definition_limits '+q,bool(s['limits']),'route/economic descendants/runtime overrides remain bounded')
 # Independent actual raw-scene ACK fault, production unchanged.
 raw=copy.deepcopy(read(next(p['json']for p in pins if p.get('depot')==hs)));changed=0
 for x in walk(raw):
  if x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='holo_wakako_calls_v_start_done'and x.get('value')==1:x['value']=0;changed+=1
 mm=Resource(raw).normalize();caught=not any(w.get('factName')=='holo_wakako_calls_v_start_done'and w['value']==1 for nd in mm['graphs']['scene']['nodes'].values()for w in nd['writes']);ck('raw_Wakako_ACK_fault_detected',changed>0 and caught,'actual raw mutation, no fabricated success accepted');write(O/'ACK_mutation.scene.json',raw)
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'phone_directions.json',directions);r={'status':'PASS_INDEPENDENT_SOURCE_REVIEW_WITH_EXPLICIT_LIMITS','group':'G13','quest_ids':ids,'checks':len(tests),'tests':str(O/'tests.json'),'tests_sha256':sha(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'source_pins_sha256':sha(O/'source_pins.json'),'reviewed_results_sha256':sha(P/'results.json'),'mutations':1,'findings':['All three actual native contacts are Wakako, independently enumerated across all request directions and linked to current owner/readers/real ACKs.','Original entry/map/credit selected payloads and sockets/edges match. HIL01 prestate is genuinely inert; JPN03 uppercase IN/OUT are preserved.','HIL07 requires Tyger support; complete recursive native root37 helper is retained at current22/37 except four existing positive-owner selector guards; HIL07 Started is scoped at22/37/298:78, all other payloads and edges unchanged.'],'remaining':['World/prefab/actor acquisition, native stealth and gang reaction timing, saved owner/default history, economic descendants/runtime overrides and live phone scheduling remain unverified.','Raw source preservation does not establish all named quests fully statically or gameplay verified.'],'runtime_changes':[]};write(H/'reviews/G13.json',r);print({'checks':len(tests),'review_sha256':sha(H/'reviews/G13.json')})
if __name__=='__main__':run()
