"""U10 detailed progression/presentation/runtime source gates. No builder imports."""
import sys,copy,json,re,argparse
from pathlib import Path
import inputs as I
from model import Resource,compare_graph
from verify_u10 import path
def run(group,O):
 assert not O.exists();V=I.H.parent/group/'verification_01';pins=I.read(V/'source_pins.json');M={p['depot']:I.load(p['depot'])[0] for p in pins if p.get('depot')};tests=[];allcase={}
 def ck(name,ok,evidence=None):
  tests.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,(name,str(evidence)[:700])
 def loc(d,gp,i):
  gg=M[d]['graphs'][gp];nn=gg['nodes'][str(i)];return {'depot':d,'graph':gp,'node':str(i),'payload':nn['payload'],'incoming':[e for e in gg['edges'] if e[2]==str(i)],'outgoing':[e for e in gg['edges'] if e[0]==str(i)]}
 rt=I.C/'package/r6/scripts/PTFR_Consolidated/PTFR_GigsU10.reds';code=rt.read_text(encoding='utf8');contracts=I.read(I.W/I.D['contract'])
 for needle in ['history.Certified','snapshot.FreshU10','this.Safe(','this.Fresh(','this.Own(id, "Issued")']:
  # Exact spelling census recorded; individual policy matches below use inspected source.
  allcase.setdefault('runtime_source_symbols',{})[needle]=needle in code
 for q in I.ASSIGN[group]:
  own=next(x for x in contracts['owners'] if x['id']==q);idx=next(i for i in range(8) if re.search(r'if i == '+str(i)+r' \{ return "'+re.escape(q)+r'";',code));expected={'Paths':[x['path'] for x in own['journals']],'Classes':[x['class'] for x in own['journals']],'FactNames':list(own['facts_equal'])+list(own.get('fact_ranges',{})),'ItemNames':[x['record'] for x in own['inventory_zero']]}
  for method,vals in expected.items():
   mat=re.search(r'func '+method+str(idx)+r'\(\) -> array<\w+> \{ return (\[.*?\]);',code);assert mat,(method,idx);actual=json.loads(mat.group(1));ck('effective compiled data '+q+method,actual==vals,{'index':idx,'expected':vals,'actual':actual,'script':str(rt)})
  rows=I.read(V/'quests'/q/'handlers.json');native={x['depot'] for x in rows};case={'native_handlers':len(rows),'root_prefabs':{d:M[d]['root_prefabs'] for d in sorted(native)},'journal_transitions':[x for x in rows if x['journal_paths']],'reward_and_item_operations':[x for x in rows if x['reward'] or 'ItemManager' in x['type']],'sms':[x for x in rows if x['sms']],'fact_writers':[x for x in rows if x['writes']],'external_dependencies':[],'scene_actors':{}}
  for d in native:
   for gp,g in M[d]['graphs'].items():
    for ni,n in g['nodes'].items():
     case['external_dependencies'] += [{'from':d,'graph':gp,'node':ni,'depot':r,'indexed':r in I.IDX,'decoded':r in M} for r in n['refs']]
   if d.endswith('.scene'):case['scene_actors'][d]={'actors':M[d]['metadata'].get('actors',[]),'workspots':M[d]['metadata'].get('workspots',[]),'world_markers':M[d]['metadata'].get('worldMarkers',[]),'cameras':M[d]['metadata'].get('cameras',[])}
  # Exact native authoring, independently chosen decisive outcome controls.
  specs={
   'sts_hey_gle_03':[('sts_hey_gle_03_ow.questphase','root/3',27,'Items.sts_hey_gle_03_guitar'),('sts_hey_gle_03_ow.questphase','root/3',158,'sts_hey_gle_03_guitar'),('sts_hey_gle_03_ow.questphase','root/5',2,'QuestRewards.sts_hey_gle_03_completion')],
   'sts_hey_gle_05':[('sts_hey_gle_05_openworld.questphase','root/5',54,'gle_05_track'),('sts_hey_gle_05_openworld.questphase','root/5',56,'gle_05_talked'),('sts_hey_gle_05_openworld.questphase','root/4',14,'QuestRewards.sts_hey_gle_05_completion')],
   'sts_hey_rey_01':[('sts_hey_rey_01_openworld.questphase','root/4',177,'rey_01_kill'),('sts_hey_rey_01_openworld.questphase','root/4',233,'rey_01_spare'),('sts_hey_rey_01_openworld.questphase','root/10',46,'rey_01_failed')],
   'sts_hey_rey_02':[('sts_hey_rey_02_open_world.questphase','root/5',100,'IsPersonalLinkConnected'),('sts_hey_rey_02_open_world.questphase','root/5',101,"'duration': 5"),('sts_hey_rey_02_open_world.questphase','root/4',88,'sts_valentinos_retaliation')],
   'sts_std_arr_03':[('sts_std_arr_03_openworld_phase.questphase','root/2',89,'arr_03_start'),('sts_std_arr_03_openworld_phase.questphase','root/2',90,'arr_03_finished'),('sts_std_arr_03_openworld_phase.questphase','root/2',112,'QuestRewards.sts_std_arr_03_completion')],
   'sts_wat_nid_07':[('sts_wat_nid_07_warehouse_openworld.questphase','root/3',13,'nid_07_recording_delivered'),('sts_wat_nid_07_warehouse_openworld.questphase','root/3',70,'nid_07_recording_seen'),('sts_wat_nid_07_warehouse_openworld.questphase','root/3',72,'nid_07_aaron_confronted_about_recording')],
   'sts_wbr_hil_06':[('sts_wbr_hil_06_openworld_phase.questphase','root/2',195,'hil_06_finished'),('sts_wbr_hil_06_openworld_phase.questphase','root/6',19,'QuestRewards.sts_wbr_hil_06'),('sts_wbr_hil_06_openworld_phase.questphase','root/6',23,'QuestRewards.sts_wbr_hil_06')],
   'sts_wbr_jpn_12':[('sts_wbr_jpn_12_main_phase.questphase','root',21,'jpn_12_second_location_active'),('sts_wbr_jpn_12b_openworld.questphase','root/4',54,'jpn_12_finished'),('sts_wbr_jpn_12b_openworld.questphase','root/5',15,'QuestRewards.sts_wbr_jpn_12_completion')]
  }
  decisive=[]
  for suffix,gp,ni,needle in specs.get(q,[]):
   d=next(d for d in native if d.endswith('\\'+suffix));row=loc(d,gp,ni);ck('native decisive mechanism '+q+':'+gp+':'+str(ni),needle in str(row['payload']),row);decisive.append(row)
  case['decisive_mechanisms']=decisive;I.write(O/'quests'/q/'mechanisms.json',case);allcase[q]={'mechanisms':str(O/'quests'/q/'mechanisms.json'),'sha256':I.sha(O/'quests'/q/'mechanisms.json')}
 for needle in ['state = IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1;', 'actual < minimum[k] || actual > maximum[k]', 'if actual != 0 {', 'if this.Own(i, "Issued") == 0 {', 'this.Same(this.previous[i], current) && this.Ready(i) && this.Dependencies(i)', 'SnapshotStateHS1.Admits(this.GetGameInstance(),GigDataU10.ID(i))']:
  ck('actual finite admission/persistence implementation '+needle,needle in code,{'script':str(rt),'literal':needle})
 if group=='C02':
  native=I.D['embedded_clones'][0];donor='recipe:'+native['source_raw'];cur=native['depot'];emb=next(x for x in M[donor]['embedded_files'] if x['depot']==native['original_depot']);pre=emb['graph_prefix']+'/root';original={'graphs':{'root'+gp[len(pre):]:g for gp,g in M[donor]['graphs'].items() if gp==pre or gp.startswith(pre+'/')},'metadata':emb['metadata'],'metadata_sha256':I.digest(emb['metadata'])}
  ck('Family complete embedded after-phase preserved',not compare_graph(original,M[cur]),{'original':native['original_depot'],'source':donor,'prefix':pre,'current':cur,'diff':compare_graph(original,M[cur])});I.write(O/'family_after_phase.json',{'source':donor,'original_prefix':pre,'current':cur,'graphs':len(original['graphs']),'root_prefabs':emb['root_prefabs'],'complete_comparison':compare_graph(original,M[cur])})
 # Independently reconstruct only the approved Psychofan changes from native JSON.
 if group=='C01':
  pm=I.read(I.W/'prealpha/gigs_u10/presentation/build/presentation_03/component.json');mapping=pm['reference_replacements'];pres=[]
  for item in pm['inputs']:
   d=item['depot'];raw=I.read(I.W/item['native_json']);expected=copy.deepcopy(raw);root=expected['Data']['RootChunk'];changes=[]
   if d.endswith('.scene'):
    ck('Psychofan exact native Silverhand actor3 retained',next(x for x in root['actors'] if x['actorName']=='silverhand')['actorId']['id']==3)
    root['props']=root['props'][:5];root['debugSymbols']['performersDebugSymbols']=[x for x in root['debugSymbols']['performersDebugSymbols'] if x['performerId']['id'] not in [1282,1538]];removed=set();count=0
    for h in root['sceneGraph']['Data']['graph']:
     nn=h['Data'];keep=[]
     for h2 in nn.get('events',[]):
      e=h2['Data'];typ=e['$type']
      if e.get('performerId',{}).get('id')==769 and typ in ['scneventsEquipItemToPerformer','scneventsUnequipItemFromPerformer','scneventsVFXEvent']:removed.add(e['id']['id']);continue
      if typ=='scnPlaySkAnimEvent' and e.get('performer',{}).get('id')==769:e['muteAnimEvents']='STANDARD';count+=1
      keep.append(h2)
     if 'events' in nn:nn['events']=keep
    for x in root['debugSymbols']['sceneEventsDebugSymbols']:x['sceneEventIds']=[e for e in x['sceneEventIds'] if e['id'] not in removed]
    root['debugSymbols']['sceneEventsDebugSymbols']=[x for x in root['debugSymbols']['sceneEventsDebugSymbols'] if x['sceneEventIds']]
    for x in I.walk(root):
     if 'workspotResource' in x and isinstance(x['workspotResource'],dict):
      old=I.value(x['workspotResource']['DepotPath']);target=next((v['depot'] for v in pm['inputs'] if v['depot'].endswith('.workspot') and v['native_raw'].replace('/','\\').endswith(old)),None)
      if target:x['workspotResource']['DepotPath']['$value']=target
    changes=['Remove only terminal props5/6 and matching debug performers',{'removed_Silverhand_visual_events':sorted(removed),'muted_Silverhand_animation_events':count}]
   elif d.endswith('.workspot'):
    for x in I.walk(root):
     if x.get('$type')=='animAnimNode_WorkspotHub':x['eventFilterType']='Mute'
     if x.get('$type')=='workWorkspotTree' and x.get('initialActions'):x['initialActions']=[]
    changes=['Mute animation eventFilterType in private Johnny-only workspot; remove cigarette initialActions']
   for x in I.walk(expected):
    if isinstance(x.get('DepotPath'),dict) and I.value(x['DepotPath']) in mapping:x['DepotPath']['$value']=mapping[I.value(x['DepotPath'])]
   if d not in M:
    rb=I.W/'prealpha/gigs_u10/presentation/build/presentation_03/readback'/(d+'.json');binary=I.C/'archive_source'/d;historical=I.W/'prealpha/gigs_u10/presentation/build/presentation_03/source'/d
    ck('private workspot exact serialized input '+d,I.sha(binary)==I.sha(historical)==pm['resources'][d]==I.E['source_resources'][d],{'binary':str(binary),'historical':str(historical),'readback':str(rb)})
    M[d]=Resource(I.read(rb)).normalize();pins.append({'depot':d,'binary':str(binary),'sha256':I.sha(binary),'json':str(rb),'json_sha256':I.sha(rb),'scope':'Exact historical binary/readback pair reused only after present staged byte equality'})
   em=Resource(expected).normalize();ck('Psychofan independent approved-only native transformation '+d,not compare_graph(em,M[d]),{'resource':d,'native':item['native_json'],'changes':changes});pres.append({'depot':d,'native':item['native_json'],'native_sha256':I.sha(I.W/item['native_json']),'changes':changes,'diff_after_exact_authorized_transform':compare_graph(em,M[d])})
  I.write(O/'psychofan_presentation.json',pres)
 I.write(O/'tests.json',tests);I.write(O/'source_pins.json',pins);I.write(O/'evidence.json',allcase);I.write(O/'summary.json',{'status':'PASS_SPECIFIC_MECHANISMS_WITH_EXPLICIT_ASSET_ENGINE_LIMITS','group':group,'checks':len(tests),'runtime_source':str(rt),'runtime_sha256':I.sha(rt),'scene_marker_placement':'OPAQUE_NOT_RESOLVED_BY_LITERAL_BINDINGS','gameplay':False});print({'group':group,'checks':len(tests),'output':str(O)})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--group',required=True);p.add_argument('--output',required=True);a=p.parse_args();run(a.group,Path(a.output))
