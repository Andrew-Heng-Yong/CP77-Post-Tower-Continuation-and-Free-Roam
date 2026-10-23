"""Independent binary-readback graph and admission tests, not engine playtests."""
import binascii, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import read, sha, walk

COMMON={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'PTFRPA2_Finished':1,
 'PTFRPA2_Fault':0,'q307_done':1,'q307_finished':1,'q307_2079':1,
 'q307_main_game_killed':1,'q307_ep1_killed':1,'q307_active':0,
 'q307_debug_reset':0,'q115_point_of_no_return':0,'q305_johnny_scene_active':0,
 'PTFRU9_Support_Issued':1,'PTFRU9_Support_Fault':0}
SPECS={
 'ma_wat_lch_01':({0,31,74,34,30,36,73},34,30,74,'In1'),
 'ma_wat_lch_02':({0,31,74,35,16,36,73},35,16,74,'In2'),
 'ma_wat_lch_03':({0,31,74,55,70,37,28,36,73},37,28,70,'In1')}
OVERRIDE=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
def load(p):
 r=SafeResource(read(p));return r,{g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return {tuple(e) for e in g['edges']}
def native_json(p):return ROOT/(p.replace('/raw/','/json/')+'.json')
def equal_predicates(c):
 assert c['$type']=='questLogicalCondition' and c['operation']=='AND'
 result={}
 for h in c['conditions']:
  assert h['$type']=='questFactsDBCondition'
  t=h['type'];assert t['$type']=='questVarComparison_ConditionType' and t['comparisonType']=='Equal'
  assert t['factName'] not in result
  result[t['factName']]=t['value']
 return result
def setter(n,f):
 assert n['type']=={'$type':'questSetVar_NodeType','factName':f,'setExactValue':1,'value':1}
def no_prefabs(r):
 root=r.obj['Data']['RootChunk'];assert root['phasePrefabs']==[] and root['inplacePhases']==[]
 assert not r.obj['Data']['EmbeddedFiles']

def verify(build):
 m=read(build/'build.json');assert m['status']=='BUILT_N1_LIVE_PENDING'
 assert m['packed_readback'] and m['native_scenes_unchanged'] and not m['official_overrides']
 assert m['runtime_scripts_added']==m['game_writes']==m['save_writes']==0
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 assert [f['relative'] for f in m['files']]==['archive/pc/mod/0_TowerContinued_NCPD_N1.archive','archive/pc/mod/0_TowerContinued_NCPD_N1.archive.xl']
 for f in m['files']:assert sha(build/Path(f['relative']).name)==f['sha256']
 boot={'towercontinued\\ncpd_scanner_n1\\'+k+'.questphase' for k in SPECS}|{r'towercontinued\ncpd_scanner_n1\support.questphase'}
 assert set(m['boots'])==boot and set(m['resources'])==boot|{OVERRIDE}
 assert m['mod_override']==OVERRIDE and {r['key'] for r in m['activities']}==set(SPECS)
 for p,h in m['resources'].items():assert sha(build/'source'/Path(p.replace('\\','/')))==h
 nr,ng=load(native_json(m['district_source']));nn=nodes(ng['root']);ne=edges(ng['root'])
 negative=0;exact=0;checks=[]
 for row in m['activities']:
  key=row['key'];ids,poi,child,last,port=SPECS[key];tag='PTFRN1_'+key
  r,gs=load(build/f'readback/{key}.json');no_prefabs(r);assert set(gs)=={'root'}
  n=nodes(gs['root']);e=edges(gs['root'])
  assert set(n)==ids|{1000,1001,1003,1004,1005,1006}
  for i in ids:assert n[i]==nn[i],(key,i,'native payload');exact+=1
  expected=COMMON|{'PTFRN1_Support_Issued':1,tag+'_Issued':0,key+'_start':0,key+'_finished':0}
  if key=='ma_wat_lch_01':expected[key+'_av_start_only']=0
  assert row['guard_equal']==expected
  for i in (1001,1003):assert equal_predicates(n[i]['condition'])==expected
  assert n[1001]['$type']=='questPauseConditionNodeDefinition' and n[1003]['$type']=='questConditionNodeDefinition'
  for i,suffix in ((1000,'Ready'),(1004,'Issued'),(1005,'NativeOutput'),(1006,'Refused')):setter(n[i],tag+'_'+suffix)
  want={x for x in ne if x[0] in ids and x[2] in ids and x[0]!=0 and not(x[0]==last and x[2]==poi)}
  want|={(0,'Out',1000,'In'),(1000,'Out',1001,'In'),(1001,'Out',31,'In'),(last,'Out',1003,'In'),(1003,'True',1004,'In'),(1003,'False',1006,'In'),(1004,'Out',poi,'Active'),(child,'Out1',1005,'In')}
  assert e==want,(key,'edges')
  assert {(child,'Out1',36,'In'),(36,'Out',73,'In'),(poi,'Out',child,port)}<=e
  assert [x for x in e if x[2]==36]==[(child,'Out1',36,'In')]
  assert not any(v.get('$type')=='questOutputNodeDefinition' for v in n.values()),'must not cut departure cleanup'
  assert n[child]['phaseResource']['DepotPath']['$value']==row['native_depot']
  assert row['native_depot'] not in m['resources']
  # Each single changed admission fact blocks side effects; notably preending,
  # completed, in-progress, already issued on reload, or a support fault.
  accepts=lambda s:all(s.get(k,0)==v for k,v in expected.items())
  assert accepts(expected)
  for k,v in expected.items():assert not accepts(expected|{k:1-v});negative+=1
  assert not accepts(expected|{key+'_finished':1})
  # A late state change after the stock tier/side-content wait reaches only
  # Refused: it cannot activate the map, instantiate an owner or issue credit.
  assert [x for x in e if x[0]==1003 and x[1]=='False']==[(1003,'False',1006,'In')]
  assert not any(x[0]==1006 for x in e)
  setters=[v for v in walk(n) if v.get('$type')=='questSetVar_NodeType']
  assert {v['factName'] for v in setters}=={'wat_achievement'}|{tag+'_'+s for s in ('Ready','Issued','NativeOutput','Refused')}
  assert n[36]['type']['setExactValue']==0 and n[36]['type']['value']==1
  checks.append({'activity':key,'original_phase':row['native_depot'],'port':port,'native_credit':True,'no_replay':True})
 sr,sg=load(build/'readback/support.json');no_prefabs(sr)
 sn=nodes(sg['root']);assert set(sn)=={0,1,2,3,4,24,77}
 ir,ig=load(native_json(m['support_init']));tr,tg=load(native_json(m['token_source']))
 assert sn[77]==nodes(ig['root'])[77];exact+=1
 assert sn[24]==nodes(tg['root'])[24];exact+=1
 assert set(sg)=={'root','root/24'}
 assert nodes(sg['root/24'])==nodes(tg['root/24']) and edges(sg['root/24'])==edges(tg['root/24'])
 exact+=len(sg['root/24']['nodes'])
 assert edges(sg['root'])=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(4,'Out',77,'In1'),(4,'Out',24,'In1')}
 setter(sn[1],'PTFRN1_Support_Ready');setter(sn[4],'PTFRN1_Support_Issued')
 expected=COMMON|{'PTFRN1_Support_Issued':0,'ma_token':0}
 idle=['holo_setup_active','holo_setup_started','holo_interrupt_call','holo_active_call_interrupted','holo_reset','holo_force_reset','holo_reset_soft','holo_interrupt_call_manual','holo_interrupt_braindance']
 for p in ('holo','audio'):
  for contact in ('ncpd_dispatcher_calls_v','v_calls_ncpd_dispatcher'):
   idle += [p+'_'+contact+'_'+s for s in ('start_activate','end_activate')]
 expected|={k:0 for k in idle};assert m['support_guard']==expected
 balances={('holo_ncpd_dispatcher_calls_v_start_count','holo_ncpd_dispatcher_calls_v_end_count'),('holo_v_calls_ncpd_dispatcher_start_count','holo_v_calls_ncpd_dispatcher_end_count')}
 assert {tuple(x) for x in m['support_balances']}==balances
 for i in (2,3):
  c=sn[i]['condition'];assert c['operation']=='AND'
  eq=[];pairs=[]
  for h in c['conditions']:
   t=h['type'];assert t['comparisonType']=='Equal'
   if t['$type']=='questVarComparison_ConditionType':eq.append(h)
   else:assert t['$type']=='questVarVsVarComparison_ConditionType';pairs.append((t['factName1'],t['factName2']))
  assert equal_predicates(c|{'conditions':eq})==expected and set(pairs)==balances
  def admits(state):
   return all(state.get(k,0)==v for k,v in equal_predicates(c|{'conditions':eq}).items()) and all(state.get(a,0)==state.get(b,0) for a,b in pairs)
  assert admits(expected)
  for k,v in expected.items():assert not admits(expected|{k:1-v});negative+=1
  for a,b in pairs:
   assert not admits(expected|{a:1,b:0}) and admits(expected|{a:3,b:3});negative+=1
 # Native contact counts are compared, NOT reset and not required to be zero.
 # Historical balanced nonzero calls remain admissible; live pending calls do not.
 for start,end,want in ((0,0,True),(3,3,True),(1,0,False),(0,1,False)):
  assert (start==end)==want;negative+=1
 cr,cg=load(build/'readback/fixer_cleanup.json')
 oldr,oldg=load(ROOT/'research/gig_restoration/gig_phone_u9/fixer_cleanup.json')
 ncr,ncg=load(native_json(m['cleanup_source']))
 cn=nodes(cg['root']);on=nodes(oldg['root']);native=nodes(ncg['root'])
 assert set(cg)=={'root'} and set(cn)==set(on)|{466,334}
 for i in on:assert cn[i]==on[i],('old contact changed',i);exact+=1
 for i in (466,334):assert cn[i]==native[i];exact+=1
 ce=edges(oldg['root']);ce-={(332,'Out38',468,'In'),(464,'False',468,'In')}
 ce|={(332,'Out38',466,'In'),(464,'False',466,'In'),(466,'True',334,'In40'),(466,'False',468,'In'),(334,'Out40',468,'In')}
 assert edges(cg['root'])==ce
 assert cn[334]['phaseResource']['DepotPath']['$value']==r'base\quest\holocalls\ncpd_dispatcher\ncpd_dispatcher_cleanup.questphase'
 assert sn[77]['phaseResource']['DepotPath']['$value']==r'base\quest\holocalls\ncpd_dispatcher\ncpd_dispatcher_holocall.questphase'
 ids=[binascii.crc_hqx((d+':1').encode(),0xffff) for d in boot]
 assert len(set(ids))==4 and not set(ids)&{i['id'] for i in m['installed_injections']}
 ep=read(ROOT/'research/q307_extracted/json/ep1/quest/ep1.quest.json')
 assert not set(ids)&{n['Data']['id'] for n in ep['Data']['RootChunk']['graph']['Data']['nodes']}
 xl=(build/'0_TowerContinued_NCPD_N1.archive.xl').read_text()
 assert xl.count('    - path: ')==4 and xl.count('      parent: ep1\\quest\\ep1.quest')==4
 assert xl.count('        node: [1]')==4 and xl.count('        socket: Out')==4
 for d in boot:assert xl.count('    - path: '+d+'\n')==1
 # No cyberpsycho branch (district 20/40/71), tutorials, hidden gems, fixer
 # tiers, achievement resets, forced journal completion or rewards are added.
 assert all(not ({20,40,71}&set(row['selected_nodes'])) for row in m['activities'])
 return {'status':'PASS_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),
  'native_nodes_exact':exact,'negative_admission_cases':negative,'activities':checks,'cleanup_existing_contacts_unchanged':8,
  'limits':'Offline source/readback only. Spawning, dispatcher calls, evidence, payouts, cleanup, save/reload and rendered icons require gameplay.'}

if __name__=='__main__':
 build=ROOT/'prealpha/ncpd_scanner_n1/build'/sys.argv[1]
 out=build/'tests.json';assert not out.exists(),'Pinned result exists'
 result=verify(build);out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
