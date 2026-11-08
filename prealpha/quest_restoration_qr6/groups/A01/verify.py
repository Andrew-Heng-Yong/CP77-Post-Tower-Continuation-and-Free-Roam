"""Specific MQ040/MQ028/MQ018 contracts against fresh pinned original/current readbacks."""
from pathlib import Path
import sys,copy,re,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));from source_lib import *
IDS=['mq040_biosculpt','mq028_stalker','mq018_writer'];PREF='towercontinued\\sidejobs_s29\\native\\'
def semantic(m):
 return canon(dict(type=m['type'],root_prefabs=m['root_prefabs'],metadata=m['metadata'],graphs={gp:dict(edges=g['edges'],entries=g['entries'],nodes={i:{k:n[k]for k in ['payload','sockets']}for i,n in g['nodes'].items()})for gp,g in m['graphs'].items()}))
def reverse_private(x):
 if isinstance(x,dict):return{k:reverse_private(v)for k,v in x.items()}
 if isinstance(x,list):return[reverse_private(v)for v in x]
 return x[len(PREF):]if isinstance(x,str)and x.startswith(PREF)else x
def edge(m,a,s,b,t,g='root'):return[str(a),s,str(b),t]in m['graphs'][g]['edges']
def node(m,i,g='root'):return m['graphs'][g]['nodes'][str(i)]
def fact(m,i,f,v,g='root',comp=None):return any(r.get('factName')==f and r.get('value')==v and(comp is None or r.get('comparisonType')==comp)for r in node(m,i,g)['reads']+node(m,i,g)['writes'])
def run(O):
 assert not O.exists();tests=[];mutations=[];pins=read(H/'readback_01/manifest.json')+read(H/'extra_readback_01/manifest.json');M={};raw={};handler=[];specific={}
 def ck(k,v,e):
  tests.append(dict(name=k,status='PASS'if v else'FAIL',evidence=e));write(O/'tests.json',tests)
  if not v:raise AssertionError(k)
 for p in pins:
  ck('exact fresh binary/JSON '+p['depot'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);raw[p['depot']]=read(p['json']);M[p['depot']]=Resource(raw[p['depot']]).normalize()
 ck('canonical predecessor epoch08',sha(Q5/'source_epoch_08.json')=='B8BC8D6630F51E07125789FAB5A54D188EB45CE7044F35E2E6F09DE460B91D83',str(Q5/'source_epoch_08.json'))
 # Complete source comparisons: approved R4 event muting and exact old SR1 workspot replacement only.
 audit=read(W/'research/sidejobs_s29/presentation_audit_01.json');by_scene={x['depot']:x for x in audit['scenes']};comparisons=[]
 proofpath=W/'prealpha/sidejob_repair_sr1/candidate_02/visual_07/proof.json';proof=read(proofpath);sr=next(x for x in proof['additional']if'mq018'in x['depot'])
 for d,b in list(M.items()):
  if not d.startswith(PREF):continue
  orig=d[len(PREF):];a=copy.deepcopy(M[orig]);bb=reverse_private(copy.deepcopy(b));changes=[]
  if orig in by_scene:
   ad=by_scene[orig];performers=set(ad['performers']);meta=a['metadata'];owned=set(ad['owned_instances']);others=set(ad['other_instances']);instances={x['workspotInstanceId']['id']:x['dataId']['id']for x in meta['workspotInstances']};shared={instances[i]for i in owned}&{instances[i]for i in others}
   for old in sorted(shared):
    newid=max(x['dataId']['id']for x in meta['workspots'])+1;ws=copy.deepcopy(next(x for x in meta['workspots']if x['dataId']['id']==old));ws['dataId']['id']=newid;meta['workspots'].append(ws)
    for inst in meta['workspotInstances']:
     if inst['workspotInstanceId']['id']in owned and inst['dataId']['id']==old:inst['dataId']['id']=newid
    changes.append(dict(kind='approved_R4_shared_workspot_split',old=old,new=newid))
   for gp,g in a['graphs'].items():
    for i,n in g['nodes'].items():
     for x in walk(n['payload']):
      if x.get('$type')=='scnPlaySkAnimEvent'and x.get('performer',{}).get('id')in performers:
       ck('R4 exact Johnny event mute '+d+'/'+i+'/'+str(x['id']['id']),x['muteAnimEvents']in['0','STANDARD'],{'performers':sorted(performers),'source':str(W/'prealpha/sidejobs_s29/prepare_04.py')});x['muteAnimEvents']='STANDARD';changes.append({'node':i,'event':x['id']['id'],'kind':'approved_R4_mute'})
     if 'events'in n['payload']:
      removed=[x for x in n['payload']['events']if x.get('performerId',{}).get('id')in performers and x.get('$type')in['scneventsEquipItemToPerformer','scneventsUnequipItemFromPerformer','scneventsVFXEvent']];n['payload']['events']=[x for x in n['payload']['events']if x not in removed]
      changes.extend(dict(kind='approved_R4_equipment_or_VFX_removal',node=i,event=x['id']['id'])for x in removed)
   props={p['id']for p in ad['props']}
   if props:
    meta['props']=[x for x in meta['props']if x['propId']['id']not in props];pm={x['propId']['id']:i for i,x in enumerate(meta['props'])}
    for x in walk(a):
     if x.get('$type')=='scnPropId'and x['id']in pm:x['id']=pm[x['id']]
     if x.get('$type')=='scnPerformerId'and x['id']&255==2 and x['id']>>8 in pm:x['id']=(pm[x['id']>>8]<<8)|2
    changes.append(dict(kind='approved_R4_unused_Johnny_props_removed',ids=sorted(props)))
  if d==sr['depot']:
   ck('SR1 corrected donor preserved exact bytes',E['source_resources'][d]==sr['patched_sha256'],'visual07 proof '+sha(proofpath));meta=bb['metadata'];inst=[x for x in meta['workspotInstances']if x['workspotInstanceId']['id']==4292];ck('SR1 exact protein marker lease',len(inst)==1 and inst[0]['originMarker']['nodeRef']['$value']==sr['anchor']and inst[0]['playAtActorLocation']==0,inst);meta['workspotInstances']=[x for x in meta['workspotInstances']if x not in inst];ws=[x for x in meta['workspots']if x['dataId']['id']==4231323113];ck('SR1 dedicated muted workspot binding',len(ws)==1 and ws[0]['workspotResource']['DepotPath']['$value'].endswith('johnny__stand_ground_cigarette__idle__01.workspot'),ws);meta['workspots']=[x for x in meta['workspots']if x not in ws]
   for i in sr['nodes']:
    before=node(a,i,'scene')['payload']['questNode']['paramsV1'];after=node(bb,i,'scene')['payload']['questNode']['paramsV1'];ck('SR1 exact replacement fields '+str(i),before['workspotNode']['$value']==sr['anchor']and after['$type']=='scnUseSceneWorkspotParamsV1'and after['workspotInstanceId']['id']==4292 and after['workspotNode']['$value']=='0'and after['playAtActorLocation']==0,after);node(bb,i,'scene')['payload']['questNode']['paramsV1']=copy.deepcopy(before)
   changes.append({'kind':'approved_SR1_six_workspot_calls','nodes':sr['nodes'],'proof':str(proofpath),'proof_sha256':sha(proofpath)})
  if orig.endswith(r'mq040\mq040_biosculpt.questphase'):
   # Current fresh-only entry refuses active1; retain dormant historical resume branch, not a new endorsement.
   ck('MQ040 bounded historical routing additions',fact(bb,65000,'mq040_active',1,comp='Equal')and edge(bb,0,'Out',65000,'In')and edge(bb,65000,'True',4,'In1')and edge(bb,65000,'False',3,'In1'),'existing root65000, preserved, fresh entry active0')
   ck('MQ040 setup lease wait',fact(bb,64000,'elcoyote_barman_default_on',0,'root/3')and fact(bb,64000,'PTFRB0STPEPE_OwnerActive',0,'root/3')and edge(bb,11,'Out',64000,'In','root/3')and edge(bb,64000,'Out',2,'In','root/3'),'wait for service release without forcing it')
   for gp,i,old,new in [('root','65000',[['0','Out','3','In1']],[['0','Out','65000','In'],['65000','False','3','In1'],['65000','True','4','In1']]),('root/3','64000',[['11','Out','2','In']],[['11','Out','64000','In'],['64000','Out','2','In']])]:
    bb['graphs'][gp]['nodes'].pop(i);bb['graphs'][gp]['edges']=sorted([e for e in bb['graphs'][gp]['edges']if e not in new]+old)
   changes.append({'kind':'preserved_existing_Raymond_branch_and_lease_wait','limits':'No safe saved-owner handoff established; fresh entry still active0.'})
  aa=semantic(a);bbb=semantic(bb);ck('all native node payloads/edges/metadata outside exact adaptations '+d,aa==bbb,{'native':orig,'current':d,'adaptations':changes});comparisons.append(dict(vanilla=orig,current=d,all_remaining_semantics_equal=True,adaptations=changes))
 # Original parent slices and exact native eligibility/timers, not inferred from flat factsets.
 parent=r'base\quest\minor_quests\minorquests.questphase';plan={j['id']:j for j in PLANS[0]['jobs']}
 for q in IDS:
  d=f'towercontinued\\sidejobs_s29\\entries\\{q}.questphase';S=Store();em=S.load(d);M[d]=em;raw[d]=S.raw[d];pins+=S.pins;j=plan[q];g=j['parent']['graph'];p=M[parent]
  for i in j['parent']['ids']:
   aa=copy.deepcopy(node(p,i,g)['payload']);bb=reverse_private(copy.deepcopy(node(em,i)['payload']))
   if 'phaseResource'in aa:aa['phaseResource']['Flags']='Soft'
   ck('actual parent retained payload '+q+'/'+str(i),canon(aa)==canon(bb),{'native':parent,'graph':g,'node':i,'current':d})
  expected={tuple(map(str,e))for e in j['parent']['edges']};actual={tuple(e)for e in em['graphs']['root']['edges']};interior=[e for e in expected if e[0]!='0'and e[2]!=str(j['parent']['child'])];ck('actual retained prerequisite connections '+q,all(e in actual for e in interior),interior)
  guards=node(em,65003)['reads'];f={r['factName']:r['value']for r in guards if'factName'in r};ck('real Tower and no-repeat private receipts '+q,all(f.get(k)==v for k,v in {'q307_done':1,'q307_finished':1,'q307_2079':1,'PTFRS29_'+q+'_Issued':0,'PTFRS29_'+q+'_Permit':1}.items()),guards)
  ck('issued-before-original-admission and entered-before-body '+q,edge(em,65004,'True',65005,'In')and any(e[0]=='65006'and e[2]==str(j['parent']['child'])for e in em['graphs']['root']['edges']),em['graphs']['root']['edges'])
  own={d0:m for d0,m in M.items()if d0.startswith(PREF)and q[:5]in d0};rr=[dict(depot=d0,**r)for d0,m in own.items()for r in rows(m)];handler+=rr
  journals=[r for r in rr if r['journal_paths']];rewards=[r for r in rr if r['reward']];comms=[r for r in rr if r['sms']or any(re.search('Phone|Call|Message',x.get('$type',''))for x in walk(r['payload']))or any(re.search('holo_|audio_|sms',w['factName'])for w in r['writes'])]
  specific[q]=dict(entry=d,original_parent=j['parent'],guard=node(em,65003)['payload']['condition'],journal_guard=node(em,65004)['payload']['condition'],journal_nodes=journals,rewards=rewards,communications=comms,body_resources=sorted(own),root_prefabs={d0:m['root_prefabs']for d0,m in own.items()},errors={d0:m['errors']for d0,m in own.items()if m['errors']})
 ck('Raymond current active1 refusal preserved',fact(M[f'towercontinued\\sidejobs_s29\\entries\\mq040_biosculpt.questphase'],65003,'mq040_active',0,comp='Equal'),'mq040 active1 captured old state is not admitted')
 ck('Raymond original prerequisite Heroes and12gamehours',fact(M[parent],121,'sq018_done',1,comp='GreaterOrEqual')and node(M[parent],120)['payload']['condition']['type']['hours']==12,'native minorquests121→120→49')
 ck('BlueMoon exact earned predecessor pair',node(M[parent],77)['payload']['condition']['operation']=='AND'and fact(M[parent],77,'sq017_mq028_start',0,comp='Greater')and fact(M[parent],77,'sq017_us_cracks_no_deal',1,comp='NotEqual'),'no blanket Kerry restoration')
 ck('BlueMoon original two-game-day delay',node(M[parent],111)['payload']['condition']['type']['days']==2,'77→111→104→41; preserve native units')
 # Current phone owners, exact real callbacks, cleanup and registered shared studios.
 contacts={'mq040_biosculpt':['cynthia','pepe'],'mq028_stalker':['blue_moon'],'mq018_writer':['nancy']};phone=[];clean=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';cg=M[clean]['graphs']['root'];xl=C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl';xt=xl.read_text(encoding='utf-8-sig');pins.append({'path':str(xl),'sha256':sha(xl)})
 for q,cc in contacts.items():
  for c in cc:
   od=f'towercontinued\\sidejobs_s29\\phone\\{c}.questphase';oc=M[od];hc=f'base\\quest\\holocalls\\{c}\\{c}_holocall.questphase';hs=hc.replace('.questphase','.scene');cl=hc.replace('_holocall.questphase','_cleanup.questphase');child=next(n for n in oc['graphs']['root']['nodes'].values()if hc in n['refs']);ck('actual registered contact owner '+c,od in xt and edge(oc,1004,'Out',child['id'],'In1')and fact(oc,1004,f'PTFRS29_PHONE_{c}_Issued',1),{'owner':od,'native_child':child['id'],'target':hc})
   cleanup=[r for r in rows(M[clean])if cl in r['refs']];gate=[r for r in rows(M[clean])if any(x.get('factName')==f'PTFRS29_PHONE_{c}_Issued'for x in r['reads'])];ck('actual cleanup native binding plus claim gate '+c,len(cleanup)==1 and len(gate)==1 and bool(cleanup[0]['incoming'])and bool(cleanup[0]['outgoing']),{'cleanup':cleanup,'gate':gate})
   for r in handler:
    if r['depot']not in specific[q]['body_resources']:continue
    for w in r['writes']:
     req=w['factName'];ma=re.fullmatch(r'(audio|holo)_(.+)_(start|end)_activate',req)
     if not ma or w['value']<=0 or c not in req:continue
     listeners=[dict(graph=z['graph'],node=z['node'])for z in rows(M[hc])if any(x.get('factName')==req for x in z['reads'])];done='holo_'+ma.group(2)+'_'+ma.group(3)+'_done';acks=[dict(graph=z['graph'],node=z['node'])for z in rows(M[hs])if any(x['factName']==done and x['value']==1 for x in z['writes'])];ck('real listener+scene ACK '+r['depot']+'/'+r['graph']+'/'+r['node']+'/'+req,bool(listeners)and bool(acks),{'request':req,'listeners':listeners,'ack_fact':done,'real_writers':acks});phone.append({'quest':q,'producer':{k:r[k]for k in ['depot','graph','node','incoming','outgoing']},'request':req,'listeners':listeners,'ack_fact':done,'ack_writers':acks})
 ck('PH3 actual registered studio owner',r'towercontinued\phone_studios_ph3\studio_support.questphase'in xt and len(M[r'towercontinued\phone_studios_ph3\studio_support.questphase']['graphs']['root']['nodes'])>0,'registered plus exact root/ancestor PIPs recorded')
 # Distinct native retirement writers must never collapse into a fact-only liveness proof.
 base=r'base\quest\cyberpunk2077.questphase';q307=r'ep1\quest\main_quests\q307\q307.quest'
 ck('native base writer before real terminating output',fact(M[base],109,'q307_main_game_killed',1)and edge(M[base],106,'Out',109,'In')and edge(M[base],109,'Out',107,'In')and node(M[base],107)['payload']['type']=='Terminating','source path includes MQ040; write precedes termination')
 ck('native MQ040 parent chain belongs to base82/6',r'base\quest\minor_quests\minorquests.questphase'in node(M[base],6,'root/82')['refs']and plan['mq040_biosculpt']['native']in node(M[parent],49)['refs'],'saved owner may be under distinct tree')
 ck('alternate same-fact writer cuts different infrastructure',fact(M[q307],18,'q307_main_game_killed',1)and edge(M[q307],18,'Out',17,'In')and edge(M[q307],17,'CutSource',6,'CutDestination')and not any('minorquests' in r for r in node(M[q307],6)['refs']),'q30718→17cut6 does not establish base owner acknowledgement')
 # Raw-document mutations: source-specific prerequisite, graph and real callback faults.
 def mutate_raw(d,fn,test,label):
  o=copy.deepcopy(raw[d]);fn(o);mm=Resource(o).normalize();caught=not test(mm);ck('actual raw mutation detected '+label,caught,{'depot':d,'kind':'JSON document mutation before normalized comparison; not binary/game execution'});mutations.append({'depot':d,'fault':label,'detected':caught})
 ep=f'towercontinued\\sidejobs_s29\\entries\\mq028_stalker.questphase'
 mutate_raw(ep,lambda o:next(x for x in walk(o)if x.get('$type')=='questVarComparison_ConditionType'and x.get('factName')=='sq017_us_cracks_no_deal').update(value=0),lambda m:fact(m,77,'sq017_us_cracks_no_deal',1,comp='NotEqual'),'BlueMoon changed predecessor no-deal predicate')
 nd=PREF+r'base\quest\minor_quests\mq018\mq018.questphase'
 mutate_raw(nd,lambda o:next(x for x in walk(o)if x.get('$type')=='questOutputNodeDefinition'and x.get('type')=='Terminating').update(type='NonTerminating'),lambda m:semantic(m)==semantic(M[nd]),'Nancy native termination changed')
 pd=r'base\quest\holocalls\blue_moon\blue_moon_holocall.scene';ack=next(w['factName']for r in rows(M[pd])for w in r['writes']if w['value']==1 and w['factName'].endswith('_start_done'))
 mutate_raw(pd,lambda o:[x.update(value=0)for x in walk(o)if x.get('$type')=='questSetVar_NodeType'and x.get('factName')==ack],lambda m:any(w['factName']==ack and w['value']==1 for r in rows(m)for w in r['writes']),'BlueMoon all real writers of one ACK removed')
 write(O/'comparisons.json',comparisons);write(O/'quest_evidence.json',specific);write(O/'phone_protocols.json',phone);write(O/'handler_inventory.json',handler);write(O/'source_pins.json',pins);write(O/'models.json',M);write(O/'mutations.json',mutations);write(O/'summary.json',dict(checks=len(tests),mutations=len(mutations),quests=IDS,fresh_exports=70,pinned_inputs=len(pins),phone_producers=len(phone),handler_rows=len(handler),source_epoch=str(Q5/'source_epoch_08.json'),source_epoch_sha256=sha(Q5/'source_epoch_08.json'),runtime_changes=0));print(read(O/'summary.json'))
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output))
