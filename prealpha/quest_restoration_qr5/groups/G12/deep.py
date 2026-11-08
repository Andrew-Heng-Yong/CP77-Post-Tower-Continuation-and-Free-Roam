"""Direction-aware phone closure plus three Northside native story contracts."""
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
 # Quest-specific progression/reward paths, with original failure exclusion.
 a6=find('sts_wat_nid_06_openworld.questphase');a4=find('sts_wat_nid_04_openworld.questphase');a3=find('sts_wat_nid_03_openworld.questphase')
 cases=[(a6,'root/4',[(120,'End 0',91,'In'),(141,'Out',91,'In'),(91,'Out',136,'In')]),(a6,'root/5',[(34,'Out',2,'In'),(2,'Out',29,'In')]),(a4,'root/11',[(59,'Out',62,'In'),(62,'Out',45,'Active'),(92,'Out',91,'In'),(91,'Out',69,'In')]),(a4,'root/19',[(25,'End 0',26,'In'),(26,'True',23,'In'),(26,'False',19,'In'),(23,'Out',19,'In'),(19,'Out',7,'In')]),(a3,'root/4/273',[(105,'Out',139,'In'),(105,'Out',140,'In'),(164,'Out',165,'In')]),(a3,'root/5',[(41,'Out',43,'In'),(43,'Out',42,'In')])]
 for d,gp,edges in cases:
  for ed in edges:ck('native_specific_stage '+d+gp+str(ed),e(d,*ed,gp),ed)
 ck('DirtyBiz_reward_excludes_original_failed_state',n(a4,26,'root/19')['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'nid_04_failed','value':0}],'failed state skips reward23; native normal and failed finished writes remain')
 ck('LousyKleppers_original_data_drive_predicate',n(a6,133,'root/4')['reads'][0]['factName']=='sts_wat_nid_06_data_drive','actual original item/device fact predicate retained; no data possession fabricated')
 ck('DirtyBiz_duo_recording_scene_separate_writers',all(any(w.get('factName')=='nid_04_recording_found'and w['value']==1 for w in n(find('sts_wat_nid_04_gottfrid_fredrik.scene'),ni,'scene')['writes'])for ni in [391,394]),'native Gottfrid/Fredrik dialogue outcomes, alarm and recording-found retained; no death choice forced')
 omissions=[]
 for a in read(H/'verification_01/admission.json'):
  for jp,rows in a['omitted_native_journal'].items():
   act=[r for r in rows if r['class']=='gameJournalQuestObjective'and any(ed[3]=='Active'for ed in r['incoming'])];ck('omitted_native_objective_Active_scan '+jp,not act,rows);omissions.append({'quest_id':a['quest_id'],'path':jp,'rows':rows,'classification':'mappin or locally inactive/failed cleanup-only, not a newly omitted native Active objective'})
 bugscope=[{'depot':d,'root_prefabs':m['root_prefabs'],'graphs':m['graphs'],'classification':'Exact old CYB/CP77 conditions and Phase/Pause/Condition types preserved as evidence; not automatically executing after Tower'}for d,m in M.items()if d.endswith('_bugfixing.questphase')and any(q in d for q in I.Q)]
 stock={};assets={}
 for q in I.Q:
  sp=I.W/'prealpha/quest_restoration_qr5/shared/tdb_applicability_02'/str(q+'.json');s=read(sp);pins.append({'path':str(sp),'sha256':sha(sp)});rr=[r for r in s['targets']if any(a.startswith('QuestRewards.'+q)for a in r.get('requested_aliases',[]))];ck('stock_reward_definition_exists '+q,bool(rr)and all(r['exists_in_stock']for r in rr),rr);stock[q]={'path':str(sp),'sha256':sha(sp),'targets':s['targets'],'limits':s['limits']};assets[q]=[{'depot':d,'root_prefabs':m['root_prefabs'],'metadata_sha256':m['metadata_sha256'],'actors':m['metadata'].get('actors',[]),'workspots':m['metadata'].get('workspots',[]),'props':m['metadata'].get('props',[]),'refs':[{'depot':r,'inventory':I.IDX.get(r,{'status':'NOT_IN_PINNED_INVENTORY'}),'definition_decoded_here':r in M}for r in m['refs']]}for d,m in M.items()if d.startswith('base')and q in d]
 for label,d,gp,ni,key in [('real_ACK',I.HS,'scene',396,'holo_reggie_calls_v_start_done'),('DirtyBiz_failure_reward',a4,'root/19',26,'nid_04_failed'),('Lousy_reward',a6,'root/5',2,'QuestRewards.sts_wat_nid_06_completion')]:
  raw=copy.deepcopy(read(next(pn['json']for pn in pins if pn.get('depot')==d)));changes=0
  for x in walk(raw):
   if label=='Lousy_reward'and x.get('$type')=='TweakDBID'and x.get('$value')==key:x['$value']='QuestRewards.QR5_missing';changes+=1
   elif label!='Lousy_reward'and x.get('factName')==key:x['factName']='QR5_deliberately_missing_fact';changes+=1
  mm=Resource(raw).normalize();caught=mm['graphs'][gp]['nodes'][str(ni)]['payload']!=n(d,ni,gp)['payload'];ck('raw_mutation_detected '+label,changes>0 and caught,{'depot':d,'graph':gp,'node':ni,'changes':changes});mp=O/'mutations'/str(label+'.json');write(mp,raw);mut.append({'fault':label,'caught':caught,'path':str(mp),'sha256':sha(mp)})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'phone_directions.json',{'directions':directions,'all_fact_producers':phones,'typed_phone_manager_actions':direct,'limit':'Fact direction enumeration is complete in pinned native closure; external implicit engine requests and live timing remain explicit.'});write(O/'journal_omissions.json',omissions);write(O/'native_bugfix_scope.json',bugscope);write(O/'asset_bindings.json',assets);write(O/'stock_applicability.json',stock);write(O/'mutations.json',mut);print({'checks':len(tests),'mutations':len(mut),'directions':directions,'out':str(O)})
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);run(Path(ap.parse_args().out))
