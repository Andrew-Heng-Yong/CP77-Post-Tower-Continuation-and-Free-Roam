"""Independent G21 raw/native review. Imports no peer verifier or generated oracle."""
from pathlib import Path
import sys,json,copy,zlib,re,collections
W=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent;P=W/'prealpha/quest_restoration_qr5/groups/G21';O=H/'G21_evidence_01'
sys.path.insert(0,str(W/'tools/parity_audit'));from common import read,write,sha,walk
from model import Resource
sys.path.insert(0,str(W/'prealpha/quest_restoration_qr5/groups/G20'));import inputs as I
from review_remaining import path
def canon(x):
 if isinstance(x,list):return[canon(v)for v in x]
 if isinstance(x,dict):
  if x.get('$type')=='TweakDBID':
   v=x.get('$value','0');return{'$type':'TweakDBID','identity':str((len(v.encode())<<32)|zlib.crc32(v.encode()))if x.get('$storage')=='string'else str(v)}
  return{k:canon(v)for k,v in x.items()if k not in ['payload_sha256','metadata_sha256']}
 return x
def run():
 assert not O.exists();M={};pins=[];tests=[];mut=[];phone=[];assets=[];callbacks=[];Q=['sts_ep1_07','sts_ep1_04','sts_ep1_01'];epoch=read(W/'prealpha/quest_restoration_qr5/source_epoch_08.json');source_results=read(P/'results.json')
 def ck(k,v,e):tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e});assert v,json.dumps({'name':k,'evidence':e},ensure_ascii=True)
 for row in read(P/'raw_exports_01/manifest.json'):
  d=row['depot'];ck('actual_binary_and_fresh_JSON_hash '+d,sha(row['raw'])==row['raw_sha256']and sha(row['json'])==row['json_sha256'],row);m=Resource(read(row['json'])).normalize();M[d]=m;orig,pi=I.load('recipe:'+d.split(':',1)[1]if d.startswith('vanilla_recipe:')else d);pins+=[row,pi];ck('independent_complete_raw_normalization '+d,canon(m)==canon(orig),{'original':pi,'fresh':row,'limit':'Only TDB numeric identity and derived digest storage normalized; all graphs, sockets, metadata, PFs and nested payloads compared.'})
  if d in epoch['source_resources']:ck('current_canonical08_resource_unchanged '+d,epoch['source_resources'][d]==row['raw_sha256']and sha(Path(epoch['candidate'])/'archive_source'/Path(d.replace('\\','/')))==row['raw_sha256'],{'epoch':str(W/'prealpha/quest_restoration_qr5/source_epoch_08.json'),'sha256':sha(W/'prealpha/quest_restoration_qr5/source_epoch_08.json'),'resource':d})
 def load(d):
  if d not in M:m,p=I.load(d);M[d]=m;pins.append(p);ck('additional_exact_dependency '+d,not m['errors'],p)
  return M[d]
 def find(t):return next(d for d in M if d.endswith('\\'+t))
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,i,p='root'):return g(d,p)['nodes'][str(i)]
 def e(d,a,s,b,t,p='root'):return[str(a),s,str(b),t]in g(d,p)['edges']
 native=next(d for d in M if d.startswith('vanilla_recipe:')and'rollout_r2'in d);recipes=[r for r in I.U['recipes']if r['id']in Q]
 for r in recipes:
  d=r['depot'];cp=r.get('compiled_graph','root');src='vanilla_recipe:'+r['raw'];np=r['graph'];ck('original_recipe_interfaces '+d,g(d,cp)['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]),r['edges'])
  for ni in map(str,r['ids']):
   if ni=='0':continue
   old=copy.deepcopy(n(src,ni,np)['payload']);new=n(d,ni,cp)['payload']
   if'phaseResource'in old:old['phaseResource']['Flags']='Soft'
   ck('original_selected_node '+d+ni,canon(old)==canon(new),{'source':src,'graph':np,'node':ni,'relocation':'Exact original graph/PIPs/metadata; phaseResource Embedded→Soft externalization only where present.'})
   for gp,gr in M[d]['graphs'].items():
    prefix=cp+'/'+ni
    if not(gp==prefix or gp.startswith(prefix+'/'))or(r['id']=='sts_ep1_07'and r['kind']=='entry'and ni=='9'):continue
    ck('original_full_nested_graph '+d+gp,canon(gr)==canon(g(src,np+'/'+ni+gp[len(prefix):])),np+'/'+ni+gp[len(prefix):])
  if r['kind']=='entry':
   ck('original_parent50_wake_and_prefabs '+d,canon(n(d,50)['payload'])==canon(n(src,50)['payload']),n(d,50)['payload'])
   for j,comp in enumerate(r['companions']):
    ci=64000+j;old=copy.deepcopy(n('vanilla_recipe:'+comp['source_raw'],comp['source_node'],comp['source_graph'])['payload']);old['id']=ci
    if'phaseResource'in old:old['phaseResource']['Flags']='Soft'
    ck('original_companion_owner '+d+str(ci),canon(n(d,ci,cp)['payload'])==canon(old),{'native_graph':comp['source_graph'],'native_node':comp['source_node'],'current_node':ci,'kind':comp['kind']})
 # Embedded donor content is independently inspected from the fresh native parent export.
 embedded=[]
 for item in M[native]['embedded_files']:
  d=item['depot']
  if d not in M or not any(q in d for q in Q):continue
  pref=item['graph_prefix'];nativegraphs={p[len(pref+'/'):]:gg for p,gg in M[native]['graphs'].items()if p.startswith(pref+'/')};ck('original_embedded_body_full_graph '+d,canon(nativegraphs)==canon(M[d]['graphs']),{'native':native,'embedded_prefix':pref,'resource':d});ck('original_embedded_body_metadata '+d,canon(item['metadata'])==canon(M[d]['metadata']),{'prefabs':item['root_prefabs'],'metadata':item['metadata']});embedded.append(d)
 # Shared tier gate: actual complete native child and exact outer OR, not a report-derived assertion.
 tier='towercontinued\\special_gigs_u9\\ep1_tier3_gate.questphase';ck('Tier3_full_original_inner_graph','root/50/9'in M[tier]['graphs']and all(canon(gr)==canon(g(native,'root/50/9'+gp[len('root/50/9'):]))for gp,gr in M[tier]['graphs'].items()if gp=='root/50/9'or gp.startswith('root/50/9/')),'Actual native root/50/9 copied in full at shared root/9')
 guard=n(tier,65000,'root/50')['payload']['condition'];ors=[x for x in walk(guard)if x.get('$type')=='questLogicalCondition'and x.get('operation')=='OR'];ck('Tier3_outer_requests_are_two_AND_pairs_in_OR',any([{r['type']['factName']for r in x['conditions']}for x in z['conditions']]==[{'PTFRU9_sts_ep1_06_Request','PTFRU9_sts_ep1_06_Permit'},{'PTFRU9_sts_ep1_07_Request','PTFRU9_sts_ep1_07_Permit'}]for z in ors if all(x.get('operation')=='AND'for x in z['conditions'])),'Either permitted06 or07 request; native historical/debug/tier/core structure remains separate')
 hc=I.HC;hs=I.HS;init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';cl='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase';ck('actual_master_Hosm_owner_and_cleanup',hc in n(init,73)['refs']and e(init,25,'Out1',73,'In1')and I.CL in n(cl,329)['refs']and e(cl,462,'True',329,'In36'),'Actual initializer73 and cleanup329 native scene ownership; not directory presence')
 rx=re.compile(r'^(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate$');other=[]
 for d,m in list(M.items()):
  if not d.startswith('ep1')or not any(q in d for q in Q):continue
  for gp,gr in m['graphs'].items():
   for i,nd in gr['nodes'].items():
    for wr in nd['writes']:
     ma=rx.fullmatch(wr['factName'])if wr['value']==1 else None
     if ma:
      mode,inc,out,kind=ma.groups();who=inc or out;ack='holo_'+(who+'_calls_v'if inc else'v_calls_'+who)+'_'+kind+'_done';li=[k for k,nn in g(hc)['nodes'].items()if any(x.get('factName')==wr['factName']for x in nn['reads'])];aa=[k for k,nn in g(hs,'scene')['nodes'].items()if any(x.get('factName')==ack and x['value']==1 for x in nn['writes'])];rec={'resource':d,'graph':gp,'node':i,'request':wr['factName'],'ACK':ack,'listeners':li,'real_writers':aa};ck('all_actual_phone_directions '+d+gp+i,who=='mr_hands'and bool(li)and bool(aa),rec);phone.append(rec)
     elif wr['value']==1 and(wr['factName'].startswith('new_')or'call'in wr['factName'].lower()and not wr['factName'].startswith(('holo_','audio_'))):other.append({'resource':d,'graph':gp,'node':i,'write':wr})
    if nd['type']=='questSceneNodeDefinition':
     for target in [r for r in nd['refs']if r.endswith('.scene')]:
      if target not in M:load(target)
      for a,s,b,t in gr['edges']:
       if b!=i or t=='CutDestination':continue
       ok=t in M[target]['graphs']['scene']['entries']or t=='Prefetch'and{'name':'Prefetch','type':'Input'}in nd['sockets'];rec={'resource':d,'graph':gp,'node':i,'scene':target,'input':t,'from':[a,s]};ck('actual_scene_callback_binding '+d+gp+i+t,ok,rec);callbacks.append(rec)
    if nd['sms']or nd['reward']or nd['prefabs']:assets.append({'resource':d,'graph':gp,'node':i,'payload':nd['payload'],'incoming':[x for x in gr['edges']if x[2]==i],'outgoing':[x for x in gr['edges']if x[0]==i]})
 # Specific known native authored exceptions and future ownership/cleanup paths.
 road=find('sts_ep1_07_phase.questphase');roadcl=find('sts_ep1_07_cleanup.questphase');prot=find('sts_ep1_04_openworld.questphase');protcl=find('sts_ep1_04_cleanup.questphase');saints=find('sts_ep1_01_openworld.questphase');saintpre=find('sts_ep1_01_holocall_prebrief.scene')
 ck('Roads_cleanup_output_is_NonTerminating',n(roadcl,1)['payload']['type']=='NonTerminating'and n(road,159)['payload']['type']=='Terminating',{'main159':n(road,159)['payload'],'cleanup1':n(roadcl,1)['payload']})
 ck('Roads_own_finished_is_callback_not_full_retirement',e('towercontinued\\native_gigs_u9\\sts_ep1_07_entry.questphase',64000,'Out1',65006,'In','root/50')and e('towercontinued\\native_gigs_u9\\sts_ep1_07_entry.questphase',22,'Out1',64000,'In1','root/50'),'OwnerFinished only observes native cleanup callback; parallel native descendants/nonterminating output are not declared retired')
 ck('Roads_native_outcome_reward_selector',n(road,285)['reads'][0]['factName']=='sts_ep1_07_nele_captured'and e(road,285,'True',82,'In')and e(road,285,'False',284,'In'),{'selector':n(road,285)['payload'],'rewards':[n(road,i)['payload']for i in[82,284]]})
 ck('Roads_future_world_producers_are_distinct',n(roadcl,11)['writes'][0]['factName']=='wst_ep1_08_active'and n(roadcl,14)['writes'][0]['factName']=='wst_ep1_09_active',{'08':n(roadcl,11)['payload'],'09':n(roadcl,14)['payload'],'edges':g(roadcl)['edges']})
 hasan='towercontinued\\sidejobs_s23\\ep1\\hasan_boot.questphase';w9='towercontinued\\sidejobs_s29\\entries\\wst_ep1_09.questphase';load(hasan);load(w9);ck('Hasan_real_default_on_producer',n(protcl,12)['writes'][0]['factName']=='hasan_default_on',n(protcl,12)['payload']);ck('Hasan_actual_supported_native_outcomes',all(any(x.get('factName')==f and x['value']==v for x in n(hasan,2)['reads'])for f,v in [('sts_ep1_04_blueprints_corpo',1),('sts_ep1_04_mr_hands_holo_convinced',1),('sts_ep1_04_blueprints_hasan',0)]),{'guard2':n(hasan,2)['payload'],'limit':'Do not relax to every completion/default_on or infer all U9 histories rejected.'})
 ck('Native_Dogtown_end_has_no_invented_ACK_wait',e(saintpre,192,'0:0',125,'0:0','scene')and path(g(saintpre,'scene'),'125','190')and path(g(saintpre,'scene'),'190','209')and not any(x.get('factName')=='holo_mr_hands_calls_v_end_done'for nn in g(saintpre,'scene')['nodes'].values()for x in nn['reads']),{'end192→125':True,'125→190':path(g(saintpre,'scene'),'125','190'),'190→209':path(g(saintpre,'scene'),'190','209'),'limit':'Exact native clear/no-wait preserved; not certified race-free and not a missing restoration listener.'})
 # Introduce actual raw structural failures only in fresh evidence fixtures.
 row=next(r for r in read(P/'raw_exports_01/manifest.json')if r['depot']==roadcl);raw=read(row['json']);rr=Resource(raw);root=rr.d(rr.root['graph']);obj=next(rr.d(x)for x in root['nodes']if rr.d(x)['id']==1);obj['type']='Terminating';mm=Resource(raw).normalize();caught=canon(mm['graphs']['root']['nodes']['1']['payload'])!=canon(n(roadcl,1)['payload']);ck('raw_nonterminating_cleanup_changed_detected',caught,'Mutated exact native cleanup1 output lifetime');mut.append({'name':'Roads_cleanup_terminator','detected':caught});write(O/'Roads_bad_cleanup.questphase.json',raw)
 row=next(r for r in read(P/'raw_exports_01/manifest.json')if r['depot']==hs);raw=read(row['json']);changes=0
 for x in walk(raw):
  if x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='holo_v_calls_mr_hands_end_done'and x.get('value')==1:x['value']=0;changes+=1
 mm=Resource(raw).normalize();caught=not any(x.get('factName')=='holo_v_calls_mr_hands_end_done'and x['value']==1 for nn in mm['graphs']['scene']['nodes'].values()for x in nn['writes']);ck('raw_missing_actual_outgoing_ACK_detected',changes>0 and caught,changes);mut.append({'name':'Hasan_outgoing_real_end_ACK_removed','detected':caught});write(O/'Hasan_missing_OUT_ACK.scene.json',raw)
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'models.json',M);write(O/'phone_protocols.json',phone);write(O/'custom_call_like_writes.json',other);write(O/'scene_callbacks.json',callbacks);write(O/'rewards_SMS_prefab_nodes.json',assets);write(O/'embedded_original_matches.json',embedded);write(O/'mutations.json',mut);write(O/'summary.json',{'checks':len(tests),'mutations':len(mut),'actual_raw_exports_reparsed':59,'actual_protocol_producers':len(phone),'scene_inputs':len(callbacks),'additional_models':len(M)-59,'native_embedded_matches':embedded});print(json.dumps({'checks':len(tests),'mutations':len(mut),'phone':len(phone),'scene_inputs':len(callbacks),'custom':other},ensure_ascii=True))
if __name__=='__main__':run()
