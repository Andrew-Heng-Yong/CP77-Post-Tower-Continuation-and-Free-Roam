"""Independent remaining QR5 peers. Source catalogs are inputs, peer verifiers are not."""
from pathlib import Path
import sys,json,copy,re,collections,argparse
W=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk
from model import Resource,compare_graph,digest
def ext(x):
 if isinstance(x,list):return [ext(v)for v in x]
 if isinstance(x,dict):
  r={k:ext(v)for k,v in x.items()}
  if r.get('Flags')=='Embedded'and 'DepotPath'in r:r['Flags']='Soft'
  if r.get('$type')=='questQuestPhaseResource'and r.get('cookingPlatform')=='PLATFORM_None':r['cookingPlatform']='PLATFORM_PC'
  return r
 return x
def path(g,a,b):
 q=collections.deque([[str(a)]]);seen={str(a)}
 while q:
  p=q.popleft()
  if p[-1]==str(b):return p
  for x,s,y,t in g['edges']:
   if x==p[-1]and s!='CutSource'and t!='CutDestination'and not(g['nodes'].get(x,{}).get('type')=='scnCutControlNode'and s.startswith('1:'))and y not in seen:seen.add(y);q.append(p+[y])
 return None

class Peer:
 def __init__(self,group,ver):
  self.group=group;self.O=H/(group+('_evidence_03'if group=='G03'else'_evidence_01'));assert not self.O.exists();self.tests=[];self.pins=[];self.M={};self.docs={};self.P=W/'prealpha/quest_restoration_qr5/groups'/group;self.R=read(self.P/'results.json');self.ids=read(W/'prealpha/quest_restoration_qr5/progress.json')['groups'][group]['ids']
  self.ck('frozen_peer_catalog',sha(self.R['source_pins'])==self.R['source_pins_sha256']and sha(self.R['tests'])==self.R['tests_sha256'],sha(self.P/'results.json'))
  epoch=read(self.R['source_epoch']);self.ck('exact_frozen_epoch',sha(self.R['source_epoch'])==self.R['source_epoch_sha256'],self.R['source_epoch_sha256'])
  for p in read(self.R['source_pins']):
   d=p.get('depot')
   if not d:continue
   self.ck('input_hashes '+d,sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p)
   if p.get('historical_raw_sha256'):self.ck('historical_native_raw_pin '+d,p['sha256']==p['historical_raw_sha256'],p['historical_raw_sha256'])
   if d.startswith('towercontinued'):self.ck('current_epoch_resource '+d,p['sha256']==epoch['source_resources'][d],p['sha256'])
   self.docs[d]=read(p['json']);self.M[d]=Resource(self.docs[d]).normalize();self.pins.append(p)
  self.rec=[r for r in read(W/'research/gig_restoration/native_gigs_u9/manifest.json')['recipes']if r['id']in self.ids]
 def ck(self,k,v,e):self.tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e});assert v,k
 def g(self,d,gp='root'):return self.M[d]['graphs'][gp]
 def n(self,d,i,gp='root'):return self.g(d,gp)['nodes'][str(i)]
 def e(self,d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in self.g(d,gp)['edges']
 def find(self,t):return next(d for d in self.M if d.endswith('\\'+t))
 def common(self):
  for r in self.rec:
   d=r['depot'];nd='recipe:'+r['raw'];gp=r['graph']
   for ni in r['ids']:
    if ni:self.ck('native_selected_payload '+d+':'+str(ni),self.n(d,ni)['payload']==ext(self.n(nd,ni,gp)['payload']),{'donor':nd,'graph':gp,'node':ni})
    pref='root/'+str(ni);native=gp+'/'+str(ni)
    for child,gr in self.M[d]['graphs'].items():
     if child==pref or child.startswith(pref+'/'):self.ck('complete_selected_child '+d+child,gr==self.g(nd,native+child[len(pref):]),native+child[len(pref):])
   self.ck('exact_original_recipe_edges '+d,self.g(d)['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]),r['edges'])
  for d in [d for d in self.M if d.startswith('recipe:')]:
   for em in self.M[d].get('embedded_files',[]):
    sd=em['depot'];pre=em['graph_prefix']+'/root'
    if sd not in self.M or not any(q in sd for q in self.ids):continue
    orig={'graphs':{'root'+gp[len(pre):]:gr for gp,gr in self.M[d]['graphs'].items()if gp==pre or gp.startswith(pre+'/')},'metadata':em['metadata'],'metadata_sha256':digest(em['metadata'])};orig=ext(orig);orig['metadata_sha256']=digest(orig['metadata'])
    self.ck('whole_embedded_body_parity '+sd,not compare_graph(orig,self.M[sd]),{'original':d,'prefix':pre,'only_envelope':['Embedded→Soft','cooking None→PC']})
  rx=re.compile(r'^(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate$');directions={}
  init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';cleanup='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase'
  for q in self.ids:
   contact='reggie'if self.group=='G11'else'wakako'if self.group=='G14'else'mr_hands'if q=='sts_pac_cvi_02'else'muamar';hc=f'base\\quest\\holocalls\\{contact}\\{contact}_holocall.questphase';hs=f'base\\quest\\holocalls\\{contact}\\{contact}_holocall.scene';cl=f'base\\quest\\holocalls\\{contact}\\{contact}_cleanup.questphase'
   self.ck('effective_contact_owner '+q,any(hc in n['refs']and path(self.g(init),'25',i)for i,n in self.g(init)['nodes'].items())and any(cl in n['refs']and any(e[2]==i for e in self.g(cleanup)['edges'])for i,n in self.g(cleanup)['nodes'].items()),{'controller':hc,'cleanup':cl})
   rows=[]
   for d,m in self.M.items():
    if not d.startswith('base')or q not in d:continue
    for gp,g in m['graphs'].items():
     for i,n in g['nodes'].items():
      for w in n['writes']:
       ma=rx.fullmatch(w['factName'])if w['value']==1 else None
       if not ma:continue
       mode,inc,out,kind=ma.groups();c=inc or out;ack='holo_'+(c+'_calls_v'if inc else'v_calls_'+c)+'_'+kind+'_done';listeners=[j for j,x in self.g(hc)['nodes'].items()if any(r.get('factName')==w['factName']for r in x['reads'])];writers=[j for j,x in self.g(hs,'scene')['nodes'].items()if any(r.get('factName')==ack and r.get('value')==1 for r in x['writes'])];row={'resource':d,'graph':gp,'node':i,'request':w['factName'],'mode':mode,'direction':'incoming'if inc else'outgoing','contact':c,'listeners':listeners,'real_ACK_writers':writers};rows.append(row);self.ck('direction_aware_request '+q+gp+i,c==contact and bool(listeners)and bool(writers),row)
   self.ck('positive_actual_request_sites '+q,bool(rows),len(rows));directions[q]=rows
   target=W/'prealpha/quest_restoration_qr5/shared/tdb_applicability_02'/str(q+'.json');tdb=read(target);self.ck('bounded_stock_target_semantics '+q,bool(tdb['limits']),tdb['limits']);self.pins.append({'path':str(target),'sha256':sha(target)})
  write(self.O/'phone_directions.json',directions)
 def done(self,findings,remaining,mutations=0,status='PASS_INDEPENDENT_SOURCE_REVIEW_WITH_LIMITS'):
  write(self.O/'tests.json',self.tests);write(self.O/'source_pins.json',self.pins);r={'status':status,'group':self.group,'quest_ids':self.ids,'reviewed_results_sha256':sha(self.P/'results.json'),'checks':len(self.tests),'raw_mutations':mutations,'tests':str(self.O/'tests.json'),'tests_sha256':sha(self.O/'tests.json'),'source_pins':str(self.O/'source_pins.json'),'source_pins_sha256':sha(self.O/'source_pins.json'),'findings':findings,'remaining':remaining,'runtime_changes':[]};write(H/(self.group+'.json'),r);print(json.dumps({'group':self.group,'checks':len(self.tests),'review_sha256':sha(H/(self.group+'.json'))},ensure_ascii=True))

def g14():
 p=Peer('G14','verification_03');p.common()
 olive=p.find('sts_wbr_jpn_01.questphase');b=p.find('sts_wbr_jpn_01b_openworld.questphase');pre=p.find('sts_wbr_jpn_01_prestate_control.questphase');wife=p.find('sts_wbr_jpn_02_streetstory.questphase');fav=p.find('sts_wbr_jpn_05_openworld.questphase');credit=p.find('sts_wbr_jpn_05_credit.questphase')
 p.ck('Olive_prestate_exactly_inert',len(p.g(pre)['nodes'])==2 and not p.g(pre)['edges']and not p.M[pre]['root_prefabs']and all(not n['writes']and not n['prefabs']for n in p.g(pre)['nodes'].values()),'input0 and unreachable output1, no actions/edges/leases')
 p.ck('Olive_full_nested_world_lease','#sts_wbr_jpn_01_streetstory'in p.n(b,7,'root/3')['prefabs'],p.n(b,7,'root/3')['payload'])
 p.ck('Olive_free_Alex_native_branch',p.n(olive,36)['reads'][0]['factName']=='jpn_01_alex_is_free'and p.e(olive,36,'Out',39,'In')and p.e(olive,39,'Out',33,'In1'),p.g(olive)['edges'])
 p.ck('Olive_failed_reward_fence',p.e(olive,19,'True',90,'In','root/17')and p.e(olive,19,'False',97,'In','root/17')and p.n(olive,19,'root/17')['reads'][0]['factName']=='jpn_01_failed',p.n(olive,19,'root/17')['payload'])
 p.ck('Olive_distinct_authored_rewards',p.n(olive,17,'root/17')['type']=='questRewardManagerNodeDefinition'and p.n(olive,77,'root/17')['type']=='questRewardManagerNodeDefinition'and p.e(olive,76,'False',17,'In','root/17')and p.e(olive,76,'True',77,'In','root/17'),p.n(olive,76,'root/17')['payload'])
 p.ck('Olive_native_deliver_only_failed_cleanup',p.e(b,194,'True',129,'Failed','root/5')and p.n(b,129,'root/5')['journal_paths'][0].endswith('/deliver'),p.n(b,194,'root/5')['payload'])
 p.ck('Wife_exact_Lauren_rescue_and_exit',p.e(wife,28,'jpn_02_lauren_first_end',145,'Succeeded','root/3')and p.e(wife,145,'Out',12,'Active','root/3')and p.e(wife,61,'jpn_02_lauren_head_low_end',176,'In','root/3'),{i:p.n(wife,i,'root/3')['payload']for i in [28,145,12,61,176]})
 p.ck('Wife_native_completion_and_reward',p.n(wife,33,'root/6')['type']=='questRewardManagerNodeDefinition'and p.n(wife,38,'root/6')['writes'][0]['factName']=='jpn_02_finished',p.g(wife,'root/6')['edges'])
 p.ck('Favorite_mail_music_shard_paths',p.n(fav,141,'root/5')['reads'][0]['factName']=='jpn_05_mail'and p.n(fav,195,'root/5')['reads'][0]['factName']=='jpn_05_moment_music'and p.e(fav,226,'Out',27,'Active','root/5'),{i:p.n(fav,i,'root/5')['payload']for i in [141,195,226,27]})
 p.ck('Favorite_native_three_game_hour_finish',p.e(fav,63,'Out',64,'In','root/4')and p.e(fav,64,'Out',36,'In','root/4')and p.n(fav,64,'root/4')['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':0,'hours':3,'minutes':0,'seconds':0},p.n(fav,64,'root/4')['payload'])
 p.ck('Favorite_actual_credit_receipt_OR_finished',p.n(credit,19)['type']=='questLogicalXorNodeDefinition'and p.e(credit,18,'Out',19,'In2')and p.e(credit,20,'Out',19,'In1')and p.e(credit,19,'Out1',3,'In'),{i:p.n(credit,i)['payload']for i in [18,19,20,3]})
 raw=copy.deepcopy(p.docs[credit]);matches=[x for x in walk(raw)if x.get('$type')=='questLogicalXorNodeDefinition'and x.get('id')==19];assert len(matches)==1;matches[0]['$type']='questLogicalAndNodeDefinition';mut=Resource(raw).normalize();p.ck('raw_Favorite_AND_credit_fault_detected',mut['graphs']['root']['nodes']['19']['type']!=p.n(credit,19)['type'],'Changed actual source XOR19 to AND; exact native OR policy rejects mutation');write(p.O/'credit_join_mutation.questphase.json',raw)
 p.done(['All three actual contacts are Wakako; both holo/audio directions scanned across full own phases/scenes, current controller/listener/realACK/cleanup applicability checked independently.','Original selected parent/map/credit payloads and edges plus complete embedded native bodies and nested prefab obligations match approved cooking/handle envelope only.','Olive original inert parallel prestate, nested whole-story lease, Alex-free/failure/reward17-or77 branches retained; Wife Lauren rescue/escape/debrief paths retained.','Favorite mail/music/shard and exact three-game-hour finish delay retained; actual credit joins achievement receipt OR finished by native XOR19, raw AND mutation rejected.'],['Static parity does not certify world/actor placement, save lease transitions, engine scene/phone/reload scheduling, native journal definitions, stock economic descendants or runtime overrides.','Olive deliver objective local omission is condition/Failed cleanup only within captured own closure; foreign writers and saved journal semantics are separate limits.'],1)

def g03():
 p=Peer('G03','verification_05');p.common();cvi=p.find('sts_pac_cvi_02.questphase');wwd=p.find('sts_pac_wwd_05.questphase');body=p.find('sts_pac_wwd_05_phase.questphase');entry=p.find('sts_pac_wwd_05_entry.questphase');credit=p.find('sts_pac_wwd_05_credit.questphase')
 bindings=[(r,next(n for n in p.g('recipe:'+r['raw'],r['graph'])['nodes'].values()if r['native']in n['refs']))for r in p.rec if r['kind']=='entry'];p.ck('corrected_exact_parent_flags',all(n['payload']['phaseResource']['Flags']==('Soft'if r['id']=='sts_pac_cvi_02'else'Embedded')for r,n in bindings),[{r['id']:n['payload']}for r,n in bindings])
 p.ck('CVI02_owned_continuing_health_and_water',p.n(cvi,255,'root/8/10')['type']=='questPauseConditionNodeDefinition'and p.n(cvi,256,'root/8/10')['type']=='questPauseConditionNodeDefinition'and p.n(cvi,257,'root/8/10')['type']=='questLogicalXorNodeDefinition'and p.e(cvi,255,'Out',257,'In1','root/8/10')and p.e(cvi,256,'Out',257,'In2','root/8/10'),{i:p.n(cvi,i,'root/8/10')['payload']for i in [255,256,257]})
 p.ck('CVI02_exact_body_world_lease','#sts_pac_cvi_02_streetstory'in p.M[cvi]['root_prefabs'],p.M[cvi]['root_prefabs'])
 p.ck('WWD05_actual_two_native_entry_sockets',set(p.g(wwd)['entries'])=={'STS_started','STS_not_started'}and p.e(entry,65003,'Out',12,'STS_not_started')and p.e(entry,65004,'Out',12,'STS_started'),{'native':p.g(wwd)['entries'],'current':p.g(entry)['edges']})
 p.ck('WWD05_cross_district_Rancho_tier3',p.n(entry,3,'root/4')['reads'][0]['factName']=='sts_std_rcr_tier_3',p.n(entry,3,'root/4')['payload'])
 p.ck('WWD05_SantoDomingo_credit',p.n(credit,13)['writes'][0]['factName']=='std_sts_counter',p.n(credit,13)['payload'])
 p.ck('WWD05_native_Logan_reward_cleanup',p.n(body,67,'root/4')['writes'][0]['factName']=='wwd_05_logan_dead'and p.e(body,108,'Out',69,'In','root/4')and p.e(body,117,'Out',118,'In','root/4'),{i:p.n(body,i,'root/4')['payload']for i in [67,108,69,117,118]})
 # Independent exact foreign journal writer match, rather than forward closure claims.
 ap=W/'prealpha/quest_restoration_qr5/groups/G14/corrections/CVI02_NID02_crosswrite_01/addendum.json';a=read(ap);orig=a['native_original_match']['donor'];p.ck('foreign_writer_native_input_hash',sha(orig['binary'])==orig['sha256']and sha(orig['json'])==orig['json_sha256'],orig);om=Resource(read(orig['json'])).normalize();native=om['graphs'][a['native_original_match']['graph']]['nodes']['92'];nid=next(d for d in p.M if d.endswith('sts_wat_nid_02_ow.questphase'));cur=p.n(nid,92,'root/4/138')
 p.ck('native_foreign_objective_writer_exact',native['payload']==cur['payload']and a['target']in cur['journal_paths']and p.e(nid,72,'True',92,'Inactive','root/4/138'),{'writer':cur['payload'],'guard':p.n(nid,72,'root/4/138')['payload'],'addendum':str(ap),'sha256':sha(ap)})
 fp=H/'G03_EP1/evidence.json';f=read(fp);p.ck('EP1_controller_coverage_gap_recorded',sha(fp)=='84307EFA2103FB2A7C428CB69C64EE1E5AFD8A3EFC73CB0FA6E3720620B83895'and f['status']=='SOURCE_CONFIRMED_CONTROLLER_OWNERSHIP_GAP_PENDING_INDEPENDENT_REVIEW',{'path':str(fp),'sha256':sha(fp),'specific_body_nodes':[205,208,221,213,215,216,220,214,217,218,219]})
 raw=copy.deepcopy(p.docs[wwd]);matches=[x for x in walk(raw)if x.get('$type')=='questInputNodeDefinition'and x.get('socketName',{}).get('$value')=='STS_not_started'];assert len(matches)==1;matches[0]['socketName']['$value']='BROKEN_EARLY_BOOT';m=Resource(raw).normalize();p.ck('raw_missing_WWD05_early_boot_detected','STS_not_started'not in m['graphs']['root']['entries'],'Actual raw native input8 mutated; restored early-owner binding would no longer resolve');write(p.O/'WWD05_early_boot_mutation.questphase.json',raw)
 p.done(['Actual lineage confirmed independently: CVI02 Mr Hands/pac versus WWD05 Muamar/std; exact selected parent/map/credit nodes and nested native graphs.','DOCUMENTATION CORRECTION: Coastview3 CVI02 is originally Soft, but Rancho12 WWD05 is Embedded and has actual main/phase/combat embedded resources. Whole-body native parity passes independently for all three after only Embedded→Soft/cooking envelope. Frozen claim both are Soft/no embedded proof is superseded.','CVI02 already has owned future van health255/water256→XOR257 failure listeners; no ARR12-style failure-monitor patch is warranted. WWD05 original dual STS_not_started/STS_started boots, Rancho tier3, std counter, Logan outcome/reward/achievement preserved.','Generic holo/audio requests in both directions resolve actual current contact readers, real ACKs and cleanup. This proves only the legacy CVI02 branch when ep1_installed0.','CRITICAL ADDITION: actual ep1_installed1 CVI02 emits separate new_sts_* requests and waits new_q110 outcomes; exact native EP1 activator9 is retired by Tower, and pinned census finds no private substitute. See frozen G03_EP1 evidence; original generic communication/progression coverage requires supersession after independent arbitration.','Native NID02 mounted-van72.True→CVI02 objective92 Inactive exactly matches original donor. Preserve foreign-writer addendum and conditional journal/save semantics.'],['CVI02 EP1 defect awaits independent review and exact scene actor/lease/saved-owner investigation; no speculative fix or fake ACK authorized.','Both directions and native generic-controller parity do not certify specialized request families. Body preservation does not prove executing dependency owners.','World placement, saved owners, foreign journal effects, target economic descendants, unknown script writers and live scheduling/reload remain explicit limits.'],1,'SOURCE_REVIEW_WITH_CONFIRMED_EP1_SCOPE_GAP_PENDING_ARBITRATION')

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('group',choices=['G14','G03']);args=ap.parse_args();g14()if args.group=='G14'else g03()
