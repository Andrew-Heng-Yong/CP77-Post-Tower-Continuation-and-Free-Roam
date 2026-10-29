import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
checks=[]
def ck(name,ok):
 checks.append({'name':name,'pass':bool(ok)});assert ok,name
spec=read(R/'outside1004_filter_spec_02.json');j=read(spec['sector_json']);nodes={n['index']:n['definition'] for n in j['nodes']};scenes=[]
rep=read(R/'thanks_scenes_native_01/report_01.json');ck('26current128archive thanks scenes',len(rep['hits'])==26 and rep['archives']==128)
for hit in rep['hits']:
 p=Path(hit['copy']);d=read(str(p)+'.json');ww=list(walk(d));sets=[n for n in ww if n.get('$type')=='questSetVar_NodeType'];waits=[n for n in ww if n.get('$type')=='questVarComparison_ConditionType'];ck('native thanks receipt consumption '+hit['depot'],sets==[{'$type':'questSetVar_NodeType','factName':'ma_scene_thanks','setExactValue':1,'value':0}] and waits==[{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'ma_scene_thanks','value':0}]);ck('native scene bytes '+hit['depot'],sha(p)==hit['sha256']);scenes.append(hit)
ck('63isdependentthanks',any(v.get('$type')=='ResourcePath' and v.get('$value','').endswith('thanks.conversations') for v in walk(nodes[63])))
ck('65references64',nodes[65]['interestingConversationsNodeRef']['$value']=='~/../la_street_violence_02_ic_animation')
ck('retained62onlyreviewedValentinos', {v['$value'] for v in walk(nodes[62]) if v.get('$type')=='ResourcePath'}=={'base\\open_world\\scenes\\conversations\\conversation_groups\\valentinos.conversations'})
ck('73pairednativeambientsignpost',nodes[73]['enterSignpost']['$value']=='ow_valentinos_START' and nodes[73]['exitSignpost']['$value']=='ow_valentinos_STOP' and nodes[73]['exitCooldown']==5)
drop={63,64,65};ret=[n for i,n in nodes.items() if i not in drop];ck('61workspotsretained',sum(n['$type']=='worldAISpotNode' for n in ret)==61)
ck('noautopopulation',not any(n['$type']=='worldPopulationSpawnerNode' and n['spawnOnStart']!=0 for n in ret))
ck('remainingconversationsonlyValentinos', {v['$value'] for n in ret for v in walk(n) if v.get('$type')=='ResourcePath' and v['$value'].endswith(('.scene','.conversations'))}=={'base\\open_world\\scenes\\conversations\\conversation_groups\\valentinos.conversations'})
removedrefs={p['quest_ref'].split('/')[-1] for p in j['placements'] if p['node'] in drop};ck('no retained references removedtargets',not any(str(v.get('$value','')).split('/')[-1] in removedrefs for n in ret for v in walk(n) if v.get('$type')=='NodeRef'))
ck('negativeoriginalhasnativefactconsumingthanks',bool(scenes) and 63 not in drop-{63})
ck('negative64onlyfilterleavesdanglingattractor',65 not in {64} and nodes[65]['interestingConversationsNodeRef']['$value'].endswith('la_street_violence_02_ic_animation'))
spec.update(drop_nodes=sorted(drop),drop_types=[nodes[i]['$type'] for i in sorted(drop)],drop_placements=[p['datum'] for p in j['placements'] if p['node'] in drop],reason='Remove complete linkedoneoffscene support63thanks receiptconsumer,64loreanimation/nativekill,65audioattractor. Preserve61AIspots, genericValentinos62 andpairedambient73.',thanks_scenes=scenes)
(R/'outside1004_filter_spec_03.json').write_text(json.dumps(spec,indent=2)+'\n',newline='\n');report={'status':'PASS_OUTSIDE1004_FILTERED_DEPENDENCIES','checks':checks,'selected_filter_spec':str((R/'outside1004_filter_spec_03.json').resolve()),'selected_filter_sha256':sha(R/'outside1004_filter_spec_03.json'),'drop_nodes':sorted(drop),'retained_spots':61,'retained_conversations':['base\\open_world\\scenes\\conversations\\conversation_groups\\valentinos.conversations'],'paired_audio':nodes[73],'prior_conversation_proof':str((R/'conversation_assessment_01.json').resolve()),'game_writes':0,'save_writes':0};(R/'outside1004_assessment_01.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n');p=R/'outside1004_cohort_spec_01.json';c=read(p);c['filter_spec']=str((R/'outside1004_filter_spec_03.json').resolve());c['proof']=str((R/'outside1004_assessment_01.json').resolve());p.write_text(json.dumps(c,indent=2)+'\n',newline='\n');print(json.dumps({'checks':len(checks),'drop':sorted(drop)}))
