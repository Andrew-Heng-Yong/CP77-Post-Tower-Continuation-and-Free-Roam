"""Current epoch05 EP1 gig contracts: original graphs, approved Spy delta, all call families."""
from pathlib import Path
import sys,copy,json,re,argparse,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk,value
from model import Resource,reachable
def run(O):
 assert not O.exists();M={};pins=[];tests=[];raw={};mut=[]
 def ck(k,v,e):
  tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:write(O/'failed_tests.json',tests);raise AssertionError(k)
 for d in I.SEL['depots']+read(H/'phone_selection_01.json'):
  if d in M:continue
  M[d],p=I.load(d);pins.append(p)
 for p in read(H/'readback_01/manifest.json'):
  ck('fresh actual raw+JSON '+p['name'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);r=read(p['json']);m=Resource(r).normalize();ck('fresh indexed semantics '+p['depot'],I.canon(m)==I.canon(M[p['depot']]),'TDBID numeric identity, derived digests and tuple/list only');M[p['depot']]=m;raw[p['depot']]=r;pins.append(p)
 def find(s):return next(d for d in M if d.endswith('\\'+s))
 def n(d,i,g='root'):return M[d]['graphs'][g]['nodes'][str(i)]
 def ed(d,a,s,b,t,g='root'):return [str(a),s,str(b),t]in M[d]['graphs'][g]['edges']
 def wf(d,i,f,v,g='root'):return any(x.get('factName')==f and x['value']==v for x in n(d,i,g)['writes'])
 def rf(d,i,f,g='root'):return any(x.get('factName')==f for x in n(d,i,g)['reads'])
 def ext(x):
  x=copy.deepcopy(x)
  for z in walk(x):
   if isinstance(z.get('phaseResource'),dict):z['phaseResource']['Flags']='Soft'
   if z.get('$type')=='questQuestPhaseResource'and z.get('cookingPlatform')=='PLATFORM_None':z['cookingPlatform']='PLATFORM_PC'
  return x
 def path(g,a,b):
  todo=[(str(a),[])];seen=set()
  while todo:
   k,p=todo.pop(0)
   if k==str(b):return p
   if k in seen:continue
   seen.add(k)
   for e in g['edges']:
    cut=g['nodes'].get(e[0],{}).get('type')=='scnCutControlNode'and e[1].startswith('1:')
    if e[0]==k and e[1]!='CutSource'and e[3]!='CutDestination'and not cut:todo.append((e[2],p+[e]))
  return None
 ep=I.F/'source_epoch_05.json';ck('canonical epoch05 pin',sha(ep)=='EFFD80F3A4413A0AAF0127DCC215ED4E3850262FA1388358996A15994C1CCE0D',str(ep));pins.append({'path':str(ep),'sha256':sha(ep)})
 ap=I.F/'approved_changes_03.json';approved=read(ap);spyrow=next(x for x in approved['resources']if x['depot'].endswith('sts_ep1_08_entry.questphase'));ck('Spy approved current byte delta',I.E['source_resources'][spyrow['depot']]==spyrow['after']=='5D1FE58F41739C231B5006FF134EB78207FC879B9AB8652FADE69899242C2F62',spyrow);pins.append({'path':str(ap),'sha256':sha(ap)})
 sr=Path(spyrow['independent_serialized_review']);ck('independent old-Spy preservation and future-helper proof',sha(sr)==spyrow['independent_serialized_review_sha256']and read(sr)['checks']==140 and read(sr)['mutations']==5,str(sr));pins.append({'path':str(sr),'sha256':sha(sr)})
 # Every original recipe node and nested graph; current Spy is explicitly a successor.
 for r in I.SEL['recipes']:
  d=r['depot'];don='recipe:'+r['raw'];gp=r.get('compiled_graph','root');src=r['graph']
  for i in r['ids']:
   if i==0:continue
   ck('original recipe payload '+d+'/'+str(i),I.canon(n(d,i,gp)['payload'])==I.canon(ext(n(don,i,src)['payload'])),{'source':don,'graph':src,'node':i})
   pref=gp+'/'+str(i)
   for child,g in M[d]['graphs'].items():
    if child==pref or child.startswith(pref+'/'):ck('exact original nested entry '+d+child,I.canon(g)==I.canon(M[don]['graphs'][src+'/'+str(i)+child[len(pref):]]),len(g['nodes']))
  expected=[[str(a),s,str(b),t]for a,s,b,t in r['edges']]
  if r['id']=='sts_ep1_08'and r['kind']=='entry':
   expected=[e for e in expected if e not in [['65003','Out','10','In1'],['65003','Out','64001','In1']]]+[['65003','Out','1300','In'],['1300','True','1301','In'],['1301','Out','1302','In1'],['1301','Out','10','In1'],['1301','Out','64001','In1'],['1300','False','10','In1'],['1300','False','64001','In1']]
   ck('Spy actor-only four-node helper preserved',set(M[d]['graphs']['root/50/1302']['nodes'])=={'0','17','19','1303'},'explicit approved addition, no old whole-body equality claim')
  ck('actual recipe edge multiset '+d,M[d]['graphs'][gp]['edges']==sorted(expected),{'kind':r['kind'],'graph':gp,'approved_Spy_delta':r['id']=='sts_ep1_08'and r['kind']=='entry'})
  if r['kind']=='entry':
   ck('actual original body target '+r['id'],r['native']in M and r['native']not in I.E['source_resources'],r['native'])
   for c in r['companions']:ck('actual original companion '+r['id']+'/'+c['kind'],c['depot']in M and c['depot']not in I.E['source_resources'],c)
 # Current admission script exact data; omitted journal writes remain specific evidence.
 rel='r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds';script=I.C/'package'/rel;expected=next(p['sha256']for p in I.E['package_files']if p['path']==rel);ck('current U9 source code pin',sha(script)==expected,str(script));pins.append({'path':str(script),'sha256':sha(script)});text=script.read_text();cl=text[text.index('class NativeGigDataU9'):];line=next(x for x in cl.splitlines()if'func IDs()'in x);ids=json.loads(line[line.index('['):line.rindex(']')+1])
 def array(m,i):
  z=cl[cl.index('public static func '+m+'('):];z=z[:z.index('\n  public static func',1)];l=next(x for x in z.splitlines()if'if i=='+str(i)+' 'in x);return json.loads(l[l.index('['):l.rindex(']')+1])
 admissions={};inventory={}
 for q in I.Q:
  r=next(r for r in I.SEL['recipes']if r['id']==q and r['kind']=='entry');d=r['depot'];gp=r['compiled_graph'];guards=n(d,65002,gp)['reads'];facts={x['factName']:x['value']for x in guards if'factName'in x};ix=ids.index(q);data={k:array(k,ix)for k in ['Paths','Classes','Facts','TerminalFacts']};rows=[];writers={};journals={}
  for dep,m in M.items():
   if not dep.startswith('ep1\\openworld\\street_stories')or q not in dep:continue
   for ng,g in m['graphs'].items():
    for ni,nn in g['nodes'].items():
     row={'depot':dep,'graph':ng,'node':ni,'type':nn['type'],'payload_sha256':nn['payload_sha256'],'reads':nn['reads'],'writes':nn['writes'],'journal_paths':nn['journal_paths'],'refs':nn['refs'],'prefabs':nn['prefabs'],'node_refs':nn['node_refs'],'in':[e for e in g['edges']if e[2]==ni],'out':[e for e in g['edges']if e[0]==ni]};rows.append(row)
     for w in nn['writes']:
      if w['factName'].startswith(q+'_'):writers.setdefault(w['factName'],[]).append(row)
     for x in walk(nn['payload']):
      if x.get('$type')=='gameJournalPath'and x.get('realPath','').startswith('ep1/quests/'):
       journals.setdefault(x['realPath'],[]).append({'depot':dep,'graph':ng,'node':ni,'class':x['className']['$value'],'in':row['in']})
  missing={f:rr for f,rr in writers.items()if f not in data['Facts']};omitted={p:rr for p,rr in journals.items()if p not in data['Paths']}
  expected_omissions={'sts_ep1_10':{'sts_ep1_10_cleanup_done'},'sts_ep1_08':{'sts_ep1_08_cleanup_done','sts_ep1_08_cleanup_executed','sts_ep1_08_cleanup_organitopia_done','sts_ep1_08_agents_room_cleanup_done'},'sts_ep1_13':{'sts_ep1_13_done','sts_ep1_13_cleanup_done','sts_ep1_13_hands_knows_about_kids'}}
  ck('exact uncovered native cleanup/debrief history inventory '+q,set(missing)==expected_omissions[q],{'unlisted_writers':missing,'omitted_journal_paths':list(omitted),'disposition':'Explicit uncovered history fields, NOT claimed complete fact coverage or automatically an admission defect. Native start/journal/private-owner routes and arbitrary old-state compatibility stay CONDITIONAL.'})
  for f in ['q307_done','q307_finished','q307_2079','PTFRU9_Support_Issued','PTFRU9_'+q+'_Request','PTFRU9_'+q+'_Permit']:ck('positive native/private provenance '+q+'/'+f,facts.get(f)==1,guards)
  ck('guard ParentEntered and native progress unused '+q,facts.get('PTFRU9_'+q+'_ParentEntered')==0 and facts.get(q+'_start')==0 and facts.get(q+'_finished')==0,'current pointer/receipt does not reset actual history')
  admissions[q]={'index':ix,**data,'guard':n(d,65002,gp)['payload']['condition'],'native_writers':writers,'omitted_native_facts':missing,'omitted_journals':omitted};inventory[q]=rows
 ck('actual EntrySafe settled boundary',all(x in text for x in ['if this.State(paths[k],classes[k])!=1','if this.Fact(a[k])!=0','return poi==1 || poi==2;']),'journal existence/all-Inactive and zero listed progress; native POI can be Active')
 # All request families in own scopes, exact native listeners/real ACKs. Local auction requests are not holocalls.
 contacts={'mr_hands':'base','mark_bana':'ep1','janet':'ep1'};phones=[];special=[];pat=re.compile(r'^(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate$')
 for q,rows in inventory.items():
  for row in rows:
   for w in row['writes']:
    if w['value']<=0:continue
    ma=pat.fullmatch(w['factName'])
    if ma:
     mode,inc,out,kind=ma.groups();c=inc or out;ck('known exact contact '+w['factName'],c in contacts,row);base=contacts[c]+'\\quest\\holocalls\\'+c+'\\'+c+'_';hc=base+'holocall.questphase';hs=base+'holocall.scene';done='holo_'+(c+'_calls_v'if inc else'v_calls_'+c)+'_'+kind+'_done';ls=[i for g in M[hc]['graphs'].values()for i,nn in g['nodes'].items()if any(x.get('factName')==w['factName']for x in nn['reads'])];acks=[i for i,nn in M[hs]['graphs']['scene']['nodes'].items()if any(x.get('factName')==done and x['value']==1 for x in nn['writes'])];ck('actual producer listener and native ACK '+row['depot']+row['graph']+'/'+row['node'],bool(ls)and bool(acks),{'request':w,'listeners':ls,'ACK':done,'writers':acks});phones.append(row|{'request':w['factName'],'mode':mode,'contact':c,'direction':'incoming'if inc else'outgoing','listeners':ls,'ACK_writers':acks})
    elif re.search(r'call|phone|holo|audio|sms|request|new_sts|new_q110',w['factName'],re.I):special.append(row|{'candidate':w})
 ck('no unowned custom new_sts or new_q110 producer in scoped native gigs',not any(x['candidate']['factName'].startswith(('new_sts','new_q110'))for x in special),'enumerated all own positive writes; auction and local presentation facts classified separately')
 # Executing-owner evidence and cleanup, including Ana's internal Janet alias.
 init=r'towercontinued\gig_phone_u9\fixer_initializer.questphase';clean=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';studio=r'towercontinued\phone_studios_ph3\studio_support.questphase'
 ck('MrHands actual current initializer73',ed(init,25,'Out1',73,'In1')and n(init,73)['refs']==[r'base\quest\holocalls\mr_hands\mr_hands_holocall.questphase'],'file presence is not owner proof')
 ck('MrHands actual cleanup329',ed(clean,462,'True',329,'In36'),'native cleanup is connected in effective shared reset chain')
 xl=I.C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl';xp=next(x['sha256']for x in I.E['package_files']if x['path']=='archive/pc/mod/zzzz_PTFR_Combined.archive.xl');ck('current packaged XL source pin',sha(xl)==xp,str(xl));pins.append({'path':str(xl),'sha256':sha(xl)});xs=xl.read_text()
 for c,wrapper in [('mark_bana',r'towercontinued\phone_merge_ph2\mark_bana_listener.questphase'),('janet',r'towercontinued\phone_support_ph1\janet.questphase')]:
  ck('current XL exactly one registered owner '+c,xs.count('path: '+wrapper)==1 and re.search(r'path: '+re.escape(wrapper)+r'\s+parent: ep1\\quest\\ep1.quest\s+input:\s+node: \[1\]\s+socket: Out',xs)is not None,wrapper)
  ck('whole real native listener ownership '+c,n(wrapper,10)['refs']==['ep1\\quest\\holocalls\\'+c+'\\'+c+'_holocall.questphase']and ed(wrapper,4,'Out',10,'In1')and wf(wrapper,4,'PTFRPH1_'+c+'_Issued',1),'native full controller retained, not fake done facts')
 ck('obsolete PH1Mark not registered','path: towercontinued\\phone_support_ph1\\mark_bana.questphase'not in xs,'old raw exists, PH2 is sole active registration')
 master=r'ep1\quest\holocalls\holocall_cleanup_ep1.questphase'
 for current,nativegraph in [('root/1402','root/81'),('root/1405','root/79')]:
  ck('recursive original EP1 master cleanup exact '+current,I.canon(M[clean]['graphs'][current])==I.canon(M[master]['graphs'][nativegraph]),{'depot':master,'graph':nativegraph,'note':'Actual donor is the original global inline cleanup. Standalone per-contact cleanup differs (In9/Out9 and reset-counter prefix); do not infer a missing reset by comparing the wrong donor.'})
 ck('Mark+Janet cleanup chain connected',ed(clean,1400,'True',1401,'In')and ed(clean,1401,'True',1402,'In1')and ed(clean,1402,'Out1',1403,'In')and ed(clean,1403,'True',1404,'In')and ed(clean,1404,'True',1405,'In1'),'actual issued/count predicates and native end scene calls')
 ck('PH3 native shared PIPs retained in phase3',n(studio,3)['prefabs']==['$/03_night_city/c_pacifica/#holocalls_studio_ep1','$/03_night_city/ne2/#holocalls_studio']and not M[studio]['root_prefabs'],'node scope retained; empty resource root list does not remove studio duty')
 # Actual source-specific progression and completion (all nodes/edges preserved from pinned native).
 spy=find('sts_ep1_08_phase.questphase');target=find('sts_ep1_08_target_meeting.scene');dod=find('sts_ep1_10_openworld.questphase');tal=find('sts_ep1_13_openworld.questphase');tc=find('sts_ep1_13_cleanup.questphase');fiona=find('sts_ep1_13_fiona.scene');auction=find('sts_ep1_13_v_auction.scene')
 for ee in [(139,'Out',153,'In'),(153,'Out',67,'Bana intro'),(67,'phone end 01',380,'In'),(380,'Out',309,'Succeeded'),(309,'Out',281,'Active'),(281,'Out',209,'In'),(209,'Out',211,'In'),(211,'Out',146,'In'),(146,'Out',143,'In'),(143,'Out',21,'Succeeded')]:ck('Spy actual panelâ†’real callâ†’door '+str(ee),ed(spy,*ee),ee)
 ck('Spy native personal-link device condition',n(spy,139)['payload']['condition']['type']['deviceConditionFunction']['$value']=='IsPersonalLinkConnected','same source panel, not fabricated Authorization fact')
 ck('Spy native authorize/open actions',all(n(spy,i)['payload']['type']['params'][0]['deviceAction']['$value']==s for i,s in [(211,'AuthorizationDisable'),(146,'ForceOpen'),(143,'ForceOpen')]),'only reachable after real native phone end route')
 for ni,done in [(1560,'holo_mark_bana_calls_v_start_done'),(1768,'holo_mark_bana_calls_v_end_done'),(1598,'holo_janet_calls_v_start_done'),(1600,'holo_janet_calls_v_end_done')]:ck('Spy actual real call acknowledgment '+str(ni),rf(target,ni,done,'scene'),n(target,ni,'scene')['payload_sha256'])
 for ee in [(310,'True',103,'In'),(310,'False',100,'In'),(100,'Out',418,'In'),(103,'Out',418,'In'),(329,'Out',312,'In'),(312,'Out',314,'In')]:ck('Spy authored reward/outcome '+str(ee),ed(spy,*ee),ee)
 ck('Spy choice predicate preserved',rf(spy,310,'sts_ep1_08_biomonitor_destroyed')and wf(spy,81,'sts_ep1_08_biomonitor_destroyed',1,'root/46'),'two real reward records and future Steven choice fences stay separate')
 for ee in [(145,'Out',146,'In'),(78,'End 0',87,'In1'),(78,'not_rejectable_q303_end',87,'In2'),(87,'Out1',83,'In'),(77,'Out',83,'In'),(83,'Out',93,'In2'),(88,'Out',82,'In')]:ck('Dodger authored outcome/reward '+str(ee),ed(dod,*ee,'root/10'),ee)
 ck('Dodger defeated/killed/unconscious original interpretation',all(n(dod,145,'root/10')['payload']['condition']['type'][k]==1 for k in ['defeated','killed','unconscious'])and wf(dod,146,'sts_ep1_10_dodger_dead',1,'root/10'),'do not rename native broad outcome to literal-death-only')
 for ee in [(29,'True',5,'In'),(29,'False',30,'In'),(5,'Out',30,'In'),(30,'Out',51,'In'),(72,'Out',73,'In')]:ck('Talent failure/reward/cleanup '+str(ee),ed(tc,*ee),ee)
 ck('Talent failure excludes real reward',n(tc,29)['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'sts_ep1_13_failed','value':0}],'failed still native finished path, no reward5')
 ck('Talent genuine Fiona branches/data writers',wf(fiona,1315,'sts_ep1_13_fiona_deal_done',1,'scene')and wf(fiona,994,'sts_ep1_13_fiona_deal_refuse',1,'scene')and wf(tal,20,'sts_ep1_13_data_is_stolen',1,'root/3'),'native agreement/refusal/hack data branches retained')
 for fact,ws,rs in [('sts_ep1_13_auction_end_request',[788,795],[1321,1323,1781,2163,2174]),('sts_ep1_13_auction_speedup_request',[810],[1260,1670,1688,2133,2141,2189])]:ck('Talent local custom request has exact native consumers '+fact,all(wf(auction,i,fact,1,'scene')for i in ws)and all(rf(auction,i,fact,'scene')for i in rs),'local auction mechanism, not generic phone controller')
 # Meaningful faults in actual current/native raw resources.
 for label,d,change,oracle in [
 ('missing_Mark_ACK',r'ep1\quest\holocalls\mark_bana\mark_bana_holocall.scene',lambda r:[x.update(factName='QR5_missing_ack')for x in walk(r)if x.get('factName')=='holo_mark_bana_calls_v_start_done'],lambda m:any(x.get('factName')=='holo_mark_bana_calls_v_start_done'and x['value']==1 for x in m['graphs']['scene']['nodes']['36']['writes'])),
 ('missing_Ana_ACK',r'ep1\quest\holocalls\janet\janet_holocall.scene',lambda r:[x.update(factName='QR5_missing_ack')for x in walk(r)if x.get('factName')=='holo_janet_calls_v_start_done'],lambda m:any(x.get('factName')=='holo_janet_calls_v_start_done'and x['value']==1 for x in m['graphs']['scene']['nodes']['299']['writes'])),
 ('Spy_changed_authorization',spy,lambda r:[x.update({'$value':'QR5_wrong_action'})for x in walk(r)if x.get('$type')=='CName'and x.get('$value')=='AuthorizationDisable'],lambda m:m['graphs']['root']['nodes']['211']['payload']['type']['params'][0]['deviceAction']['$value']=='AuthorizationDisable'),
 ('Dodger_missing_native_outcome',dod,lambda r:[x.update(value=0)for x in walk(r)if x.get('factName')=='sts_ep1_10_dodger_dead'and x.get('$type')=='questSetVar_NodeType'],lambda m:any(x.get('factName')=='sts_ep1_10_dodger_dead'and x['value']==1 for x in m['graphs']['root/10']['nodes']['146']['writes'])),
 ('Talent_failed_reward_guard',tc,lambda r:[x.update(factName='QR5_missing_failure')for x in walk(r)if x.get('factName')=='sts_ep1_13_failed'],lambda m:m['graphs']['root']['nodes']['29']['reads'][0]['factName']=='sts_ep1_13_failed'),
 ('Talent_changed_deal_outcome',fiona,lambda r:[x.update(value=0)for x in walk(r)if x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='sts_ep1_13_fiona_deal_done'],lambda m:any(x.get('factName')=='sts_ep1_13_fiona_deal_done'and x['value']==1 for x in m['graphs']['scene']['nodes']['1315']['writes']))]:
  r=copy.deepcopy(raw[d]);change(r);mm=Resource(r).normalize();ck('actual raw fault '+label,oracle(M[d])and not oracle(mm),d);fp=O/'mutations'/str(label+'.json');write(fp,r);mut.append({'fault':label,'path':str(fp),'sha256':sha(fp),'detected':True})
 errors=[{'depot':d,'errors':m['errors']}for d,m in M.items()if m['errors']];write(O/'native_diagnostics.json',errors);write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'admission.json',admissions);write(O/'handler_inventory.json',inventory);write(O/'phone_inventory.json',{'producer_requests':phones,'nonstandard_phone_local_request_candidates':special,'all_positive_fact_census_scope':'All native per-gig body/scene inventory; not holo/audio filter only','contacts':contacts});write(O/'mutations.json',mut)
 write(O/'bindings.json',[{'depot':d,'root_prefabs':m['root_prefabs'],'actors':m['metadata'].get('actors',[]),'workspots':m['metadata'].get('workspots',[]),'refs':m['refs'],'node_prefabs':[{'graph':gp,'node':i,'prefabs':nn['prefabs']}for gp,g in m['graphs'].items()for i,nn in g['nodes'].items()if nn['prefabs']]}for d,m in M.items()if any(q in d for q in I.Q)])
 summary={'status':'PASS_SPECIFIC_STATIC_CHECKS_WITH_NATIVE_DIAGNOSTICS_AND_LIVE_LIMITS','checks':len(tests),'mutations':len(mut),'resources':len(M),'fresh_exports':18,'phone_request_sites':len(phones),'native_diagnostic_resources':len(errors),'quest_ids':I.Q,'source_epoch':str(ep),'source_epoch_sha256':sha(ep),'fully_static_verified':False,'runtime_changes':[],'code_sha256':sha(__file__)};write(O/'summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output).resolve())
