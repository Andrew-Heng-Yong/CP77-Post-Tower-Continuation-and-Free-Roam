"""MQ017, Stout followup and MQ036 against pinned original resources, actual selected inputs."""
from pathlib import Path
import sys,copy,re,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'A01'));from source_lib import *
from verify import semantic,edge,node,fact
PREF='towercontinued\\sidejobs_s29\\native\\';IDS=['mq017_streetkid','q003_stout','mq036_overload']
def reverse(x):
 if isinstance(x,dict):return{k:reverse(v)for k,v in x.items()}
 if isinstance(x,list):return[reverse(v)for v in x]
 return x[len(PREF):]if isinstance(x,str)and x.startswith(PREF)else x
def reached(g,start):
 todo=[str(start)];seen=set()
 while todo:
  i=todo.pop()
  if i in seen:continue
  seen.add(i)
  todo+=[e[2]for e in g['edges']if e[0]==i and e[1]!='CutSource'and e[3]!='CutDestination'and not(g['nodes'][i]['type']=='scnCutControlNode'and e[1].startswith('1:'))]
 return seen
def run(O):
 assert not O.exists();extra=read(H/'finalcorp_readback_01/manifest.json');pins=read(H/'readback_01/manifest.json')+(extra if isinstance(extra,list)else[extra]);M={};raw={};tests=[];mutations=[];comparisons=[];ev={}
 def ck(k,v,e):
  tests.append(dict(name=k,status='PASS'if v else'FAIL',evidence=e));write(O/'tests.json',tests)
  if not v:raise AssertionError(k)
 for p in pins:
  ck('actual fresh raw+JSON '+p['depot'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);raw[p['depot']]=read(p['json']);M[p['depot']]=Resource(raw[p['depot']]).normalize()
 audit={x['depot']:x for x in read(W/'research/sidejobs_s29/presentation_audit_01.json')['scenes']};srpath=W/'prealpha/sidejob_repair_sr1/candidate_02/visual_03/proof.json';sr=read(srpath)['sweet_dreams'];jobs={j['id']:j for j in PLANS[0]['jobs']}
 for d in [d for d in M if d.startswith(PREF)]:
  orig=d[len(PREF):];a=copy.deepcopy(M[orig]);b=reverse(copy.deepcopy(M[d]));changes=[]
  if orig in audit:
   ad=audit[orig];per=set(ad['performers']);meta=a['metadata'];owned=set(ad['owned_instances']);other=set(ad['other_instances']);inst={x['workspotInstanceId']['id']:x['dataId']['id']for x in meta['workspotInstances']};shared={inst[i]for i in owned}&{inst[i]for i in other}
   for old in sorted(shared):
    ni=max(x['dataId']['id']for x in meta['workspots'])+1;ws=copy.deepcopy(next(x for x in meta['workspots']if x['dataId']['id']==old));ws['dataId']['id']=ni;meta['workspots'].append(ws)
    for x in meta['workspotInstances']:
     if x['workspotInstanceId']['id']in owned and x['dataId']['id']==old:x['dataId']['id']=ni
    changes.append(dict(kind='R4shared_workspot_split',old=old,new=ni))
   for gp,g in a['graphs'].items():
    for i,n in g['nodes'].items():
     for x in walk(n['payload']):
      if x.get('$type')=='scnPlaySkAnimEvent'and x.get('performer',{}).get('id')in per:x['muteAnimEvents']='STANDARD';changes.append(dict(kind='R4mute',node=i,event=x['id']['id']))
     if'events'in n['payload']:
      rr=[x for x in n['payload']['events']if x.get('performerId',{}).get('id')in per and x.get('$type')in['scneventsEquipItemToPerformer','scneventsUnequipItemFromPerformer','scneventsVFXEvent']];n['payload']['events']=[x for x in n['payload']['events']if x not in rr];changes.extend(dict(kind='R4equipment/VFX',node=i,event=x['id']['id'])for x in rr)
   props={p['id']for p in ad['props']}
   if props:
    meta['props']=[x for x in meta['props']if x['propId']['id']not in props];mp={x['propId']['id']:i for i,x in enumerate(meta['props'])}
    for x in walk(a):
     if x.get('$type')=='scnPropId'and x['id']in mp:x['id']=mp[x['id']]
     if x.get('$type')=='scnPerformerId'and x['id']&255==2 and x['id']>>8 in mp:x['id']=(mp[x['id']>>8]<<8)|2
    changes.append(dict(kind='R4unused_Johnny_props',ids=sorted(props)))
  if d==sr['depot']:
   ck('SweetDreams exact SR1 corrected serialized donor',E['source_resources'][d]==sr['patched_sha256'],sr);mi=b['metadata'];ins=[x for x in mi['workspotInstances']if x['workspotInstanceId']['id']==3131];ck('SweetDreams exact dedicated exit instance',len(ins)==1 and ins[0]['originMarker']['nodeRef']['$value']=='#mq036_ws_johnny_exit'and ins[0]['playAtActorLocation']==0,ins);mi['workspotInstances']=[x for x in mi['workspotInstances']if x not in ins]
   for i in [158,1073]:
    bef=node(a,i,'scene')['payload']['questNode']['paramsV1'];aft=node(b,i,'scene')['payload']['questNode']['paramsV1'];ck('SweetDreams precise original workspot fields '+str(i),bef['workspotNode']['$value']=='#mq036_ws_johnny_exit'and aft['$type']=='scnUseSceneWorkspotParamsV1'and aft['workspotInstanceId']['id']==3131 and aft['workspotNode']['$value']=='0'and all(aft[k]==v for k,v in bef.items()if k not in['$type','workspotNode']),aft);node(b,i,'scene')['payload']['questNode']['paramsV1']=copy.deepcopy(bef)
   changes.append(dict(kind='SR1exit_workspot_adapter',nodes=[158,1073],instance=3131))
  if orig.endswith(r'phases\q003_stout.questphase'):
   j=jobs['q003_stout'];g=b['graphs']['root'];og=a['graphs']['root'];ck('Stout exact original58node followup slice',set(g['nodes'])==set(map(str,j['subset']))|{'65000'},'no prologue replay, one private input65000')
   for i in j['subset']:ck('Stout original selected node '+str(i),g['nodes'][str(i)]['payload']==og['nodes'][str(i)]['payload']and g['nodes'][str(i)]['sockets']==og['nodes'][str(i)]['sockets'],dict(original=orig,graph='root',node=i))
   expected=sorted([[str(a),s,str(b),t]for a,s,b,t in j['selected_edges']]+[['65000','Out','146','In']]);ck('Stout exact connected followup edge slice',g['edges']==expected,expected);ck('Stout all original root support obligations',a['root_prefabs']==b['root_prefabs']==['#q003_pr_stout','#q003_pr_follow_up']and a['metadata']==b['metadata'],'full metadata copied; support streaming/lifecycle remains conditional');changes.append('Exact selected58native followup nodes, retained root metadata and private65000→146')
  else:
   if semantic(a)!=semantic(b):
    from fresh_compare import leaves
    write(O/'differences.json',leaves(semantic(a),semantic(b)))
   ck('all native semantics outside exact presentation adaptations '+d,semantic(a)==semantic(b),dict(native=orig,current=d,changes=changes))
  comparisons.append(dict(native=orig,current=d,changes=changes,source_comparison=True))
 parent=r'base\quest\minor_quests\minorquests.questphase';entries={q:f'towercontinued\\sidejobs_s29\\entries\\{q}'+('_entry'if q=='q003_stout'else'')+'.questphase'for q in IDS}
 for q,d in entries.items():
  m=M[d];g=m['graphs']['root'];ck('actual atomic guard equality '+q,node(m,65003)['payload']['condition']==node(m,65004)['payload']['condition'],'same fact/journal predicate tree before claim')
  ck('actual once claim before native body '+q,fact(m,65005,'PTFRS29_'+q+'_Issued',1)and edge(m,65004,'True',65005,'In')and fact(m,65006,'PTFRS29_'+q+'_Entered',1),'no arbitrary reset/native start fact used as substitute')
  if q!='q003_stout':
   j=jobs[q]
   for i in j['parent']['ids']:
    old=copy.deepcopy(node(M[parent],i)['payload']);new=reverse(node(m,i)['payload'])
    if'phaseResource'in old:old['phaseResource']['Flags']='Soft'
    ck('actual native parent payload '+q+'/'+str(i),old==new,{'depot':parent,'node':i})
  own={d0:z for d0,z in M.items()if d0.startswith(PREF)and(q[:5]in d0 if q!='q003_stout'else'\\q003\\'in d0)};rr=[dict(depot=d0,**r)for d0,z in own.items()for r in rows(z)];ev[q]=dict(entry=d,guard=node(m,65003)['payload']['condition'],resources=list(own),handler_rows=rr,communications=[r for r in rr if r['sms']or any(re.search('Phone|Call|Message',x.get('$type',''))for x in walk(r['payload']))or any(re.search('^(holo|audio)_',w['factName'])for w in r['writes'])],journal=[r for r in rr if r['journal_paths']],rewards_inventory=[r for r in rr if r['reward']or 'ItemManager'in r['type']],prefab_scopes={d0:z['root_prefabs']for d0,z in own.items()})
 lifeid=canon({'$type':'TweakDBID','$storage':'string','$value':'LifePaths.StreetKid'})['$value']
 def streetlife(m):return any(x.get('$type')=='LifePath_ScriptConditionType'and canon(x['lifePathId'])['$value']==lifeid for x in walk(node(m,9)['payload']))
 street=PREF+r'base\quest\minor_quests\mq017\mq017_streetkid.questphase';ck('StreetKid exact lifepath and earned Heroes gate',streetlife(M[street])and fact(M[street],28,'sq018_done',1,comp='GreaterOrEqual')and edge(M[street],31,'True',28,'In'),'native normal vsstandalone routes remain exact; typed string/numeric identity canonicalized')
 sweet=PREF+r'base\quest\minor_quests\mq036\mq036_overload.questphase';ck('SweetDreams earned SQ012 market prerequisite retained',fact(M[sweet],11,'sq012_market_done',0,comp='Greater')and edge(M[sweet],0,'Out',11,'In')and edge(M[sweet],11,'Out',2,'In1'),'do not start excluded SQ012 or fabricate prior market history')
 se=M[entries['q003_stout']];ck('Stout genuine won-history and q101 prerequisite',any(x.get('factName')=='q003_meredith_won'and x.get('comparisonType')=='GreaterOrEqual'and x.get('value')==1 for x in node(se,65003)['reads'])and any(x.get('factName')=='q101_done'and x.get('value')==1 for x in node(se,65003)['reads']),'positive earned prerequisites, no blanket relationship restoration')
 stout=PREF+r'base\quest\main_quests\prologue\q003\phases\q003_stout.questphase';sc=PREF+r'base\quest\main_quests\prologue\q003\scenes\q003_07a_final_corp.scene';sg=M[sc]['graphs']['scene'];reach=reached(sg,sg['entries']['q003_07a_stout_sex_end_in']);active=[dict(node=i,writes=n['writes'])for i,n in sg['nodes'].items()if i in reach and any(w['value']>0 and re.fullmatch(r'(holo|audio)_.+_activate',w['factName'])for w in n['writes'])];ck('Stout actual farewell2197 has no reachable Meredith request3300',sg['entries']['q003_07a_stout_sex_end_in']=='2197'and'3300'not in reach and not active,{'caller':stout,'node':111,'input':'q003_07a_stout_sex_end_in','entry':2197,'inactive_request':3300,'request_payload':sg['nodes']['3300']['writes'],'reachable_nodes':sorted(reach)})
 ck('Stout subset native body has no Out1 output receipt',not any(n['type']=='questOutputNodeDefinition'for n in M[stout]['graphs']['root']['nodes'].values())and edge(se,64000,'Out1',65007,'In'),'wrapperFinished cannot be assumed; Issued and real native history remain one-time guards, do not fake child output')
 # Kirk's actual executing listener and exact real callback path; Meredith inactive branch is context-only.
 phone=[];hc=r'base\quest\holocalls\kirk\kirk_holocall.questphase';hs=hc.replace('.questphase','.scene');own=r'towercontinued\sidejobs_s29\phone\kirk.questphase';cl=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';xl=C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl';text=xl.read_text();pins.append(dict(path=str(xl),sha256=sha(xl)))
 for r in ev['mq017_streetkid']['handler_rows']:
  for w in r['writes']:
   ma=re.fullmatch(r'(holo|audio)_(.+)_(start|end)_activate',w['factName'])
   if not ma or w['value']<=0:continue
   req=w['factName'];ack='holo_'+ma.group(2)+'_'+ma.group(3)+'_done';listeners=[dict(graph=z['graph'],node=z['node'])for z in rows(M[hc])if any(x.get('factName')==req for x in z['reads'])];writers=[dict(graph=z['graph'],node=z['node'])for z in rows(M[hs])if any(x['factName']==ack and x['value']==1 for x in z['writes'])];ck('Kirk native request listener real ACK '+r['graph']+'/'+r['node'],bool(listeners)and bool(writers),{'request':req,'listeners':listeners,'ack':ack,'writers':writers});phone.append(dict(producer={k:r[k]for k in['depot','graph','node','incoming','outgoing']},request=req,listeners=listeners,ack=ack,writers=writers))
 child=next(n for n in M[own]['graphs']['root']['nodes'].values()if hc in n['refs']);ck('Kirk current registered claim/controller route',own in text and fact(M[own],1004,'PTFRS29_PHONE_kirk_Issued',1)and edge(M[own],1004,'Out',child['id'],'In1'),child);cg=M[cl]['graphs']['root'];cleans=[i for i,n in cg['nodes'].items()if r'base\quest\holocalls\kirk\kirk_cleanup.questphase'in n['refs']];ck('Kirk exact connected cleanup and own receipt',len(cleans)==1 and any(e[2]==cleans[0]for e in cg['edges'])and any(e[0]==cleans[0]for e in cg['edges'])and any(r.get('factName')=='PTFRS29_PHONE_kirk_Issued'for n in cg['nodes'].values()for r in n['reads']),{'native_cleanup_nodes':cleans})
 # Source-confirmed economic/escrow authoring remains exact, actual execution not inferred.
 stefan=PREF+r'base\quest\minor_quests\mq036\scenes\mq036_stefan_dialogues.scene';refunds=[canon({'$type':'TweakDBID','$storage':'string','$value':s})['$value']for s in ['QuestRewards.mq036_money_back','QuestRewards.mq036_money_back_end']];actual={canon(x)['$value']for x in walk(M[stefan])if x.get('$type')=='TweakDBID'};ck('SweetDreams exact refund reward targets preserved',all(x in actual for x in refunds),{'original_refund_targets':refunds,'scope':'Typed numeric/string identity, distinct authored refund branches, no new grant'})
 # Actual raw mutation controls for lifepath, genuine earned outcome and dead-branch context regression.
 def mu(d,fn,pred,label):
  o=copy.deepcopy(raw[d]);fn(o);m=Resource(o).normalize();caught=not pred(m);ck('actual raw mutation detected '+label,caught,d);mutations.append(dict(depot=d,fault=label,detected=caught))
 corpoid=canon({'$type':'TweakDBID','$storage':'string','$value':'LifePaths.Corpo'})['$value']
 mu(street,lambda o:[x['lifePathId'].update(**{'$value':corpoid,'$storage':'uint64'})for x in walk(o)if x.get('$type')=='LifePath_ScriptConditionType'],streetlife,'StreetKid changed native lifepath')
 mu(entries['q003_stout'],lambda o:[x.update(value=0)for x in walk(o)if x.get('$type')=='questVarComparison_ConditionType'and x.get('factName')=='q003_meredith_won'],lambda m:any(x.get('factName')=='q003_meredith_won'and x.get('value')==1 for x in node(m,65003)['reads']),'Stout fabricated won-history admission')
 def connect(o):
  x=next(x for x in walk(o)if x.get('$type')=='scnStartNode'and x.get('nodeId',{}).get('id')==2197);x['outputSockets'][0]['destinations'][0]['nodeId']['id']=3300
 mu(sc,connect,lambda m:'3300'not in reached(m['graphs']['scene'],'2197'),'Stout inactive Meredith request made active from selected farewell input')
 write(O/'source_pins.json',pins);write(O/'models.json',M);write(O/'comparisons.json',comparisons);write(O/'quest_evidence.json',ev);write(O/'phone_protocols.json',phone);write(O/'mutations.json',mutations);write(O/'stout_context.json',dict(selected_input='q003_07a_stout_sex_end_in',entry=2197,reachable=sorted(reach),inactive_request3300=sg['nodes']['3300']['writes'],active_generic_requests=active,no_native_phase_output=True));write(O/'summary.json',dict(checks=len(tests),mutations=3,fresh_exports=56,pinned_inputs=len(pins),quests=IDS,compared_private_resources=len(comparisons),kirk_producers=len(phone),runtime_changes=0));print(read(O/'summary.json'))
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output))
