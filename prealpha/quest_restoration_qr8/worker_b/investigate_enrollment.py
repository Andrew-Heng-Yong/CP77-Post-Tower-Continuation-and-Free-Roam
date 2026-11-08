"""QR8 read-only actual-resource enrollment/physical-owner investigation.

No builder import. Fresh output required; all mutations are private JSON/byte fixtures.
Run from workspace: python -X utf8 -B prealpha/quest_restoration_qr8/worker_b/investigate_enrollment.py --out enrollment_verification_01
"""
from lib import *
import argparse,copy,struct,re

def refhash(s):
 s=re.sub(r';[^/]*','',s).replace('#','');h=0xcbf29ce484222325
 for b in s.encode():h=((h^b)*0x100000001b3)&0xffffffffffffffff
 return h

def setups(raw,rr):
 if len(raw)%144:raise ValueError('Non-144-byte setup buffer')
 ns=[rr.d(n)for n in rr.root['nodes']];out=[]
 for i in range(len(raw)//144):
  b=raw[i*144:(i+1)*144];ni=struct.unpack_from('<Q',b,0x70)[0]&0x7ffff
  if ni>=len(ns):raise ValueError('Packed setup node index outside definitions')
  t=rr.root['nodeData']['Data'][i];v=val(t['QuestPrefabRefHash']);number=int(v)if str(v).isdigit()else refhash(v)
  gid=struct.unpack_from('<Q',b,0x58)[0]
  if gid!=number:raise ValueError('Packed global identity disagrees with actual reference')
  out.append({'setup':i,'definition':ni,'global_id':str(gid),'ref':v,'type':ns[ni]['$type'],'debug_name':val(ns[ni].get('debugName')),'position':list(struct.unpack_from('<fff',b,0)),'secondary_distance':struct.unpack_from('<f',b,0x78)[0],'streaming_distance':struct.unpack_from('<f',b,0x7c)[0]})
 return out

def enrollment_errors(m,n):
 e=[];g=m['graphs']['scene'];ng=n['graphs']['scene'];choice=g['nodes']['839']['payload'];native=ng['nodes']['839']['payload']
 for i,dst in [(3,'1422'),(4,'1451')]:
  if choice['options'][i]==native['options'][i]and ['839','0:'+str(i),dst,'0:0']in g['edges']:e.append('lost-route-no-longer-defective:'+str(i))
 if ['1750','2:0','1755','0:1']not in g['edges']:e.append('native-yes-event-writer-route-lost')
 if g['nodes']['1755']['writes']!=[{'$type':'questSetVar_NodeType','factName':'q302_ronald_messages_enabled','setExactValue':1,'value':1}]:e.append('genuine-enrollment-writer-changed')
 for i in ['1730','1731','1769','1746']:
  if g['nodes'][i]['payload']!=ng['nodes'][i]['payload']:e.append('offered-counter-choice-history-changed:'+i)
 for k in ['workspots','workspotInstances','localMarkers','referencePoints','screenplayStore']:
  if m['metadata'][k]!=n['metadata'][k]:e.append('scene-bindings-changed:'+k)
 actor=lambda x:next(a for a in x['metadata']['actors']if a['actorId']['id']==5)
 if actor(m)!=actor(n):e.append('native-Ronald-community-binding-changed')
 return e

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=H/a.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir();checks=[];mutants=[]
 def ck(name,ok,**ev):checks.append({'name':name,'pass':bool(ok),**ev})
 pins=read(H/'readback_01/manifest.json')+read(H/'readback_02/manifest.json');models={}
 for p in pins:
  ck('actual-raw-json-pin:'+p['depot'],p['status']=='EXPORTED'and sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256'])
  models[p['depot']]=Resource(read(p['json'])).normalize()
 bo=models[BO];bs=models[BS];ns=models[NS];rn=models[RN];g=bs['graphs']['scene'];ng=ns['graphs']['scene'];b=bo['graphs']['root/5']
 ck('current-scene-source-invariants-and-defective-menu-shape',not enrollment_errors(bs,ns),errors=enrollment_errors(bs,ns))
 ck('both-authored-dogtown-menu-edges-disconnected',all(['839','0:'+str(i),d,'0:0']in ng['edges']and not any(e[0]=='839'and e[1]=='0:'+str(i)for e in g['edges'])for i,d in[(3,'1422'),(4,'1451')]))
 ck('story-related-option5-remains-disconnected',not any(e[0]=='839'and e[1]=='0:5'for e in g['edges']))
 incoming=[e for e in g['edges']if e[2]=='1755'];ck('genuine-yes1750-is-enrollment-writer-only-input',incoming==[['1750','2:0','1755','0:1']],incoming=incoming)
 seeds=['1422','1451'];boundaries={'839','827','920','3811','3258'};seen=set();todo=seeds[:]
 while todo:
  i=todo.pop()
  if i in seen:continue
  seen.add(i)
  if i not in boundaries:todo.extend(e[2]for e in ng['edges']if e[0]==i)
 ck('bounded-native-lore-consent-slice-preserves-all179-identities',len(seen)==179 and all(i in g['nodes']for i in seen),node_count=len(seen))
 work=[];instances={str(x['workspotInstanceId']['id']):x for x in bs['metadata']['workspotInstances']};works={str(x['dataId']['id']):x for x in bs['metadata']['workspots']}
 for i in sorted(seen,key=int):
  n=g['nodes'][i]
  for command in walk(n['payload']):
   if command.get('$type')=='scnUseSceneWorkspotParamsV1':
    wi=command['workspotInstanceId']['id'];inst=instances[str(wi)];res=works[str(inst['dataId']['id'])]
    work.append({'node':i,'command':command,'instance':inst,'resource':res})
 ck('all25-native-workspot-commands-resolve-scene-local-instances',len(work)==25 and all(x['instance']['playAtActorLocation']==1 and val(x['instance']['originMarker']['nodeRef'])in('0',0)for x in work),command_count=len(work),external_assets=sorted({val(x['resource']['workspotResource']['DepotPath'])for x in work}))
 save(out/'scene_local_workspot_bindings.json',work)
 ck('native-and-current-actor5-exact-community-acquisition',next(x for x in bs['metadata']['actors']if x['actorId']['id']==5)['acquisitionPlan']=='community'and next(x for x in bs['metadata']['actors']if x['actorId']['id']==5)==next(x for x in ns['metadata']['actors']if x['actorId']['id']==5))
 actorpin=next(x for x in read(W/'prealpha/quest_restoration_qr7/worker_a/actor_provider_exports_01/manifest.json')['records']if x['source_pin']['raw'].endswith('provider_3.streamingsector'))
 ck('current-registry-source-bytes-reverified',sha(actorpin['source_pin']['raw'])==actorpin['source_pin']['raw_sha256']and sha(W/actorpin['json'])==actorpin['json_sha256'])
 ar=Resource(read(W/actorpin['json']));reg=ar.d(ar.root['nodes'][3495]);communities=reg['communitiesData'];target=ar.clean(communities[481]);entry=target['template']['entries'][0]
 ck('current-native-scav-hobo-entry-and-tree-reference',target['communityId']['entityId']['hash']=='5761222262686403033'and val(entry['entryName'])=='scav_hobo'and val(entry['characterRecordId'])=='162080029830'and any(val(p['phaseName'])=='tree'and val(p['timePeriods'][0]['spotNodeRefs'][0])=='#q302_ws_scav_hobo_tree'for p in entry['phases']))
 ck('existing-B0-controller-keeps-exact-native-actor-start',b['nodes']['6']['payload']==rn['graphs']['root']['nodes']['6']['payload']and b['nodes']['7']['payload']==rn['graphs']['root']['nodes']['7']['payload']and b['nodes']['8']['payload']==rn['graphs']['root']['nodes']['8']['payload'])
 ck('existing-B0-no-root-or-instance-prefab-owner',not bo['root_prefabs']and all(not n['prefabs']for graph in bo['graphs'].values()for n in graph['nodes'].values()))
 ck('native-Ronald-root-owns-bar-prefab',rn['root_prefabs']==['#q302_pr_bar'])
 ck('B0-still-waits-native-near-trigger-before-scene',b['nodes']['2']['node_refs']==['#q302_tr_ronald_area_02']and ['8','Out','2','In']in b['edges']and ['2','Out','200','In']in b['edges']and ['200','Out','3','q302_05_ronald_in']in b['edges'])
 xl=W/'prealpha/quest_restoration_qr7/candidate_01/package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl';s=xl.read_text(encoding='utf-8-sig')
 pattern='- path: '+BO+'\n      parent: ep1\\quest\\ep1.quest\n      input:\n        node: [1]\n        socket: Out'
 ck('B0-direct-root-registration-no-hidden-XL-parent-prefab',pattern in s,xl=str(xl),sha256=sha(xl))
 ep=models[r'ep1\quest\ep1.questphase']['graphs']['root/10'];ad=models[r'ep1\quest\ep1_additional_game_elements.questphase']['graphs']['root'];pc=models[r'ep1\quest\ep1_persistent_content.questphase']
 ck('native-EP1-retirement-cut-precedes-receipt',all(e in ep['edges']for e in[['8','Out','9','In'],['9','CutSource','4','CutDestination'],['9','Out','10','In']])and ep['nodes']['10']['writes']==[{'$type':'questSetVar_NodeType','factName':'q307_ep1_killed','setExactValue':1,'value':1}])
 ck('retired-owner-envelope-encloses-original-Ronald',ep['nodes']['4']['refs']==[r'ep1\quest\ep1_additional_game_elements.questphase']and ad['nodes']['2']['refs']==[r'ep1\quest\ep1_persistent_content.questphase']and pc['graphs']['root/30']['nodes']['26']['refs']==[RN]and ['11','Out','26','In1']in pc['graphs']['root/30']['edges'])
 ck('retirement-predicate-actual-Tower-journal-or-PONR',ep['nodes']['8']['payload']['condition']['operation']=='OR'and ep['nodes']['8']['journal_paths']==['ep1/quests/main_quest/q307_before_tomorrow']and ep['nodes']['8']['reads'][0].get('state')=='Succeeded',predicate=ep['nodes']['8']['payload']['condition'])
 blockpin=next(p for p in pins if p['depot'].endswith('streamingblock')and 'all.streamingblock'in p['depot']);block=Resource(read(blockpin['json']));desc=block.root['descriptors'][1995];full=val(desc['questPrefabNodeRef'])
 ck('actual-bar-descriptor-is-quest-owned-no-variants',desc['category']=='Quest'and full.endswith('/#q302_pr_bar')and desc['variants']==[]and desc['numNodeRanges']==1 and val(desc['data']['DepotPath']).endswith(r'ep1\quest_7abca2b8d18f8562.streamingsector'))
 bufferpins=read(H/'buffers_01/manifest.json');bp=next(x for x in bufferpins if x['name']=='bar');sp=next(x for x in pins if x['depot'].endswith('quest_7abca2b8d18f8562.streamingsector'));sector=Resource(read(sp['json']));raw=Path(bp['buffer']).read_bytes();rows=setups(raw,sector)
 ck('bar-current-packed-buffer-pin',sha(bp['buffer'])==bp['buffer_sha256']and bp['raw_sha256']==sp['raw_sha256']and len(rows)==75)
 selected=[x for x in rows if str(x['ref']).endswith(('/#q302_ws_scav_hobo_tree','/#q302_tr_ronald_area_02','/#q302_tr_ronald_area_02_closer'))]
 ck('tree-AISpot-and-near-triggers-exact-packed-placements',len(selected)==3 and {(x['definition'],x['type'])for x in selected}=={(0,'worldAISpotNode'),(1,'worldTriggerAreaNode'),(3,'worldTriggerAreaNode')}and all('/#q302_pr_bar/'in str(x['ref'])and x['global_id']!='0'for x in selected),selected=selected)
 persistent=[{'index':i,'data':ar.clean(x)}for i,x in enumerate(reg['workspotsPersistentData'])if '7106761085964620863'in str(x)]
 ck('counterevidence-native-tree-position-is-persistently-compiled',len(persistent)==1 and persistent[0]['index']==47255 and persistent[0]['data']['isEnabled']==1 and persistent[0]['data']['globalNodeId']['hash']=='7106761085964620863',persistent=persistent)
 wa3=[models[p['depot']]['metadata']for p in pins if 'world_support_wa3'in p['depot']]
 ck('neither-current-WA3-block-registers-native-bar',all(not any(val(d.get('questPrefabNodeRef'))==full or val(d.get('data',{}).get('DepotPath',{}))==sp['depot']for d in r['descriptors'])for r in wa3))
 mp=read(W/'prealpha/quest_restoration_qr7/shared/marker_providers_01/manifest.json')['providers'][2];ck('current-static-marker-provider-pin',sha(mp['raw'])==mp['raw_sha256']and sha(mp['json'])==mp['json_sha256']);mr=Resource(read(mp['json']));mb=next(x for x in bufferpins if x['name']=='always0');mrows=setups(Path(mb['buffer']).read_bytes(),mr);marker=[x for x in mrows if x['definition']==2599]
 ck('scene-marker-is-actual-AlwaysLoaded-placement',len(marker)==1 and marker[0]['debug_name']=='q302_05_sm_bar'and marker[0]['type']=='worldStaticMarkerNode'and marker[0]['global_id']!='0',marker=marker)
 # Edit actual exported resource documents, then independently normalize the changed bytes' structure.
 scene_doc=read(next(p['json']for p in pins if p['depot']==BS))
 def quest_type(rr,i):
  node=next(rr.d(x)for x in rr.d(rr.root['sceneGraph'])['graph']if rr.d(x)['nodeId']['id']==i)
  return rr.d(rr.d(node['questNode'])['type'])
 for name,edit in [('genuine-Yes-writer-value0',lambda rr:quest_type(rr,1755).__setitem__('value',0)),('offered-history-reset',lambda rr:quest_type(rr,1769).__setitem__('value',0)),('scene-workspot-table-deleted',lambda rr:rr.root.__setitem__('workspots',[])),('Ronald-community-rebound',lambda rr:next(rr.d(x)for x in rr.root['actors']if rr.d(x)['actorId']['id']==5)['communityParams']['reference'].__setitem__('$value','#wrong'))]:
  d=copy.deepcopy(scene_doc);rr=Resource(d);edit(rr);e=enrollment_errors(rr.normalize(),ns);save(out/(name+'.json'),d);mutants.append({'fault':name,'detected':bool(e),'errors':e,'fixture':'actual-resource-export-mutated-then-renormalized'})
 mutated=bytearray(raw);struct.pack_into('<Q',mutated,0x70,999999)
 try:setups(mutated,sector);found=False
 except ValueError:found=True
 mutants.append({'fault':'tree-packed-index-outside-definitions','detected':found})
 mutated=bytearray(raw);mutated[0x58]^=1
 try:setups(mutated,sector);found=False
 except ValueError:found=True
 mutants.append({'fault':'tree-native-global-identity-changed','detected':found})
 for m in mutants:ck('mutation:'+m['fault'],m['detected'])
 findings=[{'id':'ENROLLMENT_MENU_DISCONNECTED','status':'FAIL','scope':'Existing B0 scene920: authored two Dogtown lore choices unavailable; no path to native genuine consent from those choices. Native Yes1750→1755 and refusal/offered history are intact but unreachable from current seven entries.','evidence':['scene839 options3/4 and exact native sockets','native1750 event2:0→1755 input0:1','scene1730/1731/1769 native offered/counter guards'],'repair':'Not integrated. Restoring two edges alone does not satisfy the omitted physical owner/contact dependencies.'}, {'id':'B0_NATIVE_BAR_SUPPORT_OMISSION','status':'FAIL','scope':'Static owner contract: private B0 has no original bar lease while still requesting tree community phase and native area02. The original native owner was enclosed by the genuine EP1 retirement cut. No source-confirmed filtered successor or parent lease is supplied.','evidence':['native root #q302_pr_bar','bar descriptor1995, packed definitions0/1/3','B0 root/5 zero prefabs, direct XL root registration','EP1 root/10 cut9→additional4→persistent root/30 node26'],'limit':'This proves omitted support obligation, not a live assertion that the actor or areas are absent on every save. Already-loaded original resources, another mod, closed-engine state and current effective dependency closure can alter observation. No compiled-community-area absence is used as proof.','repair':'Held: do not acquire unfiltered bar, duplicate actor, rebind saved community, or make a menu-only release.'}, {'id':'FIRST_CONTACT_BOOTSTRAP_MISSING','status':'CONDITIONAL','scope':'Current QR7 news requires actual Active Ronald contact and intentionally never runs native AddContact. Newly consenting missing-contact histories are not admitted; current B0 provides no native23/159/121 bootstrap.','evidence':['native phase11 158→154→23 / 159→121.NonCallable','native23 true branch has3-second HUD restore155→156','current QR7 root200 existing contact Active guard'],'repair':'Exact future-only design recorded separately; blocked until physical/saved-owner closure and independent approval. Existing Failed/Succeeded/Active contact history must never be overwritten or re-notified.'}]
 result={'status':'PASS_SOURCE_INVESTIGATION_WITH_BLOCKED_REPAIR'if all(c['pass']for c in checks)else'FAIL_VERIFIER','checks':checks,'check_count':len(checks),'mutations':mutants,'source_pins':pins,'actor_provider':actorpin,'buffer_pins':bufferpins,'selected_native_placements':selected,'static_scene_marker':marker,'native_persistent_tree_counterevidence':persistent,'native_contact_bootstrap':{i:rn['graphs']['root/11']['nodes'][i]for i in['158','154','23','159','121','155','156']},'native_contact_edges':[e for e in rn['graphs']['root/11']['edges']if e[0]in ['158','154','23','159','121','155','156']],'native_retirement_edges':[e for e in ep['edges']if e[0]in ['8','9','10']],'new_findings':findings,'runtime_writes':0,'serialized_resources':0,'integration_approved':False,'limits':['No live or save state has been observed.','Current native actor registry entries were decoded using QR7 bounded known-default acceptance; direct target populated fields and raw hash are pinned. No generic parsing repair is asserted.','Static scene-local references are intact; ten external workspot payloads are not newly decoded here. Their presence is not asserted as current merged-provider proof.','The actual AlwaysLoaded registry contains enabled persistent tree spot position/yaw. Consequently actor spawning is not declared broken just because the physical AISpot lives in the retired quest prefab. Engine use of this cache is LIVE_ONLY.','Only the two actual current WA3 blocks and exact original/registered B0 parents are compared; this is not a repeat of the full provider census.']}
 save(out/'checks.json',checks);save(out/'evidence.json',result);save(out/'findings.json',findings);save(out/'hash_observations.json',list(OBS.values()));print(result['status'],len(checks),'checks',len(mutants),'mutants')
 if result['status']=='FAIL_VERIFIER':raise SystemExit(1)
if __name__=='__main__':main()
