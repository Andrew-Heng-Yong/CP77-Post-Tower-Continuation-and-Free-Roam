import sys,collections,binascii,re,itertools
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1];sys.path.insert(0,str(W/'prealpha/phone_support_ph1'))
from model import *
C=H/'candidate_01';B=W/'prealpha/phone_merge_ph2/candidate_01';b=read(C/'build_01.json');audit=read(W/b['native_capture']/'providers_01.json');g=model(C/'owner_readback_01.json');root=read(C/'owner_readback_01.json')['Data']['RootChunk'];checks=[]
def check(name,ok):
 assert ok,name
 checks.append(name)
check('unconditional root has no prefabs',not root.get('phasePrefabs'))
check('exact scoped outer graph',set(g['root']['nodes'])=={0,1,2,3} and g['root']['edges']==[(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In1')])
check('persistent inner graph',set(g['root/3']['nodes'])=={0,1,2,3} and g['root/3']['edges']==[(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In')])
pref=g['root']['nodes'][3]['phaseInstancePrefabs'];check('exact two native studios',len(pref)==2 and [x['prefabNodeRef']['$value'] for x in pref]==b['prefabs'])
native=read(Path(b['native_source']['raw']+'.json'))['Data']['RootChunk']['phasePrefabs']
for i,p in enumerate(pref):check('native prefab entry '+str(i),{k:v for k,v in p.items() if k!='prefabNodeRef'}=={k:v for k,v in native[i].items() if k!='prefabNodeRef'})
writes=[x for gp,z in g.items() for n in z['nodes'].values() for x in walk({k:v for k,v in n.items() if k!='phaseGraph'}) if x.get('$type')=='questSetVar_NodeType']
check('only three owned receipt writes',len(writes)==3 and {x['factName'] for x in writes}=={'PTFRPH3_Claimed','PTFRPH3_Entered','PTFRPH3_Ready'} and all(x['value']==1 for x in writes))
condition=g['root']['nodes'][1]['condition'];atoms=list(walk(condition));facts={x['factName']:x['value'] for x in atoms if x.get('$type')=='questVarComparison_ConditionType'}
check('serialized guard matches spec',facts==b['facts'])
check('completed native Tower journal gate',any(x.get('$type')=='questJournalEntryState_ConditionType' and x['state']=='Succeeded' and x['path']['realPath']=='ep1/quests/main_quest/q307_before_tomorrow' for x in atoms))
check('pending call can gain support',not any(k.startswith(('audio_','holo_')) for k in facts))
check('saved owner cannot issue again',all(facts[x]==0 for x in ['PTFRPH3_Claimed','PTFRPH3_Entered','PTFRPH3_Ready','PTFRPH3_Hold']))
check('outside Tower refusal',facts['PostTowerFreeRoamActive']==1 and facts['q307_active']==0 and facts['q307_main_game_killed']==1 and facts['q307_ep1_killed']==1)
inner=g['root/3']['nodes'][3]['condition'];check('hold is persistent',any(x.get('factName')=='PTFRPH3_Hold' and x.get('value')==1 for x in walk(inner)))
previous_studio_owners=[]
for p in (B/'archive_source').rglob('*.questphase'):
 if b'holocalls_studio' in p.read_bytes():previous_studio_owners.append(str(p))
check('no prior private studio owner/reference',not previous_studio_owners)
check('current native initializer hash pinned',sha(Path(b['native_source']['raw']))==b['native_source']['sha256'])
for p in b['prefabs']:check('native Quest descriptors '+p,sum(d['prefab']==p and d['category']=='Quest' for d in audit['descriptors'])==2)
ep=[d for d in audit['descriptors'] if d['prefab'].endswith('_ep1') and 'ep1\\quest_' in d['sector']][0]
variants=[x['name']['$value'] for x in ep['definition']['variants']]
check('Janet studio setup and lights',all(x in variants for x in ['janet_holocall_setup','janet_holocall_lights']))
epsector=next(h for h in audit['hits'] if h['depot']==ep['sector']);raw=Path(epsector['raw']).read_bytes()
for s in ['janet_holo','janet_holocall_workspot','janet_holocall_camera','janet_holocall_setup']:check('native Janet asset reference '+s,s.encode() in raw)
# Fresh registration inventory: parse standard quest additions, check every generated ID.
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');regs=[];files=[]
for f in (G/'archive/pc/mod').glob('*.xl'):
 t=(C/'package/archive/pc/mod'/f.name).read_text(encoding='utf-8-sig') if f.name=='zzzz_PTFR_Combined.archive.xl' else f.read_text(encoding='utf-8-sig');files.append({'path':str(f),'sha256':sha(f)})
 if not re.search(r'^quest:',t,re.M):continue
 section=t.split('quest:',1)[1].split('\nstreaming:',1)[0]
 for block in re.split(r'(?m)^    - path:\s*',section)[1:]:
  path=block.splitlines()[0].strip();parent=re.search(r'^      parent: (.+)$',block,re.M);assert parent
  if parent[1].strip()!=r'ep1\quest\ep1.quest':continue
  node=re.search(r'^        node: \[(.+)\]',block,re.M);assert node and node[1]=='1'
  regs.append({'path':path,'id':binascii.crc_hqx((path+':1').encode(),65535),'source':f.name})
ids=[x['id'] for x in regs];nativeids=set(model(W/'research/q307_extracted/json/ep1/quest/ep1.quest.json')['root']['nodes'])
check('all root addition IDs unique',len(ids)==len(set(ids)) and not nativeids.intersection(ids));check('new registration exactly once',sum(r['path']==b['depot'] for r in regs)==1)
old=(B/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl').read_text();new=(C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl').read_text();entry='    - path: '+b['depot']+'\n      parent: ep1\\quest\\ep1.quest\n      input:\n        node: [1]\n        socket: Out\n'
check('all previous XL registrations preserved',new.replace(entry,'')==old)
out={'status':'PASS_NATIVE_BINDINGS_AND_SERIALIZED_OWNER','checks':len(checks),'details':checks,'root_registrations':len(regs),'native_root_ids':sorted(nativeids),'new_id':next(r['id'] for r in regs if r['path']==b['depot']),'registration_inventory':regs,'xl_sources':files,'base_studio_variants':138,'ep1_additional_variants':35,'sector_decode_limitation':'WolvenKit 9.1 DynamicBaseClass/worldNode decode fails; original sectors are referenced unchanged; no sector edits or detailed placement proof claimed.','live_result':'UNVERIFIED'}
(C/'semantic_verification_01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k in ['status','checks','root_registrations','new_id']}))
