"""Fresh raw readback, actual caller routes, journal/asset ownership, and controls."""
from pathlib import Path
import sys,copy,json,zlib
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import inputs as I
sys.path.insert(0,str(I.W/'prealpha/quest_restoration_qr5/reviews/worker_b'))
from review_remaining import path
from common import read,write,sha,walk
from model import Resource
def canon(x):
 if isinstance(x,list):return [canon(v)for v in x]
 if isinstance(x,dict):
  if x.get('$type')=='TweakDBID':
   v=x.get('$value','0');return {'$type':'TweakDBID','identity':str((len(v.encode())<<32)|zlib.crc32(v.encode()))if x.get('$storage')=='string'else str(v)}
  return {k:canon(v)for k,v in x.items()if k not in ['payload_sha256','metadata_sha256']}
 return x
def run():
 O=H/'deep_01';assert not O.exists();M=read(H/'inspection_01/models.json');pins=read(H/'inspection_01/source_pins.json');tests=[];mut=[];calls=[];journal={};assets=[]
 def ck(k,v,e):tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e});assert v,k
 for r in read(H/'raw_exports_01/manifest.json'):
  ck('fresh_actual_raw_hash '+r['depot'],sha(r['raw'])==r['raw_sha256']and sha(r['json'])==r['json_sha256'],r);mm=Resource(read(r['json'])).normalize();ck('independent_actual_raw_readback '+r['depot'],canon(mm)==canon(M[r['depot']]),{'fresh':r,'canonicalization':'Exact numeric TDB identity only, remove derived digest fields; no graph, node, socket, edge or condition omissions'})
 for q,pre in zip(I.Q,['mq305','mq306']):
  o=next(o for o in I.OWN if o['id']==q);known={j['path']:j for j in o['journals']};jp={}
  for d,m in M.items():
   if not d.startswith('ep1')or pre not in d:continue
   for gp,g in m['graphs'].items():
    for ni,n in g['nodes'].items():
     for x in walk(n['payload']):
      if x.get('$type')=='gameJournalPath'and x.get('realPath'):
       j=x['realPath'];cl=x.get('className',{}).get('$value');jp.setdefault(j,[]).append({'resource':d,'graph':gp,'node':ni,'class':cl,'type':n['type'],'incoming':[e for e in g['edges']if e[2]==ni]})
     for ref in n['refs']:assets.append({'quest':q,'resource':d,'graph':gp,'node':ni,'reference':ref,'indexed':ref in I.IDX,'decoded_graph':bool(I.IDX.get(ref,{}).get('graphs')),'resource_sha256':I.IDX.get(ref,{}).get('sha256'),'limit':'Literal/depot match is not a scene actor/prefab acquisition or binary definition proof.'})
     if n['type']=='questSceneNodeDefinition':
      scenes=[r for r in n['refs']if r.endswith('.scene')]
      for target in scenes:
       for a,s,b,t in g['edges']:
        if b!=ni or t=='CutDestination':continue
        declared=target in M and t in M[target]['graphs']['scene']['entries'];control=t=='Prefetch'and {'name':'Prefetch','type':'Input'}in n['sockets'];ok=declared or control;row={'resource':d,'graph':gp,'node':ni,'source_node':a,'source_socket':s,'scene_input':t,'scene':target,'entry_node':M.get(target,{}).get('graphs',{}).get('scene',{}).get('entries',{}).get(t),'binding_class':'DECLARED_SCENE_ENTRY'if declared else'NATIVE_SCENE_NODE_PREFETCH_CONTROL'if control else'UNRESOLVED','limit':'Prefetch is the exact native node Input socket, not an invented scene entry; engine prefetch behavior is not certified.'if control else''};ck('actual_scene_input_binding '+d+gp+ni+t,ok,row);calls.append(row)
  omitted={j:rs for j,rs in jp.items()if j.startswith(('ep1/quests/minor_quest/'+q,'ep1/contacts/aaron/mq306','contacts/mr_hands/mq305','contacts/trainer_fred/mq306_hook'))and j not in known};classes={j:sorted({r['class']for r in rs})for j,rs in omitted.items()};journal[q]={'guarded':len(known),'native_paths':len(jp),'omitted':omitted,'omitted_actual_classes':classes,'all_uses':jp,'disposition':'CONDITIONAL: omissions remain explicit; exact root/phase guards and discovered local progress writer coverage are proven, but no claim that every original journal reference is catalogued.'};ck('native_journal_omission_inventory_has_no_unrecorded_root_or_phase '+q,all(all(x['class']not in ['gameJournalQuest','gameJournalQuestPhase']for x in rs)for rs in omitted.values()),{'omitted_actual_classes':classes,'limit':'Includes native codex/map pins, two MQ305 objective references and MQ306 later meeting SMS/choice refs. These are not silently promoted to full eligibility PASS.'})
 for p in read(H/'verification_01/protocols.json'):
  if p['graph']!='scene':continue
  g=M[p['resource']]['graphs']['scene'];waits=p['waits'];clears=p['clears'];direct=[i for i in waits if path(g,p['node'],i)];fork=[i for i in g['nodes']if len([e for e in g['edges']if e[0]==i])>1 and path(g,i,p['node'])and any(path(g,i,w)for w in waits)];after=[(w,c)for w in waits for c in clears if path(g,w,c)];ck('actual_scene_request_ACK_wait_clear_path '+p['resource']+p['node'],bool(direct or fork)and bool(after),{'request':p,'direct_wait':direct,'prearmed_fork':fork,'wait_to_clear':after})
 # Exact world/cast metadata is preserved; rendering/streaming remains separate.
 actorbind={}
 for d,m in M.items():
  if not any(pre in d for pre in ['mq305','mq306'])or not d.endswith('.scene'):continue
  actorbind[d]=[{'name':a['actorName'],'acquisition':a['acquisitionPlan'],'community':a.get('communityParams'),'spawn_set':a.get('spawnSetParams'),'spawn':a.get('spawnDespawnParams'),'context':a.get('findActorInContextParams')}for a in m['metadata'].get('actors',[])]
 intro=next(d for d in M if d.endswith('mq306_01_intro.questphase'));ck('MQ306_owns_original_intro_and_Aaron_leases',M[intro]['root_prefabs']==['#mq306_pr_intro','#mq306_aaron_prefab'],M[intro]['root_prefabs'])
 ring=next(d for d in M if d.endswith('mq306_boxing_ring.questphase'));r=M[ring]['graphs']['root'];ck('MQ306_separate_ambient_ring_scope',not M[ring]['root_prefabs']and r['nodes']['34']['reads'][0]['factName']=='mq306_active'and r['nodes']['36']['type']=='questLogicalAndNodeDefinition',{'resource':ring,'actual_communities':sorted({a for n in r['nodes'].values()for a in n['node_refs']}),'limit':'Community switch owns ambient #cz... areas, distinct from intro #mq306_com_aaron/boxer/spectators; no absent-owner defect inferred from reference alone.'})
 jv=I.C/'package/r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds';s=jv.read_text(encoding='utf8');ck('exact_JV1_presentation_constraint','visual.TemporaryHide(true)'in s and 'Character.Silverhand'in s and 'SetFact'not in s and 'actor.IsAttached()'in s,{'path':str(jv),'sha256':sha(jv),'limit':'Independent props, actual Character record mapping, hide timing and presentation still require live observation.'})
 # Mutations alter actual raw JSON and use distinct native-source expectations.
 pin=next(p for p in pins if p['depot'].endswith('mq306_fresh_boot.questphase'));raw=read(pin['json']);rr=Resource(raw);root=rr.d(rr.root['graph']);nd=next(rr.d(h)for h in root['nodes']if rr.d(h)['id']==3);nd['id']=2;mm=Resource(raw).normalize();caught=any(x['kind']=='DUPLICATE_NODE_ID'for x in mm['errors']);ck('raw_saved_node_ID_collision_detected',caught,mm['errors']);mut.append({'name':'private_saved_node_collision','detected':caught});write(O/'saved_ID_collision.questphase.json',raw)
 pin=next(p for p in pins if p['depot']==intro);raw=read(pin['json']);raw['Data']['RootChunk']['phasePrefabs']=[p for p in raw['Data']['RootChunk']['phasePrefabs']if p['prefabNodeRef']['$value']!='#mq306_aaron_prefab'];mm=Resource(raw).normalize();caught=mm['root_prefabs']!=M[intro]['root_prefabs'];ck('raw_missing_Aaron_native_lease_detected',caught,mm['root_prefabs']);mut.append({'name':'missing_native_Aaron_lease','detected':caught});write(O/'missing_Aaron_prefab.questphase.json',raw)
 ck('all_discovered_local_progress_writers_guarded',all(not r['native_local_writers_not_in_fresh_guard']for r in read(H/'verification_01/handlers.json').values()),'MQ305 and MQ306: zero omitted discovered native local progress writer names; missing scalar serialization remains0, not historical proof')
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'scene_inputs.json',calls);write(O/'journal.json',journal);write(O/'assets.json',assets);write(O/'actor_bindings.json',actorbind);write(O/'mutations.json',mut);write(O/'summary.json',{'checks':len(tests),'raw_mutations':len(mut),'fresh_raw_resources':8,'scene_input_bindings':len(calls),'asset_reference_uses':len(assets),'journal_omissions':{q:len(d['omitted'])for q,d in journal.items()}});print(json.dumps({'checks':len(tests),'raw_mutations':len(mut),'scene_inputs':len(calls),'asset_uses':len(assets)},ensure_ascii=True))
if __name__=='__main__':run()
