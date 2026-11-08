"""Direction-aware phone closure plus four Little China native story contracts."""
import sys,copy,re,argparse
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource
from verify import path
PHONE=re.compile(r'^(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate$')
def run(O):
 assert not O.exists();M={};pins=[];tests=[];mut=[]
 def ck(name,ok,e):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':e});assert ok,name
 for d in I.selected():M[d],p=I.load(d);pins.append(p)
 def find(t):return next(d for d in M if d.endswith('\\'+t))
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,k,p='root'):return g(d,p)['nodes'][str(k)]
 def e(d,a,s,b,t,p='root'):return [str(a),s,str(b),t]in g(d,p)['edges']
 def wr(d,k,f,v,p='root'):return any(w.get('factName')==f and w.get('value')==v for w in n(d,k,p)['writes'])
 init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';cl='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase';ck('Regina_actual_initializer84',n(init,84)['refs']==[I.HC]and e(init,25,'Out1',84,'In1'),'current raw private owner84');ck('Regina_actual_cleanup',e(cl,474,'True',342,'In48')and n(cl,342)['refs']==[I.CL],'actual native cleanup342, not inferred from files on disk')
 for inp,ack in [('holo_reggie_calls_v_start',396),('holo_reggie_calls_v_end',398),('holo_v_calls_reggie_start',400),('holo_v_calls_reggie_end',401)]:ck('Regina_real_ACK '+inp,wr(I.HS,ack,inp+'_done',1,'scene')and bool(path(g(I.HS,'scene'),g(I.HS,'scene')['entries'][inp],ack)),{'input':inp,'node':ack})
 phones={};directions={};direct=[]
 for q in I.Q:
  rows=[]
  for d,m in M.items():
   if q not in d or not d.startswith('base'):continue
   for gp,gr in m['graphs'].items():
    for ni,nd in gr['nodes'].items():
     for x in walk(nd['payload']):
      if x.get('$type')in ['questCallContact_NodeType','questSendMessage_NodeType']:direct.append({'quest_id':q,'depot':d,'graph':gp,'node':ni,'type':x['$type'],'payload':x})
     for w in nd['writes']:
      if w.get('value')!=1:continue
      ma=PHONE.fullmatch(w['factName'])
      if not ma:continue
      mode,inc,out,kind=ma.groups();contact=inc or out;direction='incoming'if inc else'outgoing';ack='holo_'+(contact+'_calls_v'if inc else'v_calls_'+contact)+'_'+kind+'_done';listeners=[{'node':i,'condition':nn['payload'].get('condition')}for i,nn in g(I.HC)['nodes'].items()if any(r.get('factName')==w['factName']for r in nn['reads'])];writers=[i for i,nn in g(I.HS,'scene')['nodes'].items()if any(ww.get('factName')==ack and ww.get('value')==1 for ww in nn['writes'])];row={'depot':d,'graph':gp,'node':ni,'request':w['factName'],'mode':mode,'direction':direction,'contact':contact,'real_ACK':ack,'listener_nodes':listeners,'real_ACK_writers':writers,'incoming_edges':[ed for ed in gr['edges']if ed[2]==ni],'native_scene_event_callers':[{'node':ed[0],'event':ed[1],'scene_refs':gr['nodes'][ed[0]]['refs']}for ed in gr['edges']if ed[2]==ni and gr['nodes'][ed[0]]['type']=='questSceneNodeDefinition']};rows.append(row);ck('all_direction_request_owned '+q+gp+ni,contact=='reggie'and bool(listeners)and bool(writers),row)
  phones[q]=rows;directions[q]={'incoming_holo':sum(r['mode']=='holo'and r['direction']=='incoming'for r in rows),'outgoing_holo':sum(r['mode']=='holo'and r['direction']=='outgoing'for r in rows),'incoming_audio':sum(r['mode']=='audio'and r['direction']=='incoming'for r in rows),'outgoing_audio':sum(r['mode']=='audio'and r['direction']=='outgoing'for r in rows)};ck('explicit_direction_coverage '+q,bool(rows)and sum(directions[q].values())==len(rows),directions[q])
 # Native objective outcomes and device branches, not generic success labels.
 h=find('sts_wat_lch_06_ow.questphase');p=find('sts_wat_lch_05_openworld.questphase');t=find('sts_wat_lch_01_openworld.questphase');b=find('sts_wat_lch_03_streetstory.questphase')
 cases=[(h,'root/3',[(130,'Out',31,'Succeeded'),(143,'Out',31,'Succeeded'),(31,'Out',18,'Active'),(20,'Out',21,'Succeeded')]),(h,'root/4',[(4,'Out',6,'In'),(3,'Out',7,'In'),(40,'True',41,'In'),(41,'Out',31,'In')]),(t,'root/3',[(72,'Out',21,'Succeeded'),(21,'Out',24,'Active'),(19,'Out',74,'Active')]),(t,'root/5',[(2,'Out',4,'In'),(7,'Out',6,'In'),(35,'True',37,'In'),(37,'Out',36,'In'),(36,'Out',24,'In')]),(p,'root/6',[(9,'Out',6,'In'),(3,'Out',4,'In1'),(3,'Out',5,'In1')]),(b,'root/6',[(167,'End 0',212,'In'),(169,'End 0',213,'In'),(299,'False',297,'Active'),(299,'True',301,'Active'),(303,'False',302,'Active'),(303,'True',304,'Active'),(297,'Out',213,'In'),(301,'Out',213,'In'),(302,'Out',212,'In'),(304,'Out',212,'In'),(212,'Out',191,'In'),(213,'Out',192,'In')])]
 for d,gp,edges in cases:
  for ed in edges:ck('native_specific_stage '+d+gp+str(ed),e(d,*ed,gp),ed)
 ck('Heisenberg_authored_disable_alternative',n(h,143,'root/3')['payload']['condition']['operation']=='AND'and'IsDisabled'in str(n(h,143,'root/3')['payload'])and'#lch_06_dvc_lab_appl_triple'in str(n(h,143,'root/3')['payload']),'native in-room AND disabled lab device alternative, alongside original destruction/cut control route130')
 ck('Tyger_native_upload_then_unpower',n(t,72,'root/3')['payload']['type']['params'][0]['deviceAction']['$value']=='ForceUnpower','retain original netrunner laptop action only after native upload prerequisite; no fake personal-link acknowledgement')
 ck('PlayingKeep_native_eye_fact_and_failure_branch',n(p,206,'root/4')['reads'][0]['factName']=='sts_wat_lch_05_eye_implant'and n(p,215,'root/4')['reads'][0]['factName']=='lch_05_have_eye','separate native engine/item fact and authored success/failure objective tests')
 ck('Bloodsport_alarm_selects_sms_and_both_rewards_retained',n(b,299,'root/6')['reads'][0]['factName']=='lch_03_optional_alarm'and n(b,303,'root/6')['reads'][0]['factName']=='lch_03_optional_alarm'and n(b,212,'root/6')['payload']['type']==n(b,213,'root/6')['payload']['type'],'original alarm optional status/SMS and authored reward alternatives preserved, not relabelled kill/death')
 omissions=[]
 for a in read(H/'verification_02/admission.json'):
  for jp,rows in a['omitted_native_journal'].items():
   act=[r for r in rows if r['class']=='gameJournalQuestObjective'and any(ed[3]=='Active'for ed in r['incoming'])];ck('omitted_native_objective_Active_scan '+jp,not act,rows);omissions.append({'quest_id':a['quest_id'],'path':jp,'rows':rows,'classification':'mappin or locally inactive/failed cleanup-only, not a newly omitted native Active objective'})
 bugscope=[{'depot':d,'root_prefabs':m['root_prefabs'],'graphs':m['graphs'],'classification':'Exact old CYB/CP77 conditions and Phase/Pause/Condition types preserved as evidence; not automatically executing after Tower'}for d,m in M.items()if d.endswith('_bugfixing.questphase')and any(q in d for q in I.Q)]
 stock={};assets={}
 for q in I.Q:
  sp=I.W/'prealpha/quest_restoration_qr5/shared/tdb_applicability_02'/str(q+'.json');s=read(sp);pins.append({'path':str(sp),'sha256':sha(sp)});rr=[r for r in s['targets']if any(a.startswith('QuestRewards.'+q)for a in r.get('requested_aliases',[]))];ck('stock_reward_definition_exists '+q,bool(rr)and all(r['exists_in_stock']for r in rr),rr);stock[q]={'path':str(sp),'sha256':sha(sp),'targets':s['targets'],'limits':s['limits']};assets[q]=[{'depot':d,'root_prefabs':m['root_prefabs'],'metadata_sha256':m['metadata_sha256'],'actors':m['metadata'].get('actors',[]),'workspots':m['metadata'].get('workspots',[]),'props':m['metadata'].get('props',[]),'refs':[{'depot':r,'inventory':I.IDX.get(r,{'status':'NOT_IN_PINNED_INVENTORY'}),'definition_decoded_here':r in M}for r in m['refs']]}for d,m in M.items()if d.startswith('base')and q in d]
 for label,d,gp,ni,key in [('real_ACK',I.HS,'scene',396,'holo_reggie_calls_v_start_done'),('Bloodsport_alarm',b,'root/6',299,'lch_03_optional_alarm'),('Heisenberg_reward',h,'root/4',4,'QuestRewards.sts_wat_lch_06_completion')]:
  raw=copy.deepcopy(read(next(pn['json']for pn in pins if pn.get('depot')==d)));changes=0
  for x in walk(raw):
   if label=='Heisenberg_reward'and x.get('$type')=='TweakDBID'and x.get('$value')==key:x['$value']='QuestRewards.QR5_missing';changes+=1
   elif label!='Heisenberg_reward'and x.get('factName')==key:x['factName']='QR5_deliberately_missing_fact';changes+=1
  mm=Resource(raw).normalize();caught=mm['graphs'][gp]['nodes'][str(ni)]['payload']!=n(d,ni,gp)['payload'];ck('raw_mutation_detected '+label,changes>0 and caught,{'depot':d,'graph':gp,'node':ni,'changes':changes});mp=O/'mutations'/str(label+'.json');write(mp,raw);mut.append({'fault':label,'caught':caught,'path':str(mp),'sha256':sha(mp)})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'phone_directions.json',{'directions':directions,'all_fact_producers':phones,'typed_phone_manager_actions':direct,'limit':'Fact direction enumeration is complete in pinned native closure; external implicit engine requests and live timing remain explicit.'});write(O/'journal_omissions.json',omissions);write(O/'native_bugfix_scope.json',bugscope);write(O/'asset_bindings.json',assets);write(O/'stock_applicability.json',stock);write(O/'mutations.json',mut);print({'checks':len(tests),'mutations':len(mut),'directions':directions,'out':str(O)})
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);run(Path(ap.parse_args().out))
