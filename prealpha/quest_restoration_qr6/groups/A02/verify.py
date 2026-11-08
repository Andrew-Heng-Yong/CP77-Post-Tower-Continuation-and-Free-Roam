"""KOLD MIRAGE, Love Rollercoaster, Highwayman exact original/current contracts."""
from pathlib import Path
import sys,copy,collections,re
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'A01'));from source_lib import *
from verify import semantic,edge,node,fact
IDS=['mq016_bartmoss','mq006_rollercoaster','mq029_tourist']
def replace(x,mp):
 if isinstance(x,dict):return{k:replace(v,mp)for k,v in x.items()}
 if isinstance(x,list):return[replace(v,mp)for v in x]
 return mp.get(x,x)if isinstance(x,str)else x
def run(O):
 assert not O.exists();M={};raw={};pins=read(H/'readback_01/manifest.json');tests=[];mutations=[];comparisons=[];inventory={}
 def ck(k,v,e):
  tests.append(dict(name=k,status='PASS'if v else'FAIL',evidence=e));write(O/'tests.json',tests)
  if not v:raise AssertionError(k)
 for p in pins:
  ck('actual fresh raw+JSON '+p['depot'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);raw[p['depot']]=read(p['json']);M[p['depot']]=Resource(raw[p['depot']]).normalize()
 ct=read(W/'prealpha/sidejobs_s28/vehicles/build/vehicles_05/component.json');s30=read(W/'prealpha/sidejobs_s30/prepared_02/manifest.json');s29audit=read(W/'research/sidejobs_s29/presentation_audit_01.json');srpath=W/'prealpha/sidejob_repair_sr1/candidate_02/visual_07/proof.json';sr=next(x for x in read(srpath)['additional']if'mq016'in x['depot']);prefixes=['towercontinued\\sidejobs_s29\\native\\','towercontinued\\sidejobs_s30\\native\\'];rev={d:d[len(pre):]for d in E['source_resources']for pre in prefixes if d.startswith(pre)};rev.update({v:k for k,v in ct['presentation']['mapping'].items()});by_scene={x['depot']:x for x in s29audit['scenes']}
 def compare(d,orig,a,b,changes):
  if semantic(a)!=semantic(b):
   from fresh_compare import leaves
   write(O/'differences.json',leaves(semantic(a),semantic(b)))
  ck('all native semantics outside precise approved edits '+d,semantic(a)==semantic(b),{'native':orig,'current':d,'changes':changes});comparisons.append(dict(vanilla=orig,current=d,changes=changes,all_remaining_semantics_equal=True))
 for d in [d for d in M if any(d.startswith(pre)for pre in prefixes)and not d.endswith('.workspot')]:
  orig=rev[d];a=copy.deepcopy(M[orig]);b=replace(copy.deepcopy(M[d]),rev);changes=[]
  if orig in by_scene:
   ad=by_scene[orig];per=set(ad['performers'])
   for g in a['graphs'].values():
    for i,n in g['nodes'].items():
     for x in walk(n['payload']):
      if x.get('$type')=='scnPlaySkAnimEvent'and x.get('performer',{}).get('id')in per:x['muteAnimEvents']='STANDARD';changes.append(dict(kind='R4mute',node=i,event=x['id']['id']))
     if 'events'in n['payload']:
      removed=[x for x in n['payload']['events']if x.get('performerId',{}).get('id')in per and x.get('$type')in['scneventsEquipItemToPerformer','scneventsUnequipItemFromPerformer','scneventsVFXEvent']];n['payload']['events']=[x for x in n['payload']['events']if x not in removed];changes+=['R4exact performer equipment/VFX removal '+x['id']['id']for x in removed]
  if orig.endswith(r'mq016\mq016_bartmoss.questphase'):
   ck('exact Nix late handoff',fact(b,64000,'nix_default_on',0)and fact(b,64001,'nix_default_on',0)and fact(b,64001,'PTFRB0S4NIX_OwnerActive',0)and edge(b,6,'Out',64000,'In')and edge(b,64000,'Out',64001,'In')and edge(b,64001,'Out',3,'In1'),'only future Freezer→Afterlife seam; saved native descendants retained');b['graphs']['root']['nodes'].pop('64000');b['graphs']['root']['nodes'].pop('64001');b['graphs']['root']['edges']=sorted([e for e in b['graphs']['root']['edges']if e not in[['6','Out','64000','In'],['64000','Out','64001','In'],['64001','Out','3','In1']]]+[['6','Out','3','In1']]);changes.append(dict(kind='existing_Nix_service_release_wait',nodes=[64000,64001]))
  if d==sr['depot']:
   ck('SR1 actual KOLD corrected donor',E['source_resources'][d]==sr['patched_sha256'],sr);meta=b['metadata'];inst=[x for x in meta['workspotInstances']if x['workspotInstanceId']['id']==6318];ck('SR1 exact KOLD marker instance',len(inst)==1 and inst[0]['originMarker']['nodeRef']['$value']=='#mq016_ws_johnny_at_coffin'and inst[0]['playAtActorLocation']==0,inst);meta['workspotInstances']=[x for x in meta['workspotInstances']if x not in inst];ws=[x for x in meta['workspots']if x['dataId']['id']==3237006318];ck('SR1 KOLD dedicated muted workspot',len(ws)==1 and ws[0]['workspotResource']['DepotPath']['$value']==r'towercontinued\sidejob_repair_sr1\workspots\sq006__johnny__stand_cigarette__stand_around__01.workspot',ws);meta['workspots']=[x for x in meta['workspots']if x not in ws];old=node(a,318,'scene')['payload']['questNode']['paramsV1'];new=node(b,318,'scene')['payload']['questNode']['paramsV1'];ck('SR1 KOLD preserves exact original actor command fields',new['$type']=='scnUseSceneWorkspotParamsV1'and new['workspotInstanceId']['id']==6318 and new['workspotNode']['$value']=='0'and all(new[k]==v for k,v in old.items()if k not in['$type','workspotNode']),new);node(b,318,'scene')['payload']['questNode']['paramsV1']=copy.deepcopy(old);changes.append(dict(kind='SR1_KOLD_world_to_scene_workspot',node=318,instance=6318))
  if orig.endswith('mq006_02_finale.scene'):
   # Original Johnny actor5 voice removal was explicitly requested in SC1; preserve all other dialogue and timing.
   for x in walk(a):
    if x.get('$type')=='scnPlaySkAnimEvent'and x.get('performer',{}).get('id')==1281:x['muteAnimEvents']='STANDARD'
    if x.get('$type')=='questVarComparison_ConditionType'and x.get('factName')=='mq006_ride_no_quest':ck('JC1 exact native noquest predicate source',x['comparisonType']=='GreaterOrEqual'and x['value']==1,x);x.update(comparisonType='Equal',factName='PTFRWORLD_Coaster_QuestOwns',value=0)
   lines={x['itemId']['id']for x in a['metadata']['screenplayStore']['lines']if x.get('$type')=='scnscreenplayDialogLine'and x.get('speaker',{}).get('id')==5};removed=[]
   for i,n in a['graphs']['scene']['nodes'].items():
    ev=n['payload'].get('events',[]);rr=[x for x in ev if x.get('$type')=='scnDialogLineEvent'and x['screenplayLineId']['id']in lines];removed+=rr
    if 'events'in n['payload']:n['payload']['events']=[x for x in ev if x not in rr]
   ck('SC1 exactly14original Johnny dialogue events removed',len(lines)==len(removed)==14,{'actor':5,'lines':sorted(lines),'event_ids':[x['id']['id']for x in removed]});ids={x['id']['id']for x in removed}
   def clear(x):
    if isinstance(x,dict):return{k:clear(v)for k,v in x.items()}
    if isinstance(x,list):return[clear(v)for v in x if not(isinstance(v,dict)and v.get('$type')=='scnSceneEventId'and v.get('id')in ids)]
    return x
   a=clear(a);changes+=['JC1 five actual noquest predicates use private lease','SC1 fourteen Johnny-only dialogue events removed; exact durations retained','R4 actor5 animation mute']
  compare(d,orig,a,b,changes)
 # Highwayman: all native branch bodies and exact authored R4 scene wrappers, not resource presence.
 for item in ct['presentation']['inputs']:
  if'mq029'not in item['depot']or item['depot'].endswith('.workspot'):continue
  d=item['depot'];orig=Resource(read(W/item['original'])).normalize();a=copy.deepcopy(orig);b=replace(copy.deepcopy(M[d]),rev);changes=[]
  if item['kind']=='scene':
   meta=b['metadata'];ck('Highwayman exact added private instance '+d,len(meta['workspots'])==1 and len(meta['workspotInstances'])==1 and meta['workspotInstances'][0]['workspotInstanceId']['id']==65000 and meta['workspotInstances'][0]['originMarker']['nodeRef']['$value']==item['anchor'],meta['workspotInstances']);meta['workspots']=[];meta['workspotInstances']=[]
   matches=[x for g in b['graphs'].values()for n in g['nodes'].values()for x in walk(n['payload'])if x.get('$type')=='questUseWorkspotNodeDefinition'and x['id']==item['node']];olds=[x for g in a['graphs'].values()for n in g['nodes'].values()for x in walk(n['payload'])if x.get('$type')=='questUseWorkspotNodeDefinition'and x['id']==item['node']];ck('Highwayman original world command→dedicated scene workspot '+d,len(matches)==len(olds)==1 and matches[0]['paramsV1']['$type']=='scnUseSceneWorkspotParamsV1'and matches[0]['paramsV1']['workspotInstanceId']['id']==65000,matches);matches[0]['paramsV1']=copy.deepcopy(olds[0]['paramsV1'])
   for g in a['graphs'].values():
    for n in g['nodes'].values():
     for x in walk(n['payload']):
      if x.get('$type')=='scnPlaySkAnimEvent'and x.get('performer',{}).get('id')==1:x['muteAnimEvents']='STANDARD'
   changes.append(dict(kind='S28specific_workspot_adapter',node=item['node'],marker=item['anchor']))
  compare(d,item['original'],a,b,changes)
 # Exact original parent slices, story/repeatable lease and explicitly requested CC1 upper bound.
 parent=M[r'base\quest\minor_quests\minorquests.questphase'];plan=next(x for x in PLANS[0]['jobs']if x['id']=='mq016_bartmoss');entry=r'towercontinued\sidejobs_s29\entries\mq016_bartmoss.questphase'
 for i in plan['parent']['ids']:
  a=copy.deepcopy(node(parent,i)['payload']);b=replace(copy.deepcopy(node(M[entry],i)['payload']),rev)
  if'phaseResource'in a:a['phaseResource']['Flags']='Soft'
  ck('KOLD actual native parent node '+str(i),a==b,{'source':'minorquests','node':i})
 ck('KOLD original MQ015 exclusion and Rogue earned prerequisite',fact(parent,196,'mq015_active',0,comp='Equal')and fact(parent,78,'q103_rogue_done',0,comp='Greater'),'borrowed service cannot overlap unfinished sibling')
 ce=r'towercontinued\sidejobs_s30\entries\mq006_rollercoaster.questphase';cm=M[ce];ck('Coaster exact CC1 cutoff in both guard copies',fact(cm,65003,'q105_done',0,comp='Equal')and fact(cm,65004,'q105_done',0,comp='Equal'),'User correction docs/coaster_post_doublelife_20261027.md; no permission to remove it')
 ck('Coaster JC1 native ride flag range0through1',all({(x.get('comparisonType'),x['value'])for x in node(cm,i)['reads']if x.get('factName')=='mq006_ride_no_quest'}=={('GreaterOrEqual',0),('LessOrEqual',1)}for i in [65003,65004]),'existing false-history flag is not cleared')
 ck('Coaster acquire before story release after real body output',fact(cm,65008,'PTFRWORLD_Coaster_QuestOwns',1)and fact(cm,65009,'PTFRWORLD_Coaster_QuestOwns',0)and edge(cm,65005,'Out',65008,'In')and edge(cm,65008,'Out',65006,'In')and edge(cm,20,'Out1',65009,'In')and edge(cm,65009,'Out',65007,'In'),'one physical cart owner, no synthetic completion')
 for d,i in [(r'towercontinued\world_interactions\coaster_gate.questphase',1),(r'towercontinued\world_interactions\coaster_owner.questphase',32)]:ck('repeatable earned gate and story lease exclusion '+d,fact(M[d],i,'PTFRWORLD_Coaster_QuestOwns',0)and fact(M[d],i,'mq006_enable_repeatable_rollercoaster',1),node(M[d],i)['payload'])
 story=r'towercontinued\sidejobs_s30\native\base\quest\minor_quests\mq006\mq006.questphase';ck('native q110 actual story failure gate untouched','quests/main_quest/act_01/q110_01_voodooboys'in str(node(M[story],30,'root/50')['payload'])and edge(M[story],30,'Out',32,'In','root/50'),'native q110Active monitor differs from requested DoubleLife q105 upper bound');ck('native finale reward precedes mq006 done receipt',node(M[story],26,'root/50')['reward']and edge(M[story],4,'mq006_02_finale_out',26,'In','root/50')and edge(M[story],26,'Out',61,'In','root/50')and fact(M[story],61,'mq006',1,'root/50'),'native reward26→61mq0061→24 checkpoint')
 ne=r'towercontinued\b0_story_eight\nix.questphase';ck('Nix service lease has actual native exit receipt',fact(M[ne],6,'PTFRB0S4NIX_OwnerActive',0)and edge(M[ne],5,'Out1',6,'In')and edge(M[ne],6,'Out',2,'In')and node(M[ne],5)['prefabs']==['#pr_nix_default'],'source wait does not fake OwnerActive0')
 he=r'towercontinued\sidejobs_s28\vehicles\mq029_tourist_entry.questphase';hm=M[he];recipe=next(x for x in ct['recipes']if x['id']=='mq029_tourist');ck('Highwayman original parent child payload',node(hm,100)['refs']==[recipe['private_native']]and hm['graphs']['root']['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in recipe['edges']]),recipe)
 pc=node(hm,4)['payload']['condition'];pr=[x for x in walk(pc)if x.get('$type')=='questPrereq_ConditionType'];ck('Highwayman typed actual player vehicle-unowned prerequisite',len(pr)==1 and pr[0]['isObjectPlayer']==1 and pr[0]['prereq']['$className']=='PTFR.SideJobsS28.PTFRS28HighwaymanVehicleUnownedPrereq',pr)
 for filename in ['PTFR_SideJobsS28.reds','PTFR_SideJobsS29.reds']:
  script=C/'package/r6/scripts/PTFR_Consolidated'/filename;sp=next(x for x in E['package_files']if x['path'].endswith('/'+filename));ck('current exact runtime source '+filename,sha(script)==sp['sha256'],sp);pins.append(dict(path=str(script),sha256=sha(script)))
  if filename=='PTFR_SideJobsS28.reds':
   code=script.read_text();part=code[code.index('public class PTFRS28HighwaymanVehicleUnownedPrereq'):code.index('public class PTFRS28HoonVehicleUnownedPrereq')];ck('Highwayman actual runtime unowned test and fail-closed context',all(t in part for t in ['player.IsReplacer()','player != localPlayer','return false','!vehicles.IsVehiclePlayerUnlocked(TDBID.Create("Vehicle.v_sportbike2_arch_tyger_player"))']),part)
  else:ck('CC1 runtime authoritative exact0bound',all(t in script.read_text()for t in ['"PTFRWORLD_Coaster_Registered", "q105_done"','FactMin0() -> array<Int32> { return [0, 0, 0, 0, 0, 0, 0, 0]','FactMax0() -> array<Int32> { return [0, 0, 0, 0, 1, 0, 0, 0]']),'q105 current runtime0; native rideflag0..1')
 ck('Nix native service actual exit condition and nested termination',fact(M[ne],11,'nix_default_on',1,'root/5',comp='Less')and fact(M[ne],18,'nix_dd_holo',0,'root/5')and edge(M[ne],11,'Out',18,'In','root/5')and edge(M[ne],18,'Out',1,'In','root/5')and node(M[ne],1,'root/5')['payload']['type']=='Terminating','native11→18→terminating1 then root5.Out1→OwnerActive0; engine effect stays conditional')
 for q in IDS:
  ds=[d for d in M if q[:5]in d and not'\\versions\\'in d];rr=[dict(depot=d,**r)for d in ds for r in rows(M[d])];own=[r for r in rr if r['depot'].startswith('towercontinued')and('\\native\\'in r['depot']or'\\vehicles\\'in r['depot'])];positive=[dict(depot=r['depot'],graph=r['graph'],node=r['node'],writes=r['writes'],incoming=r['incoming'],outgoing=r['outgoing'])for r in own if any(re.search(r'^(holo|audio)_.+_(start|end)_activate$',x['factName'])and x['value']>0 for x in r['writes'])];ck('specific native generic-call producer census '+q,not positive,{'all_native_private_handlers':len(own),'positive_generic_calls':positive,'limits':'No claim every possible engine message is absent; typed journal/event actions remain inventoried.'});inventory[q]=dict(resources=ds,handler_rows=rr,positive_generic_phone_requests=positive,journal=[r for r in own if r['journal_paths']],rewards=[r for r in own if r['reward']],prefab_scopes={d:M[d]['root_prefabs']for d in ds})
 # Mutate actual serialized documents at independently defined mechanism boundaries.
 def mu(d,fn,pred,label):
  obj=copy.deepcopy(raw[d]);fn(obj);m=Resource(obj).normalize();caught=not pred(m);ck('actual raw mutation caught '+label,caught,d);mutations.append(dict(fault=label,depot=d,caught=caught))
 mu(ce,lambda o:[x.update(value=1)for x in walk(o)if x.get('$type')=='questVarComparison_ConditionType'and x.get('factName')=='q105_done'],lambda m:fact(m,65003,'q105_done',0,comp='Equal'),'removed CC1 DoubleLife cutoff')
 kd=r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq016\mq016_bartmoss.questphase';mu(kd,lambda o:[x.update(value=1)for x in walk(o)if x.get('$type')=='questVarComparison_ConditionType'and x.get('factName')=='PTFRB0S4NIX_OwnerActive'],lambda m:fact(m,64001,'PTFRB0S4NIX_OwnerActive',0),'reversed Nix lease-release predicate')
 mu(he,lambda o:[x.update(**{'$className':'PTFR.Invalid'})for x in walk(o)if x.get('$className')=='PTFR.SideJobsS28.PTFRS28HighwaymanVehicleUnownedPrereq'],lambda m:'PTFR.SideJobsS28.PTFRS28HighwaymanVehicleUnownedPrereq'in str(node(m,4)['payload']),'lost earned-vehicle predicate')
 write(O/'comparisons.json',comparisons);write(O/'quest_evidence.json',inventory);write(O/'source_pins.json',pins);write(O/'models.json',M);write(O/'mutations.json',mutations);write(O/'summary.json',dict(checks=len(tests),mutations=len(mutations),fresh_exports=len(read(H/'readback_01/manifest.json')),pinned_inputs=len(pins),quests=IDS,compared_private_resources=len(comparisons),runtime_changes=0));print(read(O/'summary.json'))
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output))
